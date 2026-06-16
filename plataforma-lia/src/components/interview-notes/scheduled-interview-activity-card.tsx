"use client"

import React from"react"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Card } from"@/components/ui/card"
import {
  Calendar,
  Clock,
  Video,
  Users,
  MessageSquare,
  ChevronRight,
  MapPin,
} from"lucide-react"
import { textStyles, badgeStyles } from"@/lib/design-tokens"
import { cn } from"@/lib/utils"

interface ScheduledInterviewActivityCardProps {
  interview: {
    id: string
    candidateId: string
    candidateName: string
    jobId: string
    jobTitle: string
    scheduledAt: string
    duration: number
    platform:"teams" |"meet" |"zoom" |"presencial"
    interviewerName: string
  }
  onPrepareNotes: (interviewId: string) => void
  onViewSuggestedQuestions: (interviewId: string) => void
}

interface TimeUntilInterview {
  label: string
  urgency:"critical" |"warning" |"normal"
}

export function ScheduledInterviewActivityCard({
  interview,
  onPrepareNotes,
  onViewSuggestedQuestions,
}: ScheduledInterviewActivityCardProps) {
  const getTimeUntilInterview = (): TimeUntilInterview => {
    const now = new Date()
    const scheduledTime = new Date(interview.scheduledAt)
    const diffInMs = scheduledTime.getTime() - now.getTime()
    const diffInMinutes = Math.floor(diffInMs / 60000)
    const diffInHours = Math.floor(diffInMs / 3600000)
    const diffInDays = Math.floor(diffInMs / 86400000)

    if (diffInMinutes < 0) {
      return { label:"Entrevista finalizada", urgency:"normal" }
    }

    if (diffInMinutes < 60) {
      return { label: `Em ${diffInMinutes} min`, urgency:"critical" }
    }

    if (diffInHours < 24) {
      const scheduledDate = new Date(interview.scheduledAt)
      const timeStr = scheduledDate.toLocaleTimeString("pt-BR", {
        hour:"2-digit",
        minute:"2-digit",
      })
      return { label: `Hoje às ${timeStr}`, urgency:"warning" }
    }

    if (diffInDays === 1) {
      const scheduledDate = new Date(interview.scheduledAt)
      const timeStr = scheduledDate.toLocaleTimeString("pt-BR", {
        hour:"2-digit",
        minute:"2-digit",
      })
      return { label: `Amanhã às ${timeStr}`, urgency:"normal" }
    }

    const scheduledDate = new Date(interview.scheduledAt)
    const dateStr = scheduledDate.toLocaleDateString("pt-BR", {
      weekday:"short",
      day:"numeric",
      month:"short",
    })
    const timeStr = scheduledDate.toLocaleTimeString("pt-BR", {
      hour:"2-digit",
      minute:"2-digit",
    })
    return { label: `${dateStr} às ${timeStr}`, urgency:"normal" }
  }

  const getUrgencyBadgeStyle = (urgency:"critical" |"warning" |"normal") => {
    switch (urgency) {
      case"critical":
        return badgeStyles.error
      case"warning":
        return badgeStyles.warning
      case"normal":
        return badgeStyles.success
    }
  }

  const getPlatformIcon = (platform: string) => {
    switch (platform) {
      case"teams":
        return <Video className="w-3.5 h-3.5" />
      case"meet":
        return <Video className="w-3.5 h-3.5" />
      case"zoom":
        return <Video className="w-3.5 h-3.5" />
      case"presencial":
        return <MapPin className="w-3.5 h-3.5" />
      default:
        return <Video className="w-3.5 h-3.5" />
    }
  }

  const getPlatformLabel = (platform: string) => {
    switch (platform) {
      case"teams":
        return"Teams"
      case"meet":
        return"Google Meet"
      case"zoom":
        return"Zoom"
      case"presencial":
        return"Presencial"
      default:
        return platform
    }
  }

  const timeInfo = getTimeUntilInterview()
  const scheduledDate = new Date(interview.scheduledAt)
  const dateStr = scheduledDate.toLocaleDateString("pt-BR", {
    weekday:"long",
    day:"numeric",
    month:"long",
  })
  const timeStr = scheduledDate.toLocaleTimeString("pt-BR", {
    hour:"2-digit",
    minute:"2-digit",
  })

  return (
    <Card className="bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl hover:transition-shadow">
      <div className="p-3 space-y-2.5">
        {/* Urgency Badge */}
        <div className="flex items-center justify-between">
          <Chip variant="neutral" muted className={cn(getUrgencyBadgeStyle(timeInfo.urgency),"border-0")}>
            {timeInfo.label}
          </Chip>
          <span className={`${textStyles.caption} text-lia-text-tertiary`}>
            Entrevista agendada
          </span>
        </div>

        {/* Candidate and Job Info */}
        <div className="space-y-1">
          <h4 className={`${textStyles.title}`}>
            {interview.candidateName}
          </h4>
          <p className={`${textStyles.subtitle}`}>
            {interview.jobTitle}
          </p>
        </div>

        {/* Date, Time, and Platform Info */}
        <div className="space-y-1.5 bg-lia-bg-secondary dark:bg-lia-bg-primary/30 rounded-xl p-2.5">
          {/* Date and Time */}
          <div className="flex items-center gap-2">
            <Calendar className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0" />
            <span className={`${textStyles.bodySmall}`}>
              {dateStr}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <Clock className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0" />
            <span className={`${textStyles.bodySmall}`}>
              {timeStr} ({interview.duration}min)
            </span>
          </div>

          {/* Platform */}
          <div className="flex items-center gap-2">
            {getPlatformIcon(interview.platform)}
            <span className={`${textStyles.bodySmall}`}>
              {getPlatformLabel(interview.platform)}
            </span>
          </div>

          {/* Interviewer */}
          <div className="flex items-center gap-2">
            <Users className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0" />
            <span className={`${textStyles.bodySmall}`}>
              {interview.interviewerName}
            </span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 pt-1">
          <Button
            onClick={() => onPrepareNotes(interview.id)}
            className="flex-1 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active font-medium rounded-md px-3 py-1.5 transition-colors motion-reduce:transition-none text-xs h-auto"
          >
            <MessageSquare className="w-3.5 h-3.5 mr-1.5" />
            Preparar Notas
          </Button>
          <Button
            onClick={() => onViewSuggestedQuestions(interview.id)}
            variant="outline"
            className="flex-1 border border-lia-border-subtle hover:bg-lia-bg-secondary dark:border-lia-border-subtle dark:hover:bg-lia-btn-primary-bg/50 text-lia-text-primary font-medium rounded-xl px-3 py-1.5 transition-colors motion-reduce:transition-none text-xs h-auto"
          >
            <MessageSquare className="w-3.5 h-3.5 mr-1.5" />
            Perguntas
          </Button>
        </div>
      </div>
    </Card>
  )
}
