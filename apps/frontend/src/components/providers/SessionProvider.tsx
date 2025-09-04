'use client'

import { createContext, useContext, ReactNode, useEffect } from 'react'
import { useAppStore } from '@/stores/app-store'
import { User, Subscription } from '@/types/domain'

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

interface SessionContextValue {
  session: Session | null
}

const SessionContext = createContext<SessionContextValue | undefined>(undefined)

export function SessionProvider({ 
  children, 
  session 
}: { 
  children: ReactNode
  session: Session | null 
}) {
  const setUser = useAppStore(state => state.setUser)
  
  // Sync SSR session data to Zustand store on mount and when session changes
  useEffect(() => {
    if (session?.user) {
      // Use supabaseUserId as the primary ID since that's what comes from server
      const userId = session.user.supabaseUserId || session.user.id
      
      // Create a User object that matches the domain type
      const user: User = {
        id: userId,
        email: session.user.email,
        name: session.user.fullName,
        avatar: session.user.avatar,
        role: session.user.role,
        subscription: {
          id: `sub_${userId}`,
          userId: userId,
          plan: 'free',
          status: 'trial',
          currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
          aiCredits: 100,
          aiCreditsUsed: 0,
          maxCourses: 3,
          features: ['basic_ai', 'limited_courses']
        },
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
      
      // Update Zustand store with SSR user data
      setUser(user)
      
      // NOTE: We now use HTTP-only cookies for security instead of localStorage
      // No need to store tokens client-side - they are handled by server cookies
      console.log('[SESSION-PROVIDER] User session synced from SSR cookies')
    } else {
      // Clear store if no session or no user
      setUser(null)
      console.log('[SESSION-PROVIDER] No session found, user cleared from store')
    }
  }, [session, setUser])
  
  return (
    <SessionContext.Provider value={{ session }}>
      {children}
    </SessionContext.Provider>
  )
}

export function useSession() {
  const context = useContext(SessionContext)
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider')
  }
  return context
}