'use client'

import Link from "next/link"
import { useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Header } from "@/components/layout/header"
import { Footer } from "@/components/layout/footer"
import { AICourseCard } from "@/components/course/ai-course-card"
import { MetricWidget } from "@/components/dashboard/metrics-widget"
import { AgentCard } from "@/components/ai/agent-card"
import { ArrowRight, Sparkles, Brain, Target, BookOpen } from "lucide-react"
import { useAppStore } from "@/stores/app-store"

interface HomePageClientProps {
  featuredCourses: any[]
  platformStats: any
}

export function HomePageClient({ featuredCourses, platformStats }: HomePageClientProps) {
  // Access the store - data will be synced by DataSyncProvider
  const storedCourses = useAppStore(state => state.courses)
  const user = useAppStore(state => state.profile)
  
  // Optional: You can also directly update the store here if needed
  useEffect(() => {
    // The data is already synced by DataSyncProvider
    // But you can access it from the store for any client-side operations
    console.log('Featured courses synced to store:', storedCourses)
    console.log('Current user from SSR:', user)
  }, [storedCourses, user])

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      
      <main className="flex-1 pt-16">
        <section className="relative overflow-hidden bg-gradient-to-b from-background to-muted py-20">
          <div className="container px-4">
            <div className="mx-auto max-w-3xl text-center">
              <h1 className="mb-6 text-5xl font-bold tracking-tight">
                Learn Faster with{" "}
                <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  AI-Powered
                </span>{" "}
                Learning
              </h1>
              <p className="mb-8 text-xl text-muted-foreground">
                The only platform that measures how you learn, not just what you watch. 
                Get contextual hints, personalized quizzes, and adaptive learning paths.
              </p>
              <div className="flex justify-center gap-4">
                <Button size="lg" asChild>
                  <Link href="/courses">
                    Browse Courses
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
                <Button size="lg" variant="outline" asChild>
                  <Link href="/signup">Start Free Trial</Link>
                </Button>
              </div>
            </div>
          </div>
        </section>

        <section className="py-16">
          <div className="container px-4">
            <h2 className="mb-12 text-center text-3xl font-bold">
              AI Agents That Accelerate Your Learning
            </h2>
            <div className="grid gap-6 md:grid-cols-3">
              <AgentCard
                type="hint"
                title="Context Agent"
                description="Provides instant explanations based on what you're watching"
                content="Get real-time hints, concept connections, and visual explanations"
                badge="AI-Powered"
              />
              <AgentCard
                type="check"
                title="Quiz Agent"
                description="Creates personalized quizzes to test your understanding"
                content="Adaptive difficulty, instant feedback, and progress tracking"
                badge="Interactive"
              />
              <AgentCard
                type="path"
                title="Progress Agent"
                description="Tracks your learning journey and suggests next steps"
                content="Learning analytics, skill mapping, and custom pathways"
                badge="Personalized"
              />
            </div>
          </div>
        </section>

        {platformStats && platformStats.total_courses > 0 && (
          <section className="bg-muted py-16">
            <div className="container px-4">
              <h2 className="mb-4 text-center text-3xl font-bold">
                Platform Statistics
              </h2>
              <p className="mb-12 text-center text-muted-foreground">
                Join thousands of learners accelerating their education
              </p>
              <div className="grid gap-4 md:grid-cols-4">
                <MetricWidget
                  title="Active Learners"
                  value={platformStats.active_learners?.toLocaleString() || '0'}
                  change={platformStats.learners_change || '+0%'}
                  icon={<Brain className="h-4 w-4" />}
                />
                <MetricWidget
                  title="Courses Available"
                  value={platformStats.total_courses?.toLocaleString() || '0'}
                  change={platformStats.courses_change || '+0%'}
                  icon={<BookOpen className="h-4 w-4" />}
                />
                <MetricWidget
                  title="Completion Rate"
                  value={`${platformStats.completion_rate || 0}%`}
                  change={platformStats.completion_change || '+0%'}
                  icon={<Target className="h-4 w-4" />}
                />
                <MetricWidget
                  title="AI Interactions"
                  value={platformStats.ai_interactions?.toLocaleString() || '0'}
                  change={platformStats.interactions_change || '+0%'}
                  icon={<Sparkles className="h-4 w-4" />}
                />
              </div>
            </div>
          </section>
        )}

        <section className="py-16">
          <div className="container px-4">
            <h2 className="mb-12 text-center text-3xl font-bold">
              Featured Courses
            </h2>
            {featuredCourses && featuredCourses.length > 0 ? (
              <>
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                  {featuredCourses.map((course: any) => (
                    <AICourseCard
                      key={course.id}
                      course={course}
                      variant="default"
                    />
                  ))}
                </div>
                <div className="mt-8 text-center">
                  <Button variant="outline" size="lg" asChild>
                    <Link href="/courses">
                      View All Courses
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Link>
                  </Button>
                </div>
              </>
            ) : (
              <div className="text-center py-8">
                <p className="text-muted-foreground">No featured courses available</p>
              </div>
            )}
          </div>
        </section>

        <section className="bg-gradient-to-r from-blue-600 to-purple-600 py-20 text-white">
          <div className="container px-4 text-center">
            <h2 className="mb-4 text-4xl font-bold">
              Ready to Accelerate Your Learning?
            </h2>
            <p className="mb-8 text-xl opacity-90">
              Join Unpuzzle today and experience the future of education
            </p>
            <div className="flex justify-center gap-4">
              <Button size="lg" variant="secondary" asChild>
                <Link href="/signup">Get Started Free</Link>
              </Button>
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white/10" asChild>
                <Link href="/courses">Explore Courses</Link>
              </Button>
            </div>
          </div>
        </section>
      </main>
      
      <Footer />
    </div>
  )
}