"""
WebSocket authentication middleware for Django Channels.
Validates Supabase JWT tokens and attaches user information to the scope.
"""
import logging
import os
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from supabase import create_client, Client
from accounts.models import UserProfile

logger = logging.getLogger(__name__)

# Initialize Supabase client
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    logger.error("Supabase configuration missing!")
    supabase: Client = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


class WebSocketAuthMiddleware:
    """
    Custom middleware that authenticates WebSocket connections using Supabase JWT tokens.
    Token can be passed either in query parameters or in the first message after connection.
    """
    
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Try to get token from query string
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        # Authenticate user if token is provided
        if token:
            user = await self.authenticate_token(token)
            scope['user'] = user
            scope['user_id'] = user.supabase_user_id if hasattr(user, 'supabase_user_id') else None
        else:
            scope['user'] = AnonymousUser()
            scope['user_id'] = None
            
        logger.info(f"WebSocket auth: user_id={scope.get('user_id')}, path={scope.get('path')}")
        
        return await self.app(scope, receive, send)
    
    @database_sync_to_async
    def authenticate_token(self, token):
        """
        Validates the JWT token with Supabase and returns the UserProfile.
        """
        if not supabase:
            logger.error("Supabase client not initialized")
            return AnonymousUser()
            
        try:
            # Verify token with Supabase
            response = supabase.auth.get_user(token)
            
            if not response or not response.user:
                logger.warning("Invalid token - no user returned from Supabase")
                return AnonymousUser()
            
            user_data = response.user
            user_id = user_data.id
            email = user_data.email
            
            # Get or create UserProfile
            try:
                user_profile = UserProfile.objects.get(supabase_user_id=user_id)
                logger.info(f"WebSocket auth successful for {email}")
                return user_profile
            except UserProfile.DoesNotExist:
                # Auto-create profile for authenticated users
                user_profile = UserProfile.objects.create(
                    supabase_user_id=user_id,
                    email=email,
                    email_verified=user_data.email_confirmed_at is not None,
                    status='active'
                )
                logger.info(f"Created new UserProfile for WebSocket user {email}")
                return user_profile
                
        except Exception as e:
            logger.error(f"WebSocket authentication error: {e}")
            return AnonymousUser()


def WebSocketAuthMiddlewareStack(inner):
    """
    Convenience function to wrap the WebSocket auth middleware.
    """
    return WebSocketAuthMiddleware(inner)