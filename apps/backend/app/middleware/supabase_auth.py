"""
Supabase authentication middleware for Django.
Validates JWT tokens from Supabase Auth.
"""
import os
import jwt
from django.http import JsonResponse
from supabase import create_client, Client


class SupabaseAuthMiddleware:
    """Middleware to authenticate requests using Supabase JWT tokens"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.supabase_url = os.environ.get('SUPABASE_URL')
        self.supabase_anon_key = os.environ.get('SUPABASE_ANON_KEY')
        self.jwt_secret = os.environ.get('SUPABASE_JWT_SECRET')
        
        if self.supabase_url and self.supabase_anon_key:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_anon_key)
        else:
            self.supabase = None
    
    def __call__(self, request):
        # Skip auth for public endpoints
        public_paths = [
            '/api/v1/auth/signup',
            '/api/v1/auth/register',  # Alias for signup
            '/api/v1/auth/signin',
            '/api/v1/auth/login',  # Alias for signin
            '/api/v1/auth/refresh',
            '/api/v1/auth/refresh-token',  # Alternative naming
            '/api/v1/auth/reset-password',
            '/api/v1/auth/oauth/signin',  # OAuth sign in
            '/api/v1/auth/oauth/callback',  # OAuth callback
            '/api/v1/auth/oauth/providers',  # Get OAuth providers
            '/api/v1/payments/config/stripe/',  # Stripe config endpoint
            '/api/v1/payments/webhooks/stripe/',  # Stripe webhook endpoint
            '/health/',  # Health check
            '/static/',
            '/media/',
        ]
        
        # Add API root endpoint check separately to avoid conflicts
        api_root_exact = ['/api/', '/api']
        
        # Special handling for course endpoints - only specific patterns are public
        import re
        
        # Exact matches for public course endpoints
        course_public_exact = ['/api/v1/courses/', '/api/v1/courses', '/api/v1/courses/recommended/']
        # UUID pattern: 8-4-4-4-12 hexadecimal characters
        course_id_pattern = r'^/api/v1/courses/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/?$'
        course_reviews_pattern = r'^/api/v1/courses/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/reviews/?$'
        
        is_public_course = (
            request.path in course_public_exact or
            re.match(course_id_pattern, request.path) or
            re.match(course_reviews_pattern, request.path)
        )
        
        # Check if this is a public endpoint
        is_public_general = any(request.path.startswith(path) for path in public_paths)
        is_api_root = request.path in api_root_exact
        is_public = is_public_general or is_api_root or is_public_course
        
        if is_public:
            return self.get_response(request)
        
        # Try to get JWT token from multiple sources
        token = self._get_auth_token(request)
        
        if not token:
            return JsonResponse({'error': 'No authorization token provided'}, status=401)
        
        try:
            # Verify JWT token
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=['HS256'],
                audience='authenticated'
            )
            
            # Add user info to request
            request.supabase_user = payload
            request.user_id = payload.get('sub')
            
        except jwt.ExpiredSignatureError:
            response = JsonResponse({'error': 'Token has expired'}, status=401)
            # Clear expired cookie if it exists
            response.delete_cookie('auth_token')
            return response
        except jwt.InvalidTokenError as e:
            response = JsonResponse({'error': f'Invalid token: {str(e)}'}, status=401)
            # Clear invalid cookie if it exists
            response.delete_cookie('auth_token')
            return response
        
        response = self.get_response(request)
        return response
    
    def _get_auth_token(self, request):
        """
        Get authentication token from cookie first, then fallback to Authorization header
        """
        # Priority 1: Check for auth cookie
        cookie_token = request.COOKIES.get('auth_token')
        if cookie_token:
            return cookie_token
        
        # Priority 2: Check Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
        
        return None