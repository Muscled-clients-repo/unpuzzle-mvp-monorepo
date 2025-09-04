import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'

// Use server-side environment variable for backend URL, not client-side
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001'

export async function GET(request: NextRequest) {
  try {
    console.log('[API-OAUTH] Processing Django OAuth callback in API route')
    
    const searchParams = request.nextUrl.searchParams
    const code = searchParams.get('code')
    const nextUrl = searchParams.get('next') || '/'
    
    console.log('[API-OAUTH] Received parameters:', { 
      hasCode: !!code, 
      nextUrl 
    })
    
    if (!code) {
      console.error('[API-OAUTH] Missing authorization code')
      return NextResponse.redirect(new URL('/?error=missing_code', request.url))
    }
    
    // Get existing cookies to send to Django (for CSRF, etc.)
    const cookieStore = await cookies()
    const cookieHeader = cookieStore.toString()
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    }
    
    // Include cookies for CSRF tokens and Django session
    if (cookieHeader) {
      headers['Cookie'] = cookieHeader
      
      // Extract CSRF token if present and include in headers
      const csrfMatch = cookieHeader.match(/csrftoken=([^;]+)/)
      if (csrfMatch) {
        headers['X-CSRFToken'] = csrfMatch[1]
      }
    }
    
    console.log('[API-OAUTH] Calling Django OAuth callback...')
    
    // Call Django OAuth callback with next parameter
    const djangoUrl = `${API_BASE_URL}/api/v1/auth/oauth/callback/`
    console.log('[API-OAUTH] Making request to Django URL:', djangoUrl)
    
    const response = await fetch(djangoUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        code,
        next: nextUrl,
        provider: 'google',
      }),
      cache: 'no-store',
      credentials: 'omit' // Don't include browser credentials to Django backend
    })
    
    console.log('[API-OAUTH] Django response status:', response.status)
    console.log('[API-OAUTH] Response headers:', Array.from(response.headers.entries()))
    
    // Check content type to see what we're getting
    const contentType = response.headers.get('content-type')
    console.log('[API-OAUTH] Response content type:', contentType)
    
    // If we're getting HTML, something is wrong
    if (contentType?.includes('text/html')) {
      console.error('[API-OAUTH] ERROR: Got HTML response instead of JSON/redirect from Django')
      const bodyText = await response.text()
      console.error('[API-OAUTH] HTML response preview:', bodyText.substring(0, 500))
    }
    
    // Extract Set-Cookie headers from Django response
    const setCookieHeaders = response.headers.getSetCookie?.() || []
    console.log('[API-OAUTH] Set-Cookie headers from Django:', setCookieHeaders)
    
    // Handle successful JSON response from Django
    if (response.ok) {
      // Django should now always return JSON
      const data = await response.json()
      console.log('[API-OAUTH] Django returned success:', { 
        hasUser: !!data.user, 
        hasSession: !!data.session,
        success: data.success,
        redirectUrl: data.redirect_url,
        hasAccessToken: !!data.session?.access_token,
        hasRefreshToken: !!data.session?.refresh_token
      })
      
      // Extract session data
      const session = data.session
      if (!session || !session.access_token) {
        console.error('[API-OAUTH] No access token in session data')
        return NextResponse.redirect(new URL('/?error=no_token', request.url))
      }
      
      // Get the redirect URL from response or use the default
      const redirectPath = data.redirect_url || nextUrl
      console.log('[API-OAUTH] Will redirect to:', redirectPath)
      
      // Create redirect response
      const nextResponse = NextResponse.redirect(
        new URL(redirectPath, request.url),
        { status: 302 }
      )
      
      // First, set cookies from Django response headers
      let authTokenSet = false
      if (setCookieHeaders.length > 0) {
        for (const cookieHeader of setCookieHeaders) {
          console.log('[API-OAUTH] Processing Django cookie:', cookieHeader.substring(0, 50) + '...')
          
          // Parse cookie header: "auth_token=value; Max-Age=3600; HttpOnly; Path=/; SameSite=Lax"
          const [nameValue, ...attributes] = cookieHeader.split(';').map(s => s.trim())
          const [name, value] = nameValue.split('=')
          
          if (name === 'auth_token' && value) {
            authTokenSet = true
            // Parse attributes
            const options: any = {
              httpOnly: true,
              secure: process.env.NODE_ENV === 'production',
              sameSite: 'lax' as const,
              path: '/',
              maxAge: session.expires_in || 3600 // Use session expiry or default 1 hour
            }
            
            // Apply Django's cookie settings
            attributes.forEach(attr => {
              const lowerAttr = attr.toLowerCase()
              if (lowerAttr.startsWith('max-age=')) {
                options.maxAge = parseInt(attr.split('=')[1])
              } else if (lowerAttr.startsWith('domain=')) {
                options.domain = attr.split('=')[1]
              } else if (lowerAttr === 'secure') {
                options.secure = true
              }
            })
            
            console.log('[API-OAUTH] Setting auth_token cookie from Django with options:', options)
            nextResponse.cookies.set(name, value, options)
          }
        }
      }
      
      // If Django didn't set auth_token, set it from session data
      if (!authTokenSet && session.access_token) {
        console.log('[API-OAUTH] Django did not set auth_token, setting from session data')
        nextResponse.cookies.set('auth_token', session.access_token, {
          httpOnly: true,
          secure: process.env.NODE_ENV === 'production',
          sameSite: 'lax',
          path: '/',
          maxAge: session.expires_in || 3600
        })
      }
      
      // Also store refresh token if available (in a separate secure cookie)
      if (session.refresh_token) {
        console.log('[API-OAUTH] Setting refresh_token cookie')
        nextResponse.cookies.set('refresh_token', session.refresh_token, {
          httpOnly: true,
          secure: process.env.NODE_ENV === 'production',
          sameSite: 'lax',
          path: '/',
          maxAge: 30 * 24 * 60 * 60 // 30 days
        })
      }
      
      console.log('[API-OAUTH] Authentication successful, redirecting...')
      return nextResponse
    }
    
    // Handle error response
    console.error('[API-OAUTH] Django returned error:', response.status)
    const errorText = await response.text()
    console.error('[API-OAUTH] Error details:', errorText)
    
    return NextResponse.redirect(new URL('/?error=oauth_failed', request.url))
    
  } catch (error: any) {
    console.error('[API-OAUTH] OAuth callback processing failed:', error)
    return NextResponse.redirect(new URL('/?error=oauth_error', request.url))
  }
}