"use client"

/**
 * InputEvaluationStage — painel lateral da etapa input-evaluation.
 * Extraído de expanded-chat-modal.tsx (Sprint 4.4 — 2026-03-27).
 * Portabilidade Vue: props → defineProps; callbacks → emit.
 */

import { Settings, Check } from "lucide-react"
import { cn } from "@/lib/utils"
import { FastTrackSuggestions } from "@/components/job-wizard/FastTrackSuggestions"
import type { FastTrackSuggestion } from "@/hooks/useFastTrack"

type CriteriaItem = {
  key: string
  label: string
  value: string | string[] | null
}

export interface InputEvaluationStageProps {
  configLoaded: boolean
  hasConfigData: boolean
  criteriaItems: CriteriaItem[]
  isHighlighted: (key: string) => boolean
  // FastTrack
  hasFastTrackSuggestions: boolean
  fastTrackIsLoading: boolean
  fastTrackSuggestions: FastTrackSuggestion[]
  fastTrackSelectedJob: FastTrackSuggestion | null
  fastTrackSuggestionsShownTracked: boolean
  onFastTrackSelectJob: (job: FastTrackSuggestion) => void
  onFastTrackDismiss: () => void
}

function getCriteriaStatus(value: string | string[] | null): boolean {
  if (Array.isArray(value)) return value.length > 0
  return value !== null && value !== ''
}

export function InputEvaluationStage({
  configLoaded,
  hasConfigData,
  criteriaItems,
  isHighlighted,
  hasFastTrackSuggestions,
  fastTrackIsLoading,
  fastTrackSuggestions,
  fastTrackSelectedJob,
  fastTrackSuggestionsShownTracked: _fastTrackSuggestionsShownTracked,
  onFastTrackSelectJob,
  onFastTrackDismiss,
}: InputEvaluationStageProps) {
  return (
    <>
      {/* Banner when using company config */}
      {configLoaded && hasConfigData && (
        <div className="mb-3 px-3 py-2 bg-lia-bg-tertiary border border-lia-border-default rounded-md flex items-center gap-2">
          <Settings className="w-3.5 h-3.5 text-lia-text-secondary" />
          <span className="text-xs text-lia-text-secondary">
            Usando dados das Configurações da sua empresa
          </span>
        </div>
      )}

      {/* Seção: Critérios Detectados */}
      <div className="mb-4">
        <h4
          className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wider mb-2 px-1"
         
        >
          Critérios Detectados
        </h4>
        <div className="space-y-2">
          {criteriaItems.map((item) => {
            const isDetected = getCriteriaStatus(item.value)
            const displayValue = Array.isArray(item.value)
              ? item.value.join(', ')
              : item.value

            const isItemHighlighted =
              isHighlighted(item.key) ||
              (item.key === 'cargo' && isHighlighted('cargo')) ||
              (item.key === 'departamento' && (isHighlighted('departamento') || isHighlighted('department'))) ||
              (item.key === 'localizacao' && (isHighlighted('localizacao') || isHighlighted('location'))) ||
              (item.key === 'senioridade' && (isHighlighted('senioridade') || isHighlighted('seniority'))) ||
              (item.key === 'modeloTrabalho' && isHighlighted('modeloTrabalho')) ||
              (item.key === 'gestor' && (isHighlighted('gestor') || isHighlighted('manager')))

            return (
              <div
                key={item.key}
                className={cn(
 "flex items-center gap-2.5 py-2 px-3 rounded-md transition-colors duration-300",
                  isDetected ? "bg-lia-bg-secondary" : "bg-lia-bg-primary",
                  isItemHighlighted && "field-highlight field-pulse"
                )}
              >
                <div
                  className={cn(
 "w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 transition-[width,height] duration-300",
                    isDetected ? "bg-wedo-green" : "border border-lia-border-default"
                  )}
                >
                  {isDetected && (
                    <Check className="w-2.5 h-2.5 text-white" strokeWidth={3} />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p
                    className="text-xs font-medium text-lia-text-primary transition-colors motion-reduce:transition-none duration-300"
                   
                  >
                    {item.label}
                  </p>
                  {isDetected && displayValue && (
                    <p
                      className="text-micro mt-0.5 truncate text-lia-text-secondary font-medium"
                     
                    >
                      {displayValue}
                    </p>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Progress Summary */}
      <div className="mt-3 p-2.5 rounded-md bg-lia-bg-primary">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-micro text-lia-text-secondary">
            Detectando critérios...
          </span>
          <span
            className="text-micro font-semibold text-lia-text-primary"
           
          >
            {criteriaItems.filter(item => getCriteriaStatus(item.value)).length} / {criteriaItems.length}
          </span>
        </div>
        <div className="w-full h-1.5 bg-lia-interactive-active rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-[width,height] duration-500 bg-lia-btn-primary-bg"
            style={{width: `${(criteriaItems.filter(item => getCriteriaStatus(item.value)).length / criteriaItems.length) * 100}%`}}
          />
        </div>
      </div>

      {/* Fast Track Suggestions */}
      {(hasFastTrackSuggestions || fastTrackIsLoading) && (
        <div className="mt-4">
          <FastTrackSuggestions
            suggestions={fastTrackSuggestions}
            selectedJob={fastTrackSelectedJob}
            isLoading={fastTrackIsLoading}
            onSelectJob={onFastTrackSelectJob}
            onDismiss={onFastTrackDismiss}
          />
        </div>
      )}
    </>
  )
}
