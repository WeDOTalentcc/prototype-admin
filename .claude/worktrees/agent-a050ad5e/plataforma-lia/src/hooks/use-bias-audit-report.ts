/**
 * use-bias-audit-report — hook para auditoria de adverse impact por vaga
 *
 * Separação de concerns (vue-migration-prep): toda lógica de fetch/state aqui.
 * Componente = template + binding apenas.
 *
 * Vue 3 equivalent: useBiasAuditReport composable em composables/useBiasAuditReport.ts
 */
import { useState, useCallback } from "react"

// ---------------------------------------------------------------------------
// Types — alinhados com BiasAuditReportResponse do backend (E.2)
// ---------------------------------------------------------------------------

export interface DimensionGroup {
  count: number
  approved: number
  rate: number
}

export interface AuditDimension {
  dimension: string
  groups: Record<string, DimensionGroup>
  adverse_impact_ratio: number
  below_threshold: boolean
  alert_level: "ok" | "warning"
}

export interface BiasAuditReport {
  job_id: string
  evaluated_at: string
  total_candidates: number
  dimensions: AuditDimension[]
  has_alerts: boolean
}

export interface UseBiasAuditReportState {
  jobIdInput: string
  loading: boolean
  error: string | null
  auditData: BiasAuditReport | null
}

export interface UseBiasAuditReportActions {
  setJobIdInput: (value: string) => void
  fetchAudit: (id: string) => Promise<void>
  handleSearch: () => void
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useBiasAuditReport(): UseBiasAuditReportState & UseBiasAuditReportActions {
  const [jobIdInput, setJobIdInput] = useState<string>("")
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [auditData, setAuditData] = useState<BiasAuditReport | null>(null)

  const fetchAudit = useCallback(async (id: string) => {
    if (!id.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`/api/backend-proxy/bias-audit/${id.trim()}`)
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        setError(body.error || `Erro ${res.status} ao carregar auditoria`)
        setAuditData(null)
        return
      }
      const data: BiasAuditReport = await res.json()
      setAuditData(data)
    } catch {
      setError("Erro de conexão ao carregar auditoria de viés")
      setAuditData(null)
    } finally {
      setLoading(false)
    }
  }, [])

  const handleSearch = useCallback(() => {
    fetchAudit(jobIdInput)
  }, [jobIdInput, fetchAudit])

  return {
    jobIdInput,
    loading,
    error,
    auditData,
    setJobIdInput,
    fetchAudit,
    handleSearch,
  }
}
