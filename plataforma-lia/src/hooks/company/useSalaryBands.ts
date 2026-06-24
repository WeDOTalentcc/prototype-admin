"use client"

/**
 * useSalaryBands — faixa salarial canonica GRANULAR (SalaryBand) por catalogo.
 *
 * Fonte unica (Configuracoes -> Faixas Salariais por Nivel). useSalaryBands lista
 * todas as faixas (catalogo). useSalaryBandMap traz {nivel: faixa-base} para o
 * preview de R$ da verba (backend escolhe a faixa mais ampla por nivel).
 */
import { useQuery } from "@tanstack/react-query"
import type { BandLite } from "@/lib/compensation/resolve"

export interface SalaryBandRow {
  id?: string
  level: string
  label?: string | null
  min?: number | null
  mid?: number | null
  max?: number | null
  currency?: string | null
  contract_types?: string[]
  departments?: Record<string, unknown>
  area?: string[]
  subsidiaries?: Array<{ name: string; cnpj?: string | null }>
  valid_from?: string | null
  valid_until?: string | null
  is_active?: boolean
  order?: number
}

const BASE = "/api/backend-proxy/company/salary-bands"

export function useSalaryBands() {
  return useQuery<SalaryBandRow[]>({
    queryKey: ["company-salary-bands"],
    queryFn: async () => {
      const res = await fetch(`${BASE}/`, { signal: AbortSignal.timeout(12000) })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      return Array.isArray(json) ? json : json?.data || []
    },
    staleTime: 30_000,
    retry: 1,
  })
}

/** A faixa que CASA o escopo da vaga (nivel + departamento/contrato) — p/ derivar R$. */
export function useResolvedSalaryBand(
  seniorityLevel?: string,
  department?: string,
  contractType?: string,
) {
  return useQuery<SalaryBandRow | null>({
    queryKey: ["company-salary-band-resolve", seniorityLevel || "", department || "", contractType || ""],
    enabled: !!seniorityLevel,
    queryFn: async () => {
      const qs = new URLSearchParams()
      if (seniorityLevel) qs.set("seniority_level", seniorityLevel)
      if (department) qs.set("department", department)
      if (contractType) qs.set("contract_type", contractType)
      const res = await fetch(`${BASE}/resolve?${qs.toString()}`, { signal: AbortSignal.timeout(12000) })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      return json || null
    },
    staleTime: 30_000,
    retry: 1,
  })
}

/** {nivel: {min,mid,max,currency}} — faixa-base por nivel (preview de R$ da verba). */
export function useSalaryBandMap() {
  return useQuery<Record<string, BandLite>>({
    queryKey: ["company-salary-band-map"],
    queryFn: async () => {
      const res = await fetch(`${BASE}/map`, { signal: AbortSignal.timeout(12000) })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      return json && typeof json === "object" ? json : {}
    },
    staleTime: 30_000,
    retry: 1,
  })
}

/** Benchmark de mercado (estimativa). Resultado do GET /api/v1/salary-benchmark. */
export interface SalaryBenchmarkResult {
  min?: number | null
  max?: number | null
  currency?: string | null
  confidence?: string | null
  is_estimate?: boolean | null
  source?: string | null
}

/**
 * useSalaryBenchmark — estimativa de mercado p/ o FALLBACK da faixa salarial
 * quando NAO ha banda cadastrada da empresa. NUNCA e ancorada como fato: o UI
 * rotula como "estimativa de mercado" e exige confirmacao do recrutador
 * (proveniencia honesta, CLAUDE.md REGRA 4). Habilitar via opts.enabled p/
 * nao buscar mercado quando a banda da empresa ja resolveu.
 */
export function useSalaryBenchmark(
  jobTitle?: string,
  seniority?: string,
  opts?: { location?: string; enabled?: boolean },
) {
  return useQuery<SalaryBenchmarkResult | null>({
    queryKey: ["salary-benchmark", jobTitle || "", seniority || "", opts?.location || ""],
    enabled: !!jobTitle && (opts?.enabled ?? true),
    queryFn: async () => {
      const qs = new URLSearchParams({ job_title: jobTitle as string })
      if (seniority) qs.set("seniority", seniority)
      if (opts?.location) qs.set("location", opts.location)
      const res = await fetch(`/api/backend-proxy/salary-benchmark?${qs.toString()}`, { signal: AbortSignal.timeout(12000) })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      return json || null
    },
    staleTime: 60_000,
    retry: 1,
  })
}
