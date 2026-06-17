"use client"

import { Label } from "@/components/ui/label"
import { Loader2 } from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import {
  APPLICABLE_TO_OPTIONS,
  CONTRACT_TYPE_OPTIONS,
  SENIORITY_OPTIONS,
  type BenefitTabRecord,
} from "./benefits-types"
import { ChipMultiSelect } from "@/components/settings/_shared"


// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface BenefitFormSectionQuemRecebeProps {
  benefit: BenefitTabRecord
  onChange: (updated: BenefitTabRecord) => void
  departments: { id: string; name: string }[]
  deptsLoading: boolean
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function BenefitFormSectionQuemRecebe({
  benefit,
  onChange,
  departments,
  deptsLoading,
}: BenefitFormSectionQuemRecebeProps) {
  // Normaliza selectedDepartmentIds
  const selectedDepartmentIds: string[] = (() => {
    const v = benefit.departments
    if (!v) return []
    if (Array.isArray(v)) return v.filter((x): x is string => typeof x === "string")
    if (typeof v === "object") return Object.keys(v as Record<string, unknown>)
    return []
  })()

  const toggleDepartment = (deptId: string) => {
    const next = selectedDepartmentIds.includes(deptId)
      ? selectedDepartmentIds.filter((id) => id !== deptId)
      : [...selectedDepartmentIds, deptId]
    onChange({ ...benefit, departments: next })
  }

  return (
    <>
      <div>
        <Label className={textStyles.label}>Senioridade aplicável</Label>
        <ChipMultiSelect
          options={SENIORITY_OPTIONS}
          value={benefit.seniority_levels || []}
          onChange={(next) => onChange({ ...benefit, seniority_levels: next })}
          ariaLabel="Senioridade aplicável"
        />
      </div>
      <div>
        <Label className={textStyles.label}>Aplicável a</Label>
        <ChipMultiSelect
          options={APPLICABLE_TO_OPTIONS}
          value={benefit.applicable_to || []}
          onChange={(next) => onChange({ ...benefit, applicable_to: next })}
          ariaLabel="Aplicável a"
        />
      </div>
      <div>
        <Label className={textStyles.label}>Tipos de contrato</Label>
        <ChipMultiSelect
          options={CONTRACT_TYPE_OPTIONS}
          value={benefit.contract_types || []}
          onChange={(next) => onChange({ ...benefit, contract_types: next })}
          ariaLabel="Tipos de contrato"
        />
      </div>
      <div>
        <Label className={textStyles.label}>
          Departamentos específicos (opcional)
        </Label>
        <p className="text-xs text-lia-text-secondary mb-2">
          {selectedDepartmentIds.length === 0
            ? "Nenhum departamento selecionado (aplica a todos)"
            : `${selectedDepartmentIds.length} selecionado(s)`}
        </p>
        {deptsLoading ? (
          <div className="flex items-center gap-2 text-xs text-lia-text-tertiary">
            <Loader2 size={14} className="animate-spin motion-reduce:animate-none" />
            Carregando departamentos...
          </div>
        ) : departments.length === 0 ? (
          <p className="text-xs text-lia-text-tertiary italic">
            Nenhum departamento cadastrado. Cadastre em Configurações →
            Departamentos primeiro.
          </p>
        ) : (
          <div
            className="flex flex-wrap gap-1.5"
            role="group"
            aria-label="Departamentos específicos"
          >
            {departments.map((dept) => {
              const isSel = selectedDepartmentIds.includes(dept.id)
              return (
                <button
                  key={dept.id}
                  type="button"
                  onClick={() => toggleDepartment(dept.id)}
                  aria-pressed={isSel}
                  className={[
                    "px-2.5 py-1 rounded-full text-xs border transition-colors motion-reduce:transition-none",
                    isSel
                      ? "bg-lia-bg-tertiary border-lia-btn-primary-bg text-lia-text-primary"
                      : "bg-lia-bg-secondary border-lia-border-subtle text-lia-text-secondary hover:bg-lia-interactive-hover hover:text-lia-text-primary",
                  ].join(" ")}
                >
                  {dept.name}
                </button>
              )
            })}
          </div>
        )}
      </div>
    </>
  )
}
