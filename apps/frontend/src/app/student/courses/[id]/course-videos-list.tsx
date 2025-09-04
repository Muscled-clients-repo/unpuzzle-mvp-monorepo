'use client'

import { useState } from "react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import {
  Play,
  Lock,
  CheckCircle2,
  Clock,
  ChevronDown
} from "lucide-react"

interface Video {
  id: string
  title: string
  duration: number
  is_locked: boolean
  is_completed: boolean
  order_index: number
}

interface Section {
  id: string
  title: string
  description?: string
  order_index: number
  videos: Video[]
}

interface CourseVideosListProps {
  sections: Section[]
  courseId: string
}

export default function CourseVideosList({ sections, courseId }: CourseVideosListProps) {
  const [expandedSections, setExpandedSections] = useState<string[]>(
    sections.length > 0 ? [sections[0].id] : []
  )

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev =>
      prev.includes(sectionId)
        ? prev.filter(id => id !== sectionId)
        : [...prev, sectionId]
    )
  }

  return (
    <div className="space-y-4">
      {sections.map((section, sectionIndex) => {
        const sectionProgress = section.videos?.filter(v => v.is_completed).length || 0
        const totalVideos = section.videos?.length || 0
        const isExpanded = expandedSections.includes(section.id)

        return (
          <Card key={section.id}>
            <CardHeader 
              className="cursor-pointer"
              onClick={() => toggleSection(section.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <CardTitle className="text-lg">
                    Section {sectionIndex + 1}: {section.title}
                  </CardTitle>
                  {section.description && (
                    <p className="text-sm text-muted-foreground mt-1">
                      {section.description}
                    </p>
                  )}
                  <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                    <span>{totalVideos} lessons</span>
                    {sectionProgress > 0 && (
                      <span className="text-green-600 dark:text-green-400">
                        {sectionProgress}/{totalVideos} completed
                      </span>
                    )}
                  </div>
                </div>
                <ChevronDown 
                  className={`h-5 w-5 transition-transform ${
                    isExpanded ? 'rotate-180' : ''
                  }`}
                />
              </div>
            </CardHeader>
            
            {isExpanded && (
              <CardContent className="pt-0">
                <div className="space-y-2">
                  {section.videos?.map((video, videoIndex) => (
                    <div
                      key={video.id}
                      className="flex items-center gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex-shrink-0">
                        {video.is_completed ? (
                          <CheckCircle2 className="h-5 w-5 text-green-600" />
                        ) : video.is_locked ? (
                          <Lock className="h-5 w-5 text-muted-foreground" />
                        ) : (
                          <Play className="h-5 w-5 text-blue-600" />
                        )}
                      </div>
                      
                      <div className="flex-1">
                        {video.is_locked ? (
                          <div>
                            <p className="font-medium text-muted-foreground">
                              {videoIndex + 1}. {video.title}
                            </p>
                            <p className="text-sm text-muted-foreground">
                              Complete previous lessons to unlock
                            </p>
                          </div>
                        ) : (
                          <Link
                            href={`/student/courses/${courseId}/video/${video.id}`}
                            className="block group"
                          >
                            <p className="font-medium group-hover:text-blue-600 transition-colors">
                              {videoIndex + 1}. {video.title}
                            </p>
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <Clock className="h-3 w-3" />
                              <span>{formatDuration(video.duration)}</span>
                              {video.is_completed && (
                                <span className="text-green-600 dark:text-green-400">
                                  • Completed
                                </span>
                              )}
                            </div>
                          </Link>
                        )}
                      </div>
                      
                      {!video.is_locked && (
                        <Button
                          variant={video.is_completed ? "outline" : "default"}
                          size="sm"
                          asChild
                        >
                          <Link href={`/student/courses/${courseId}/video/${video.id}`}>
                            {video.is_completed ? 'Review' : 'Start'}
                          </Link>
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            )}
          </Card>
        )
      })}
    </div>
  )
}