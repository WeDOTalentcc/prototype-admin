'use client'

import React from 'react'
import { Badge } from '@/components/ui/badge'

const STAGE_LABELS: Record<string, string> = {
  applied:             'Candidatura Recebida',
  screening:           'Em Triagem',
  interview_scheduled: 'Entrevista Agendada',
  interview_done:      'Entrevista Realizada',
  offer_sent:          'Proposta Enviada',
  hired:               'Contratado(a)',
  rejected:            'Processo Encerrado',
}

const STAGE_COLORS: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  applied:             'secondary',
  screening:           'default',
  interview_scheduled: 'default',
  interview_done:      'default',
  offer_sent:          'default',
  hired:               'default',
  rejected:            'outline',
}

interface CandidateChatHeaderProps {
  companyName?: string
  vacancyTitle?: string
  stage?: string
  logoUrl?: string
}

export function CandidateChatHeader({
  companyName,
  vacancyTitle,
  stage,
  logoUrl,
}: CandidateChatHeaderProps) {
  const stageLabel = stage ? (STAGE_LABELS[stage] ?? stage) : null
  const badgeVariant = stage ? (STAGE_COLORS[stage] ?? 'secondary') : 'secondary'

  return (
    <header className="flex items-center gap-3 border-b border-border px-4 py-3 bg-background">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-wedo-cyan/10 overflow-hidden">
        {logoUrl ? (
          <img src={logoUrl} alt={companyName ?? 'Empresa'} className="h-full w-full object-contain" />
        ) : (
          <span className="text-wedo-cyan text-sm font-semibold">
            {(companyName ?? 'E')[0].toUpperCase()}
          </span>
        )}
      </div>

      <div className="flex-1 min-w-0">
        {companyName && (
          <p className="text-xs text-muted-foreground truncate">{companyName}</p>
        )}
        {vacancyTitle && (
          <p className="text-sm font-medium text-foreground truncate">{vacancyTitle}</p>
        )}
        {!companyName && !vacancyTitle && (
          <p className="text-sm font-medium text-foreground">Portal do Candidato</p>
        )}
      </div>

      {stageLabel && (
        <Badge variant={badgeVariant} className="shrink-0 text-xs">
          {stageLabel}
        </Badge>
      )}
    </header>
  )
}
