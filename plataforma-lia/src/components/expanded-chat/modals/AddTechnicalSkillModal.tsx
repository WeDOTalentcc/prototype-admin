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
    <div className="fixed inset-0 z-overlay flex items-center justify-center bg-lia-overlay">
      <div className="bg-lia-bg-primary rounded-xl w-panel-lg p-6">
        <h3
          className="text-lg font-semibold text-lia-text-primary mb-4"
         
        >
          Adicionar {CATEGORY_LABELS[skillCategory]}
        </h3>
        <input
          type="text"
          value={skillName}
          onChange={(e) => onSkillNameChange(e.target.value)}
          placeholder={`Nome da ${CATEGORY_PLACEHOLDERS[skillCategory]}...`}
          className="w-full px-4 py-3 border border-lia-border-subtle rounded-md text-sm focus:outline-none focus:border-lia-border-medium"
         
          autoFocus
          onKeyDown={(e) => e.key === 'Enter' && onAdd(skillName)}
        />
        <div className="flex gap-3 mt-4">
          <Button
            variant="outline"
            onClick={onCancel}
            className="flex-1 h-10 rounded-md border-lia-border-subtle"
          >
            Cancelar
          </Button>
          <Button
            onClick={() => onAdd(skillName)}
            disabled={!skillName.trim()}
            className={cn("flex-1 h-10 rounded-md", skillName.trim() ? "bg-lia-btn-primary-bg text-lia-btn-primary-text" : "bg-lia-interactive-active")}
          >
            Adicionar
          </Button>
        </div>
      </div>
    </div>
  )
}
