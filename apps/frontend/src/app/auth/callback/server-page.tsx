import { redirect } from 'next/navigation'
import { cookies } from 'next/headers'
import { oauthService } from '@/services/oauth.service'

interface OAuthCallbackPageProps {
  searchParams: {
    code?: string
    state?: string
    error?: string
    error_description?: string
  }
}

export default async function ServerOAuthCallbackPage({ 
  searchParams 
}: OAuthCallbackPageProps) {
  const { code, state, error, error_description } = searchParams
  
  // Handle OAuth errors
  if (error) {
    console.error('[SSR-OAUTH] OAuth error:', error, error_description)
    // Redirect with error parameter
    redirect(`/login?error=${encodeURIComponent(error_description || 'Authentication failed')}`)
  }
  
  // Validate authorization code
  if (!code) {
    console.error('[SSR-OAUTH] No authorization code received')
    redirect('/login?error=No%20authorization%20code%20received')
  }
  
  try {
    console.log('[SSR-OAUTH] Processing OAuth callback on server side')
    
    // Validate state parameter if present
    if (state && !oauthService.validateState(state)) {
      console.error('[SSR-OAUTH] Invalid state parameter')
      redirect('/login?error=Security%20validation%20failed')
    }
    
    // Exchange code for tokens on the server
    const response = await oauthService.handleCallback(code, state)
    
    if (!response.success || !response.user) {
      console.error('[SSR-OAUTH] OAuth callback failed:', response)
      redirect('/login?error=Authentication%20failed')
    }
    
    console.log('[SSR-OAUTH] OAuth callback successful, setting cookies')
    
    // Set HTTP-only cookies with the token
    const cookieStore = await cookies()
    
    if (response.session?.access_token) {
      // Set the auth token cookie with the same name as other auth flows
      cookieStore.set('auth_token', response.session.access_token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 * 7, // 7 days
        path: '/'
      })
      
      // Also set refresh token if available
      if (response.session.refresh_token) {
        cookieStore.set('refresh_token', response.session.refresh_token, {
          httpOnly: true,
          secure: process.env.NODE_ENV === 'production',
          sameSite: 'lax',
          maxAge: 60 * 60 * 24 * 30, // 30 days
          path: '/'
        })
      }
    }
    
    // Clear OAuth session data
    oauthService.clearOAuthSession()
    
    // Determine redirect URL based on user role
    const userRole = response.user.roles?.[0] || 'student'
    const isInstructor = userRole === 'instructor'
    const redirectPath = isInstructor ? '/instructor' : '/student'
    
    console.log('[SSR-OAUTH] Redirecting user to:', redirectPath)
    
    // Redirect to appropriate dashboard
    redirect(redirectPath)
    
  } catch (error) {
    console.error('[SSR-OAUTH] Server-side OAuth processing failed:', error)
    
    // Redirect with error
    const errorMessage = error instanceof Error ? error.message : 'Authentication failed'
    redirect(`/login?error=${encodeURIComponent(errorMessage)}`)
  }
}