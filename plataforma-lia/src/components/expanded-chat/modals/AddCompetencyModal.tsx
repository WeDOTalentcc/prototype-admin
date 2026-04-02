"use client"

/**
 * AddCompetencyModal — overlay para adicionar competência comportamental.
 * Extraído de expanded-chat-modal.tsx (Sprint 4.5 — 2026-03-27).
 * Portabilidade Vue: props → defineProps; callbacks → emit.
 */

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

export interface CompanySuggestion {
  competency: string
  weight: string
}

export interface AddCompetencyModalProps {
  show: boolean
  companySuggestions: CompanySuggestion[]
  competencyName: string
  competencyJustification: string
  onCompetencyNameChange: (name: string) => void
  onCompetencyJustificationChange: (justification: string) => void
  onAdd: () => void
  onCancel: () => void
}

export function AddCompetencyModal({
  show,
  companySuggestions,
  competencyName,
  competencyJustification,
  onCompetencyNameChange,
  onCompetencyJustificationChange,
  onAdd,
  onCancel,
}: AddCompetencyModalProps) {
  if (!show) return null

  return (
    <div className="fixed inset-0 z-overlay flex items-center justify-center bg-lia-overlay">
      <div className="bg-lia-bg-primary rounded-xl w-[440px] p-6">
        <h3
          className="text-lg font-semibold text-lia-text-primary mb-4"
         
        >
          Adicionar Competência Comportamental
        </h3>

        {companySuggestions.length > 0 && (
          <div className="mb-4">
            <label className="text-xs font-medium text-lia-text-secondary mb-2 block">Sugestões da Empresa</label>
            <div className="flex flex-wrap gap-2">
              {companySuggestions.map((comp, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => onCompetencyNameChange(comp.competency)}
                  className={cn(
 "px-3 py-1.5 text-xs rounded-md border transition-colors",
                    competencyName === comp.competency
                      ? "bg-lia-bg-tertiary border-lia-btn-primary-bg text-lia-text-secondary"
                      : "bg-lia-bg-secondary border-lia-border-subtle text-lia-text-secondary hover:border-lia-btn-primary-bg hover:text-lia-text-primary"
                  )}
                >
                  {comp.competency}
                  <span className="ml-1.5 text-micro opacity-70">
                    ({comp.weight === 'Essencial' ? '●●●' : comp.weight === 'Importante' ? '●●○' : '●○○'})
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-3">
          <input
            type="text"
            value={competencyName}
            onChange={(e) => onCompetencyNameChange(e.target.value)}
            placeholder="Nome da competência (ex: Liderança)"
            className="w-full px-4 py-3 border border-lia-border-subtle rounded-md text-sm focus:outline-none focus:border-lia-border-medium"
           
            autoFocus
          />
          <textarea
            value={competencyJustification}
            onChange={(e) => onCompetencyJustificationChange(e.target.value)}
            placeholder="Justificativa (ex: Necessário para gestão de equipe)"
            className="w-full px-4 py-3 border border-lia-border-subtle rounded-md text-sm focus:outline-none focus:border-lia-border-medium resize-none"
           
            rows={3}
          />
        </div>

        <div className="flex gap-3 mt-4">
          <Button
            variant="outline"
            onClick={onCancel}
            className="flex-1 h-10 rounded-md border-lia-border-subtle"
          >
            Cancelar
          </Button>
          <Button
            onClick={onAdd}
            disabled={!competencyName.trim()}
            className={cn("flex-1 h-10 rounded-md", competencyName.trim() ? "bg-lia-btn-primary-bg text-lia-btn-primary-text" : "bg-lia-interactive-active")}
          >
            Adicionar
          </Button>
        </div>
      </div>
    </div>
  )
}
