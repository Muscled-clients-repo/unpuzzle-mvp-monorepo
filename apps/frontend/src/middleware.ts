import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

/**
 * Middleware for handling authentication and routing
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const authToken = request.cookies.get('auth_token')?.value || request.cookies.get('authToken')?.value
  
  // Protected routes that require authentication
  const protectedPaths = [
    '/student/courses',
    '/student/reflections',
    '/instructor',
    '/moderator',
    '/admin'
  ]
  
  // Check if the current path requires authentication
  const isProtectedPath = protectedPaths.some(path => pathname.startsWith(path))
  
  // Redirect to login if accessing protected route without auth
  if (isProtectedPath && !authToken) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('from', pathname)
    return NextResponse.redirect(loginUrl)
  }
  
  // Handle auth token from localStorage to cookie migration
  // This helps with SSR auth by ensuring the token is in cookies
  const response = NextResponse.next()
  
  // If we have a token in the Authorization header but not in cookies,
  // set it as a cookie for SSR to work
  const authHeader = request.headers.get('authorization')
  if (authHeader && !authToken) {
    const token = authHeader.replace('Bearer ', '')
    response.cookies.set('auth_token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 7 // 7 days
    })
  }
  
  return response
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (public directory)
     */
    '/((?!api|_next/static|_next/image|favicon.ico|public).*)',
  ],
}