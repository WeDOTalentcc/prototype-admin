'use client'

import React, { useState } from 'react'
import { 
  ThumbsUp, ThumbsDown, Linkedin, MapPin, Briefcase, 
  Building, Clock, ExternalLink, Loader2, X, CheckCircle2,
  Brain
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import { Textarea } from '@/components/ui/textarea'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

export interface CalibrationCandidate {
  id: string
  name: string
  current_title: string
  current_company: string
  location: string
  years_experience: number
  skills: string[]
  avatar_url?: string
  linkedin_url?: string
  summary?: string
  lia_score?: number
}

interface CalibrationProgress {
  currentIndex: number
  totalRequired: number
  likesCount: number
  dislikesCount: number
  isComplete: boolean
  sourcingBlocked: boolean
}

interface CalibrationCardProps {
  candidate: CalibrationCandidate
  onLike: (candidateId: string) => void
  onDislike: (candidateId: string, reason?: string) => void
  isLoading?: boolean
  className?: string
  progress?: CalibrationProgress
}

export function CalibrationCard({ 
  candidate, 
  onLike, 
  onDislike,
  isLoading = false,
  className,
  progress
}: CalibrationCardProps) {
  const [showReasonInput, setShowReasonInput] = useState(false)
  const [dislikeReason, setDislikeReason] = useState('')
  const [feedbackGiven, setFeedbackGiven] = useState<'like' | 'dislike' | null>(null)

  const progressPercentage = progress 
    ? Math.round((progress.currentIndex / progress.totalRequired) * 100)
    : 0
  const feedbacksRemaining = progress 
    ? Math.max(0, progress.totalRequired - progress.currentIndex)
    : 0

  const handleLike = () => {
    if (isLoading || feedbackGiven) return
    setFeedbackGiven('like')
    onLike(candidate.id)
  }

  const handleDislike = () => {
    if (isLoading || feedbackGiven) return
    setShowReasonInput(true)
  }

  const submitDislike = () => {
    setFeedbackGiven('dislike')
    setShowReasonInput(false)
    onDislike(candidate.id, dislikeReason || undefined)
  }

  const cancelDislike = () => {
    setShowReasonInput(false)
    setDislikeReason('')
  }

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .substring(0, 2)
      .toUpperCase()
  }

  return (
    <Card className={cn(
      "w-full border transition-all duration-200",
      feedbackGiven === 'like' && "border-status-success/30 bg-status-success/10/50 dark:bg-status-success/10",
      feedbackGiven === 'dislike' && "border-gray-300 bg-gray-50/50 dark:bg-gray-900/10 opacity-60",
      !feedbackGiven && "border-gray-100 dark:border-gray-700 hover:bg-gray-50 hover:border-gray-200 hover:",
      className
    )}>
      {progress && (
        <CardHeader className="p-3 pb-0">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
                <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                {progress.isComplete ? (
                  <span className="text-status-success font-medium flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Calibração completa! Sourcing liberado.
                  </span>
                ) : (
                  <span>
                    Candidato {progress.currentIndex + 1} de {progress.totalRequired} - Avalie para eu aprender seu perfil
                  </span>
                )}
              </span>
              <span className="text-gray-600 dark:text-gray-400 font-medium">
                {progressPercentage}%
              </span>
            </div>
            <Progress 
              value={progressPercentage} 
              className="h-1.5 bg-gray-100 dark:bg-gray-800"
            />
            {!progress.isComplete && feedbacksRemaining > 0 && (
              <p className="text-xs text-gray-800 dark:text-gray-200">
                {feedbacksRemaining === 1 
                  ? 'Falta apenas 1 avaliação para liberar o sourcing automático'
                  : `Faltam ${feedbacksRemaining} avaliações para liberar o sourcing automático`
                }
              </p>
            )}
            {progress.sourcingBlocked && !progress.isComplete && (
              <div className="flex items-center gap-1.5 text-xs text-status-warning dark:text-status-warning bg-status-warning/10 dark:bg-status-warning/20 rounded-full px-2 py-1">
                <span>Sourcing automático bloqueado até completar a calibração</span>
              </div>
            )}
          </div>
        </CardHeader>
      )}
      <CardContent className="p-3">
        <div className="flex gap-3">
          <div className="flex-shrink-0">
            <Avatar className="w-12 h-12 border-2 border-white dark:border-gray-800">
              {candidate.avatar_url ? (
                <AvatarImage src={candidate.avatar_url} alt={candidate.name} />
              ) : null}
              <AvatarFallback className="bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 text-sm font-medium">
                {getInitials(candidate.name)}
              </AvatarFallback>
            </Avatar>
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2 mb-1">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-semibold text-gray-950 dark:text-gray-50 truncate">
                    {candidate.name}
                  </h4>
                  {candidate.linkedin_url && (
                    <a
                      href={candidate.linkedin_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-gray-600 hover:text-gray-700 transition-colors"
                      title="Ver perfil no LinkedIn"
                    >
                      <Linkedin className="w-3.5 h-3.5" />
                    </a>
                  )}
                  {candidate.lia_score && (
                    <Badge className="text-xs py-0 px-1.5 bg-gray-100 text-gray-800 dark:text-gray-200 border-gray-200">
                      Score: {candidate.lia_score}
                    </Badge>
                  )}
                </div>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <Briefcase className="w-3 h-3 text-gray-600" />
                  <span className="text-xs text-gray-600 dark:text-gray-400 truncate">
                    {candidate.current_title}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400 mb-2">
              {candidate.current_company && (
                <div className="flex items-center gap-1">
                  <Building className="w-3 h-3" />
                  <span className="truncate max-w-[100px]">{candidate.current_company}</span>
                </div>
              )}
              {candidate.location && (
                <div className="flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  <span className="truncate max-w-20">{candidate.location}</span>
                </div>
              )}
              {candidate.years_experience > 0 && (
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  <span>{candidate.years_experience} anos</span>
                </div>
              )}
            </div>

            {candidate.summary && (
              <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2 mb-2">
                {candidate.summary}
              </p>
            )}

            {candidate.skills && candidate.skills.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-2">
                {candidate.skills.slice(0, 5).map((skill) => (
                  <Badge 
                    key={skill} 
                    variant="secondary"
                    className="text-xs py-0 px-1.5 bg-gray-100 dark:bg-gray-800"
                  >
                    {skill}
                  </Badge>
                ))}
                {candidate.skills.length > 5 && (
                  <Badge 
                    variant="outline"
                    className="text-xs py-0 px-1.5"
                  >
                    +{candidate.skills.length - 5}
                  </Badge>
                )}
              </div>
            )}

            {!feedbackGiven && !showReasonInput && (
              <div className="flex items-center gap-2 pt-1">
                <Button
                  size="sm"
                  className="flex-1 h-8 text-xs gap-1.5 bg-status-success hover:bg-status-success text-white"
                  onClick={handleLike}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <ThumbsUp className="w-3.5 h-3.5" />
                  )}
                  Interessante
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="flex-1 h-8 text-xs gap-1.5 hover:bg-gray-100 dark:hover:bg-gray-800"
                  onClick={handleDislike}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <ThumbsDown className="w-3.5 h-3.5" />
                  )}
                  Não é o perfil
                </Button>
              </div>
            )}

            {showReasonInput && (
              <div className="space-y-2 pt-1">
                <Textarea
                  placeholder="Por que este perfil não é adequado? (opcional)"
                  value={dislikeReason}
                  onChange={(e) => setDislikeReason(e.target.value)}
                  className="text-xs h-16 resize-none"
                />
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1 h-7 text-xs"
                    onClick={cancelDislike}
                  >
                    <X className="w-3 h-3 mr-1" />
                    Cancelar
                  </Button>
                  <Button
                    size="sm"
                    className="flex-1 h-7 text-xs bg-gray-600 hover:bg-gray-700"
                    onClick={submitDislike}
                  >
                    <ThumbsDown className="w-3 h-3 mr-1" />
                    Confirmar
                  </Button>
                </div>
              </div>
            )}

            {feedbackGiven && (
              <div className={cn(
                "flex items-center gap-2 pt-1 text-xs",
                feedbackGiven === 'like' ? "text-status-success" : "text-gray-800 dark:text-gray-200"
              )}>
                {feedbackGiven === 'like' ? (
                  <>
                    <ThumbsUp className="w-3.5 h-3.5" />
                    <span>Feedback registrado - Perfil interessante</span>
                  </>
                ) : (
                  <>
                    <ThumbsDown className="w-3.5 h-3.5" />
                    <span>Feedback registrado - Não é o perfil</span>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
