import { cache } from 'react'
import { getAuthHeaders } from './auth-server'

/**
 * Server-side API utilities for Next.js App Router
 * These functions fetch data on the server and can be used in Server Components
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001'

// Cache wrapper for GET requests (cached per request cycle)
const fetchWithCache = cache(async (url: string, options?: RequestInit) => {
  try {
    const response = await fetch(url, options)
    if (!response.ok) {
      // Don't throw for 401/403, return null for auth errors
      if (response.status === 401 || response.status === 403) {
        console.log(`Auth error fetching ${url}: ${response.status}`)
        return null
      }
      // For other errors, log but don't crash
      console.error(`API error fetching ${url}: ${response.status}`)
      return null
    }
    return response.json()
  } catch (error) {
    console.error(`Network error fetching ${url}:`, error)
    return null
  }
})

/**
 * Fetch courses with optional filters (server-side, public endpoint)
 */
export async function getCourses(params?: {
  category?: string
  page?: number
  limit?: number
  search?: string
}) {
  const searchParams = new URLSearchParams()
  
  if (params?.category) searchParams.append('category', params.category)
  if (params?.page) searchParams.append('page', params.page.toString())
  if (params?.limit) searchParams.append('limit', params.limit.toString())
  if (params?.search) searchParams.append('search', params.search)
  
  const url = `${API_BASE_URL}/api/v1/courses/?${searchParams.toString()}`
  
  try {
    console.log('[API-SERVER] Fetching courses (public endpoint)')
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json'
        // No Authorization header for public endpoint
      },
      next: { 
        revalidate: 300, // Cache for 5 minutes
        tags: ['courses']
      }
    })
    
    if (!response.ok) {
      console.log(`[API-SERVER] Courses endpoint returned ${response.status} - using fallback`)
      return {
        results: [],
        count: 0,
        total_pages: 0,
        next: null,
        previous: null
      }
    }
    
    const result = await response.json()
    console.log('[API-SERVER] Successfully fetched courses:', result.count || 0, 'total')
    return result
  } catch (error) {
    console.error('[API-SERVER] Error fetching courses:', error)
    // Return empty results structure if fetch failed
    return {
      results: [],
      count: 0,
      total_pages: 0,
      next: null,
      previous: null
    }
  }
}

/**
 * Fetch single course by ID (server-side, public endpoint)
 */
export async function getCourse(courseId: string) {
  const url = `${API_BASE_URL}/api/v1/courses/${courseId}/`
  
  try {
    console.log('[API-SERVER] Fetching course details (public endpoint):', courseId)
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json'
        // No Authorization header for public endpoint
      },
      next: { 
        revalidate: 300,
        tags: [`course-${courseId}`]
      }
    })
    
    if (!response.ok) {
      console.log(`[API-SERVER] Course endpoint returned ${response.status} for course ${courseId}`)
      return null
    }
    
    const result = await response.json()
    
    // Django returns { success: true, data: {...} } format
    const courseData = result.data || result
    
    console.log('[API-SERVER] Successfully fetched course:', courseData.title || courseId)
    console.log('[API-SERVER] Course data structure:', {
      hasDataWrapper: !!result.data,
      title: courseData.title,
      price: courseData.price,
      instructor: courseData.instructor?.full_name || courseData.instructor?.display_name
    })
    
    return courseData
  } catch (error) {
    console.error('[API-SERVER] Error fetching course:', error)
    return null
  }
}

/**
 * Fetch course sections with media (server-side)
 */
export async function getCourseSections(courseId: string) {
  const url = `${API_BASE_URL}/api/v1/courses/${courseId}/sections/`
  
  return fetchWithCache(url, {
    next: { 
      revalidate: 300,
      tags: [`course-sections-${courseId}`]
    }
  })
}

/**
 * Fetch user's course progress (requires auth)
 */
export async function getCourseProgress(courseId: string) {
  const headers = await getAuthHeaders()
  const url = `${API_BASE_URL}/api/v1/courses/${courseId}/progress/`
  
  try {
    const response = await fetch(url, {
      headers,
      cache: 'no-store' // Don't cache user-specific data
    })
    
    if (!response.ok) {
      if (response.status === 401) {
        return null // Not authenticated
      }
      throw new Error(`Failed to fetch progress: ${response.status}`)
    }
    
    return response.json()
  } catch (error) {
    console.error('Error fetching course progress:', error)
    return null
  }
}

/**
 * Fetch user's enrolled courses (requires auth)
 */
export async function getEnrolledCourses() {
  const headers = await getAuthHeaders()
  const url = `${API_BASE_URL}/api/v1/enrollments/`
  
  try {
    const response = await fetch(url, {
      headers,
      cache: 'no-store'
    })
    
    if (!response.ok) {
      if (response.status === 401) {
        return []
      }
      throw new Error(`Failed to fetch enrollments: ${response.status}`)
    }
    
    return response.json()
  } catch (error) {
    console.error('Error fetching enrolled courses:', error)
    return []
  }
}

/**
 * Fetch featured courses for homepage (public endpoint - no auth required)
 */
export async function getFeaturedCourses(limit = 6) {
  // For public endpoints, don't use auth headers
  const url = `${API_BASE_URL}/api/v1/courses/featured/?limit=${limit}`
  
  try {
    console.log('[API-SERVER] Fetching featured courses (public endpoint)')
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json'
        // No Authorization header for public endpoint
      },
      next: { 
        revalidate: 3600, // Cache for 1 hour
        tags: ['featured-courses']
      }
    })
    
    if (!response.ok) {
      console.log(`[API-SERVER] Featured courses endpoint returned ${response.status} - using fallback`)
      // Return mock data for development
      return [
        {
          id: '1',
          title: 'Introduction to React',
          description: 'Learn the basics of React development',
          instructor: { full_name: 'John Doe' },
          difficulty_level: 'Beginner',
          average_rating: 4.5,
          total_enrolled: 150,
          price: 49.99,
          thumbnail: '/images/react-course.jpg'
        },
        {
          id: '2', 
          title: 'Advanced JavaScript',
          description: 'Master advanced JavaScript concepts',
          instructor: { full_name: 'Jane Smith' },
          difficulty_level: 'Advanced',
          average_rating: 4.8,
          total_enrolled: 89,
          price: 79.99,
          thumbnail: '/images/js-course.jpg'
        }
      ]
    }
    
    const result = await response.json()
    console.log('[API-SERVER] Successfully fetched featured courses:', result.length || 0, 'courses')
    return result || []
  } catch (error) {
    console.error('[API-SERVER] Error fetching featured courses:', error)
    return [] // Return empty array on error
  }
}

/**
 * Fetch platform statistics for homepage (public endpoint - no auth required)
 */
export async function getPlatformStats() {
  const url = `${API_BASE_URL}/api/v1/stats/platform/`
  
  try {
    console.log('[API-SERVER] Fetching platform stats (public endpoint)')
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json'
        // No Authorization header for public endpoint
      },
      next: { 
        revalidate: 3600,
        tags: ['platform-stats']
      }
    })
    
    if (!response.ok) {
      console.log(`[API-SERVER] Platform stats endpoint returned ${response.status} - using fallback`)
      // Return mock stats for development
      return {
        active_learners: 1234,
        total_courses: 156,
        completion_rate: 78,
        ai_interactions: 45200,
        learners_change: '+12%',
        courses_change: '+8%',
        completion_change: '+15%',
        interactions_change: '+25%'
      }
    }
    
    const result = await response.json()
    console.log('[API-SERVER] Successfully fetched platform stats')
    return result || {
      active_learners: 0,
      total_courses: 0,
      completion_rate: 0,
      ai_interactions: 0
    }
  } catch (error) {
    console.error('[API-SERVER] Error fetching platform stats:', error)
    // Return default stats if fetch failed
    return {
      active_learners: 0,
      total_courses: 0,
      completion_rate: 0,
      ai_interactions: 0
    }
  }
}

/**
 * Fetch video details
 */
export async function getVideo(videoId: string) {
  const url = `${API_BASE_URL}/api/v1/media/${videoId}/`
  
  return fetchWithCache(url, {
    next: { 
      revalidate: 300,
      tags: [`video-${videoId}`]
    }
  })
}

/**
 * Fetch instructor's courses (requires auth)
 */
export async function getInstructorCourses() {
  const headers = await getAuthHeaders()
  const url = `${API_BASE_URL}/api/v1/instructor/courses/`
  
  try {
    const response = await fetch(url, {
      headers,
      cache: 'no-store'
    })
    
    if (!response.ok) {
      return []
    }
    
    return response.json()
  } catch (error) {
    console.error('Error fetching instructor courses:', error)
    return []
  }
}

/**
 * Fetch course analytics (instructor only)
 */
export async function getCourseAnalytics(courseId: string) {
  const headers = await getAuthHeaders()
  const url = `${API_BASE_URL}/api/v1/courses/${courseId}/analytics/`
  
  try {
    const response = await fetch(url, {
      headers,
      cache: 'no-store'
    })
    
    if (!response.ok) {
      return null
    }
    
    return response.json()
  } catch (error) {
    console.error('Error fetching course analytics:', error)
    return null
  }
}

/**
 * Revalidate cache by tag
 * Use this after mutations to update cached data
 */
export async function revalidateCache(tag: string | string[]) {
  const { revalidateTag } = await import('next/cache')
  
  const tags = Array.isArray(tag) ? tag : [tag]
  tags.forEach(t => revalidateTag(t))
}