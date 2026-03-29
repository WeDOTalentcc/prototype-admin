"use client"

/**
 * SkipCompetenciesWarningModal — aviso quando usuário tenta avançar sem competências mínimas.
 * Extraído de expanded-chat-modal.tsx (Sprint 4.5 — 2026-03-27).
 * Portabilidade Vue: props → defineProps; callbacks → emit.
 */

import { AlertTriangle } from "lucide-react"
import { Button } from "@/components/ui/button"

export interface SkipCompetenciesWarningModalProps {
  show: boolean
  technicalSkillsCount: number
  behavioralCompetenciesCount: number
  onClose: () => void
  onConfirm: () => void
}

export function SkipCompetenciesWarningModal({
  show,
  technicalSkillsCount,
  behavioralCompetenciesCount,
  onClose,
  onConfirm,
}: SkipCompetenciesWarningModalProps) {
  if (!show) return null

  return (
    <div className="fixed inset-0 z-overlay flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-2xl w-panel-lg p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-status-warning/10 rounded-full flex items-center justify-center">
            <AlertTriangle className="w-5 h-5 text-status-warning" />
          </div>
          <div>
            <h3
              className="text-lg font-semibold text-gray-800"
             
            >
              Competências incompletas
            </h3>
          </div>
        </div>
        <p
          className="text-sm text-gray-500 mb-4"
         
        >
          Recomendamos pelo menos <strong>3 competências técnicas</strong> e <strong>3 comportamentais</strong> para que a LIA encontre candidatos de forma mais assertiva.
        </p>
        <p
          className="text-xs text-gray-400 mb-4"
         
        >
          Atualmente você tem: {technicalSkillsCount} técnicas e {behavioralCompetenciesCount} comportamentais.
        </p>
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={onClose}
            className="flex-1 h-10 rounded-md border-gray-900 dark:border-gray-50 text-gray-600 dark:text-gray-400"
          >
            Voltar e completar
          </Button>
          <Button
            onClick={onConfirm}
            className="flex-1 h-10 rounded-md bg-status-warning text-white"
            
          >
            Confirmar assim mesmo
          </Button>
        </div>
      </div>
    </div>
  )
}
