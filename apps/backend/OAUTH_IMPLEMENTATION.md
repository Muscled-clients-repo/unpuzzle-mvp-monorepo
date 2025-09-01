# OAuth Implementation Guide

## Overview
OAuth authentication has been successfully implemented for the Unpuzzle MVP backend, supporting multiple social login providers through Supabase Auth.

## Supported Providers
- Google
- LinkedIn  
- GitHub
- Facebook
- Twitter/X
- Apple
- Microsoft
- GitLab
- Discord
- Spotify

## Implementation Details

### 1. Backend Components

#### Supabase Service (`app/services/supabase_client.py`)
- `sign_in_with_oauth()` - Generate OAuth URL for provider authentication
- `exchange_code_for_session()` - Exchange authorization code for session
- `get_user_identities()` - Get user's linked OAuth identities
- `unlink_identity()` - Unlink OAuth identity from account

#### OAuth Views (`accounts/oauth_views.py`)
- `oauth_sign_in` - Initiate OAuth flow, returns provider URL
- `oauth_callback` - Handle OAuth callback, exchange code for session
- `get_linked_identities` - Get user's linked social accounts
- `link_identity` - Link new OAuth provider to existing account
- `unlink_identity` - Remove OAuth provider from account
- `get_supported_providers` - List all supported OAuth providers

#### URLs (`accounts/urls.py`)
OAuth endpoints are available under `/api/v1/auth/`:
- `POST /api/v1/auth/oauth/signin/` - Start OAuth flow
- `POST/GET /api/v1/auth/oauth/callback/` - Handle OAuth callback
- `GET /api/v1/auth/oauth/providers/` - Get supported providers
- `GET /api/v1/auth/oauth/identities/` - Get linked identities (requires auth)
- `POST /api/v1/auth/oauth/identities/link/` - Link new provider (requires auth)
- `DELETE /api/v1/auth/oauth/identities/<id>/unlink/` - Unlink provider (requires auth)

### 2. Database Integration
- UserProfile is automatically created via database trigger when user signs up with OAuth
- Profile fields (full_name, avatar_url) are populated from OAuth provider metadata
- Default student role is assigned to new OAuth users

## Frontend Integration

### 1. Initiate OAuth Sign In
```javascript
// Request
POST /api/v1/auth/oauth/signin/
{
  "provider": "google",
  "redirect_url": "http://localhost:3000/auth/callback"  // optional
}

// Response
{
  "success": true,
  "url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "provider": "google"
}

// Redirect user to the returned URL
window.location.href = response.url;
```

### 2. Handle OAuth Callback
After user authorizes, they're redirected back with a code:
```javascript
// Your callback page receives: /auth/callback?code=xyz123

// Exchange code for session
POST /api/v1/auth/oauth/callback/
{
  "code": "xyz123"
}

// Response
{
  "success": true,
  "user": {
    "supabase_user_id": "...",
    "email": "user@example.com",
    "full_name": "John Doe",
    "avatar_url": "https://...",
    "roles": ["student"]
  },
  "session": {
    "access_token": "...",
    "refresh_token": "...",
    "expires_in": 3600
  }
}
```

### 3. Get Supported Providers
```javascript
GET /api/v1/auth/oauth/providers/

// Response
{
  "success": true,
  "providers": [
    {
      "id": "google",
      "name": "Google",
      "enabled": true,
      "icon": "google"
    },
    // ... other providers
  ]
}
```

## Supabase Configuration

### Required Setup in Supabase Dashboard

1. **Enable OAuth Providers**
   - Go to Authentication > Providers in Supabase Dashboard
   - Enable desired providers (Google, LinkedIn, etc.)
   
2. **Configure OAuth Credentials**
   For each provider, you need:
   - Client ID
   - Client Secret
   - Authorized redirect URLs

3. **OAuth Redirect URLs**
   Add these to each provider's authorized redirects:
   - `https://dndfnoyltoqzrbnuxafz.supabase.co/auth/v1/callback`
   - Your frontend callback URL (e.g., `http://localhost:3000/auth/callback`)

### Provider-Specific Setup

#### Google
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials
3. Add authorized redirect URIs
4. Copy Client ID and Secret to Supabase

#### LinkedIn
1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Create an app
3. Add OAuth 2.0 settings
4. Copy Client ID and Secret to Supabase

#### GitHub
1. Go to GitHub Settings > Developer settings > OAuth Apps
2. Create new OAuth App
3. Set authorization callback URL
4. Copy Client ID and Secret to Supabase

## Testing

Run the test script to verify OAuth implementation:
```bash
python test_oauth.py
```

This tests:
- Getting supported providers
- Initiating OAuth sign in
- Invalid provider handling
- Callback without code error handling

## Security Considerations

1. **HTTPS Required**: OAuth callbacks must use HTTPS in production
2. **State Parameter**: Supabase handles CSRF protection via state parameter
3. **Token Storage**: Access tokens are set as httpOnly cookies
4. **Profile Sync**: Database triggers ensure UserProfile exists for all users
5. **Multiple Auth Methods**: Users can link multiple OAuth providers to one account

## Troubleshooting

### Common Issues

1. **"Profile not created" error**
   - Check database triggers are properly set up
   - Verify UserProfile table has trigger for auth.users inserts

2. **OAuth URL not generated**
   - Verify provider is enabled in Supabase Dashboard
   - Check OAuth credentials are correctly configured

3. **Callback fails**
   - Ensure redirect URL is whitelisted in provider settings
   - Verify authorization code is being passed correctly

4. **User can't unlink last auth method**
   - System prevents unlinking the only authentication method
   - User must have either password or another OAuth provider linked

## Next Steps

1. Configure OAuth providers in Supabase Dashboard
2. Update frontend to handle OAuth flow
3. Add provider-specific icons/branding
4. Implement account linking UI
5. Add OAuth provider management in user settings