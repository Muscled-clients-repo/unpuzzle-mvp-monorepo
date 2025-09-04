import Link from "next/link"
import { Suspense } from "react"
import { Button } from "@/components/ui/button"
import { Header } from "@/components/layout/header"
import { Footer } from "@/components/layout/footer"
import { getFeaturedCourses, getPlatformStats } from "@/lib/api-server"
import { ArrowRight, Sparkles, Brain, Target } from "lucide-react"
import { CourseGridSkeleton } from "@/components/common/CourseCardSkeleton"
import { BookOpen } from "lucide-react"
import { DataSyncProvider } from "@/components/providers/DataSyncProvider"
import { HomePageClient } from "./home-page-client"

// Revalidate every hour
export const revalidate = 3600

export default async function HomePage() {
  // Fetch data on the server
  const [featuredCourses, platformStats] = await Promise.all([
    getFeaturedCourses(6),
    getPlatformStats()
  ])

  // Pass the SSR data to be synced with Zustand
  const initialData = {
    featuredCourses,
    platformStats
  }

  return (
    <DataSyncProvider initialData={initialData}>
      <HomePageClient 
        featuredCourses={featuredCourses}
        platformStats={platformStats}
      />
    </DataSyncProvider>
  )
}