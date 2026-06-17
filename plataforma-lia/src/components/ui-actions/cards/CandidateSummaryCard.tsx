"use client"

import React from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  MapPin,
  Briefcase,
  GraduationCap,
  DollarSign,
  ExternalLink,
  Star,
  ThumbsUp,
  ThumbsDown,
  Calendar
} from "lucide-react"
import { CandidateAvatar } from "@/components/candidate-profile/CandidateAvatar"
import { CandidateScoreBadge } from "@/components/candidate-profile/CandidateScoreBadge"
import { CandidateSkillsList } from "@/components/candidate-profile/CandidateSkillsList"

interface CandidateSummaryData {
  id: string
  name: string
  title: string
  avatar_url?: string
  location?: string
  experience_years?: number
  education?: string
  current_company?: string
  salary_expectation?: string
  email?: string
  phone?: string
  linkedin_url?: string
  skills?: string[]
  match_score?: number
  highlights?: string[]
  concerns?: string[]
}

interface CandidateSummaryCardProps {
  data: CandidateSummaryData
  onApprove?: () => void
  onReject?: () => void
  onSchedule?: () => void
  onViewProfile?: () => void
  compact?: boolean
}

export function CandidateSummaryCard({
  data,
  onApprove,
  onReject,
  onSchedule,
  onViewProfile,
  compact = false
}: CandidateSummaryCardProps) {
  return (
    <Card
      className="w-full max-w-md border-l-4 overflow-hidden bg-lia-bg-secondary"
     
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          <CandidateAvatar
            name={data.name}
            avatarUrl={data.avatar_url}
            size="lg"
            className="border-2 border-lia-bg-primary"
          />

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h4 className="font-semibold truncate text-lia-text-primary">
                  {data.name}
                </h4>
                <p className="text-sm truncate text-lia-text-secondary">
                  {data.title}
                </p>
              </div>
              {data.match_score !== undefined && (
                <CandidateScoreBadge score={data.match_score} format="percent" />
              )}
            </div>

            {!compact && (
              <div className="mt-3 space-y-1.5 text-sm text-lia-text-secondary">
                {data.location && (
                  <div className="flex items-center gap-2">
                    <MapPin className="h-3.5 w-3.5 text-lia-text-tertiary" />
                    <span>{data.location}</span>
                  </div>
                )}
                {data.experience_years !== undefined && (
                  <div className="flex items-center gap-2">
                    <Briefcase className="h-3.5 w-3.5 text-lia-text-tertiary" />
                    <span>{data.experience_years} anos de experiência</span>
                  </div>
                )}
                {data.current_company && (
                  <div className="flex items-center gap-2">
                    <GraduationCap className="h-3.5 w-3.5 text-lia-text-tertiary" />
                    <span>{data.current_company}</span>
                  </div>
                )}
                {data.salary_expectation && (
                  <div className="flex items-center gap-2">
                    <DollarSign className="h-3.5 w-3.5 text-lia-text-secondary" />
                    <span>{data.salary_expectation}</span>
                  </div>
                )}
              </div>
            )}

            {data.skills && data.skills.length > 0 && (
              <CandidateSkillsList
                skills={data.skills}
                maxVisible={compact ? 3 : 5}
                className="mt-3"
              />
            )}

            {!compact && data.highlights && data.highlights.length > 0 && (
              <div className="mt-3 space-y-1">
                {data.highlights.slice(0, 2).map((highlight, index) => (
                  <div
                    key={`highlight-${index}`}
                    className="flex items-start gap-2 text-xs px-2 py-1 rounded-xl bg-lia-bg-tertiary text-lia-text-secondary"
                  >
                    <ThumbsUp className="h-3 w-3 mt-0.5 shrink-0 text-wedo-green" />
                    <span>{highlight}</span>
                  </div>
                ))}
              </div>
            )}

            {!compact && data.concerns && data.concerns.length > 0 && (
              <div className="mt-2 space-y-1">
                {data.concerns.slice(0, 1).map((concern, index) => (
                  <div
                    key={`concern-${index}`}
                    className="flex items-start gap-2 text-xs px-2 py-1 rounded-xl bg-lia-bg-tertiary text-lia-text-secondary"
                  >
                    <ThumbsDown className="h-3 w-3 mt-0.5 shrink-0 text-lia-text-secondary" />
                    <span>{concern}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {(onApprove || onReject || onSchedule || onViewProfile) && (
          <div
            className="mt-4 pt-3 border-t flex items-center gap-2 flex-wrap border-lia-border-subtle"
          >
            {onApprove && (
              <Button
                size="sm"
                variant="outline"
                className="hover:bg-opacity-10 border-lia-border-default text-lia-text-primary"
                onClick={onApprove}
              >
                <ThumbsUp className="h-3.5 w-3.5 mr-1.5 text-wedo-green" />
                Aprovar
              </Button>
            )}
            {onReject && (
              <Button
                size="sm"
                variant="outline"
                className="hover:bg-opacity-10 border-lia-border-default text-lia-text-primary"
                onClick={onReject}
              >
                <ThumbsDown className="h-3.5 w-3.5 mr-1.5 text-wedo-magenta" />
                Reprovar
              </Button>
            )}
            {onSchedule && (
              <Button
                size="sm"
                variant="outline"
                className="border-lia-border-default text-lia-text-primary"
                onClick={onSchedule}
              >
                <Calendar className="h-3.5 w-3.5 mr-1.5" />
                Agendar
              </Button>
            )}
            {onViewProfile && (
              <Button
                size="sm"
                variant="ghost"
                className="ml-auto text-lia-text-secondary"
                onClick={onViewProfile}
              >
                Ver Perfil
                <ExternalLink className="h-3.5 w-3.5 ml-1.5" />
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
