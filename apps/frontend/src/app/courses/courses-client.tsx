'use client'

import { useState, useCallback } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { AICourseCard } from "@/components/course/ai-course-card"
import { CourseFiltersComponent } from "@/components/course/course-filters"
import { Button } from "@/components/ui/button"
import { ChevronLeft, ChevronRight } from "lucide-react"

interface CoursesClientProps {
  initialCourses: any[]
  totalCount: number
  currentPage: number
  totalPages: number
  initialFilters: {
    category: string
    search: string
    level: string
    sort: string
  }
}

export default function CoursesClient({
  initialCourses,
  totalCount,
  currentPage,
  totalPages,
  initialFilters
}: CoursesClientProps) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [courses] = useState(initialCourses)
  const [filters, setFilters] = useState(initialFilters)

  const updateUrl = useCallback((newFilters: typeof filters, page?: number) => {
    const params = new URLSearchParams()
    
    if (newFilters.category) params.set('category', newFilters.category)
    if (newFilters.search) params.set('search', newFilters.search)
    if (newFilters.level) params.set('level', newFilters.level)
    if (newFilters.sort) params.set('sort', newFilters.sort)
    if (page && page > 1) params.set('page', page.toString())
    
    const queryString = params.toString()
    router.push(`/courses${queryString ? `?${queryString}` : ''}`)
  }, [router])

  const handleFiltersChange = (newFilters: Partial<typeof filters>) => {
    const updated = { ...filters, ...newFilters }
    setFilters(updated)
    updateUrl(updated, 1) // Reset to page 1 when filters change
  }

  const handlePageChange = (page: number) => {
    updateUrl(filters, page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleClearFilters = () => {
    const cleared = { category: '', search: '', level: '', sort: 'popular' }
    setFilters(cleared)
    router.push('/courses')
  }

  return (
    <>
      <div className="mb-8">
        <CourseFiltersComponent
          filters={filters}
          onFiltersChange={handleFiltersChange}
          onClearFilters={handleClearFilters}
          totalCount={totalCount}
        />
      </div>

      {courses.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-xl text-muted-foreground mb-4">
            No courses found matching your criteria
          </p>
          <Button onClick={handleClearFilters} variant="outline">
            Clear Filters
          </Button>
        </div>
      ) : (
        <>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {courses.map((course: any) => (
              <AICourseCard
                key={course.id}
                course={course}
                variant="default"
              />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="mt-8 flex justify-center gap-2">
              <Button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage <= 1}
                variant="outline"
                size="sm"
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>
              
              <div className="flex items-center gap-2">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum: number
                  if (totalPages <= 5) {
                    pageNum = i + 1
                  } else if (currentPage <= 3) {
                    pageNum = i + 1
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i
                  } else {
                    pageNum = currentPage - 2 + i
                  }
                  
                  return (
                    <Button
                      key={pageNum}
                      onClick={() => handlePageChange(pageNum)}
                      variant={currentPage === pageNum ? "default" : "outline"}
                      size="sm"
                      className="min-w-[40px]"
                    >
                      {pageNum}
                    </Button>
                  )
                })}
              </div>
              
              <Button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage >= totalPages}
                variant="outline"
                size="sm"
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </>
      )}
    </>
  )
}