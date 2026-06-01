"use client"

/**
 * EligibilityScopeEditor — editor canonico de escopo de elegibilidade.
 *
 * Senioridade (niveis canonicos) + tipos de contrato + departamentos. Compartilhado
 * por verbas variaveis (CompensationComponent) e, futuramente, beneficios + PRV
 * (Rule of Three). Departments armazenados como dict { nomeDept: true } — shape que
 * o matcher do backend (app/shared/eligibility_matching.matches_department) consome
 * (compara nome normalizado da vaga). Vazio em qualquer dimensao = aplica a todos.
 */
import { Label } from "@/components/ui/label"
import { Loader2 } from "lucide-react"
import { ChipMultiSelect } from "./ChipMultiSelect"
import {
  SENIORITY_SCOPE_OPTIONS,
  CONTRACT_TYPE_OPTIONS,
} from "@/lib/compensation/seniority-levels"

export interface EligibilityScopeValue {
  seniority_levels?: string[]
  contract_types?: string[]
  departments?: Record<string, unknown>
}

export interface EligibilityScopeEditorProps<T extends EligibilityScopeValue> {
  value: T
  onChange: (patch: Partial<EligibilityScopeValue>) => void
  departments: { id: string; name: string }[]
  deptsLoading?: boolean
}

const labelCls = "text-xs mb-1 block text-lia-text-secondary"

function selectedDeptNames(departments: unknown): string[] {
  if (!departments) return []
  if (Array.isArray(departments)) return departments.filter((x): x is string => typeof x === "string")
  if (typeof departments === "object") {
    const rec = departments as Record<string, unknown>
    return Object.keys(rec).filter((k) => rec[k])
  }
  return []
}

export function EligibilityScopeEditor<T extends EligibilityScopeValue>({
  value,
  onChange,
  departments,
  deptsLoading,
}: EligibilityScopeEditorProps<T>) {
  const selected = selectedDeptNames(value.departments)

  const toggleDept = (name: string) => {
    const next: Record<string, true> = {}
    const set = new Set(selected)
    if (set.has(name)) set.delete(name)
    else set.add(name)
    for (const n of set) next[n] = true
    onChange({ departments: next })
  }

  return (
    <div className="space-y-3">
      <div>
        <Label className={labelCls}>Senioridade aplicável</Label>
        <ChipMultiSelect
          options={SENIORITY_SCOPE_OPTIONS}
          value={value.seniority_levels || []}
          onChange={(next) => onChange({ seniority_levels: next })}
          ariaLabel="Senioridade aplicável"
          allOptionId="all"
        />
      </div>

      <div>
        <Label className={labelCls}>Tipos de contrato</Label>
        <ChipMultiSelect
          options={CONTRACT_TYPE_OPTIONS}
          value={value.contract_types || []}
          onChange={(next) => onChange({ contract_types: next })}
          ariaLabel="Tipos de contrato"
        />
      </div>

      <div>
        <Label className={labelCls}>Departamentos específicos (opcional)</Label>
        <p className="text-xs text-lia-text-tertiary mb-2">
          {selected.length === 0
            ? "Nenhum departamento selecionado (aplica a todos)"
            : `${selected.length} selecionado(s)`}
        </p>
        {deptsLoading ? (
          <div className="flex items-center gap-2 text-xs text-lia-text-tertiary">
            <Loader2 size={14} className="animate-spin motion-reduce:animate-none" />
            Carregando departamentos...
          </div>
        ) : departments.length === 0 ? (
          <p className="text-xs text-lia-text-tertiary italic">
            Nenhum departamento cadastrado. Cadastre em Configurações → Departamentos primeiro.
          </p>
        ) : (
          <div className="flex flex-wrap gap-1.5" role="group" aria-label="Departamentos específicos">
            {departments.map((dept) => {
              const isSel = selected.includes(dept.name)
              return (
                <button
                  key={dept.id}
                  type="button"
                  onClick={() => toggleDept(dept.name)}
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
    </div>
  )
}
