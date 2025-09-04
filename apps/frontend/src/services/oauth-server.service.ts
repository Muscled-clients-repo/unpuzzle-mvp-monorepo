/**
 * Server-side OAuth service for handling OAuth callbacks
 * Uses cookies instead of localStorage for server-side compatibility
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001'

interface OAuthCallbackResponse {
  success: boolean
  user?: {
    id: string
    email: string
    full_name?: string
    name?: string
    first_name?: string
    last_name?: string
    avatar_url?: string
    roles?: string[]
    role?: string
    supabase_user_id?: string
  }
  session?: {
    access_token: string
    refresh_token?: string
    expires_at?: number
    token_type?: string
  }
  error?: string
  redirect?: string
}

export class OAuthServerService {
  /**
   * Handle OAuth callback on server side
   * No localStorage usage - pure server-side implementation
   */
  async handleCallback(code: string, state?: string, nextUrl?: string, cookieHeader?: string): Promise<OAuthCallbackResponse> {
    try {
      console.log('[OAUTH-SERVER] Processing OAuth callback with code:', code?.substring(0, 10) + '...')
      
      // Build headers - include cookies for CSRF tokens and session
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      }
      
      // Include cookies if provided (for CSRF tokens and Django session)
      if (cookieHeader) {
        headers['Cookie'] = cookieHeader
        console.log('[OAUTH-SERVER] Including cookies for CSRF/session:', cookieHeader.substring(0, 100) + '...')
        
        // Extract CSRF token if present and include in headers
        const csrfMatch = cookieHeader.match(/csrftoken=([^;]+)/)
        if (csrfMatch) {
          headers['X-CSRFToken'] = csrfMatch[1]
          console.log('[OAUTH-SERVER] Including CSRF token in headers')
        }
      }
      
      // Use the correct OAuth callback endpoint
      const endpointPath = '/api/v1/auth/oauth/callback/'
      const response = await fetch(`${API_BASE_URL}${endpointPath}`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          code,
          state,
          next: nextUrl, // Send the next parameter to Django
          provider: 'google', // You can make this dynamic if needed
        }),
        cache: 'no-store' // Don't cache auth requests
      })

      console.log('[OAUTH-SERVER] Backend response status:', response.status)
      
      // Handle redirect response from Django
      if (response.status >= 300 && response.status < 400) {
        const redirectLocation = response.headers.get('Location')
        console.log('[OAUTH-SERVER] Django returned redirect to:', redirectLocation)
        
        if (redirectLocation) {
          // Django handled the redirect - redirect the browser
          console.log('[OAUTH-SERVER] Following Django redirect...')
          window.location.href = redirectLocation
          return {
            success: true,
            redirect: redirectLocation
          }
        }
      }

      if (!response.ok) {
        const errorText = await response.text()
        console.error('[OAUTH-SERVER] Backend error response:', errorText)
        
        return {
          success: false,
          error: `Backend returned ${response.status}: ${errorText}`
        }
      }

      // Check if response is JSON or HTML (redirect page)
      const contentType = response.headers.get('content-type')
      if (contentType && contentType.includes('text/html')) {
        console.log('[OAUTH-SERVER] Django returned HTML (likely a redirect page)')
        // This might be a redirect page, follow it
        window.location.href = response.url
        return {
          success: true,
          redirect: response.url
        }
      }

      const data = await response.json()
      console.log('[OAUTH-SERVER] Backend response data:', JSON.stringify(data, null, 2))

      // Handle different response formats from backend
      if (data.success === false || data.error) {
        return {
          success: false,
          error: data.error || 'OAuth callback failed'
        }
      }

      // Extract user and session data with flexible field mapping
      const user = data.user || data.profile || data
      const session = data.session || data.tokens || {
        access_token: data.access_token || data.token,
        refresh_token: data.refresh_token,
        expires_at: data.expires_at || data.expires_in
      }

      if (!session.access_token) {
        console.error('[OAUTH-SERVER] No access token in response')
        return {
          success: false,
          error: 'No access token received from server'
        }
      }

      console.log('[OAUTH-SERVER] Successfully processed OAuth callback')
      
      return {
        success: true,
        user,
        session
      }

    } catch (error: any) {
      console.error('[OAUTH-SERVER] OAuth callback failed:', error)
      
      return {
        success: false,
        error: error.message || 'OAuth callback failed'
      }
    }
  }

  /**
   * Validate state parameter (if needed)
   */
  validateState(_state: string): boolean {
    // For now, just return true
    // You can implement proper state validation if your OAuth flow uses it
    return true
  }

  /**
   * Clear OAuth session data (server-side safe)
   */
  clearOAuthSession(): void {
    // On server side, we don't need to clear localStorage
    // This is handled by cookie clearing
    console.log('[OAUTH-SERVER] OAuth session cleared (server-side)')
  }
}

export const oauthServerService = new OAuthServerService()