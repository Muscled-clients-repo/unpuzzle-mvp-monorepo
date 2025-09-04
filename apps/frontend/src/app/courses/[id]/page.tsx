import { notFound } from "next/navigation"
import { getCourse } from "@/lib/api-server"
import { CourseDetailClient } from "./course-detail-client"
import { Metadata } from "next"

// Generate metadata for SEO
export async function generateMetadata({ 
  params 
}: { 
  params: { id: string } 
}): Promise<Metadata> {
  const course = await getCourse(params.id)
  
  if (!course) {
    return {
      title: "Course Not Found",
      description: "The requested course could not be found."
    }
  }

  return {
    title: course.title,
    description: course.description,
    openGraph: {
      title: course.title,
      description: course.description,
      images: course.thumbnailUrl ? [course.thumbnailUrl] : [],
      type: 'website'
    }
  }
}

// Server Component - fetches data on the server
export default async function CoursePreviewPage({
  params
}: {
  params: { id: string }
}) {
  // Fetch course data on the server
  const course = await getCourse(params.id)
  
  console.log('[SSR] Course data fetched from server:', {
    id: course?.id,
    title: course?.title,
    price: course?.price,
    description: course?.description?.substring(0, 100),
    instructor: course?.instructor,
    hasVideos: !!course?.videos,
    videosCount: course?.videos?.length,
    duration: course?.duration,
    enrollmentCount: course?.enrollmentCount,
    thumbnailUrl: course?.thumbnailUrl
  })
  
  // If course not found, show 404
  if (!course) {
    notFound()
  }

  // Pass the server-fetched data to the client component
  return <CourseDetailClient initialCourse={course} courseId={params.id} />
}