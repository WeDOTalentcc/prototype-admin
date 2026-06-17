"use client"

import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { X, Plus } from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import { type BenefitTabRecord } from "./benefits-types"

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface BenefitFormSectionVigenciaProps {
  benefit: BenefitTabRecord
  onChange: (updated: BenefitTabRecord) => void
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function BenefitFormSectionVigencia({
  benefit,
  onChange,
}: BenefitFormSectionVigenciaProps) {
  return (
    <>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label className={textStyles.label}>Início do contrato</Label>
          <Input
            type="date"
            value={benefit.valid_from || ""}
            onChange={(e) =>
              onChange({ ...benefit, valid_from: e.target.value || null })
            }
            className="mt-1 rounded-md text-sm"
          />
        </div>
        <div>
          <Label className={textStyles.label}>Fim do contrato</Label>
          <Input
            type="date"
            value={benefit.valid_until || ""}
            onChange={(e) =>
              onChange({ ...benefit, valid_until: e.target.value || null })
            }
            className="mt-1 rounded-md text-sm"
          />
        </div>
      </div>

      <div>
        <Label className={textStyles.label}>Filiais aplicáveis</Label>
        <p className="text-xs text-lia-text-tertiary mb-2">
          Deixe em branco para aplicar a todas as entidades da empresa
        </p>
        <div className="space-y-2">
          {(benefit.subsidiaries || []).map((sub, idx) => (
            <div key={idx} className="flex gap-2 items-center">
              <Input
                value={sub.name}
                onChange={(e) => {
                  const next = [...(benefit.subsidiaries || [])]
                  next[idx] = { ...next[idx], name: e.target.value }
                  onChange({ ...benefit, subsidiaries: next })
                }}
                placeholder="Nome da filial"
                className="flex-1 rounded-md text-sm"
              />
              <Input
                value={sub.cnpj || ""}
                onChange={(e) => {
                  const next = [...(benefit.subsidiaries || [])]
                  next[idx] = { ...next[idx], cnpj: e.target.value || null }
                  onChange({ ...benefit, subsidiaries: next })
                }}
                placeholder="CNPJ"
                maxLength={18}
                className="w-40 rounded-md text-sm"
              />
              <button
                type="button"
                onClick={() => {
                  const next = (benefit.subsidiaries || []).filter((_, i) => i !== idx)
                  onChange({ ...benefit, subsidiaries: next })
                }}
                className="text-lia-text-tertiary hover:text-status-error transition-colors"
                aria-label="Remover filial"
              >
                <X size={16} />
              </button>
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => {
              const next = [
                ...(benefit.subsidiaries || []),
                { name: "", cnpj: null },
              ]
              onChange({ ...benefit, subsidiaries: next })
            }}
          >
            <Plus size={14} className="mr-1" /> Adicionar filial
          </Button>
        </div>
      </div>
    </>
  )
}
