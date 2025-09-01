"""
Accounts app URL configuration
"""
from django.urls import path
from . import views, webhooks, oauth_views

app_name = 'accounts'

urlpatterns = [
    # Authentication endpoints (with trailing slash)
    path('signup/', views.sign_up, name='signup'),
    path('signin/', views.sign_in, name='signin'),
    path('signout/', views.sign_out, name='signout'),
    path('refresh/', views.refresh_token, name='refresh'),
    path('reset-password/', views.reset_password, name='reset_password'),
    
    # OAuth endpoints
    path('oauth/signin/', oauth_views.oauth_sign_in, name='oauth_signin'),
    path('oauth/callback/', oauth_views.oauth_callback, name='oauth_callback'),
    path('oauth/identities/', oauth_views.get_linked_identities, name='get_linked_identities'),
    path('oauth/identities/link/', oauth_views.link_identity, name='link_identity'),
    path('oauth/identities/<str:identity_id>/unlink/', oauth_views.unlink_identity, name='unlink_identity'),
    path('oauth/providers/', oauth_views.get_supported_providers, name='get_supported_providers'),
    
    # Authentication endpoints (without trailing slash for frontend compatibility)
    path('signup', views.sign_up, name='signup_no_slash'),
    path('register', views.sign_up, name='register_alias'),  # Alias for signup
    path('signin', views.sign_in, name='signin_no_slash'),
    path('login', views.sign_in, name='login_alias'),  # Alias for signin
    path('signout', views.sign_out, name='signout_no_slash'),
    path('logout', views.sign_out, name='logout_alias'),  # Alias for signout
    path('refresh', views.refresh_token, name='refresh_no_slash'),
    path('refresh-token', views.refresh_token, name='refresh_token_alias'),  # Alternative naming
    path('reset-password', views.reset_password, name='reset_password_no_slash'),
    
    # Profile endpoints (with trailing slash)
    path('profile/', views.get_profile, name='get_profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    
    # Profile endpoints (without trailing slash for frontend compatibility)
    path('profile', views.get_profile, name='get_profile_no_slash'),
    path('profile/update', views.update_profile, name='update_profile_no_slash'),
    
    # Session management endpoints
    path('sessions/', views.get_user_sessions, name='get_user_sessions'),
    path('sessions/<str:session_id>/', views.revoke_session, name='revoke_session'), 
    path('sessions/revoke-all/', views.revoke_all_sessions, name='revoke_all_sessions'),
    
    # Role-Based Access Control endpoints
    path('roles/', views.get_user_roles, name='get_user_roles'),
    path('roles/assign/<str:user_id>/', views.assign_user_role, name='assign_user_role'),
    path('permissions/check/', views.check_user_permission, name='check_user_permission'),
    path('roles/check/', views.check_user_role, name='check_user_role'),
    path('csrf-token/', views.get_csrf_token, name='get_csrf_token'),
    
    # Webhook endpoints
    path('webhooks/auth/', webhooks.supabase_auth_webhook, name='auth_webhook'),
    path('webhooks/health/', webhooks.webhook_health, name='webhook_health'),
]