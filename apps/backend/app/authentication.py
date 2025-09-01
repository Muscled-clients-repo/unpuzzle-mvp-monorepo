"""
Custom authentication backend for Django REST Framework that works with Supabase.
This simply uses the user data already validated and attached by SupabaseAuthMiddleware.
"""
from rest_framework.authentication import BaseAuthentication
from accounts.models import UserProfile
import logging

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
        
        try:
            # Try to get existing UserProfile
            user_profile = UserProfile.objects.get(supabase_user_id=request.user_id)
            logger.info(f"SupabaseAuth: Found UserProfile for {user_profile.email}")
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
                
                logger.info(f"SupabaseAuth: Successfully created UserProfile for {email}")
                return (user_profile, None)
            
            # No Supabase data available - can't create profile
            logger.error(f"SupabaseAuth: No supabase_user data to create profile for user_id: {request.user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving user profile: {e}")
            return None