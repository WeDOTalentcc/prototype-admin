"use client"

import React from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { 
  MapPin, 
  Briefcase, 
  GraduationCap, 
  DollarSign, 
  Mail, 
  Phone,
  Linkedin,
  ExternalLink,
  Star,
  ThumbsUp,
  ThumbsDown,
  Calendar
} from "lucide-react"

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
  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2)
  }

  const getScoreLevel = (score: number) => {
    if (score >= 80) return "high"
    if (score >= 60) return "medium"
    return "low"
  }

  return (
    <Card 
      className="w-full max-w-md border-l-4 overflow-hidden"
      style={{backgroundColor: 'var(--lia-bg-secondary)',
        borderLeftColor: 'var(--lia-border-default)'}}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          <Avatar className="h-12 w-12 border-2" style={{borderColor: 'var(--lia-bg-primary)'}}>
            <AvatarImage src={data.avatar_url} alt={data.name} />
            <AvatarFallback 
              className="font-medium"
              style={{backgroundColor: 'var(--lia-bg-tertiary)', 
                color: 'var(--lia-text-primary)'}}
            >
              {getInitials(data.name)}
            </AvatarFallback>
          </Avatar>

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h4 className="font-semibold truncate" style={{color: 'var(--lia-text-primary)'}}>
                  {data.name}
                </h4>
                <p className="text-sm truncate" style={{color: 'var(--lia-text-secondary)'}}>
                  {data.title}
                </p>
              </div>
              {data.match_score !== undefined && (
                <Badge 
                  variant="outline" 
                  className="shrink-0"
                  style={{borderColor: 'var(--lia-border-default)',
                    backgroundColor: 'var(--lia-bg-primary)',
                    color: 'var(--lia-text-primary)'}}
                >
                  <Star className="h-3 w-3 mr-1 text-gray-600 dark:text-gray-400" />
                  {data.match_score}%
                </Badge>
              )}
            </div>

            {!compact && (
              <div className="mt-3 space-y-1.5 text-sm" style={{color: 'var(--lia-text-secondary)'}}>
                {data.location && (
                  <div className="flex items-center gap-2">
                    <MapPin className="h-3.5 w-3.5" style={{color: 'var(--lia-text-tertiary)'}} />
                    <span>{data.location}</span>
                  </div>
                )}
                {data.experience_years !== undefined && (
                  <div className="flex items-center gap-2">
                    <Briefcase className="h-3.5 w-3.5" style={{color: 'var(--lia-text-tertiary)'}} />
                    <span>{data.experience_years} anos de experiência</span>
                  </div>
                )}
                {data.current_company && (
                  <div className="flex items-center gap-2">
                    <GraduationCap className="h-3.5 w-3.5" style={{color: 'var(--lia-text-tertiary)'}} />
                    <span>{data.current_company}</span>
                  </div>
                )}
                {data.salary_expectation && (
                  <div className="flex items-center gap-2">
                    <DollarSign className="h-3.5 w-3.5 text-gray-700 dark:text-gray-300" />
                    <span>{data.salary_expectation}</span>
                  </div>
                )}
              </div>
            )}

            {data.skills && data.skills.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {data.skills.slice(0, compact ? 3 : 5).map((skill, index) => (
                  <Badge 
                    key={index} 
                    variant="secondary" 
                    className="text-xs"
                    style={{backgroundColor: 'var(--lia-bg-tertiary)', 
                      color: 'var(--lia-text-secondary)'}}
                  >
                    {skill}
                  </Badge>
                ))}
                {data.skills.length > (compact ? 3 : 5) && (
                  <Badge 
                    variant="outline" 
                    className="text-xs"
                    style={{borderColor: 'var(--lia-border-subtle)',
                      color: 'var(--lia-text-tertiary)'}}
                  >
                    +{data.skills.length - (compact ? 3 : 5)}
                  </Badge>
                )}
              </div>
            )}

            {!compact && data.highlights && data.highlights.length > 0 && (
              <div className="mt-3 space-y-1">
                {data.highlights.slice(0, 2).map((highlight, index) => (
                  <div 
                    key={index} 
                    className="flex items-start gap-2 text-xs px-2 py-1 rounded"
                    style={{backgroundColor: 'var(--lia-bg-tertiary)',
                      color: 'var(--lia-text-secondary)'}}
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
                    key={index} 
                    className="flex items-start gap-2 text-xs px-2 py-1 rounded"
                    style={{backgroundColor: 'var(--lia-bg-tertiary)',
                      color: 'var(--lia-text-secondary)'}}
                  >
                    <ThumbsDown className="h-3 w-3 mt-0.5 shrink-0 text-gray-700 dark:text-gray-300" />
                    <span>{concern}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {(onApprove || onReject || onSchedule || onViewProfile) && (
          <div 
            className="mt-4 pt-3 border-t flex items-center gap-2 flex-wrap"
            style={{borderColor: 'var(--lia-border-subtle)'}}
          >
            {onApprove && (
              <Button 
                size="sm" 
                variant="outline"
                className="hover:bg-opacity-10"
                style={{borderColor: 'var(--lia-border-default)',
                  color: 'var(--lia-text-primary)'}}
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
                className="hover:bg-opacity-10"
                style={{borderColor: 'var(--lia-border-default)',
                  color: 'var(--lia-text-primary)'}}
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
                style={{borderColor: 'var(--lia-border-default)',
                  color: 'var(--lia-text-primary)'}}
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
                className="ml-auto"
                style={{color: 'var(--lia-text-secondary)'}}
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
