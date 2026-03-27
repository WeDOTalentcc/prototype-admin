"use client"

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
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-2xl w-[400px] p-6">
        <h3
          className="text-lg font-semibold text-gray-800 mb-4"
          style={{ fontFamily: '"Open Sans", sans-serif' }}
        >
          Adicionar Benefício
        </h3>
        <div className="space-y-3">
          <input
            type="text"
            value={benefitName}
            onChange={(e) => onBenefitNameChange(e.target.value)}
            placeholder="Nome do benefício (ex: Auxílio Creche)"
            className="w-full px-4 py-3 border border-gray-200 rounded-md text-sm focus:outline-none focus:border-gray-400"
            style={{ fontFamily: '"Open Sans", sans-serif' }}
            autoFocus
          />
          <input
            type="text"
            value={benefitValue}
            onChange={(e) => onBenefitValueChange(e.target.value)}
            placeholder="Valor (opcional, ex: R$ 500/mês)"
            className="w-full px-4 py-3 border border-gray-200 rounded-md text-sm focus:outline-none focus:border-gray-400"
            style={{ fontFamily: '"Open Sans", sans-serif' }}
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
            disabled={!benefitName.trim()}
            className={cn("flex-1 h-10 rounded-md", benefitName.trim() ? "bg-gray-900 text-white" : "bg-gray-200")}
          >
            Adicionar
          </Button>
        </div>
      </div>
    </div>
  )
}
