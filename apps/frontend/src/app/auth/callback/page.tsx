import { redirect } from 'next/navigation'

// Server-side OAuth callback handler - delegates to API route for cookie handling
export default async function OAuthCallbackPage({
  searchParams,
}: {
  searchParams: { [key: string]: string | string[] | undefined }
}) {
  console.log('[SERVER-OAUTH] OAuth callback page accessed')
  
  // Get code from URL parameters
  const code = searchParams.code as string
  
  if (!code) {
    console.error('[SERVER-OAUTH] No authorization code found in callback URL')
    redirect('/?error=missing_code')
  }
  
  // Get next URL from search parameters
  let nextUrl = (searchParams.next as string) || '/'
  
  // Avoid redirect loops - don't redirect to auth pages after successful auth
  const authPages = ['/login', '/signup', '/auth/callback', '/sign-in', '/sign-up']
  const isAuthPage = authPages.some(page => nextUrl.includes(page))
  
  if (isAuthPage) {
    console.log('[SERVER-OAUTH] Next URL is auth page, using home page instead:', nextUrl)
    nextUrl = '/'
  }
  
  console.log('[SERVER-OAUTH] Redirecting to API route for cookie handling...')
  
  // Redirect to API route that can properly handle cookies
  const apiUrl = `/api/auth/oauth-callback?code=${encodeURIComponent(code)}&next=${encodeURIComponent(nextUrl)}`
  redirect(apiUrl)
}