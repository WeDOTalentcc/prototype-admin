"use client"

/**
 * useSalaryBands — faixa salarial canonica por nivel (SalaryBand).
 *
 * Fonte unica (Configuracoes -> Faixas Salariais por Nivel). Consumido pelo modal
 * de verba (preview R$ derivado) e pelo card de Configuracoes. React Query, key
 * canonica ["company-salary-bands"].
 */
import { useQuery } from "@tanstack/react-query"

export interface SalaryBandRow {
  id?: string
  level: string
  label?: string | null
  min?: number | null
  mid?: number | null
  max?: number | null
  currency?: string | null
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
