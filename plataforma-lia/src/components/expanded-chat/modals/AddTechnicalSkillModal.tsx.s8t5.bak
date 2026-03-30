"use client"

/**
 * AddTechnicalSkillModal — overlay simples para adicionar skill técnica.
 * Extraído de expanded-chat-modal.tsx (Sprint 4.5 — 2026-03-27).
 * Portabilidade Vue: props → defineProps; callbacks → emit.
 */

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

type SkillCategory = 'language' | 'framework' | 'database' | 'tool'

const CATEGORY_LABELS: Record<SkillCategory, string> = {
  language: 'Linguagem',
  framework: 'Framework',
  database: 'Banco de Dados',
  tool: 'Ferramenta',
}

const CATEGORY_PLACEHOLDERS: Record<SkillCategory, string> = {
  language: 'linguagem',
  framework: 'framework',
  database: 'banco',
  tool: 'ferramenta',
}

export interface AddTechnicalSkillModalProps {
  show: boolean
  skillCategory: SkillCategory
  skillName: string
  onSkillNameChange: (name: string) => void
  onAdd: (name: string) => void
  onCancel: () => void
}

export function AddTechnicalSkillModal({
  show,
  skillCategory,
  skillName,
  onSkillNameChange,
  onAdd,
  onCancel,
}: AddTechnicalSkillModalProps) {
  if (!show) return null

  return (
    <div className="fixed inset-0 z-overlay flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl w-panel-lg p-6">
        <h3
          className="text-lg font-semibold text-gray-800 mb-4"
         
        >
          Adicionar {CATEGORY_LABELS[skillCategory]}
        </h3>
        <input
          type="text"
          value={skillName}
          onChange={(e) => onSkillNameChange(e.target.value)}
          placeholder={`Nome da ${CATEGORY_PLACEHOLDERS[skillCategory]}...`}
          className="w-full px-4 py-3 border border-gray-200 rounded-md text-sm focus:outline-none focus:border-gray-400"
         
          autoFocus
          onKeyDown={(e) => e.key === 'Enter' && onAdd(skillName)}
        />
        <div className="flex gap-3 mt-4">
          <Button
            variant="outline"
            onClick={onCancel}
            className="flex-1 h-10 rounded-md border-gray-200"
          >
            Cancelar
          </Button>
          <Button
            onClick={() => onAdd(skillName)}
            disabled={!skillName.trim()}
            className={cn("flex-1 h-10 rounded-md", skillName.trim() ? "bg-gray-900 text-white" : "bg-gray-200")}
          >
            Adicionar
          </Button>
        </div>
      </div>
    </div>
  )
}
