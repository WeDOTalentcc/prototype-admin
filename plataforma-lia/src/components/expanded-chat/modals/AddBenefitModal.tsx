"use client"


import { CURRENCY_SYMBOL } from "@/lib/pricing"
/**
 * AddBenefitModal — overlay para adicionar benefício customizado.
 * Extraído de expanded-chat-modal.tsx (Sprint 4.5 — 2026-03-27).
 * Portabilidade Vue: props → defineProps; callbacks → emit.
 */

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

export interface AddBenefitModalProps {
  show: boolean
  benefitName: string
  benefitValue: string
  onBenefitNameChange: (name: string) => void
  onBenefitValueChange: (value: string) => void
  onAdd: () => void
  onCancel: () => void
}

export function AddBenefitModal({
  show,
  benefitName,
  benefitValue,
  onBenefitNameChange,
  onBenefitValueChange,
  onAdd,
  onCancel,
}: AddBenefitModalProps) {
  if (!show) return null

  return (
    <div className="fixed inset-0 z-overlay flex items-center justify-center bg-lia-overlay">
      <div className="bg-lia-bg-primary rounded-xl w-panel-lg p-6">
        <h3
          className="text-lg font-semibold text-lia-text-primary mb-4"
         
        >
          Adicionar Benefício
        </h3>
        <div className="space-y-3">
          <input
            type="text"
            value={benefitName}
            onChange={(e) => onBenefitNameChange(e.target.value)}
            placeholder="Nome do benefício (ex: Auxílio Creche)"
            className="w-full px-4 py-3 border border-lia-border-subtle rounded-md text-sm focus:outline-none focus:border-lia-border-medium"
           
            autoFocus
          />
          <input
            type="text"
            value={benefitValue}
            onChange={(e) => onBenefitValueChange(e.target.value)}
            placeholder={`Valor (opcional, ex: ${CURRENCY_SYMBOL} 500/mês)`}
            className="w-full px-4 py-3 border border-lia-border-subtle rounded-md text-sm focus:outline-none focus:border-lia-border-medium"
           
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
            disabled={!benefitName.trim()}
            className={cn("flex-1 h-10 rounded-md", benefitName.trim() ? "bg-lia-btn-primary-bg text-lia-btn-primary-text" : "bg-lia-interactive-active")}
          >
            Adicionar
          </Button>
        </div>
      </div>
    </div>
  )
}
