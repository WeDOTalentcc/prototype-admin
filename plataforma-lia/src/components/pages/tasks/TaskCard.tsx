"use client"

import React from"react"
import { useRouter } from "next/navigation"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import {
  CheckCircle, XCircle,
  MessageSquare, Calendar, Search, FileText, Users,
  User, Briefcase, ExternalLink
} from"lucide-react"
import { getTaskPriorityStyle, getPriorityLabel, getTaskTypeIcon } from"../task-helpers"

interface Task {
  id: string
  type: string
  title: string
  description: string
  priority: string
  dueDate: Date
  candidateName?: string
  relatedJob?: string
  relatedJobId?: string
  relatedCandidateId?: string
  rawTaskType?: string
}

interface TaskCardProps {
  task: Task
  onConfirm: (task: Task) => void
  onReject: (task: Task) => void
}

interface CTA {
  label: string
  icon: React.ComponentType<{ className?: string }>
  href: string
  variant?: "outline" | "secondary"
}

function getTaskCTAs(rawTaskType: string | undefined, jobId?: string, candidateId?: string): CTA[] {
  const candidateHref = candidateId ? `/funil-de-talentos/candidato/${candidateId}` : null
  const jobHref = jobId ? `/jobs/${jobId}` : null

  switch (rawTaskType) {
    case 'cv_review':
      return [
        ...(candidateHref ? [{ label: 'Ver CV', icon: FileText, href: candidateHref }] : []),
        ...(jobHref ? [{ label: 'Ver Vaga', icon: Briefcase, href: jobHref, variant: 'outline' as const }] : []),
      ]
    case 'feedback_pending':
      return [
        ...(candidateHref ? [{ label: 'Dar Feedback', icon: MessageSquare, href: candidateHref }] : []),
        ...(jobHref ? [{ label: 'Ver Vaga', icon: Briefcase, href: jobHref, variant: 'outline' as const }] : []),
      ]
    case 'interview_schedule':
    case 'interview_prep':
      return [
        ...(candidateHref ? [{ label: 'Ver Candidato', icon: User, href: candidateHref }] : []),
        ...(jobHref ? [{ label: 'Ver Vaga', icon: Calendar, href: jobHref, variant: 'outline' as const }] : []),
      ]
    case 'follow_up':
      return [
        ...(candidateHref ? [{ label: 'Ver Candidato', icon: User, href: candidateHref }] : []),
        ...(jobHref ? [{ label: 'Ver Vaga', icon: Briefcase, href: jobHref, variant: 'outline' as const }] : []),
      ]
    case 'sourcing':
    case 'candidate_outreach':
      return jobHref
        ? [{ label: 'Ver Vaga', icon: Search, href: jobHref }]
        : [{ label: 'Recrutar', icon: Users, href: '/recrutar' }]
    case 'send_report':
      return jobHref ? [{ label: 'Ver Relatório', icon: ExternalLink, href: jobHref }] : []
    case 'general':
    default:
      return jobHref ? [{ label: 'Ver Vaga', icon: Briefcase, href: jobHref, variant: 'outline' as const }] : []
  }
}

export const TaskCard = React.memo(function TaskCard({ task, onConfirm, onReject }: TaskCardProps) {
  const router = useRouter()
  const ctas = getTaskCTAs(task.rawTaskType, task.relatedJobId, task.relatedCandidateId)

  return (
    <div data-testid={`task-card-${task.id}`} className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-lg p-2.5 hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none bg-lia-bg-primary dark:bg-lia-bg-primary">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start gap-2 flex-1">
          <div className="w-6 h-6 rounded-xl flex items-center justify-center flex-shrink-0 bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
            {getTaskTypeIcon(task.type as 'feedback' | 'entrevista' | 'sourcing')}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 flex-wrap mb-0.5">
              <span className="text-xs font-inter font-medium text-lia-text-primary">
                {task.dueDate.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
              </span>
              <h4 className="text-xs font-inter font-semibold text-lia-text-primary">
                {task.title}
              </h4>
              <Chip variant="neutral" muted
                className={`border-0 text-micro py-0 px-1.5 font-medium ${getTaskPriorityStyle(task.priority as 'high' | 'medium' | 'low') ??""}`}
              >
                {getPriorityLabel(task.priority as 'high' | 'medium' | 'low')}
              </Chip>
            </div>
            <p className="text-xs font-open-sans text-lia-text-primary mb-1 line-clamp-1">
              {task.description}
            </p>
            <div className="flex items-center gap-2 text-xs text-lia-text-primary">
              {task.candidateName && (
                <span className="flex items-center gap-0.5">
                  <User className="w-2.5 h-2.5" />
                  {task.candidateName}
                </span>
              )}
              {task.relatedJob && (
                <span className="flex items-center gap-0.5">
                  <Briefcase className="w-2.5 h-2.5" />
                  {task.relatedJob}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-1 flex-shrink-0">
          {ctas.length > 0 && (
            <div className="flex items-center gap-1">
              {ctas.map((cta) => {
                const Icon = cta.icon
                return (
                  <Button
                    key={cta.href}
                    size="sm"
                    {...(cta.variant ? { variant: cta.variant } : {})}
                    onClick={() => router.push(cta.href)}
                    className="h-5 px-2 text-xs gap-1 border-0"
                  >
                    <Icon className="w-2.5 h-2.5" />
                    {cta.label}
                  </Button>
                )
              })}
            </div>
          )}
          <div className="flex items-center gap-1">
            <Button
              data-testid="task-confirm-btn"
              size="sm"
              variant="ghost"
              onClick={() => onConfirm(task)}
              className="h-5 px-1.5 text-xs gap-0.5"
            >
              <CheckCircle className="w-2.5 h-2.5" />
              Confirmar
            </Button>
            <Button
              data-testid="task-reject-btn"
              size="sm"
              variant="ghost"
              onClick={() => onReject(task)}
              className="h-5 px-1.5 text-xs gap-0.5 text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
            >
              <XCircle className="w-2.5 h-2.5" />
              Rejeitar
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
})

export default TaskCard
