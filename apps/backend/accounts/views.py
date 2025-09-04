"""
Authentication and user management views.
"""
import time
import logging
import os
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator

from app.services.supabase_client import supabase_service
from .models import UserProfile, Session
from .permissions import PermissionService, RoleConstants
from .serializers import (
    SignUpSerializer,
    SignInSerializer,
    RefreshTokenSerializer,
    PasswordResetSerializer,
    UserProfileSerializer,
    UpdateProfileSerializer
)


def set_auth_cookie(response, access_token):
    """Set secure auth cookie with JWT token"""
    cookie_secure = os.environ.get('COOKIE_SECURE', 'False').lower() == 'true'
    cookie_domain = os.environ.get('COOKIE_DOMAIN', '')
    
    response.set_cookie(
        'auth_token',
        access_token,
        max_age=3600,  # 1 hour
        httponly=True,
        secure=cookie_secure,
        samesite='Lax',
        domain=cookie_domain if cookie_domain else None
    )
    return response


def clear_auth_cookie(response):
    """Clear auth cookie"""
    cookie_domain = os.environ.get('COOKIE_DOMAIN', '')
    
    response.delete_cookie(
        'auth_token',
        domain=cookie_domain if cookie_domain else None
    )
    return response


@api_view(['POST'])
@permission_classes([AllowAny])
def sign_up(request):
    """
    Sign up a new user.
    Creates user in Supabase Auth and UserProfile in database.
    """
    # Debug: Log incoming request data
    print(f"[SIGNUP DEBUG] Request data: {request.data}")
    
    serializer = SignUpSerializer(data=request.data)
    if not serializer.is_valid():
        print(f"[SIGNUP DEBUG] Serializer validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Debug: Log validated data
    print(f"[SIGNUP DEBUG] Validated data: {serializer.validated_data}")
    
    try:
        # Sign up with Supabase
        result = supabase_service.sign_up(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
            metadata={
                'full_name': serializer.validated_data.get('full_name', '')
            }
        )
        
        if not result['user']:
            return Response(
                {'error': 'Sign up failed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get UserProfile (should be created automatically by database trigger)
        try:
            profile = UserProfile.objects.get(supabase_user_id=result['user']['id'])
        except UserProfile.DoesNotExist:
            return Response({
                'error': 'Profile not created automatically. Check database triggers.',
                'user_id': result['user']['id']
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Update profile with full_name if provided
        full_name = serializer.validated_data.get('full_name', '').strip()
        print(f"[SIGNUP DEBUG] Full name to save: '{full_name}'")
        print(f"[SIGNUP DEBUG] Profile before update - full_name: '{profile.full_name}', display_name: '{profile.display_name}'")
        
        if full_name:
            profile.full_name = full_name
            profile.save()
            print(f"[SIGNUP DEBUG] Profile after update - full_name: '{profile.full_name}'")
        else:
            print("[SIGNUP DEBUG] No full_name provided, skipping profile update")
        
        # Assign role to the new user
        role_name = serializer.validated_data.get('role', 'student')
        if role_name == 'instructor':
            # Assign instructor role
            PermissionService.assign_role_to_user(
                user_id=result['user']['id'],
                role_name=RoleConstants.INSTRUCTOR
            )
        else:
            # Default to student role
            PermissionService.assign_role_to_user(
                user_id=result['user']['id'],
                role_name=RoleConstants.STUDENT
            )
        
        # Get updated user profile with optimized query for roles
        profile = UserProfile.objects.prefetch_related(
            'user_roles__role'
        ).get(pk=profile.pk)
        
        # Serialize with roles included (roles are now part of the serializer)
        profile_data = UserProfileSerializer(profile).data
        
        response_data = {
            'user': profile_data,
            'session': result['session'],
            'success': True
        }
        
        response = Response(response_data, status=status.HTTP_201_CREATED)
        
        # Set auth cookie if session contains access token
        if result['session'] and result['session'].get('access_token'):
            response = set_auth_cookie(response, result['session']['access_token'])
        
        return response
        
    except Exception as e:
        return Response(
            {'error': str(e), 'success': False},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def sign_in(request):
    """
    Sign in a user.
    Returns user profile and session tokens.
    """
    serializer = SignInSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Sign in with Supabase
        result = supabase_service.sign_in(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        
        if not result['user']:
            return Response(
                {'error': 'Invalid credentials', 'success': False},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get UserProfile with optimized query (should exist via database trigger)
        try:
            profile = UserProfile.objects.prefetch_related(
                'user_roles__role'
            ).get(supabase_user_id=result['user']['id'])
        except UserProfile.DoesNotExist:
            return Response({
                'error': 'User profile not found. User may not be properly synced.',
                'user_id': result['user']['id'],
                'success': False
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Update last login
        profile.last_login = timezone.now()
        profile.save(update_fields=['last_login'])
        
        response_data = {
            'user': UserProfileSerializer(profile).data,
            'session': result['session'],
            'success': True
        }
        
        response = Response(response_data, status=status.HTTP_200_OK)
        
        # Set auth cookie if session contains access token
        if result['session'] and result['session'].get('access_token'):
            response = set_auth_cookie(response, result['session']['access_token'])
        
        return response
        
    except Exception as e:
        return Response(
            {'error': str(e), 'success': False},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['POST'])
def sign_out(request):
    """
    Sign out the current user.
    Supports both cookie and Bearer token authentication.
    """
    # Get token from cookie first, then fallback to Authorization header
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
    
    # Sign out from Supabase
    success = supabase_service.sign_out(token)
    
    if success:
        response = Response(
            {'message': 'Signed out successfully'},
            status=status.HTTP_200_OK
        )
        # Clear auth cookie
        response = clear_auth_cookie(response)
        return response
    else:
        response = Response(
            {'error': 'Sign out failed'},
            status=status.HTTP_400_BAD_REQUEST
        )
        # Clear cookie even if sign out failed (in case token is invalid)
        response = clear_auth_cookie(response)
        return response


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    Refresh access token using refresh token.
    """
    serializer = RefreshTokenSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        result = supabase_service.refresh_token(
            serializer.validated_data['refresh_token']
        )
        
        if not result['session']:
            return Response(
                {'error': 'Invalid refresh token'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get user profile
        profile = UserProfile.objects.filter(
            supabase_user_id=result['user']['id']
        ).first()
        
        return Response({
            'user': UserProfileSerializer(profile).data if profile else None,
            'session': result['session']
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """
    Send password reset email.
    """
    serializer = PasswordResetSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Send reset email via Supabase
    success = supabase_service.reset_password_request(
        serializer.validated_data['email']
    )
    
    # Always return success to prevent email enumeration
    return Response(
        {'message': 'If the email exists, a reset link has been sent'},
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
def get_profile(request):
    """
    Get current user's profile (optimized with caching).
    Requires authentication.
    """
    logger = logging.getLogger('profile_performance')
    start_time = time.time()
    
    # Debug print to verify the optimized code is running
    print(f"[PROFILE DEBUG] Optimized get_profile called for user request")
    
    # Get user ID from request (set by middleware)
    user_id = getattr(request, 'user_id', None)
    if not user_id:
        print(f"[PROFILE DEBUG] No user_id found in request")
        return Response(
            {'error': 'Not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    print(f"[PROFILE DEBUG] Checking cache for user {user_id}")
    
    # Try cache first for instant response
    cache_key = f"user_profile:{user_id}"
    cached_profile = cache.get(cache_key)
    
    if cached_profile is not None:
        cache_time = (time.time() - start_time) * 1000
        print(f"[PROFILE DEBUG] CACHE HIT! Returning cached data in {cache_time:.2f}ms")
        logger.info(f"Profile cache HIT for user {user_id} - {cache_time:.2f}ms")
        return Response(cached_profile, status=status.HTTP_200_OK)
    
    print(f"[PROFILE DEBUG] CACHE MISS - querying database")
    
    try:
        # Optimized database query - load all related data in one go
        # This prevents N+1 queries by loading subscription and plan in single query
        profile = UserProfile.objects.select_related(
            'subscription',
            'subscription__plan'
        ).prefetch_related(
            'user_roles__role'
        ).get(supabase_user_id=user_id)
        
        # Serialize the profile data (same format as before - no breaking changes)
        profile_data = UserProfileSerializer(profile).data
        
        # Cache the serialized data for 30 minutes (1800 seconds) for better performance
        # This significantly reduces database load since profile data doesn't change often
        cache.set(cache_key, profile_data, 1800)
        
        db_time = (time.time() - start_time) * 1000
        print(f"[PROFILE DEBUG] Database query completed in {db_time:.2f}ms - caching result")
        logger.info(f"Profile cache MISS for user {user_id} - DB query took {db_time:.2f}ms")
        
        return Response(profile_data, status=status.HTTP_200_OK)
        
    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'Profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['PUT', 'PATCH'])
def update_profile(request):
    """
    Update current user's profile.
    Requires authentication.
    """
    # Get user ID from request (set by middleware)
    user_id = getattr(request, 'user_id', None)
    if not user_id:
        return Response(
            {'error': 'Not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        profile = UserProfile.objects.get(supabase_user_id=user_id)
    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'Profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = UpdateProfileSerializer(
        profile,
        data=request.data,
        partial=(request.method == 'PATCH')
    )
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    serializer.save()
    
    # Clear the profile cache since data was updated
    cache_key = f"user_profile:{user_id}"
    cache.delete(cache_key)
    
    logger = logging.getLogger('profile_performance')
    logger.debug(f"Profile cache cleared for user {user_id} after update")
    
    return Response(
        UserProfileSerializer(profile).data,
        status=status.HTTP_200_OK
    )


# ============================================================================
# SESSION MANAGEMENT ENDPOINTS
# ============================================================================

@api_view(['GET'])
def get_user_sessions(request):
    """Get all active sessions for the current user"""
    user_id = getattr(request, 'user_id', None)
    if not user_id:
        return Response(
            {'error': 'Not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        profile = UserProfile.objects.get(supabase_user_id=user_id)
        sessions = Session.objects.filter(
            user=profile,
            is_active=True,
            expires_at__gt=timezone.now()
        ).order_by('-last_activity')
        
        sessions_data = []
        for session in sessions:
            sessions_data.append({
                'id': session.session_id,
                'device_info': session.device_info,
                'ip_address': session.ip_address,
                'location': session.location,
                'last_activity': session.last_activity,
                'created_at': session.created_at,
                'is_current': session.session_id == request.META.get('HTTP_SESSION_ID', '')
            })
        
        return Response({
            'success': True,
            'data': {
                'sessions': sessions_data
            }
        })
        
    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'User profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['DELETE'])
def revoke_session(request, session_id):
    """Revoke a specific user session"""
    user_id = getattr(request, 'user_id', None)
    if not user_id:
        return Response(
            {'error': 'Not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        profile = UserProfile.objects.get(supabase_user_id=user_id)
        session = Session.objects.get(
            user=profile,
            session_id=session_id,
            is_active=True
        )
        
        # Deactivate session
        session.is_active = False
        session.save()
        
        # Also revoke from Supabase if needed
        # This would require implementing session tracking in Supabase
        
        return Response({
            'success': True,
            'message': 'Session revoked successfully'
        })
        
    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'User profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Session.DoesNotExist:
        return Response(
            {'error': 'Session not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
def revoke_all_sessions(request):
    """Revoke all user sessions except the current one"""
    user_id = getattr(request, 'user_id', None)
    if not user_id:
        return Response(
            {'error': 'Not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        profile = UserProfile.objects.get(supabase_user_id=user_id)
        current_session_id = request.META.get('HTTP_SESSION_ID', '')
        
        # Deactivate all sessions except current
        revoked_count = Session.objects.filter(
            user=profile,
            is_active=True
        ).exclude(session_id=current_session_id).update(
            is_active=False
        )
        
        return Response({
            'success': True,
            'message': f'Revoked {revoked_count} sessions successfully'
        })
        
    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'User profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )


# ============================================================================
# ROLE-BASED ACCESS CONTROL ENDPOINTS
# ============================================================================

@api_view(['GET'])
def get_user_roles(request):
    """Get the current user's roles and permissions"""
    user_id = getattr(request, 'user_id', None)
    if not user_id:
        return Response(
            {'error': 'Not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        profile = UserProfile.objects.get(supabase_user_id=user_id)
        roles = profile.user_roles.all()
        
        roles_data = []
        all_permissions = set()
        
        for user_role in roles:
            role = user_role.role
            role_permissions = role.permissions.all()
            
            permissions_list = [perm.name for perm in role_permissions]
            all_permissions.update(permissions_list)
            
            roles_data.append({
                'id': role.id,
                'name': role.name,
                'description': role.description,
                'permissions': permissions_list,
                'assigned_at': user_role.assigned_at
            })
        
        return Response({
            'success': True,
            'data': {
                'roles': roles_data,
                'all_permissions': list(all_permissions)
            }
        })
        
    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'User profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
def assign_user_role(request, user_id):
    """Assign a role to a user (Admin only)"""
    current_user_id = getattr(request, 'user_id', None)
    if not current_user_id:
        return Response(
            {'error': 'Not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Check if current user has admin permissions
    try:
        current_profile = UserProfile.objects.get(supabase_user_id=current_user_id)
        if not current_profile.has_permission('user:manage_roles'):
            return Response(
                {'error': 'Insufficient permissions'},
                status=status.HTTP_403_FORBIDDEN
            )
    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'Current user profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get target user
    try:
        target_profile = UserProfile.objects.get(supabase_user_id=user_id)
    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'Target user not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    role_name = request.data.get('role')
    if not role_name:
        return Response(
            {'error': 'Role name is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from .models import Role, UserRole
        role = Role.objects.get(name=role_name)
        
        # Check if user already has this role
        user_role, created = UserRole.objects.get_or_create(
            user=target_profile,
            role=role,
            defaults={'assigned_by': current_profile}
        )
        
        if created:
            return Response({
                'success': True,
                'message': f'Role {role_name} assigned successfully'
            })
        else:
            return Response({
                'error': 'User already has this role',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Role.DoesNotExist:
        return Response(
            {'error': f'Role {role_name} not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
def check_user_permission(request):
    """Check if the current user has a specific permission"""
    user_id = getattr(request, 'user_id', None)
    if not user_id:
        return Response(
            {'error': 'Not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    permission = request.data.get('permission')
    if not permission:
        return Response(
            {'error': 'Permission name is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        profile = UserProfile.objects.get(supabase_user_id=user_id)
        has_permission = profile.has_permission(permission)
        
        return Response({
            'success': True,
            'has_permission': has_permission,
            'permission': permission
        })
        
    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'User profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
def check_user_role(request):
    """Check if the current user has a specific role"""
    user_id = getattr(request, 'user_id', None)
    if not user_id:
        return Response(
            {'error': 'Not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    role_name = request.data.get('role')
    if not role_name:
        return Response(
            {'error': 'Role name is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        profile = UserProfile.objects.get(supabase_user_id=user_id)
        has_role = profile.has_role(role_name)
        
        return Response({
            'success': True,
            'has_role': has_role,
            'role': role_name
        })
        
    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'User profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def get_csrf_token(request):
    """Get CSRF token for protected requests"""
    user_id = getattr(request, 'user_id', None)
    if not user_id:
        return Response(
            {'error': 'Not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Generate a simple CSRF token (in production, use Django's CSRF framework)
    import secrets
    csrf_token = secrets.token_urlsafe(32)
    
    # Store token in session or cache for verification
    # For now, we'll just return it
    
    return Response({
        'success': True,
        'data': {
            'csrf_token': csrf_token
        }
    })
