'use client'

import React from 'react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ArrowRight, Briefcase } from 'lucide-react'

const STAGE_LABELS: Record<string, string> = {
  applied:             'Candidatura Recebida',
  screening:           'Em Triagem',
  interview_scheduled: 'Entrevista Agendada',
  interview_done:      'Entrevista Realizada',
  offer_sent:          'Proposta Enviada',
  hired:               'Contratado(a)',
  rejected:            'Processo Encerrado',
}

export interface ApplicationSummary {
  apply_id: string
  vacancy_id: string
  vacancy_title: string
  stage: string
  stage_label?: string
  applied_at: string
}

interface CandidateJobSelectorProps {
  companyName?: string
  applications: ApplicationSummary[]
  onSelect: (application: ApplicationSummary) => void
}

export function CandidateJobSelector({
  companyName,
  applications,
  onSelect,
}: CandidateJobSelectorProps) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4 py-8">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-1">
          <h1 className="text-xl font-semibold text-foreground">
            Seus processos seletivos
          </h1>
          {companyName && (
            <p className="text-sm text-muted-foreground">em {companyName}</p>
          )}
          <p className="text-sm text-muted-foreground">
            Selecione a vaga sobre a qual deseja conversar com a IA.
          </p>
        </div>

        <div className="space-y-3">
          {applications.map((app) => {
            const stageLabel = app.stage_label ?? STAGE_LABELS[app.stage] ?? app.stage
            const appliedDate = new Date(app.applied_at).toLocaleDateString('pt-BR', {
              day: '2-digit', month: 'long', year: 'numeric',
            })

            return (
              <Card
                key={app.apply_id}
                className="cursor-pointer transition-all duration-150 hover:shadow-md hover:border-wedo-cyan/40 active:scale-[0.99] p-4"
                onClick={() => onSelect(app)}
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-wedo-cyan/10">
                    <Briefcase className="h-4 w-4 text-wedo-cyan" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">
                      {app.vacancy_title}
                    </p>
                    <p className="text-xs text-muted-foreground">Candidatura: {appliedDate}</p>
                  </div>
                  <div className="flex flex-col items-end gap-1 shrink-0">
                    <Badge variant="secondary" className="text-xs">{stageLabel}</Badge>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      </div>
    </div>
  )
}
