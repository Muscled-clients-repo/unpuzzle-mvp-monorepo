"""
Supabase authentication middleware for Django.
Validates JWT tokens from Supabase Auth with optimized caching.
"""
import os
import jwt
import time
import hashlib
import logging
from django.http import JsonResponse
from django.core.cache import cache
from supabase import create_client, Client

logger = logging.getLogger('supabase_auth')


class SupabaseAuthMiddleware:
    """Middleware to authenticate requests using Supabase JWT tokens"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.supabase_url = os.environ.get('SUPABASE_URL')
        self.supabase_anon_key = os.environ.get('SUPABASE_ANON_KEY')
        self.jwt_secret = os.environ.get('SUPABASE_JWT_SECRET')
        
        # JWT Cache settings
        self.jwt_cache_prefix = 'jwt_verified:'
        self.jwt_cache_timeout = 900  # 15 minutes default, will be overridden by token exp
        
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
            '/api/v1/auth/oauth/callback/',  # OAuth callback
            '/api/v1/auth/oauth/providers',  # Get OAuth providers
            '/api/v1/payments/config/stripe/',  # Stripe config endpoint
            '/api/v1/payments/webhooks/stripe/',  # Stripe webhook endpoint
            '/health/',  # Health check
            '/static/',
            '/media/',
            '/admin/',
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
        
        # Try to get cached JWT payload first
        start_time = time.time()
        print(f"[AUTH DEBUG] Starting JWT verification for request")
        
        payload = self._get_cached_jwt_payload(token)
        
        if payload is None:
            try:
                # Verify JWT token (expensive operation)
                jwt_start = time.time()
                logger.debug("JWT cache miss - verifying token")
                print(f"[AUTH DEBUG] JWT cache MISS - verifying token...")
                
                payload = jwt.decode(
                    token,
                    self.jwt_secret,
                    algorithms=['HS256'],
                    audience='authenticated'
                )
                
                jwt_time = (time.time() - jwt_start) * 1000
                print(f"[AUTH DEBUG] JWT verification took {jwt_time:.2f}ms")
                
                # Cache the verified payload
                self._cache_jwt_payload(token, payload)
                
            except jwt.ExpiredSignatureError:
                # Remove expired token from cache if it exists
                self._invalidate_jwt_cache(token)
                response = JsonResponse({'error': 'Token has expired'}, status=401)
                response.delete_cookie('auth_token')
                return response
            except jwt.InvalidTokenError as e:
                # Remove invalid token from cache if it exists  
                self._invalidate_jwt_cache(token)
                response = JsonResponse({'error': f'Invalid token: {str(e)}'}, status=401)
                response.delete_cookie('auth_token')
                return response
        else:
            jwt_cache_time = (time.time() - start_time) * 1000
            print(f"[AUTH DEBUG] JWT cache HIT - using cached payload ({jwt_cache_time:.2f}ms)")
            logger.debug("JWT cache hit - using cached payload")
        
        # Add user info to request
        request.supabase_user = payload
        request.user_id = payload.get('sub')
        
        # Pre-load user permissions and roles for the request (performance optimization)
        preload_start = time.time()
        print(f"[AUTH DEBUG] Starting permission preloading...")
        self._preload_user_permissions(request)
        preload_time = (time.time() - preload_start) * 1000
        print(f"[AUTH DEBUG] Permission preloading took {preload_time:.2f}ms")
        
        # Log performance for monitoring
        auth_time = (time.time() - start_time) * 1000  # Convert to ms
        print(f"[AUTH DEBUG] Total auth middleware time: {auth_time:.2f}ms")
        logger.debug(f"Auth middleware took {auth_time:.2f}ms for user {payload.get('sub')}")
        
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
    
    def _get_token_cache_key(self, token):
        """
        Generate a secure cache key for the JWT token
        """
        # Use SHA256 hash to avoid storing actual token in cache key
        token_hash = hashlib.sha256(token.encode()).hexdigest()[:32]
        return f"{self.jwt_cache_prefix}{token_hash}"
    
    def _get_cached_jwt_payload(self, token):
        """
        Try to get JWT payload from cache
        """
        cache_key = self._get_token_cache_key(token)
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            payload = cached_data.get('payload')
            expires_at = cached_data.get('expires_at', 0)
            
            # Check if token is still valid (not expired)
            current_time = int(time.time())
            if expires_at > current_time:
                return payload
            else:
                # Token expired, remove from cache
                cache.delete(cache_key)
                logger.debug("Cached JWT token expired, removing from cache")
        
        return None
    
    def _cache_jwt_payload(self, token, payload):
        """
        Cache the JWT payload with appropriate TTL
        """
        try:
            cache_key = self._get_token_cache_key(token)
            expires_at = payload.get('exp', 0)
            current_time = int(time.time())
            
            # Calculate cache timeout based on token expiry
            if expires_at > current_time:
                # Cache for the remaining token lifetime or max 15 minutes
                cache_timeout = min(expires_at - current_time, self.jwt_cache_timeout)
                
                cached_data = {
                    'payload': payload,
                    'expires_at': expires_at,
                    'cached_at': current_time
                }
                
                cache.set(cache_key, cached_data, cache_timeout)
                logger.debug(f"JWT payload cached for {cache_timeout} seconds")
            else:
                logger.warning("Attempted to cache expired JWT token")
                
        except Exception as e:
            logger.error(f"Failed to cache JWT payload: {e}")
    
    def _invalidate_jwt_cache(self, token):
        """
        Remove JWT token from cache (used for expired/invalid tokens)
        """
        try:
            cache_key = self._get_token_cache_key(token)
            cache.delete(cache_key)
            logger.debug("JWT token removed from cache")
        except Exception as e:
            logger.error(f"Failed to invalidate JWT cache: {e}")
    
    def _preload_user_permissions(self, request):
        """
        Pre-load user permissions and roles to avoid multiple database queries per request
        """
        try:
            from accounts.permissions import PermissionService
            
            user_id = request.user_id
            if user_id:
                # Load permissions and roles once for the entire request
                # These will be cached, so subsequent calls will be fast
                permissions = PermissionService.get_user_permissions(user_id)
                roles = PermissionService.get_user_roles(user_id)
                
                # Attach to request for fast access in views
                request.user_permissions = set(permissions)  # Use set for O(1) lookups
                request.user_roles = set(roles)
                
                # Add helper methods to request object for convenience
                def has_permission(permission: str) -> bool:
                    return permission in request.user_permissions
                
                def has_any_permission(perms: list) -> bool:
                    return any(perm in request.user_permissions for perm in perms)
                
                def has_all_permissions(perms: list) -> bool:
                    return all(perm in request.user_permissions for perm in perms)
                
                def has_role(role: str) -> bool:
                    return role in request.user_roles
                
                # Attach helper methods to request
                request.has_permission = has_permission
                request.has_any_permission = has_any_permission  
                request.has_all_permissions = has_all_permissions
                request.has_role = has_role
                
                logger.debug(f"Pre-loaded {len(permissions)} permissions and {len(roles)} roles for user {user_id}")
                
        except Exception as e:
            logger.error(f"Failed to preload user permissions: {e}")
            # Set empty permissions as fallback
            request.user_permissions = set()
            request.user_roles = set()
            request.has_permission = lambda perm: False
            request.has_any_permission = lambda perms: False
            request.has_all_permissions = lambda perms: False
            request.has_role = lambda role: False