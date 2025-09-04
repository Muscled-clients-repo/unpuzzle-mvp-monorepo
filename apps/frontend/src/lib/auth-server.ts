import { cookies } from 'next/headers'
import { cache } from 'react'

interface UserProfile {
  id: string
  email: string
  role: 'student' | 'instructor' | 'moderator' | 'admin'
  fullName: string
  avatar?: string
  supabaseUserId: string
}

interface Session {
  user: UserProfile
  token: string
}

/**
 * Server-side auth utilities for Next.js App Router
 * These functions can only be used in Server Components
 */

// Get the API base URL from environment
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001'

/**
 * Get the current session from cookies (server-side only)
 * Cached per request to avoid multiple API calls
 */
export const getServerSession = cache(async (): Promise<Session | null> => {
  try {
    console.log('[AUTH-SERVER] Fetching server session...')
    const cookieStore = await cookies()
    
    // Debug: List all cookies
    const allCookies = cookieStore.getAll()
    console.log('[AUTH-SERVER] All cookies found:', allCookies.map(c => `${c.name}=${c.value.substring(0, 10)}...`))
    
    const token = cookieStore.get('auth_token')?.value || cookieStore.get('authToken')?.value

    if (!token) {
      console.log('[AUTH-SERVER] No auth token found in cookies - this is normal for anonymous users')
      console.log('[AUTH-SERVER] Available cookie names:', allCookies.map(c => c.name))
      return null
    }
    
    console.log('[AUTH-SERVER] Auth token found, verifying with backend...')

    // Verify token and get user profile from backend
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/profile/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      // Important: disable Next.js caching for auth requests
      cache: 'no-store'
    })

    if (!response.ok) {
      // Don't log errors for expected auth failures
      if (response.status === 401 || response.status === 403) {
        console.log(`[AUTH-SERVER] Auth failed - token invalid/expired (${response.status})`)
        return null
      }
      // Log other unexpected errors but still return null
      console.warn(`[AUTH-SERVER] Unexpected auth error: ${response.status}`)
      return null
    }

    const userData = await response.json()
    console.log('[AUTH-SERVER] Successfully fetched user profile from backend')
    console.log('[AUTH-SERVER] Raw user data received:', JSON.stringify(userData, null, 2))
    console.log('[AUTH-SERVER] User ID:', userData.id)
    console.log('[AUTH-SERVER] User email:', userData.email)
    console.log('[AUTH-SERVER] User role:', userData.role)
    
    // Extract user data with fallbacks for different backend formats
    const userId = userData.id || userData.user_id || userData.pk || userData.supabase_user_id
    const userEmail = userData.email || userData.email_address
    const userRole = userData.role || userData.user_role || userData.roles?.[0] || 'student'
    const userFullName = userData.full_name || userData.fullName || userData.name || 
                        `${userData.first_name || userData.firstName || ''} ${userData.last_name || userData.lastName || ''}`.trim() || 'User'
    const userAvatar = userData.avatar || userData.avatar_url || userData.picture
    const supabaseUserId = userData.supabase_user_id || userData.supabaseUserId || userId
    
    console.log('[AUTH-SERVER] Extracted user data:')
    console.log('[AUTH-SERVER] - ID:', userId)
    console.log('[AUTH-SERVER] - Email:', userEmail)
    console.log('[AUTH-SERVER] - Role:', userRole)
    console.log('[AUTH-SERVER] - Full Name:', userFullName)
    console.log('[AUTH-SERVER] - Supabase User ID:', supabaseUserId)
    
    // Validate required fields
    if (!userId || !userEmail) {
      console.warn('[AUTH-SERVER] Invalid user data received from auth endpoint - missing id or email')
      console.warn('[AUTH-SERVER] Available fields:', Object.keys(userData))
      return null
    }
    
    const session = {
      user: {
        id: userId,
        email: userEmail,
        role: userRole,
        fullName: userFullName,
        avatar: userAvatar,
        supabaseUserId: supabaseUserId
      },
      token
    }
    
    console.log('[AUTH-SERVER] Session created successfully for user:', session.user.fullName)
    return session
  } catch (error) {
    // Network errors or other unexpected issues
    if (error instanceof Error && !error.message.includes('ECONNREFUSED')) {
      console.error('[AUTH-SERVER] Session fetch error:', error.message)
    } else {
      console.log('[AUTH-SERVER] Backend connection failed (expected during development)')
    }
    return null
  }
})

/**
 * Require authentication - redirects to login if not authenticated
 * Use in Server Components that require auth
 */
export async function requireAuth() {
  const session = await getServerSession()
  
  if (!session) {
    const { redirect } = await import('next/navigation')
    redirect('/login')
  }
  
  return session
}

/**
 * Check if user has specific role
 */
export async function hasRole(role: string | string[]): Promise<boolean> {
  const session = await getServerSession()
  
  if (!session) return false
  
  const roles = Array.isArray(role) ? role : [role]
  return roles.includes(session.user.role)
}

/**
 * Get auth headers for server-side API calls
 */
export async function getAuthHeaders(): Promise<HeadersInit> {
  const session = await getServerSession()
  console.log('[AUTH-SERVER] Getting auth headers for server-side request')
  console.log('[AUTH-SERVER] Session exists:', !!session)
  console.log('[AUTH-SERVER] User ID:', session?.user?.id || 'none')
  
  if (!session) {
    console.log('[AUTH-SERVER] No session - returning basic headers')
    return {
      'Content-Type': 'application/json'
    }
  }
  
  console.log('[AUTH-SERVER] Returning authenticated headers with token')
  return {
    'Authorization': `Bearer ${session.token}`,
    'Content-Type': 'application/json'
  }
}