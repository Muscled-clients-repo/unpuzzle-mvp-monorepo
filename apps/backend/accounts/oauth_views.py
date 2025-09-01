"""
OAuth authentication views for social login providers.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings
import os

from app.services.supabase_client import supabase_service
from .models import UserProfile
from .permissions import PermissionService, RoleConstants
from .serializers import UserProfileSerializer
from .views import set_auth_cookie


SUPPORTED_PROVIDERS = [
    'google',
    'linkedin',
    'github',
    'facebook',
    'twitter',
    'apple',
    'microsoft',
    'gitlab',
    'discord',
    'spotify'
]


@api_view(['POST'])
@permission_classes([AllowAny])
def oauth_sign_in(request):
    """
    Initiate OAuth sign in flow.
    Returns the OAuth provider URL for authentication.
    """
    provider = request.data.get('provider', '').lower()
    redirect_url = request.data.get('redirect_url')
    
    # Validate provider
    if not provider:
        return Response(
            {'error': 'Provider is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if provider not in SUPPORTED_PROVIDERS:
        return Response(
            {
                'error': f'Unsupported provider: {provider}',
                'supported_providers': SUPPORTED_PROVIDERS
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Use frontend URL as redirect if not provided
    if not redirect_url:
        redirect_url = f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/auth/callback"
    
    try:
        # Get OAuth URL from Supabase
        result = supabase_service.sign_in_with_oauth(
            provider=provider,
            redirect_to=redirect_url
        )
        
        return Response({
            'success': True,
            'url': result['url'],
            'provider': result['provider']
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e), 'success': False},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def oauth_callback(request):
    """
    Handle OAuth callback and exchange code for session.
    The database trigger automatically creates UserProfile.
    """
    # Get code from either POST body or GET query params
    code = request.data.get('code') if request.method == 'POST' else request.GET.get('code')
    
    if not code:
        return Response(
            {'error': 'Authorization code is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Exchange code for session
        result = supabase_service.exchange_code_for_session(code)
        
        if not result['user']:
            return Response(
                {'error': 'Failed to authenticate with provider'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_data = result['user']
        session_data = result['session']
        
        # Get UserProfile (created automatically by database trigger)
        try:
            profile = UserProfile.objects.get(supabase_user_id=user_data['id'])
            # Update last login
            profile.last_login = timezone.now()
            
            # Update profile with OAuth provider metadata if fields are empty
            if user_data.get('user_metadata'):
                metadata = user_data['user_metadata']
                updated = False
                
                # Update name if not set
                if not profile.full_name:
                    full_name = metadata.get('full_name') or metadata.get('name')
                    if full_name:
                        profile.full_name = full_name
                        updated = True
                
                # Update avatar if not set
                if not profile.avatar_url:
                    avatar = metadata.get('avatar_url') or metadata.get('picture')
                    if avatar:
                        profile.avatar_url = avatar
                        updated = True
                
                if updated:
                    profile.save()
            else:
                profile.save(update_fields=['last_login'])
                
        except UserProfile.DoesNotExist:
            # Database trigger should create profile, but return error if not
            return Response({
                'error': 'Profile not created. Check database triggers.',
                'user_id': user_data['id']
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Assign default role if user doesn't have one
        if not profile.user_roles.exists():
            PermissionService.assign_role_to_user(
                user_id=user_data['id'],
                role_name=RoleConstants.STUDENT
            )
        
        # Prepare response
        profile.refresh_from_db()
        profile_data = UserProfileSerializer(profile).data
        
        # Add roles
        user_roles = profile.user_roles.select_related('role').values_list('role__name', flat=True)
        profile_data['roles'] = list(user_roles)
        
        response_data = {
            'user': profile_data,
            'session': session_data,
            'success': True
        }
        
        response = Response(response_data, status=status.HTTP_200_OK)
        
        # Set auth cookie
        if session_data and session_data.get('access_token'):
            response = set_auth_cookie(response, session_data['access_token'])
        
        return response
        
    except Exception as e:
        return Response(
            {'error': str(e), 'success': False},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_linked_identities(request):
    """
    Get user's linked OAuth identities.
    Requires authentication.
    """
    # Get user ID from request (set by middleware)
    user_id = getattr(request, 'user_id', None)
    if not user_id:
        return Response(
            {'error': 'Not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Get token from cookie or header
    token = request.COOKIES.get('auth_token')
    if not token:
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    
    if not token:
        return Response(
            {'error': 'No token provided'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        identities = supabase_service.get_user_identities(token)
        
        # Format identities for response
        formatted_identities = []
        for identity in identities:
            formatted_identities.append({
                'id': identity.get('id'),
                'provider': identity.get('provider'),
                'created_at': identity.get('created_at'),
                'updated_at': identity.get('updated_at'),
                'email': identity.get('email'),
                'identity_data': {
                    'email': identity.get('identity_data', {}).get('email'),
                    'name': identity.get('identity_data', {}).get('name') or 
                           identity.get('identity_data', {}).get('full_name'),
                    'avatar_url': identity.get('identity_data', {}).get('avatar_url') or 
                                 identity.get('identity_data', {}).get('picture'),
                    'provider_id': identity.get('identity_data', {}).get('sub')
                }
            })
        
        return Response({
            'success': True,
            'identities': formatted_identities
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e), 'success': False},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def link_identity(request):
    """
    Link a new OAuth identity to existing account.
    Requires authentication.
    """
    # Get user ID from request (set by middleware)
    user_id = getattr(request, 'user_id', None)
    if not user_id:
        return Response(
            {'error': 'Not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    provider = request.data.get('provider', '').lower()
    redirect_url = request.data.get('redirect_url')
    
    # Validate provider
    if not provider:
        return Response(
            {'error': 'Provider is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if provider not in SUPPORTED_PROVIDERS:
        return Response(
            {
                'error': f'Unsupported provider: {provider}',
                'supported_providers': SUPPORTED_PROVIDERS
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Use frontend URL as redirect if not provided
    if not redirect_url:
        redirect_url = f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/settings/linked-accounts"
    
    try:
        # Get OAuth URL for linking
        result = supabase_service.sign_in_with_oauth(
            provider=provider,
            redirect_to=redirect_url
        )
        
        return Response({
            'success': True,
            'url': result['url'],
            'provider': result['provider'],
            'action': 'link'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e), 'success': False},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
def unlink_identity(request, identity_id):
    """
    Unlink an OAuth identity from user account.
    Requires authentication.
    """
    # Get user ID from request (set by middleware)
    user_id = getattr(request, 'user_id', None)
    if not user_id:
        return Response(
            {'error': 'Not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Get token from cookie or header
    token = request.COOKIES.get('auth_token')
    if not token:
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    
    if not token:
        return Response(
            {'error': 'No token provided'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        # Check if user has multiple auth methods before unlinking
        identities = supabase_service.get_user_identities(token)
        
        # Get user profile to check if they have password set
        try:
            profile = UserProfile.objects.get(supabase_user_id=user_id)
            # Check if user has email/password auth (you may need to verify this with Supabase)
            has_password = profile.email is not None
        except UserProfile.DoesNotExist:
            has_password = False
        
        # Prevent unlinking if it's the only auth method
        if len(identities) <= 1 and not has_password:
            return Response(
                {'error': 'Cannot unlink the only authentication method'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        success = supabase_service.unlink_identity(token, identity_id)
        
        if success:
            return Response({
                'success': True,
                'message': 'Identity unlinked successfully'
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Failed to unlink identity'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        return Response(
            {'error': str(e), 'success': False},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_supported_providers(request):
    """
    Get list of supported OAuth providers.
    """
    # You can customize this based on what's configured in Supabase
    providers = []
    
    for provider in SUPPORTED_PROVIDERS:
        provider_info = {
            'id': provider,
            'name': provider.title(),
            'enabled': True  # You can check environment variables to see if configured
        }
        
        # Add provider-specific information
        if provider == 'google':
            provider_info['name'] = 'Google'
            provider_info['icon'] = 'google'
        elif provider == 'linkedin':
            provider_info['name'] = 'LinkedIn'
            provider_info['icon'] = 'linkedin'
        elif provider == 'github':
            provider_info['name'] = 'GitHub'
            provider_info['icon'] = 'github'
        elif provider == 'facebook':
            provider_info['name'] = 'Facebook'
            provider_info['icon'] = 'facebook'
        elif provider == 'twitter':
            provider_info['name'] = 'Twitter/X'
            provider_info['icon'] = 'twitter'
        elif provider == 'microsoft':
            provider_info['name'] = 'Microsoft'
            provider_info['icon'] = 'microsoft'
        elif provider == 'apple':
            provider_info['name'] = 'Apple'
            provider_info['icon'] = 'apple'
        
        providers.append(provider_info)
    
    return Response({
        'success': True,
        'providers': providers
    }, status=status.HTTP_200_OK)