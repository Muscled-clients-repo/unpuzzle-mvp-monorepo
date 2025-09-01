import { Header } from "@/components/layout/header"
import { Sidebar } from "@/components/layout/sidebar"
import { CourseSelector } from "@/components/instructor/course-selector"
import { mockUsers } from "@/data/mock"

export default function InstructorLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const instructor = mockUsers.instructors[0]
  
  return (
    <div className="min-h-screen">
      <Header user={{ name: instructor.name, email: instructor.email, role: instructor.role }} />
      <Sidebar role="instructor" />
      <div className="md:pl-64 pt-16">
        <CourseSelector />
        <main className="min-h-[calc(100vh-4rem)]">
          {children}
        </main>
      </div>
    </div>
  )
}