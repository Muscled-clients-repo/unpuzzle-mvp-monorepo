'use server'

import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

/**
 * Server action to handle logout
 * Clears HTTP-only cookies and redirects to home page
 */
export async function logoutAction() {
  const cookieStore = await cookies()
  
  // Clear auth cookies
  cookieStore.delete('auth_token')
  cookieStore.delete('authToken')
  cookieStore.delete('refresh_token')
  
  console.log('[LOGOUT-ACTION] Cleared authentication cookies')
  
  // Redirect to home page
  redirect('/')
}