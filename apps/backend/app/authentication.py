"""
Custom authentication backend for Django REST Framework that works with Supabase.
This simply uses the user data already validated and attached by SupabaseAuthMiddleware.
"""
import time
from rest_framework.authentication import BaseAuthentication
from django.core.cache import cache
from accounts.models import UserProfile
import logging
import time

logger = logging.getLogger(__name__)


class SupabaseAuthentication(BaseAuthentication):
    """
    Simple authentication class that uses the Supabase user data
    already validated and attached to the request by SupabaseAuthMiddleware.
    
    The middleware handles:
    - JWT validation
    - Token verification with Supabase
    - Attaching user_id and supabase_user to request
    
    This class just retrieves or creates the UserProfile based on that data.
    """
    
    def authenticate(self, request):
        """
        Get the user from request data set by middleware.
        Returns (user, None) tuple if authenticated, or None.
        """
        # If middleware didn't attach user_id, this request wasn't authenticated
        if not hasattr(request, 'user_id') or not request.user_id:
            logger.debug("SupabaseAuth: No user_id in request - not authenticated")
            return None
        
        logger.info(f"SupabaseAuth: Authenticating user_id: {request.user_id}")
        
        # Check if we already have the user profile attached to the request by middleware
        if hasattr(request, '_cached_user_profile'):
            logger.debug(f"SupabaseAuth: Using cached UserProfile from request")
            return (request._cached_user_profile, None)
        
        try:
            # Try to get UserProfile from cache first
            cache_key = f"user_profile_auth:{request.user_id}"
            cached_profile = cache.get(cache_key)
            
            if cached_profile is not None:
                logger.debug(f"SupabaseAuth: Cache HIT for UserProfile {cached_profile.email}")
                # Attach to request for subsequent calls in same request
                request._cached_user_profile = cached_profile
                return (cached_profile, None)
            
            # Cache miss - query database with optimized query
            logger.debug(f"SupabaseAuth: Cache MISS - querying database")
            start_time = time.time()
            
            user_profile = UserProfile.objects.select_related(
                'subscription',
                'subscription__plan'
            ).prefetch_related(
                'user_roles__role'
            ).get(supabase_user_id=request.user_id)
            
            query_time = (time.time() - start_time) * 1000
            logger.debug(f"SupabaseAuth: Database query took {query_time:.2f}ms")
            
            # Cache the profile for 15 minutes
            cache.set(cache_key, user_profile, 900)
            
            # Attach to request for subsequent calls in same request
            request._cached_user_profile = user_profile
            
            logger.info(f"SupabaseAuth: Found and cached UserProfile for {user_profile.email}")
            return (user_profile, None)
            
        except UserProfile.DoesNotExist:
            logger.warning(f"SupabaseAuth: UserProfile not found for user_id: {request.user_id}")
            
            # Auto-create UserProfile for authenticated Supabase users
            if hasattr(request, 'supabase_user') and request.supabase_user:
                supabase_data = request.supabase_user
                email = supabase_data.get('email', '')
                
                logger.info(f"SupabaseAuth: Auto-creating UserProfile for {email}")
                
                # Create minimal profile - let user complete it later
                user_profile = UserProfile.objects.create(
                    supabase_user_id=request.user_id,
                    email=email,
                    email_verified=supabase_data.get('email_confirmed_at') is not None,
                    status='active'
                )
                
                # Cache the newly created profile
                cache_key = f"user_profile_auth:{request.user_id}"
                cache.set(cache_key, user_profile, 900)
                
                # Attach to request
                request._cached_user_profile = user_profile
                
                logger.info(f"SupabaseAuth: Successfully created and cached UserProfile for {email}")
                return (user_profile, None)
            
            # No Supabase data available - can't create profile
            logger.error(f"SupabaseAuth: No supabase_user data to create profile for user_id: {request.user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving user profile: {e}")
            return None