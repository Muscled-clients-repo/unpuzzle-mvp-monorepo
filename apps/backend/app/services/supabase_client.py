"""
Supabase client service for authentication and database operations.
"""
import os
from typing import Optional, Dict, Any
from supabase import create_client, Client
from supabase.client import ClientOptions
import jwt
from django.conf import settings


class SupabaseService:
    """Service for interacting with Supabase"""
    
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._client:
            self.supabase_url = os.environ.get('SUPABASE_URL')
            self.supabase_anon_key = os.environ.get('SUPABASE_ANON_KEY')
            self.supabase_service_key = os.environ.get('SUPABASE_SERVICE_KEY')
            self.jwt_secret = os.environ.get('SUPABASE_JWT_SECRET')
            
            if not all([self.supabase_url, self.supabase_anon_key]):
                raise ValueError("Supabase credentials not configured")
            
            # Create client with service role for backend operations
            options = ClientOptions(
                auto_refresh_token=True,
                persist_session=False
            )
            
            # Use service role key if available for backend operations
            key = self.supabase_service_key or self.supabase_anon_key
            self._client = create_client(self.supabase_url, key, options)
    
    @property
    def client(self) -> Client:
        """Get Supabase client instance"""
        return self._client
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token and return payload.
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=['HS256'],
                audience='authenticated'
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get user data from Supabase using token.
        
        Args:
            token: JWT token string
            
        Returns:
            User data if valid, None otherwise
        """
        try:
            # Set the auth header for this request
            self._client.auth.set_session(token, token)
            user = self._client.auth.get_user(token)
            return user.dict() if user else None
        except Exception:
            return None
    
    def sign_up(self, email: str, password: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Sign up a new user.
        
        Args:
            email: User email
            password: User password
            metadata: Additional user metadata
            
        Returns:
            Sign up response with user and session
        """
        try:
            response = self._client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": metadata or {}
                }
            })
            return {
                "user": response.user.dict() if response.user else None,
                "session": response.session.dict() if response.session else None
            }
        except Exception as e:
            import traceback
            print(f"[SUPABASE ERROR] Sign up failed: {str(e)}")
            print(f"[SUPABASE ERROR] Type: {type(e).__name__}")
            print(f"[SUPABASE ERROR] Traceback: {traceback.format_exc()}")
            
            # Check if it's a specific database error
            error_msg = str(e).lower()
            if "database" in error_msg or "trigger" in error_msg or "function" in error_msg:
                raise Exception(f"Sign up failed: Database error saving new user")
            else:
                raise Exception(f"Sign up failed: {str(e)}")
    
    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """
        Sign in a user.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Sign in response with user and session
        """
        try:
            response = self._client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return {
                "user": response.user.dict() if response.user else None,
                "session": response.session.dict() if response.session else None
            }
        except Exception as e:
            raise Exception(f"Sign in failed: {str(e)}")
    
    def sign_out(self, token: str) -> bool:
        """
        Sign out a user.
        
        Args:
            token: JWT token string
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._client.auth.set_session(token, token)
            self._client.auth.sign_out()
            return True
        except Exception:
            return False
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token.
        
        Args:
            refresh_token: Refresh token string
            
        Returns:
            New session data
        """
        try:
            response = self._client.auth.refresh_session(refresh_token)
            return {
                "user": response.user.dict() if response.user else None,
                "session": response.session.dict() if response.session else None
            }
        except Exception as e:
            raise Exception(f"Token refresh failed: {str(e)}")
    
    def reset_password_request(self, email: str) -> bool:
        """
        Send password reset email.
        
        Args:
            email: User email
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._client.auth.reset_password_for_email(email)
            return True
        except Exception:
            return False
    
    def update_user(self, token: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user data.
        
        Args:
            token: JWT token string
            updates: Dictionary of updates
            
        Returns:
            Updated user data
        """
        try:
            self._client.auth.set_session(token, token)
            response = self._client.auth.update_user(updates)
            return response.user.dict() if response.user else None
        except Exception as e:
            raise Exception(f"User update failed: {str(e)}")
    
    def sign_in_with_oauth(self, provider: str, redirect_to: str = None) -> Dict[str, Any]:
        """
        Generate OAuth URL for provider authentication.
        
        Args:
            provider: OAuth provider name (google, linkedin, github, facebook, etc.)
            redirect_to: URL to redirect after authentication
            
        Returns:
            OAuth URL and provider information
        """
        try:
            options = {}
            if redirect_to:
                options['redirect_to'] = redirect_to
            
            response = self._client.auth.sign_in_with_oauth({
                "provider": provider,
                "options": options
            })
            
            return {
                "url": response.url,
                "provider": response.provider
            }
        except Exception as e:
            raise Exception(f"OAuth sign in failed: {str(e)}")
    
    def exchange_code_for_session(self, code: str) -> Dict[str, Any]:
        """
        Exchange OAuth authorization code for session.
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            User and session data
        """
        try:
            response = self._client.auth.exchange_code_for_session({
                "auth_code": code
            })
            
            return {
                "user": response.user.dict() if response.user else None,
                "session": response.session.dict() if response.session else None
            }
        except Exception as e:
            raise Exception(f"Code exchange failed: {str(e)}")
    
    def get_user_identities(self, token: str) -> list:
        """
        Get user's linked OAuth identities.
        
        Args:
            token: JWT token string
            
        Returns:
            List of linked OAuth providers
        """
        try:
            self._client.auth.set_session(token, token)
            user = self._client.auth.get_user(token)
            
            if user and user.user and hasattr(user.user, 'identities'):
                return user.user.identities
            return []
        except Exception:
            return []
    
    def unlink_identity(self, token: str, identity_id: str) -> bool:
        """
        Unlink an OAuth identity from user account.
        
        Args:
            token: JWT token string
            identity_id: Identity ID to unlink
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._client.auth.set_session(token, token)
            self._client.auth.unlink_identity({"identity_id": identity_id})
            return True
        except Exception:
            return False


# Singleton instance
supabase_service = SupabaseService()