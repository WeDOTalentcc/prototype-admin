"use client"

import React from"react"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import {
  Clock, Eye, Edit, Share2, FileText, Users, Briefcase,
  MoreVertical, MapPin, Brain, Copy, Trash2, User, Linkedin, Globe
} from"lucide-react"
import { getUrgencyBadge, getConversionRate, getAlertIcon, getAlertStyle, getAlertColor } from"../task-helpers"
import type { JobWithAlert } from"../use-tasks-core"
import { useUIPreferencesStore } from"@/stores/ui-preferences-store"
import { JobAgentDot } from "./JobAgentDot"

interface JobListItemProps {
  job: JobWithAlert
  onLIAAction: (action: string, job: JobWithAlert) => void
  onNavigate?: (page: string) => void
}

export function JobListItem({ job, onLIAAction, onNavigate }: JobListItemProps) {
  return (
    <div className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl p-3 hover:border-lia-border-medium dark:hover:border-lia-border-medium hover:shadow-sm transition-shadow transition-[color,background-color,border-color] duration-200 bg-lia-bg-primary dark:bg-lia-bg-primary cursor-pointer">
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-sm text-lia-text-primary">{job.title}</h3>
            {/* Onda 2 F4 — pingo cyan estatico quando ha agentes acoplados a esta vaga. */}
            <JobAgentDot targetId={job.id} />
            <Chip density="relaxed" variant="neutral" >{job.jobId}</Chip>
            {getUrgencyBadge(job.urgencyLevel, job.daysOpen)}
            {job.publishedLinkedIn && (
              <Chip density="relaxed" variant="neutral" muted className="border-transparent dark:bg-wedo-cyan/20 dark:text-wedo-cyan flex items-center gap-1 font-medium">
                <Linkedin className="w-2.5 h-2.5" />
                LI
              </Chip>
            )}
            {job.publishedWebsite && (
              <Chip density="relaxed" variant="neutral" muted className="border-transparent dark:bg-wedo-green/20 dark:text-wedo-green flex items-center gap-1 font-medium">
                <Globe className="w-2.5 h-2.5" />
                Site
              </Chip>
            )}
            {job.publishedIndeed && (
              <Chip density="relaxed" variant="neutral" muted className="border-transparent dark:bg-wedo-orange/20 dark:text-wedo-orange flex items-center gap-1 font-medium">
                <Briefcase className="w-2.5 h-2.5" />
                Indeed
              </Chip>
            )}
          </div>
          <div className="flex items-center gap-3 text-xs text-lia-text-primary flex-wrap">
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              <span className="font-medium">{job.daysOpen}d</span>
            </div>
            <span className="text-lia-text-tertiary">•</span>
            <div className="flex items-center gap-1">
              <User className="w-3 h-3" />
              <span>{job.manager.split(' ')[0]}</span>
            </div>
            <span className="text-lia-text-tertiary">•</span>
            <div className="flex items-center gap-1">
              <MapPin className="w-3 h-3" />
              <span>{job.department}</span>
            </div>
            <span className="text-lia-text-tertiary">•</span>
            <div className="flex items-center gap-1">
              <Users className="w-3 h-3" />
              <span>{job.totalCandidates} candidatos</span>
            </div>
          </div>
        </div>
        <div className="relative group">
          <Button variant="ghost" size="sm" className="h-6 w-6 p-0" aria-label="Ações da vaga">
            <MoreVertical className="w-3.5 h-3.5" />
          </Button>
          <div className="absolute right-0 top-full mt-1 w-48 bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-opacity motion-reduce:transition-none duration-200 z-10">
            <div className="py-1">
              {([
                { action: 'kanban', icon: <Eye className="w-3 h-3" />, label: 'Ver Kanban Completo' },
                { action: 'report', icon: <FileText className="w-3 h-3" />, label: 'Gerar Relatório' },
                { action: 'share', icon: <Share2 className="w-3 h-3" />, label: 'Compartilhar Vaga' },
                { action: 'edit', icon: <Edit className="w-3 h-3" />, label: 'Editar Requisitos' },
                { action: 'duplicate', icon: <Copy className="w-3 h-3" />, label: 'Duplicar Vaga' },
              ] as const).map(({ action, icon, label }) => (
                <button
                  key={action}
                  onClick={() => onLIAAction(action, job)}
                  className="w-full px-3 py-2 text-left text-xs hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover hover:text-lia-text-primary dark:hover:text-lia-text-inverse transition-colors motion-reduce:transition-none flex items-center gap-2"
                >
                  {icon}
                  {label}
                </button>
              ))}
              <div className="mt-1"></div>
              <button
                onClick={() => onLIAAction('cancel', job)}
                className="w-full px-3 py-2 text-left text-xs hover:bg-status-error/10 dark:hover:bg-status-error/20 text-status-error hover:text-status-error dark:hover:text-status-error transition-colors motion-reduce:transition-none flex items-center gap-2"
              >
                <Trash2 className="w-3 h-3" />
                Cancelar Vaga
              </button>
            </div>
          </div>
        </div>
      </div>

      <JobFunnel stages={job.stages} />

      <div className="flex items-center gap-1.5">
        {job.liaPendencies.length > 0 && (
          <div className="flex items-center gap-1 bg-lia-bg-tertiary dark:bg-lia-bg-secondary border border-lia-border-default dark:border-lia-border-subtle rounded-lg px-1.5 py-1 flex-1">
            <Brain className="w-2.5 h-2.5 text-wedo-cyan flex-shrink-0" />
            <span className="text-xs text-lia-text-primary truncate font-medium">
              {job.liaPendencies.length} pendência{job.liaPendencies.length > 1 ? 's' : ''}
            </span>
          </div>
        )}

        <div
          className={`flex items-center gap-1 ${getAlertColor(job.alert.type)} ${getAlertStyle(job.alert.type)} rounded-lg px-1.5 py-1 flex-1`}
        >
          {getAlertIcon(job.alert.type)}
          <span className="text-xs font-medium truncate flex-1">{job.alert.message}</span>
          <Button
            size="sm"
            className="gap-0.5 h-4 text-xs px-1 hover:scale-105 transition-transform motion-reduce:transition-none flex-shrink-0"
            onClick={() => {
              const actionPrompt = `${job.alert.action} para a vaga ${job.title} (${job.jobId})`
              useUIPreferencesStore.getState().setLiaPrompt(actionPrompt)
              if (onNavigate) {
                onNavigate('Chat com LIA')
              }
            }}
          >
            {job.alert.action}
          </Button>
        </div>
      </div>
    </div>
  )
}

interface JobFunnelProps {
  stages: JobWithAlert['stages']
}

function JobFunnel({ stages }: JobFunnelProps) {
  const funnelSteps = [
    { key: 'new' as const, label: 'Novos' },
    { key: 'uncontacted' as const, label: 'Triag' },
    { key: 'contacted' as const, label: 'Cont' },
    { key: 'replied' as const, label: 'Resp' },
    { key: 'phoneScreen' as const, label: 'Tel' },
    { key: 'onsite' as const, label: 'Entrev' },
    { key: 'makeOffer' as const, label: 'Ofert' },
    { key: 'hired' as const, label: 'Contr' },
  ]

  return (
    <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-lg p-1.5 mb-1.5">
      <div className="flex items-center justify-between gap-1">
        {funnelSteps.map((step, idx) => (
          <React.Fragment key={step.key}>
            {idx > 0 && (
              <div className="flex flex-col items-center">
                <span className={`text-xs font-medium ${getConversionRate(stages[funnelSteps[idx - 1].key], stages[step.key])}`}>
                  {getConversionRate(stages[funnelSteps[idx - 1].key], stages[step.key])}%
                </span>
                <span className="text-xs text-lia-text-primary">→</span>
              </div>
            )}
            <div className="flex flex-col items-center">
              <span className="text-xs font-medium text-lia-text-primary">{stages[step.key]}</span>
              <span className="text-xs text-lia-text-primary uppercase">{step.label}</span>
            </div>
          </React.Fragment>
        ))}
      </div>
    </div>
  )
}
