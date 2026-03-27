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
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-2xl w-[440px] p-6">
        <h3
          className="text-lg font-semibold text-gray-800 mb-4"
          style={{ fontFamily: '"Open Sans", sans-serif' }}
        >
          Adicionar Competência Comportamental
        </h3>

        {companySuggestions.length > 0 && (
          <div className="mb-4">
            <label className="text-xs font-medium text-gray-500 mb-2 block">Sugestões da Empresa</label>
            <div className="flex flex-wrap gap-2">
              {companySuggestions.map((comp, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => onCompetencyNameChange(comp.competency)}
                  className={cn(
                    "px-3 py-1.5 text-xs rounded-md border transition-all",
                    competencyName === comp.competency
                      ? "bg-gray-100 dark:bg-gray-800 border-gray-900 dark:border-gray-50 text-gray-600 dark:text-gray-400"
                      : "bg-gray-50 border-gray-200 text-gray-500 hover:border-gray-900 dark:hover:border-gray-50 hover:text-gray-900 dark:hover:text-gray-50"
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
            className="w-full px-4 py-3 border border-gray-200 rounded-md text-sm focus:outline-none focus:border-gray-400"
            style={{ fontFamily: '"Open Sans", sans-serif' }}
            autoFocus
          />
          <textarea
            value={competencyJustification}
            onChange={(e) => onCompetencyJustificationChange(e.target.value)}
            placeholder="Justificativa (ex: Necessário para gestão de equipe)"
            className="w-full px-4 py-3 border border-gray-200 rounded-md text-sm focus:outline-none focus:border-gray-400 resize-none"
            style={{ fontFamily: '"Open Sans", sans-serif' }}
            rows={3}
          />
        </div>

        <div className="flex gap-3 mt-4">
          <Button
            variant="outline"
            onClick={onCancel}
            className="flex-1 h-10 rounded-md border-gray-200"
          >
            Cancelar
          </Button>
          <Button
            onClick={onAdd}
            disabled={!competencyName.trim()}
            className={cn("flex-1 h-10 rounded-md", competencyName.trim() ? "bg-gray-900 text-white" : "bg-gray-200")}
          >
            Adicionar
          </Button>
        </div>
      </div>
    </div>
  )
}
