/**
 * Preview client-side de R$ derivado da verba (% x faixa salarial do nivel).
 *
 * ESPELHO do motor canonico do backend
 * (lia-agent-system/app/domains/company/services/compensation_resolution_service.py).
 * Aqui SO para preview ao vivo no formulario (sem round-trip por tecla); a fonte
 * autoritativa do R$ em vaga/oferta e o servico backend. Manter as duas regras em
 * sincronia (mesma formula: R$ = % / 100 x banda[nivel]).
 */
import type { VariableCompRecord } from "@/components/compensation/variable-comp-types"

export interface BandLite {
  min?: number | null
  mid?: number | null
  max?: number | null
  currency?: string | null
}

export interface ResolvedAmount {
  min: number | null
  max: number | null
  currency: string
  basis: "fixed" | "percent_of_salary" | "n_salaries" | "undefined"
}

function num(x: unknown): number | null {
  if (x === null || x === undefined || x === "") return null
  const n = Number(x)
  return Number.isFinite(n) ? n : null
}

export function resolveForBand(c: VariableCompRecord, band: BandLite | null | undefined): ResolvedAmount {
  const valueType = (c.value_type || "percent").toLowerCase()
  const currency = c.currency || band?.currency || "BRL"

  const minAmount = num(c.min_amount)
  const maxAmount = num(c.max_amount)
  if (valueType === "currency" || minAmount !== null || maxAmount !== null) {
    if (minAmount !== null || maxAmount !== null) {
      return { min: minAmount, max: maxAmount, currency, basis: "fixed" }
    }
  }

  const bandMin = num(band?.min)
  const bandMax = num(band?.max)

  let minPct = num(c.min_pct)
  let maxPct = num(c.max_pct)
  const targetPct = num(c.target_pct)
  if (minPct === null && maxPct === null && targetPct !== null) {
    minPct = targetPct
    maxPct = targetPct
  }
  if ((minPct !== null || maxPct !== null) && (bandMin !== null || bandMax !== null)) {
    const lo = bandMin !== null && minPct !== null ? (bandMin * minPct) / 100 : null
    const hi = bandMax !== null && maxPct !== null ? (bandMax * maxPct) / 100 : null
    return { min: lo, max: hi, currency, basis: "percent_of_salary" }
  }

  const spec = (c.spec || {}) as Record<string, unknown>
  const nMin = num(spec.n_salaries_min)
  const nMax = num(spec.n_salaries_max)
  if ((nMin !== null || nMax !== null) && (bandMin !== null || bandMax !== null)) {
    const lo = bandMin !== null && nMin !== null ? bandMin * nMin : null
    const hi = bandMax !== null && nMax !== null ? bandMax * nMax : null
    return { min: lo, max: hi, currency, basis: "n_salaries" }
  }

  return { min: null, max: null, currency, basis: "undefined" }
}

export function fmtBRL(v: number | null, currency = "BRL"): string {
  if (v === null) return "—"
  try {
    return v.toLocaleString("pt-BR", { style: "currency", currency, maximumFractionDigits: 0 })
  } catch {
    return `R$ ${Math.round(v).toLocaleString("pt-BR")}`
  }
}

export function bandMapFromList(
  bands: Array<{ level: string; min?: number | null; mid?: number | null; max?: number | null; currency?: string | null }>,
): Record<string, BandLite> {
  const map: Record<string, BandLite> = {}
  for (const b of bands || []) {
    if (b && b.level) map[b.level] = { min: b.min, mid: b.mid, max: b.max, currency: b.currency }
  }
  return map
}
