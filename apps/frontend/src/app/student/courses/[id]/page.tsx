import { Suspense } from "react"
import Link from "next/link"
import { notFound } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import {
  Play,
  Clock,
  CheckCircle2,
  BookOpen,
  Award,
  Brain,
  MessageSquare,
  Sparkles,
  ChevronRight,
  Lock
} from "lucide-react"
import { getCourse, getCourseSections, getCourseProgress } from "@/lib/api-server"
import { getServerSession } from "@/lib/auth-server"
import { StudentCourseOverviewSkeleton, ChapterVideosSkeleton } from "@/components/common/CourseCardSkeleton"
import CourseVideosList from "./course-videos-list"

// Course sections component that loads videos
async function CourseSections({ courseId }: { courseId: string }) {
  const sections = await getCourseSections(courseId)
  
  if (!sections || sections.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <p className="text-muted-foreground">No content available yet</p>
        </CardContent>
      </Card>
    )
  }
  
  return <CourseVideosList sections={sections} courseId={courseId} />
}

// Progress component that loads user-specific data
async function CourseProgressSection({ courseId }: { courseId: string }) {
  const [session, progress] = await Promise.all([
    getServerSession(),
    getCourseProgress(courseId)
  ])
  
  if (!session || !progress) {
    return null
  }
  
  const completionRate = progress.completion_percentage || 0
  const completedLessons = progress.completed_lessons || 0
  const totalLessons = progress.total_lessons || 0
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Your Progress</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span>Overall Progress</span>
            <span className="font-medium">{Math.round(completionRate)}%</span>
          </div>
          <Progress value={completionRate} className="h-2" />
        </div>
        
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-muted-foreground">Completed</p>
            <p className="text-xl font-bold">{completedLessons}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Total Lessons</p>
            <p className="text-xl font-bold">{totalLessons}</p>
          </div>
        </div>
        
        {completionRate === 100 && (
          <div className="flex items-center gap-2 p-3 bg-green-50 dark:bg-green-950 rounded-lg">
            <Award className="h-5 w-5 text-green-600" />
            <span className="text-sm font-medium">Course Completed!</span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default async function StudentCoursePage({
  params
}: {
  params: { id: string }
}) {
  // Fetch course data on the server
  const course = await getCourse(params.id)
  
  if (!course) {
    notFound()
  }
  
  const session = await getServerSession()
  const isEnrolled = session && course.is_enrolled
  
  return (
    <div className="container max-w-7xl mx-auto px-4 py-8">
      {/* Course Header */}
      <div className="mb-8">
        <Link 
          href="/student/courses" 
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-4"
        >
          <ChevronRight className="h-4 w-4 rotate-180 mr-1" />
          Back to My Courses
        </Link>
        
        <div className="grid gap-8 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            <div>
              <h1 className="text-3xl font-bold mb-4">{course.title}</h1>
              <p className="text-lg text-muted-foreground mb-4">
                {course.description}
              </p>
              
              <div className="flex flex-wrap gap-2 mb-6">
                <Badge variant="secondary">
                  <BookOpen className="h-3 w-3 mr-1" />
                  {course.total_lessons || 0} Lessons
                </Badge>
                <Badge variant="secondary">
                  <Clock className="h-3 w-3 mr-1" />
                  {course.duration || 'Self-paced'}
                </Badge>
                <Badge variant="secondary">
                  {course.difficulty_level || 'All Levels'}
                </Badge>
                {course.certificate_available && (
                  <Badge variant="default">
                    <Award className="h-3 w-3 mr-1" />
                    Certificate Available
                  </Badge>
                )}
              </div>
              
              <div className="flex items-center gap-4">
                {course.instructor && (
                  <div className="flex items-center gap-2">
                    <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500" />
                    <div>
                      <p className="text-sm text-muted-foreground">Instructor</p>
                      <p className="font-medium">{course.instructor.full_name}</p>
                    </div>
                  </div>
                )}
                
                <div className="flex items-center gap-1 ml-auto">
                  <Star className="h-4 w-4 fill-yellow-500 text-yellow-500" />
                  <span className="font-medium">{course.average_rating || 4.5}</span>
                  <span className="text-muted-foreground">
                    ({course.total_reviews || 0} reviews)
                  </span>
                </div>
              </div>
            </div>
            
            {/* AI Features */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-purple-500" />
                  AI-Powered Features
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="flex gap-3">
                    <Brain className="h-5 w-5 text-blue-500 mt-0.5" />
                    <div>
                      <p className="font-medium">Contextual Hints</p>
                      <p className="text-sm text-muted-foreground">
                        Get AI-powered explanations while watching
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <MessageSquare className="h-5 w-5 text-green-500 mt-0.5" />
                    <div>
                      <p className="font-medium">Interactive Q&A</p>
                      <p className="text-sm text-muted-foreground">
                        Ask questions and get instant answers
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
          
          <div className="space-y-6">
            {/* Enrollment Card */}
            <Card>
              <CardHeader>
                <CardTitle>Course Access</CardTitle>
              </CardHeader>
              <CardContent>
                {isEnrolled ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                      <CheckCircle2 className="h-5 w-5" />
                      <span className="font-medium">Enrolled</span>
                    </div>
                    <Button className="w-full" asChild>
                      <Link href={`/student/courses/${params.id}/learn`}>
                        <Play className="h-4 w-4 mr-2" />
                        Continue Learning
                      </Link>
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="text-2xl font-bold">
                      ${course.price || 49.99}
                    </div>
                    <Button className="w-full">
                      <Lock className="h-4 w-4 mr-2" />
                      Enroll Now
                    </Button>
                    <p className="text-xs text-muted-foreground text-center">
                      30-day money-back guarantee
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
            
            {/* Progress Card - Only shown if enrolled */}
            {isEnrolled && (
              <Suspense fallback={<StudentCourseOverviewSkeleton />}>
                <CourseProgressSection courseId={params.id} />
              </Suspense>
            )}
          </div>
        </div>
      </div>
      
      {/* Course Content */}
      <div>
        <h2 className="text-2xl font-bold mb-6">Course Content</h2>
        <Suspense fallback={<ChapterVideosSkeleton />}>
          <CourseSections courseId={params.id} />
        </Suspense>
      </div>
    </div>
  )
}

// Add missing import
import { Star } from "lucide-react"