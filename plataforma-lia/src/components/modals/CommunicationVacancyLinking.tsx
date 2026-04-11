"use client"

import React from "react"
import { Switch } from "@/components/ui/switch"
import {
  Briefcase, CheckCircle, Clock
} from "lucide-react"
import { textStyles, cardStyles } from '@/lib/design-tokens'
import type { CommunicationType } from "./unified-communication-modal"

const PIPELINE_STAGES = [
  { value: 'novo', label: 'Novo' },
  { value: 'triagem', label: 'Triagem' },
  { value: 'entrevista', label: 'Entrevista' },
  { value: 'avaliacao', label: 'Avaliação' },
  { value: 'oferta', label: 'Oferta' }
]

interface JobVacancy {
  id: string
  title: string
  department?: string
  location?: string
  status?: string
}

interface CommunicationVacancyLinkingProps {
  type: CommunicationType
  linkToVacancy: boolean
  setLinkToVacancy: (v: boolean) => void
  selectedVacancyId: string | null
  setSelectedVacancyId: (v: string | null) => void
  selectedStage: string
  setSelectedStage: (v: string) => void
  vacancies: JobVacancy[]
  isLoadingVacancies: boolean
  linkOnCompletionOnly: boolean
  setLinkOnCompletionOnly: (v: boolean) => void
  isBulkMode: boolean
  selectedCandidates: Array<{ id: string; name: string }>
}

export function CommunicationVacancyLinking({
  type,
  linkToVacancy,
  setLinkToVacancy,
  selectedVacancyId,
  setSelectedVacancyId,
  selectedStage,
  setSelectedStage,
  vacancies,
  isLoadingVacancies,
  linkOnCompletionOnly,
  setLinkOnCompletionOnly,
  isBulkMode,
  selectedCandidates,
}: CommunicationVacancyLinkingProps) {
  return (
    <div className={`${cardStyles.default} p-4`}>
      <div className="flex items-center justify-between mb-3">
        <h4 className={`${textStyles.label} flex items-center gap-2`}>
          <Briefcase className="w-4 h-4 text-lia-text-secondary" />
          Vincular à Vaga
        </h4>
        <Switch
          checked={linkToVacancy}
          onCheckedChange={setLinkToVacancy}
        />
      </div>
      
      {linkToVacancy && (
        <div className="space-y-3">
          <div>
            <label className={`${textStyles.caption} font-medium mb-1.5 block`}>
              Selecionar Vaga
            </label>
            <select
              value={selectedVacancyId || ''}
              onChange={(e) => setSelectedVacancyId(e.target.value || null)}
              disabled={isLoadingVacancies}
              className="w-full h-9 text-xs border border-lia-border-subtle rounded-xl focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20 bg-lia-bg-primary disabled:bg-lia-bg-tertiary disabled:cursor-not-allowed"
            >
              <option value="">
                {isLoadingVacancies ? 'Carregando vagas...' : 'Selecione uma vaga'}
              </option>
              {vacancies.map((vacancy) => (
                <option key={vacancy.id} value={vacancy.id}>
                  {vacancy.title}
                  {vacancy.department ? ` - ${vacancy.department}` : ''}
                  {vacancy.status ? ` (${vacancy.status})` : ''}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className={`${textStyles.caption} font-medium mb-1.5 block`}>
              Etapa do Pipeline
            </label>
            <select
              value={selectedStage}
              onChange={(e) => setSelectedStage(e.target.value)}
              className="w-full h-9 text-xs border border-lia-border-subtle rounded-xl focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20 bg-lia-bg-primary"
            >
              {PIPELINE_STAGES.map((stage) => (
                <option key={stage.value} value={stage.value}>
                  {stage.label}
                </option>
              ))}
            </select>
          </div>
          
          {type === 'triagem' && (
            <div className="bg-status-warning/10 border border-status-warning/30 rounded-xl p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Clock className="w-3.5 h-3.5 text-status-warning flex-shrink-0" />
                  <div>
                    <span className="text-xs font-medium text-status-warning">
                      Vincular após completar triagem
                    </span>
                    <p className="text-micro text-status-warning mt-0.5">
                      Candidato só entra na vaga se responder a triagem
                    </p>
                  </div>
                </div>
                <Switch
                  checked={linkOnCompletionOnly}
                  onCheckedChange={setLinkOnCompletionOnly}
                />
              </div>
            </div>
          )}
          
          {selectedVacancyId && (
            <div className={`${type === 'triagem' && linkOnCompletionOnly ? 'bg-status-warning/10 border-status-warning/30' : 'bg-status-success/10 border-status-success/30'} border rounded-md p-2.5`}>
              <div className="flex items-center gap-2">
                {type === 'triagem' && linkOnCompletionOnly ? (
                  <Clock className="w-3.5 h-3.5 text-status-warning flex-shrink-0" />
                ) : (
                  <CheckCircle className="w-3.5 h-3.5 text-status-success flex-shrink-0" />
                )}
                <span className={`text-micro ${type === 'triagem' && linkOnCompletionOnly ? 'text-status-warning' : 'text-status-success'}`}>
                  {type === 'triagem' && linkOnCompletionOnly ? (
                    isBulkMode 
                      ? `${selectedCandidates.length} candidato(s) serão vinculados à vaga "${PIPELINE_STAGES.find(s => s.value === selectedStage)?.label}" somente após completarem a triagem`
                      : `Candidato será vinculado à vaga na etapa "${PIPELINE_STAGES.find(s => s.value === selectedStage)?.label}" somente após completar a triagem`
                  ) : (
                    isBulkMode 
                      ? `${selectedCandidates.length} candidato(s) serão vinculados à vaga selecionada na etapa "${PIPELINE_STAGES.find(s => s.value === selectedStage)?.label}"`
                      : `Candidato será vinculado à vaga selecionada na etapa "${PIPELINE_STAGES.find(s => s.value === selectedStage)?.label}"`
                  )}
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
