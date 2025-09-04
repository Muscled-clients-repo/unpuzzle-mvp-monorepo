'use client'

import { useEffect } from 'react'
import { useAppStore } from '@/stores/app-store'

interface DataSyncProviderProps {
  children: React.ReactNode
  initialData?: {
    courses?: any[]
    enrolledCourses?: any[]
    courseProgress?: any
    featuredCourses?: any[]
    platformStats?: any
  }
}

/**
 * DataSyncProvider - Syncs SSR data to Zustand store
 * This component takes data fetched on the server and syncs it to the client-side store
 * ensuring that client components have immediate access to server-fetched data
 */
export function DataSyncProvider({ children, initialData = {} }: DataSyncProviderProps) {
  // Get store actions for syncing data
  const setCourses = useAppStore(state => state.setCourses)
  const setEnrolledCourses = useAppStore(state => state.setEnrolledCourses) 
  const setCourseProgress = useAppStore(state => state.setCourseProgress)
  const setFeaturedCourses = useAppStore(state => state.setFeaturedCourses)
  const setPlatformStats = useAppStore(state => state.setPlatformStats)

  // Sync initial data to store on mount
  useEffect(() => {
    if (initialData.courses) {
      setCourses(initialData.courses)
    }
    
    if (initialData.enrolledCourses) {
      setEnrolledCourses(initialData.enrolledCourses)
    }
    
    if (initialData.courseProgress) {
      setCourseProgress(initialData.courseProgress)
    }
    
    if (initialData.featuredCourses) {
      setFeaturedCourses(initialData.featuredCourses)
    }
    
    if (initialData.platformStats) {
      setPlatformStats(initialData.platformStats)
    }
  }, [
    initialData.courses, 
    initialData.enrolledCourses,
    initialData.courseProgress,
    initialData.featuredCourses,
    initialData.platformStats,
    setCourses,
    setEnrolledCourses,
    setCourseProgress,
    setFeaturedCourses,
    setPlatformStats
  ])

  return <>{children}</>
}

/**
 * Hook to use SSR data in client components
 * This ensures components can access server-fetched data from the store
 */
export function useSSRData() {
  const courses = useAppStore(state => state.courses)
  const enrolledCourses = useAppStore(state => state.enrolledCourses)
  const courseProgress = useAppStore(state => state.courseProgress)
  const currentCourse = useAppStore(state => state.currentCourse)
  const user = useAppStore(state => state.profile)
  const isAuthenticated = useAppStore(state => state.isAuthenticated)
  
  return {
    courses,
    enrolledCourses,
    courseProgress,
    currentCourse,
    user,
    isAuthenticated: isAuthenticated()
  }
}