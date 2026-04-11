"use client"

import React from "react"
import { CURRENCY_SYMBOL, formatBRLCompact } from "@/lib/pricing"
import { SCREENING_STATUS_LABELS } from "@/types/screening"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Calendar, Clock, MapPin, DollarSign, Heart, Shield, Building, Lock, Globe,
  Expand, X, ChevronRight,
} from "lucide-react"
import { type Job } from "@/components/jobs"
import { getStatusColor } from "@/components/jobs/jobsPageConstants"

interface JobPreviewHeaderProps {
  previewJob: Job
  onClose: () => void
  onJobClick: (job: Job) => void
}

export function JobPreviewHeader({ previewJob, onClose, onJobClick }: JobPreviewHeaderProps) {
  return (
    <div data-testid="job-preview-header" className="bg-lia-bg-primary dark:bg-lia-bg-primary border-b border-lia-border-subtle">
      <div className="px-3 pt-3 pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-base-ui font-semibold text-lia-text-primary truncate">
                {previewJob.title}
              </h3>
              <Badge className="text-[0.625rem] leading-none px-1.5 py-0.5 flex-shrink-0 font-mono font-medium bg-lia-bg-tertiary text-lia-text-secondary border border-lia-border-default">
                {previewJob.jobId}
              </Badge>
              {previewJob.isAffirmative && (
                <span title="Vaga Afirmativa">
                  <Heart className="w-3 h-3 text-wedo-magenta" />
                </span>
              )}
            </div>

            <div className="flex items-center gap-3 mb-1 text-micro text-lia-text-tertiary">
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3 text-lia-text-disabled" />
                {previewJob.openDate ? new Date(previewJob.openDate).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}
              </span>
              {previewJob.deadline && (
                <span className={`flex items-center gap-1 ${
                  new Date(previewJob.deadline) < new Date() ? 'text-status-error' : 'text-lia-text-tertiary'
                }`}>
                  <Clock className="w-3 h-3" />
                  {(() => {
                    const days = Math.ceil((new Date(previewJob.deadline).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))
                    return days > 0 ? `${days}d restantes` : `${Math.abs(days)}d atraso`
                  })()}
                </span>
              )}
            </div>

            <div className="flex items-center gap-3 mb-1.5 text-micro text-lia-text-disabled">
              <span>Criado: {previewJob.createdAt 
                ? new Date(previewJob.createdAt).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: '2-digit' })
                : previewJob.openDate 
                  ? new Date(previewJob.openDate).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: '2-digit' })
                  : '—'}</span>
              <span>Atualizado: {previewJob.updatedAt 
                ? new Date(previewJob.updatedAt).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })
                : '—'}</span>
              {previewJob.publishedAt && (
                <span>Publicado: {new Date(previewJob.publishedAt).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })}</span>
              )}
              {previewJob.closedAt && (
                <span>Fechado: {new Date(previewJob.closedAt).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })}</span>
              )}
            </div>

            <div className="flex items-center gap-1 flex-wrap">
              {previewJob.department && (
                <Badge className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-secondary border border-lia-border-subtle">
                  {previewJob.department}
                </Badge>
              )}
              {previewJob.level && (
                <Badge className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-status-warning/10 text-status-warning border border-status-warning/30">
                  {previewJob.level}
                </Badge>
              )}
              {previewJob.location && (
                <Badge className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-wedo-cyan/10 text-wedo-cyan-dark border border-wedo-cyan/30 flex items-center gap-0.5">
                  <MapPin className="w-2.5 h-2.5" />
                  {previewJob.location}
                </Badge>
              )}
              {previewJob.workModel && (
                <Badge className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-secondary border border-lia-border-subtle">
                  {previewJob.workModel === 'remoto' ? 'Remoto' : previewJob.workModel === 'híbrido' ? 'Híbrido' : 'Presencial'}
                </Badge>
              )}
              {previewJob.type && (
                <Badge className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-secondary border border-lia-border-subtle">
                  {previewJob.type}
                </Badge>
              )}
              {(previewJob.visibility === 'confidential' || previewJob.isConfidential) && (
                <Badge variant="outline" className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-wedo-orange/10 text-wedo-orange border-wedo-orange/30">
                  <Shield className="w-2.5 h-2.5 mr-0.5" />
                  Confidencial
                </Badge>
              )}
              {previewJob.visibility === 'internal' && (
                <Badge variant="outline" className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-wedo-cyan/10 text-wedo-cyan-dark border-wedo-cyan/30">
                  <Building className="w-2.5 h-2.5 mr-0.5" />
                  Interna
                </Badge>
              )}
              {previewJob.visibility === 'hidden' && (
                <Badge variant="outline" className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle">
                  <Lock className="w-2.5 h-2.5 mr-0.5" />
                  Oculta
                </Badge>
              )}
              {(previewJob.publishedLinkedIn || previewJob.publishedWebsite) ? (
                <Badge variant="outline" className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-status-success/10 text-status-success border-status-success/30 flex items-center gap-0.5">
                  <Globe className="w-2.5 h-2.5" />
                  Publicada
                </Badge>
              ) : (
                <Badge variant="outline" className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-tertiary border-lia-border-subtle flex items-center gap-0.5">
                  <Globe className="w-2.5 h-2.5" />
                  Não publicada
                </Badge>
              )}
              {(previewJob.salaryRange?.min || previewJob.salaryRange?.max || (previewJob as unknown as Record<string, number | undefined>).salaryMin || (previewJob as unknown as Record<string, number | undefined>).salaryMax) && (
                <Badge className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-status-success/10 text-status-success border border-status-success/30 flex items-center gap-0.5">
                  <DollarSign className="w-2.5 h-2.5" />
                  {(() => {
                    const min = previewJob.salaryRange?.min || (previewJob as unknown as Record<string, number | undefined>).salaryMin
                    const max = previewJob.salaryRange?.max || (previewJob as unknown as Record<string, number | undefined>).salaryMax
                    if (min && max) return `${formatBRLCompact(min as number)} - ${formatBRLCompact(max as number)}`
                    if (min) return `A partir de ${formatBRLCompact(min as number)}`
                    if (max) return `Até ${formatBRLCompact(max as number)}`
                    return ''
                  })()}
                </Badge>
              )}
              <Badge 
                className="text-[0.625rem] leading-none px-1.5 py-0.5 font-medium"
                style={{backgroundColor: getStatusColor(previewJob.status as Job['status']), color: 'var(--white)'}}
              >
                {previewJob.status}
              </Badge>
              {(() => {
                const scrStatus = previewJob.screeningStatus || 'not_configured'
                const scrLabels = Object.fromEntries(
                  Object.entries(SCREENING_STATUS_LABELS).map(([k, v]) => [k, `Triagem: ${v}`])
                ) as Record<string, string>
                const scrColors: Record<string, string> = {
                  not_configured: 'var(--lia-border-subtle)',
                  not_started: 'var(--lia-bg-tertiary)',
                  active: 'var(--status-success)',
                  paused: 'var(--lia-border-default)',
                  completed: 'var(--lia-border-medium)',
                }
                return (
                  <Badge 
                    className="text-[0.625rem] leading-none px-1.5 py-0.5 font-medium text-lia-text-primary"
                    style={{backgroundColor: scrColors[scrStatus] || 'var(--lia-border-subtle)'}}
                  >
                    {scrLabels[scrStatus] || 'Triagem: N/C'}
                  </Badge>
                )
              })()}
            </div>
          </div>
          <div className="flex items-center gap-0.5 flex-shrink-0">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onJobClick(previewJob)}
              className="h-6 w-6 p-0 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
              title="Abrir vaga completa"
            >
              <Expand className="w-3 h-3" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                onClose()
              }}
              className="h-6 w-6 p-0 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
            >
              <X className="w-3 h-3" />
            </Button>
          </div>
        </div>
      </div>

      {previewJob.hiringProcess && previewJob.hiringProcess.length > 0 && (
        <div className="px-3 pb-2 border-t border-lia-border-subtle/50 pt-2">
          <div className="flex items-center gap-0.5 overflow-x-auto">
            {previewJob.hiringProcess.map((step, idx) => (
              <React.Fragment key={idx}>
                <div className={`px-1.5 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${
                  idx === 0 ? 'bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-elevated font-semibold' :
                  idx === (previewJob.hiringProcess?.length || 0) - 1 ? 'bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-elevated font-semibold' :
                  'bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-elevated'
                }`}>
                  {step}
                </div>
                {idx < (previewJob.hiringProcess?.length || 0) - 1 && (
                  <ChevronRight className="w-2 h-2 text-lia-text-primary flex-shrink-0" />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
