"use client"

import React from"react"
import { Button } from"@/components/ui/button"
import { Avatar, AvatarImage, AvatarFallback } from"@/components/ui/avatar"
import { Chip } from "@/components/ui/chip"
import {
  ExternalLink, CalendarClock, XCircle as XCircleIcon,
  Briefcase, Building2, User, Check, Share2
} from"lucide-react"
import type { ScheduledInterview } from"./tasks-page-utils"
import {
  getPlatformIcon, getPlatformLabel, getAvatarUrl, getInitials,
  getStatusLabel, getStatusClasses, getStatusIcon
} from"./tasks-page-utils"

interface InterviewCardProps {
  interview: ScheduledInterview
  copiedId: string | null
  onOpenMeeting: (interview: ScheduledInterview) => void
  onCopyLink: (interview: ScheduledInterview) => void
  onReschedule?: (interview: ScheduledInterview) => void
  onReject?: (interview: ScheduledInterview) => void
  onOpenJob: (interview: ScheduledInterview) => void
  variant: 'active' | 'past'
}

export function InterviewCard({
  interview,
  copiedId,
  onOpenMeeting,
  onCopyLink,
  onReschedule,
  onReject,
  onOpenJob,
  variant,
}: InterviewCardProps) {
  const renderJobLink = () => {
    if (!interview.jobCode && !interview.jobTitle) return null
    return (
      <button
        onClick={() => onOpenJob(interview)}
        className="text-xs font-medium text-wedo-cyan-text dark:text-wedo-cyan-dark hover:text-wedo-cyan-dark dark:hover:text-wedo-cyan-dark hover:underline truncate cursor-pointer"
        title="Abrir vaga no kanban"
      >
        {interview.jobCode && <span className="font-[Inter,sans-serif] mr-0.5">{interview.jobCode}</span>}
        {interview.jobTitle}
      </button>
    )
  }

  const renderCandidateInfo = () => (
    <div className="grid grid-cols-2 gap-4 text-xs">
      <div className="space-y-0.5 min-w-0">
        <span className="text-base-ui font-medium text-lia-text-primary truncate block">
          {interview.candidateName}
        </span>
        {interview.candidateRole && (
          <span className="flex items-center gap-1 text-lia-text-tertiary truncate">
            <Briefcase className="w-3 h-3 flex-shrink-0" />
            {interview.candidateRole}
          </span>
        )}
        {interview.company && (
          <span className="flex items-center gap-1 text-lia-text-tertiary truncate">
            <Building2 className="w-3 h-3 flex-shrink-0" />
            {interview.company}
          </span>
        )}
      </div>
      <div className="space-y-0.5 min-w-0">
        {renderJobLink()}
        {interview.jobManager && (
          <span className="flex items-center gap-1 text-lia-text-tertiary truncate">
            <User className="w-3 h-3 flex-shrink-0" />
            {interview.jobManager}
          </span>
        )}
      </div>
    </div>
  )

  return (
    <div
      className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl p-3.5 bg-lia-bg-primary dark:bg-lia-bg-primary transition-colors motion-reduce:transition-none duration-150 hover:border-lia-border-default dark:hover:border-lia-border-medium"
    >
      <div className="flex gap-3">
        <Avatar className="w-10 h-10 flex-shrink-0 mt-0.5">
          <AvatarImage src={interview.candidateAvatar || getAvatarUrl(interview.id, interview.candidateName)} />
          <AvatarFallback className="text-micro font-medium text-lia-text-secondary bg-wedo-cyan/15">
            {getInitials(interview.candidateName)}
          </AvatarFallback>
        </Avatar>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 mb-1">
            <div className="flex items-center gap-1.5 min-w-0">
              <span className="text-base-ui font-[Inter,sans-serif] font-semibold text-lia-text-primary tabular-nums">
                {interview.time}
              </span>
              <span className="text-lia-text-disabled">·</span>
              <span className="text-sm-ui font-semibold text-lia-text-primary truncate">
                {interview.type}
              </span>
              <span className="text-lia-text-disabled">·</span>
              <span className="text-xs text-lia-text-tertiary flex items-center gap-1">
                {getPlatformIcon(interview.platform)}
                {getPlatformLabel(interview.platform)}
                <button
                  onClick={(e) => { e.stopPropagation(); onCopyLink(interview) }}
                  className="ml-0.5 text-lia-text-disabled hover:text-lia-text-secondary transition-colors motion-reduce:transition-none"
                  title={copiedId === interview.id ? 'Link copiado!' : 'Copiar link da reunião'}
                >
                  {copiedId === interview.id ? <Check className="w-3.5 h-3.5 text-status-success stroke-[2.5]" /> : <Share2 className="w-3.5 h-3.5 stroke-[2.5]" />}
                </button>
              </span>
              <span className="text-lia-text-disabled">·</span>
              <span className="text-xs font-[Inter,sans-serif] tabular-nums text-lia-text-tertiary">
                {interview.duration}min
              </span>
              {variant === 'past' && (
                <Chip variant="neutral" muted className={`text-micro px-1.5 py-0 ml-1 border font-medium flex items-center gap-1 ${getStatusClasses(interview.status)}`}>
                  {getStatusIcon(interview.status)}
                  {getStatusLabel(interview.status)}
                </Chip>
              )}
            </div>

            <div className="flex items-center gap-1.5 flex-shrink-0">
              <Button
                size="sm"
                onClick={() => onOpenMeeting(interview)}
                className="h-7 px-3 text-xs font-medium gap-1.5 bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover rounded-md"
              >
                <ExternalLink className="w-3 h-3" />
                Abrir Reunião
              </Button>
              {variant === 'active' && onReschedule && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onReschedule(interview)}
                  className="h-7 px-2.5 text-xs font-medium gap-1 text-lia-text-secondary border-lia-border-default hover:bg-lia-bg-secondary hover:border-lia-border-medium dark:border-lia-border-default dark:hover:bg-lia-btn-primary-hover rounded-xl"
                >
                  <CalendarClock className="w-3 h-3" />
                  Alterar Horário
                </Button>
              )}
              {variant === 'active' && onReject && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onReject(interview)}
                  className="h-7 px-2.5 text-xs font-medium gap-1 text-status-error border-status-error/30 hover:bg-status-error/10 hover:border-status-error/30 dark:text-status-error dark:border-status-error/30 dark:hover:bg-status-error/20 rounded-md"
                >
                  <XCircleIcon className="w-3 h-3" />
                  Cancelar
                </Button>
              )}
              {variant === 'past' && (
                <span className="text-xs font-[Inter,sans-serif] text-lia-text-tertiary tabular-nums">
                  {interview.completedAt || interview.cancelledAt}
                </span>
              )}
            </div>
          </div>

          {renderCandidateInfo()}

          {variant === 'past' && interview.cancelReason && (
            <p className="text-xs text-lia-text-disabled italic mt-1.5">
              {interview.cancelReason}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
