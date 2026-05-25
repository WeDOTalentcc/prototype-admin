"use client"

import React from"react"
import { CURRENCY_SYMBOL, formatBRLCompact } from"@/lib/pricing"
import { SCREENING_STATUS_LABELS } from"@/types/screening"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import {
  Calendar, Clock, MapPin, DollarSign, Heart, Shield, Building, Lock, Globe,
  Expand, X, ChevronRight,
} from"lucide-react"
import { type Job } from"@/components/jobs"
import { getStatusColor } from"@/components/jobs/jobsPageConstants"

interface JobPreviewHeaderProps {
  previewJob: Job
  onClose: () => void
  onJobClick: (job: Job) => void
}

export function JobPreviewHeader({ previewJob, onClose, onJobClick }: JobPreviewHeaderProps) {
  return (
    <div data-testid="job-preview-header" className="bg-lia-bg-primary dark:bg-lia-bg-primary">
      <div className="px-3 pt-3 pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-base-ui font-semibold text-lia-text-primary truncate">
                {previewJob.title}
              </h3>
              <Chip variant="neutral" muted className="text-[0.625rem] leading-none px-1.5 py-0.5 flex-shrink-0 font-mono font-medium bg-lia-bg-tertiary text-lia-text-secondary border border-lia-border-default">
                {previewJob.jobId}
              </Chip>
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
                <Chip variant="neutral" muted className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-secondary border border-lia-border-subtle">
                  {previewJob.department}
                </Chip>
              )}
              {previewJob.seniority ? (
                <Chip variant="warning" muted className="text-[0.625rem] leading-none px-1.5 py-0.5">
                  {previewJob.seniority}
                </Chip>
              ) : (
                <Chip
                  variant="neutral"
                  muted
                  className="text-[0.625rem] leading-none px-1.5 py-0.5 italic bg-lia-bg-tertiary text-lia-text-tertiary border border-lia-border-subtle"
                  title="O backend não devolveu o nível de senioridade desta vaga"
                >
                  Senioridade não informada
                </Chip>
              )}
              {previewJob.location && (
                <Chip variant="neutral" muted className="text-[0.625rem] leading-none px-1.5 py-0.5 -dark border border-wedo-cyan/30 flex items-center gap-0.5">
                  <MapPin className="w-2.5 h-2.5" />
                  {previewJob.location}
                </Chip>
              )}
              {previewJob.workModel && (
                <Chip variant="neutral" muted className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-secondary border border-lia-border-subtle">
                  {previewJob.workModel === 'remoto' ? 'Remoto' : previewJob.workModel === 'híbrido' ? 'Híbrido' : 'Presencial'}
                </Chip>
              )}
              {previewJob.type && (
                <Chip variant="neutral" muted className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-secondary border border-lia-border-subtle">
                  {previewJob.type}
                </Chip>
              )}
              {(previewJob.visibility === 'confidential' || previewJob.isConfidential) && (
                <Chip variant="neutral" className="text-[0.625rem] leading-none px-1.5 py-0.5  border-wedo-orange/30">
                  <Shield className="w-2.5 h-2.5 mr-0.5" />
                  Confidencial
                </Chip>
              )}
              {previewJob.visibility === 'internal' && (
                <Chip variant="neutral" className="text-[0.625rem] leading-none px-1.5 py-0.5 -dark border-wedo-cyan/30">
                  <Building className="w-2.5 h-2.5 mr-0.5" />
                  Interna
                </Chip>
              )}
              {previewJob.visibility === 'hidden' && (
                <Chip variant="neutral" className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle">
                  <Lock className="w-2.5 h-2.5 mr-0.5" />
                  Oculta
                </Chip>
              )}
              {(previewJob.publishedLinkedIn || previewJob.publishedWebsite) ? (
                <Chip variant="success" className="text-[0.625rem] leading-none px-1.5 py-0.5 flex items-center gap-0.5">
                  <Globe className="w-2.5 h-2.5" />
                  Publicada
                </Chip>
              ) : (
                <Chip variant="neutral" className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-tertiary border-lia-border-subtle flex items-center gap-0.5">
                  <Globe className="w-2.5 h-2.5" />
                  Não publicada
                </Chip>
              )}
              {(previewJob.salaryRange?.min || previewJob.salaryRange?.max || (previewJob as unknown as Record<string, number | undefined>).salaryMin || (previewJob as unknown as Record<string, number | undefined>).salaryMax) && (
                <Chip variant="success" muted className="text-[0.625rem] leading-none px-1.5 py-0.5 flex items-center gap-0.5">
                  <DollarSign className="w-2.5 h-2.5" />
                  {(() => {
                    const min = previewJob.salaryRange?.min || (previewJob as unknown as Record<string, number | undefined>).salaryMin
                    const max = previewJob.salaryRange?.max || (previewJob as unknown as Record<string, number | undefined>).salaryMax
                    if (min && max) return `${formatBRLCompact(min as number)} - ${formatBRLCompact(max as number)}`
                    if (min) return `A partir de ${formatBRLCompact(min as number)}`
                    if (max) return `Até ${formatBRLCompact(max as number)}`
                    return ''
                  })()}
                </Chip>
              )}
              <Chip variant="neutral" muted 
                className="text-[0.625rem] leading-none px-1.5 py-0.5 font-medium"
                style={{backgroundColor: getStatusColor(previewJob.status as Job['status']), color: 'var(--white)'}}
              >
                {previewJob.status}
              </Chip>
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
                  <Chip variant="neutral" muted 
                    className="text-[0.625rem] leading-none px-1.5 py-0.5 font-medium text-lia-text-primary"
                    style={{backgroundColor: scrColors[scrStatus] || 'var(--lia-border-subtle)'}}
                  >
                    {scrLabels[scrStatus] || 'Triagem: N/C'}
                  </Chip>
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
                <div className={`px-1.5 py-0.5 rounded-full text-micro font-medium whitespace-nowrap ${
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
