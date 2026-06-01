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
