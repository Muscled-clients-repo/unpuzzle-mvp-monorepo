import { Suspense } from "react"
import { Header } from "@/components/layout/header"
import { Footer } from "@/components/layout/footer"
import { getCourses } from "@/lib/api-server"
import { CourseGridSkeleton, CourseFiltersSkeleton } from "@/components/common/CourseCardSkeleton"
import CoursesClient from "./courses-client"

interface SearchParams {
  category?: string
  page?: string
  search?: string
  level?: string
  sort?: string
}

// Revalidate every 5 minutes
export const revalidate = 300

export default async function CoursesPage({
  searchParams,
}: {
  searchParams: SearchParams
}) {
  // Fetch courses based on search params
  const coursesData = await getCourses({
    category: searchParams.category,
    page: searchParams.page ? parseInt(searchParams.page) : 1,
    search: searchParams.search,
  })

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      
      <main className="flex-1 pt-16">
        <section className="bg-gradient-to-b from-background to-muted py-12">
          <div className="container px-4">
            <h1 className="mb-4 text-center text-4xl font-bold">
              Explore Our Courses
            </h1>
            <p className="text-center text-xl text-muted-foreground">
              Learn from industry experts with AI-powered assistance
            </p>
          </div>
        </section>

        <section className="py-8">
          <div className="container px-4">
            <Suspense fallback={<CourseFiltersSkeleton />}>
              <CoursesClient 
                initialCourses={coursesData.results || coursesData}
                totalCount={coursesData.count || 0}
                currentPage={searchParams.page ? parseInt(searchParams.page) : 1}
                totalPages={coursesData.total_pages || Math.ceil((coursesData.count || 0) / 20)}
                initialFilters={{
                  category: searchParams.category || '',
                  search: searchParams.search || '',
                  level: searchParams.level || '',
                  sort: searchParams.sort || 'popular'
                }}
              />
            </Suspense>
          </div>
        </section>
      </main>
      
      <Footer />
    </div>
  )
}