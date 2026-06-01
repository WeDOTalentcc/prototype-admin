"use client"

/**
 * EligibilityScopeEditor — editor canonico de escopo de elegibilidade.
 *
 * Senioridade (niveis canonicos) + tipos de contrato + departamentos + AREA (tokens
 * livres). Compartilhado por verbas variaveis, faixas salariais e (futuro) beneficios
 * (Rule of Three). Departments = dict { nomeDept: true } (shape do matcher backend).
 * Vazio em qualquer dimensao = aplica a todos. showSeniority=false p/ faixa salarial
 * (onde o nivel e identidade, escolhido fora do editor).
 */
import { useState } from "react"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Loader2, X, Plus } from "lucide-react"
import { ChipMultiSelect } from "./ChipMultiSelect"
import {
  SENIORITY_SCOPE_OPTIONS,
  CONTRACT_TYPE_OPTIONS,
} from "@/lib/compensation/seniority-levels"

export interface EligibilityScopeValue {
  seniority_levels?: string[]
  contract_types?: string[]
  departments?: Record<string, unknown>
  area?: string[]
}

export interface EligibilityScopeEditorProps<T extends EligibilityScopeValue> {
  value: T
  onChange: (patch: Partial<EligibilityScopeValue>) => void
  departments: { id: string; name: string }[]
  deptsLoading?: boolean
  showSeniority?: boolean
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
  showSeniority = true,
}: EligibilityScopeEditorProps<T>) {
  const selected = selectedDeptNames(value.departments)
  const [areaDraft, setAreaDraft] = useState("")
  const areas = value.area || []

  const toggleDept = (name: string) => {
    const next: Record<string, true> = {}
    const set = new Set(selected)
    if (set.has(name)) set.delete(name)
    else set.add(name)
    for (const n of set) next[n] = true
    onChange({ departments: next })
  }

  const addArea = () => {
    const v = areaDraft.trim()
    if (!v || areas.some((a) => a.toLowerCase() === v.toLowerCase())) {
      setAreaDraft("")
      return
    }
    onChange({ area: [...areas, v] })
    setAreaDraft("")
  }

  return (
    <div className="space-y-3">
      {showSeniority && (
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
      )}

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

      <div>
        <Label className={labelCls}>Áreas de negócio (opcional)</Label>
        <p className="text-xs text-lia-text-tertiary mb-2">
          Dimensão separada de departamento. Deixe vazio para aplicar a todas as áreas.
        </p>
        {areas.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-2" role="group" aria-label="Áreas selecionadas">
            {areas.map((a) => (
              <span key={a} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs border border-lia-btn-primary-bg bg-lia-bg-tertiary text-lia-text-primary">
                {a}
                <button type="button" onClick={() => onChange({ area: areas.filter((x) => x !== a) })} aria-label={`Remover área ${a}`}>
                  <X size={12} />
                </button>
              </span>
            ))}
          </div>
        )}
        <div className="flex gap-2">
          <Input
            value={areaDraft}
            onChange={(e) => setAreaDraft(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addArea() } }}
            placeholder="Ex: Tecnologia, Comercial"
            className="flex-1 rounded-md text-sm"
          />
          <button
            type="button"
            onClick={addArea}
            className="inline-flex items-center gap-1 text-xs text-lia-btn-primary-bg hover:underline px-2"
          >
            <Plus size={14} /> Adicionar
          </button>
        </div>
      </div>
    </div>
  )
}
