"use client"

import React, { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useCurrentCompany } from "@/hooks/use-current-company"
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  RefreshCw,
  Loader2,
  TrendingDown,
  Zap,
} from "lucide-react"

interface DomainHealth {
  domain: string
  total_executions: number
  avg_duration_ms: number
  avg_iterations: number
  avg_confidence: number
  tool_failure_rate: number
  last_execution: string | null
  days_since_last_execution: number | null
  status: "healthy" | "warning" | "degraded" | "stale"
}

interface HealthResponse {
  company_id: string
  window_days: number
  domains: DomainHealth[]
  total_domains: number
  unhealthy_count: number
}

const STATUS_CONFIG = {
  healthy:  { label: "Saudável",  color: "bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success", icon: CheckCircle2 },
  warning:  { label: "Atenção",   color: "bg-status-warning/15 text-status-warning dark:bg-status-warning/30 dark:text-status-warning", icon: AlertTriangle },
  degraded: { label: "Degradado", color: "bg-status-error/15 text-status-error dark:bg-status-error/30 dark:text-status-error", icon: TrendingDown },
  stale:    { label: "Inativo",   color: "bg-gray-100 lia-text-600 dark:bg-lia-bg-secondary dark:text-lia-text-tertiary", icon: Clock },
}

const DOMAIN_LABELS: Record<string, string> = {
  pipeline: "Pipeline",
  sourcing: "Sourcing",
  cv_screening: "Triagem de CVs",
  job_management: "Gestão de Vagas",
  recruiter_assistant: "Assistente Recrutador",
  hiring_policy: "Política de Contratação",
  pipeline_transition: "Transição de Pipeline",
}

export default function AgentHealthDashboardPage() {
  const [data, setData] = useState<HealthResponse | null>(null)
  const [dataLoading, setDataLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [windowDays, setWindowDays] = useState("30")
  const { companyId, loading: companyLoading } = useCurrentCompany()
  const loading = companyLoading || dataLoading

  const fetchHealth = useCallback(async () => {
    if (!companyId) return
    setDataLoading(true)
    setError(null)
    try {
      const res = await fetch(
        `/api/backend-proxy/agent-monitoring/domains/health?company_id=${companyId}&days=${windowDays}`
      )
      if (!res.ok) throw new Error(`Erro ${res.status}`)
      const json = await res.json()
      setData(json)
    } catch (err) {
      setError("Não foi possível carregar os dados de saúde dos agentes.")
    } finally {
      setDataLoading(false)
    }
  }, [companyId, windowDays])

  useEffect(() => {
    fetchHealth()
  }, [fetchHealth])

  const domains = data?.domains ?? []
  const healthyCnt  = domains.filter(d => d.status === "healthy").length
  const warningCnt  = domains.filter(d => d.status === "warning").length
  const degradedCnt = domains.filter(d => d.status === "degraded").length
  const staleCnt    = domains.filter(d => d.status === "stale").length

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold lia-text-900 dark:text-lia-text-primary flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Saúde dos Agentes IA
          </h1>
          <p className="text-xs lia-text-500 dark:text-lia-text-tertiary mt-0.5">
            Métricas de execução por domínio — baseado em registros reais
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={windowDays} onValueChange={setWindowDays}>
            <SelectTrigger className="w-32 h-8 text-xs rounded-md border-lia-border-subtle dark:border-lia-border-subtle">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">7 dias</SelectItem>
              <SelectItem value="30">30 dias</SelectItem>
              <SelectItem value="60">60 dias</SelectItem>
              <SelectItem value="90">90 dias</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchHealth}
            disabled={loading}
            className="h-8 text-xs rounded-md"
          >
            {loading ? (
              <Loader2 className="h-3 w-3 animate-spin motion-reduce:animate-none" />
            ) : (
              <RefreshCw className="h-3 w-3" />
            )}
          </Button>
        </div>
      </div>

      {/* Resumo */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Saudáveis",  value: healthyCnt,  color: "text-status-success dark:text-status-success" },
          { label: "Atenção",    value: warningCnt,  color: "text-status-warning dark:text-status-warning" },
          { label: "Degradados", value: degradedCnt, color: "text-status-error dark:text-status-error" },
          { label: "Inativos",   value: staleCnt,    color: "lia-text-500 dark:text-lia-text-tertiary" },
        ].map((item) => (
          <Card key={item.label} className="rounded-md border border-lia-border-subtle dark:border-lia-border-subtle shadow-none">
            <CardContent className="p-4">
              <p className="text-xs lia-text-500 dark:text-lia-text-tertiary">{item.label}</p>
              <p className={`text-2xl font-semibold mt-1 ${item.color}`}>{item.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Estado de carregamento / erro */}
      {loading && (
        <div className="flex justify-center py-12" role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="h-6 w-6 animate-spin motion-reduce:animate-none lia-text-400" />
        </div>
      )}

      {error && !loading && (
        <div className="rounded-md border border-status-error/30 bg-status-error/10 dark:bg-status-error/20 dark:border-status-error/30 p-4 text-xs text-status-error dark:text-status-error">
          {error}
        </div>
      )}

      {!loading && !error && domains.length === 0 && (
        <div className="rounded-md border border-lia-border-subtle dark:border-lia-border-subtle p-8 text-center text-xs lia-text-400">
          Nenhum dado de execução encontrado nos últimos {windowDays} dias.
        </div>
      )}

      {/* Tabela de domínios */}
      {!loading && domains.length > 0 && (
        <Card className="rounded-md border border-lia-border-subtle dark:border-lia-border-subtle shadow-none">
          <CardHeader className="py-3 px-4 border-b border-lia-border-subtle dark:border-lia-border-subtle">
            <CardTitle className="text-xs font-medium lia-text-700 dark:text-lia-text-secondary">
              Métricas por Domínio
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-lia-border-subtle dark:lia-border-800">
                  {["Domínio", "Status", "Execuções", "Confiança Média", "Falha Tools", "Iterações", "Duração (ms)", "Última Execução"].map((h) => (
                    <th key={h} className="text-left px-4 py-2.5 lia-text-500 dark:text-lia-text-tertiary font-medium">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {domains.map((domain) => {
                  const cfg = STATUS_CONFIG[domain.status]
                  const StatusIcon = cfg.icon
                  const label = DOMAIN_LABELS[domain.domain] ?? domain.domain
                  return (
                    <tr
                      key={domain.domain}
                      className="border-b border-gray-50 dark:lia-border-800/50 hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors motion-reduce:transition-none"
                    >
                      <td className="px-4 py-3 font-medium lia-text-900 dark:text-lia-text-primary">
                        <span className="flex items-center gap-1.5">
                          <Zap className="h-3 w-3 lia-text-400" />
                          {label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <Badge className={`${cfg.color} border-0 text-xs font-normal gap-1`}>
                          <StatusIcon className="h-3 w-3" />
                          {cfg.label}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 lia-text-700 dark:text-lia-text-secondary">
                        {domain.total_executions.toLocaleString("pt-BR")}
                      </td>
                      <td className="px-4 py-3 lia-text-700 dark:text-lia-text-secondary">
                        <span className={domain.avg_confidence < 0.5 ? "text-status-error dark:text-status-error" : ""}>
                          {(domain.avg_confidence * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-4 py-3 lia-text-700 dark:text-lia-text-secondary">
                        <span className={domain.tool_failure_rate > 0.1 ? "text-status-warning dark:text-status-warning" : ""}>
                          {(domain.tool_failure_rate * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-4 py-3 lia-text-700 dark:text-lia-text-secondary">
                        {domain.avg_iterations.toFixed(1)}
                      </td>
                      <td className="px-4 py-3 lia-text-700 dark:text-lia-text-secondary">
                        {domain.avg_duration_ms > 0 ? domain.avg_duration_ms.toFixed(0) : "—"}
                      </td>
                      <td className="px-4 py-3 lia-text-500 dark:text-lia-text-tertiary">
                        {domain.days_since_last_execution !== null
                          ? domain.days_since_last_execution === 0
                            ? "Hoje"
                            : `${domain.days_since_last_execution}d atrás`
                          : "—"}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
