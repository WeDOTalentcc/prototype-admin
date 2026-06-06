"use client"

import React, { useEffect, useState } from "react"
import { Building2, Lock, Pencil, RotateCcw, TrendingUp } from "lucide-react"
import { CURRENCY_SYMBOL } from "@/lib/pricing"
import { Card, CardContent } from "@/components/ui/card"
import {
  inputClass,
  labelClass,
  groupHeaderClass,
} from "./job-edit-tab.constants"
import { ScreeningBadge } from "./ScreeningBadge"
import { VacancyBenefitsManager } from "@/components/benefits/VacancyBenefitsManager"
import { VacancyVariableCompManager } from "@/components/compensation/VacancyVariableCompManager"
import {
  useResolvedSalaryBand,
  useSalaryBenchmark,
  type SalaryBandRow,
} from "@/hooks/company/useSalaryBands"
import { seniorityLabel, CONTRACT_TYPE_OPTIONS } from "@/lib/compensation/seniority-levels"

interface JobRemuneracaoSectionProps {
  jobEditForm: Record<string, unknown>
  companyDefaults?: Record<string, unknown>
  isEditing: boolean
  updateField: (key: string, value: unknown) => void
}

function fmt(v: number | null | undefined): string {
  if (v == null) return "—"
  return new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 }).format(v)
}

function contractLabel(id: string): string {
  return CONTRACT_TYPE_OPTIONS.find((c) => c.id === id.toLowerCase())?.label ?? id
}

/** Rotulo do escopo da faixa herdada: "Sênior · Tecnologia · CLT". */
function bandScopeLabel(band: SalaryBandRow): string {
  const parts: string[] = [seniorityLabel(band.level)]
  const depts = Object.entries(band.departments || {})
    .filter(([, v]) => !!v)
    .map(([k]) => k)
  if (depts.length) parts.push(depts.join(", "))
  if (band.contract_types?.length) parts.push(band.contract_types.map(contractLabel).join(", "))
  return parts.filter(Boolean).join(" · ")
}

const isEmpty = (v: unknown) => v === undefined || v === null || v === ""

export function JobRemuneracaoSection({
  jobEditForm,
  companyDefaults,
  isEditing,
  updateField,
}: JobRemuneracaoSectionProps) {
  const level = jobEditForm.level as string | undefined
  const department = jobEditForm.department as string | undefined
  const contractType = jobEditForm.type as string | undefined
  const title = jobEditForm.title as string | undefined

  // "A combinar" — recrutador optou por NAO divulgar faixa nesta vaga. Vence a
  // heranca da empresa (sentinela salary_range.undisclosed, sem migration).
  const undisclosed = !!jobEditForm.salaryUndisclosed

  // Faixa CADASTRADA da empresa (Configuracoes -> Faixas Salariais por Nivel),
  // casada por nivel + departamento + contrato. Fonte verificada (politica).
  const { data: band, isFetched: bandFetched } = useResolvedSalaryBand(level, department, contractType)
  const hasBand = !!(band && (band.min != null || band.max != null))

  // Fallback: estimativa de mercado SO quando nao ha banda pro escopo e a faixa
  // nao foi marcada como "A combinar".
  const { data: market } = useSalaryBenchmark(title, level, {
    enabled: bandFetched && !hasBand && !undisclosed,
  })
  const hasMarket = !!(market && market.min != null)

  // Recrutador clicou "Personalizar" -> destrava a faixa herdada p/ editar.
  const [overriding, setOverriding] = useState(false)

  const minVal = jobEditForm.salaryMin
  const maxVal = jobEditForm.salaryMax
  const valuesEmpty = isEmpty(minVal) && isEmpty(maxVal)
  const eqBand =
    hasBand && Number(minVal) === Number(band?.min) && Number(maxVal) === Number(band?.max)
  // Herdado = banda casa + nao personalizou + nao e "A combinar" + (vazio ou == banda).
  const inherited = hasBand && !overriding && !undisclosed && (valuesEmpty || eqBand)

  // Materializa a faixa herdada no form quando o recrutador entra em edicao com
  // a faixa ainda vazia — assim o save persiste o valor da banda (a vaga nao
  // sai publicada com salary_min/max nulos). So roda em edicao (acao explicita).
  useEffect(() => {
    if (isEditing && inherited && valuesEmpty && band) {
      updateField("salaryMin", band.min ?? "")
      updateField("salaryMax", band.max ?? "")
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isEditing, inherited, valuesEmpty, band?.min, band?.max])

  function personalizar() {
    if (band) {
      updateField("salaryMin", band.min ?? "")
      updateField("salaryMax", band.max ?? "")
    }
    setOverriding(true)
  }

  function restaurarFaixaEmpresa() {
    if (band) {
      updateField("salaryMin", band.min ?? "")
      updateField("salaryMax", band.max ?? "")
    }
    setOverriding(false)
  }

  function usarEstimativaMercado() {
    if (market) {
      updateField("salaryMin", market.min ?? "")
      updateField("salaryMax", market.max ?? "")
    }
  }

  function toggleUndisclosed(next: boolean) {
    updateField("salaryUndisclosed", next)
    if (next) {
      // "A combinar": limpa a faixa e descarta o override.
      updateField("salaryMin", "")
      updateField("salaryMax", "")
      setOverriding(false)
    }
  }

  const lockedInputs = inherited
  const minDisplay = inherited ? (band?.min ?? "") : ((minVal as string) || "")
  const maxDisplay = inherited ? (band?.max ?? "") : ((maxVal as string) || "")

  return (
    <div className="space-y-5">
      <div>
        <h3 className={groupHeaderClass}>Faixa Salarial<ScreeningBadge /></h3>

        {undisclosed ? (
          <div className="flex items-center gap-2 mb-2 px-3 py-2 rounded-md border border-lia-border-subtle bg-lia-bg-tertiary/40 text-xs text-lia-text-secondary">
            <Lock className="w-3.5 h-3.5 text-lia-text-tertiary shrink-0" />
            <span><strong className="text-lia-text-primary">A combinar</strong> — faixa não divulgada nesta vaga (não herda da empresa).</span>
          </div>
        ) : (
          <>
            {inherited && (
              <div className="flex items-center gap-2 mb-2 px-3 py-2 rounded-md border border-lia-border-subtle bg-lia-bg-tertiary/40 text-xs text-lia-text-secondary">
                <Building2 className="w-3.5 h-3.5 text-lia-text-tertiary shrink-0" />
                <span>
                  <strong className="text-lia-text-primary">Faixa herdada da empresa</strong>
                  {band ? <> · {bandScopeLabel(band)}</> : null}
                  {" — definida em Configurações → Faixas Salariais por Nível."}
                </span>
              </div>
            )}

            {!inherited && hasBand && (
              <div className="flex items-center justify-between gap-2 mb-2 px-3 py-2 rounded-md border border-lia-border-subtle bg-lia-bg-tertiary/40 text-xs text-lia-text-secondary">
                <span className="flex items-center gap-2">
                  <Pencil className="w-3.5 h-3.5 text-lia-text-tertiary shrink-0" />
                  Faixa personalizada (difere da faixa da empresa).
                </span>
                {isEditing && (
                  <button
                    type="button"
                    onClick={restaurarFaixaEmpresa}
                    className="flex items-center gap-1 text-lia-btn-primary-bg hover:underline shrink-0"
                  >
                    <RotateCcw className="w-3 h-3" />Restaurar faixa da empresa
                  </button>
                )}
              </div>
            )}

            {!hasBand && hasMarket && (
              <div className="flex items-center justify-between gap-2 mb-2 px-3 py-2 rounded-md border border-amber-300/40 bg-amber-50/50 text-xs text-lia-text-secondary">
                <span className="flex items-center gap-2">
                  <TrendingUp className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                  Estimativa de mercado (não-verificada): {CURRENCY_SYMBOL} {fmt(market?.min)} – {CURRENCY_SYMBOL} {fmt(market?.max)}
                </span>
                {isEditing && (
                  <button
                    type="button"
                    onClick={usarEstimativaMercado}
                    className="text-lia-btn-primary-bg hover:underline shrink-0"
                  >
                    Usar estimativa
                  </button>
                )}
              </div>
            )}
          </>
        )}

        <Card className="border border-lia-border-subtle">
          <CardContent className="p-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>Mínimo</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-lia-text-tertiary">{CURRENCY_SYMBOL}</span>
                  <input type="number" className={`${inputClass(!isEditing || lockedInputs || undisclosed)} pl-9`} value={undisclosed ? "" : minDisplay} onChange={(e) => updateField("salaryMin", e.target.value)} disabled={!isEditing || lockedInputs || undisclosed} placeholder={undisclosed ? "A combinar" : "0,00"} />
                </div>
              </div>
              <div>
                <label className={labelClass}>Máximo</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-lia-text-tertiary">{CURRENCY_SYMBOL}</span>
                  <input type="number" className={`${inputClass(!isEditing || lockedInputs || undisclosed)} pl-9`} value={undisclosed ? "" : maxDisplay} onChange={(e) => updateField("salaryMax", e.target.value)} disabled={!isEditing || lockedInputs || undisclosed} placeholder={undisclosed ? "A combinar" : "0,00"} />
                </div>
              </div>
            </div>

            {inherited && isEditing && !undisclosed && (
              <button
                type="button"
                onClick={personalizar}
                className="flex items-center gap-1 mt-3 text-xs text-lia-btn-primary-bg hover:underline"
              >
                <Lock className="w-3 h-3" />Personalizar faixa desta vaga
              </button>
            )}

            {isEditing && (
              <label className="flex items-center gap-2 mt-3 text-xs text-lia-text-secondary cursor-pointer select-none">
                <input
                  type="checkbox"
                  className="h-3.5 w-3.5 accent-lia-btn-primary-bg"
                  checked={undisclosed}
                  onChange={(e) => toggleUndisclosed(e.target.checked)}
                />
                Não divulgar faixa (A combinar)
              </label>
            )}
          </CardContent>
        </Card>
      </div>
      <div>
        <VacancyVariableCompManager
          value={(jobEditForm.variable_compensation as unknown[]) || []}
          onChange={(next) => updateField("variable_compensation", next)}
          editable={isEditing}
          seniorityLevel={jobEditForm.level as string | undefined}
          department={jobEditForm.department as string | undefined}
          contractType={jobEditForm.type as string | undefined}
        />
      </div>
      <div>
        <VacancyBenefitsManager
          benefits={(jobEditForm.benefits as unknown[]) || []}
          onChange={(next) => updateField("benefits", next)}
          editable={isEditing}
          seniorityLevel={jobEditForm.level as string | undefined}
          department={jobEditForm.department as string | undefined}
          contractType={jobEditForm.type as string | undefined}
        />
      </div>
    </div>
  )
}
