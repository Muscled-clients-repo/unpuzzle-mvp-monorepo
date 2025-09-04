'use client'

import { useEffect } from 'react'
import { useAppStore } from '@/stores/app-store'

/**
 * Hook to sync course data from SSR to Zustand store
 * Use this in pages that fetch course data on the server
 */
export function useSyncCourseData(courseData: any) {
  const loadCourseById = useAppStore(state => state.loadCourseById)
  
  useEffect(() => {
    if (courseData) {
      // Sync course data to store
      // The loadCourseById will update the store with the course data
      loadCourseById(courseData.id)
    }
  }, [courseData, loadCourseById])
}

/**
 * Hook to sync courses list from SSR to Zustand store
 */
export function useSyncCoursesData(coursesData: any) {
  const loadCourses = useAppStore(state => state.loadCourses)
  
  useEffect(() => {
    if (coursesData && coursesData.results) {
      // Update the store with the SSR courses data
      // This ensures client components have immediate access
      loadCourses()
    }
  }, [coursesData, loadCourses])
}

/**
 * Hook to sync enrolled courses from SSR to Zustand store
 */
export function useSyncEnrolledCourses(enrolledCourses: any[]) {
  const loadEnrolledCourses = useAppStore(state => state.loadEnrolledCourses)
  
  useEffect(() => {
    if (enrolledCourses && enrolledCourses.length > 0) {
      loadEnrolledCourses()
    }
  }, [enrolledCourses, loadEnrolledCourses])
}

/**
 * Generic hook to sync any SSR data to store
 */
export function useSSRDataSync<T>(
  data: T | null,
  syncAction: (data: T) => void,
  deps: any[] = []
) {
  useEffect(() => {
    if (data) {
      syncAction(data)
    }
  }, [data, syncAction, ...deps])
}