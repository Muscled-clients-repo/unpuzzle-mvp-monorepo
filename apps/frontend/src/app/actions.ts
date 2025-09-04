'use server'

import { revalidatePath, revalidateTag } from 'next/cache'
import { redirect } from 'next/navigation'
import { getAuthHeaders } from '@/lib/auth-server'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001'

/**
 * Server Actions for data mutations
 * These functions handle form submissions and data updates
 */

// Course enrollment action
export async function enrollInCourse(courseId: string) {
  const headers = await getAuthHeaders()
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/enrollments/`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ course_id: courseId })
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Failed to enroll in course')
    }
    
    // Revalidate related data
    revalidateTag(`course-${courseId}`)
    revalidatePath(`/student/courses/${courseId}`)
    revalidatePath('/student/courses')
    
    return { success: true }
  } catch (error) {
    console.error('Enrollment error:', error)
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'Failed to enroll'
    }
  }
}

// Update course progress
export async function updateVideoProgress(
  videoId: string, 
  progress: number,
  completed: boolean = false
) {
  const headers = await getAuthHeaders()
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/progress/video/`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ 
        video_id: videoId,
        progress_percentage: progress,
        is_completed: completed
      })
    })
    
    if (!response.ok) {
      throw new Error('Failed to update progress')
    }
    
    // Revalidate progress data
    revalidateTag(`video-${videoId}`)
    
    return { success: true }
  } catch (error) {
    console.error('Progress update error:', error)
    return { success: false }
  }
}

// Submit reflection
export async function submitReflection(
  videoId: string,
  content: string,
  timestamp: number
) {
  const headers = await getAuthHeaders()
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/reflections/`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        video_id: videoId,
        content,
        timestamp
      })
    })
    
    if (!response.ok) {
      throw new Error('Failed to submit reflection')
    }
    
    const data = await response.json()
    
    // Revalidate reflections
    revalidateTag(`video-${videoId}`)
    
    return { success: true, reflection: data }
  } catch (error) {
    console.error('Reflection submission error:', error)
    return { 
      success: false, 
      error: 'Failed to submit reflection'
    }
  }
}

// Create course (instructor)
export async function createCourse(formData: FormData) {
  const headers = await getAuthHeaders()
  
  const courseData = {
    title: formData.get('title'),
    description: formData.get('description'),
    difficulty_level: formData.get('difficulty_level'),
    category_id: formData.get('category_id'),
    price: parseFloat(formData.get('price') as string),
    is_published: false
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/instructor/courses/`, {
      method: 'POST',
      headers,
      body: JSON.stringify(courseData)
    })
    
    if (!response.ok) {
      throw new Error('Failed to create course')
    }
    
    const course = await response.json()
    
    // Revalidate course listings
    revalidateTag('courses')
    revalidatePath('/instructor/courses')
    
    // Redirect to edit page
    redirect(`/instructor/course/${course.id}/edit`)
  } catch (error) {
    console.error('Course creation error:', error)
    throw error
  }
}

// Update course (instructor)
export async function updateCourse(courseId: string, formData: FormData) {
  const headers = await getAuthHeaders()
  
  const updates = Object.fromEntries(formData.entries())
  
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/instructor/courses/${courseId}/`,
      {
        method: 'PATCH',
        headers,
        body: JSON.stringify(updates)
      }
    )
    
    if (!response.ok) {
      throw new Error('Failed to update course')
    }
    
    // Revalidate course data
    revalidateTag(`course-${courseId}`)
    revalidatePath(`/instructor/course/${courseId}/edit`)
    
    return { success: true }
  } catch (error) {
    console.error('Course update error:', error)
    return { 
      success: false,
      error: 'Failed to update course'
    }
  }
}

// Publish course (instructor)
export async function publishCourse(courseId: string) {
  const headers = await getAuthHeaders()
  
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/instructor/courses/${courseId}/publish/`,
      {
        method: 'POST',
        headers
      }
    )
    
    if (!response.ok) {
      throw new Error('Failed to publish course')
    }
    
    // Revalidate course data
    revalidateTag(`course-${courseId}`)
    revalidateTag('courses')
    revalidatePath(`/instructor/course/${courseId}/edit`)
    revalidatePath('/courses')
    
    return { success: true }
  } catch (error) {
    console.error('Course publish error:', error)
    return { 
      success: false,
      error: 'Failed to publish course'
    }
  }
}

// Upload video (instructor)
export async function uploadVideo(formData: FormData) {
  const headers = await getAuthHeaders()
  // Remove Content-Type to let browser set it with boundary for multipart
  delete (headers as any)['Content-Type']
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/media/upload/`, {
      method: 'POST',
      headers,
      body: formData // Send FormData directly
    })
    
    if (!response.ok) {
      throw new Error('Failed to upload video')
    }
    
    const data = await response.json()
    return { success: true, media: data }
  } catch (error) {
    console.error('Video upload error:', error)
    return { 
      success: false,
      error: 'Failed to upload video'
    }
  }
}

// Delete video (instructor)
export async function deleteVideo(videoId: string) {
  const headers = await getAuthHeaders()
  
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/media/${videoId}/`,
      {
        method: 'DELETE',
        headers
      }
    )
    
    if (!response.ok) {
      throw new Error('Failed to delete video')
    }
    
    // Revalidate related data
    revalidateTag(`video-${videoId}`)
    
    return { success: true }
  } catch (error) {
    console.error('Video deletion error:', error)
    return { 
      success: false,
      error: 'Failed to delete video'
    }
  }
}