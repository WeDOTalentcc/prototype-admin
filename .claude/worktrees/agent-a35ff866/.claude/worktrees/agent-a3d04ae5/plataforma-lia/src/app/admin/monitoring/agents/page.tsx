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
  healthy:  { label: "Saudável",  color: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400", icon: CheckCircle2 },
  warning:  { label: "Atenção",   color: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400", icon: AlertTriangle },
  degraded: { label: "Degradado", color: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400", icon: TrendingDown },
  stale:    { label: "Inativo",   color: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400", icon: Clock },
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
          <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Saúde dos Agentes IA
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            Métricas de execução por domínio — baseado em registros reais
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={windowDays} onValueChange={setWindowDays}>
            <SelectTrigger className="w-32 h-8 text-xs rounded-md border-gray-200 dark:border-gray-700">
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
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <RefreshCw className="h-3 w-3" />
            )}
          </Button>
        </div>
      </div>

      {/* Resumo */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Saudáveis",  value: healthyCnt,  color: "text-green-600 dark:text-green-400" },
          { label: "Atenção",    value: warningCnt,  color: "text-yellow-600 dark:text-yellow-400" },
          { label: "Degradados", value: degradedCnt, color: "text-red-600 dark:text-red-400" },
          { label: "Inativos",   value: staleCnt,    color: "text-gray-500 dark:text-gray-400" },
        ].map((item) => (
          <Card key={item.label} className="rounded-md border border-gray-200 dark:border-gray-700 shadow-none">
            <CardContent className="p-4">
              <p className="text-xs text-gray-500 dark:text-gray-400">{item.label}</p>
              <p className={`text-2xl font-semibold mt-1 ${item.color}`}>{item.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Estado de carregamento / erro */}
      {loading && (
        <div className="flex justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
        </div>
      )}

      {error && !loading && (
        <div className="rounded-md border border-red-200 bg-red-50 dark:bg-red-900/20 dark:border-red-800 p-4 text-xs text-red-700 dark:text-red-400">
          {error}
        </div>
      )}

      {!loading && !error && domains.length === 0 && (
        <div className="rounded-md border border-gray-200 dark:border-gray-700 p-8 text-center text-xs text-gray-400">
          Nenhum dado de execução encontrado nos últimos {windowDays} dias.
        </div>
      )}

      {/* Tabela de domínios */}
      {!loading && domains.length > 0 && (
        <Card className="rounded-md border border-gray-200 dark:border-gray-700 shadow-none">
          <CardHeader className="py-3 px-4 border-b border-gray-200 dark:border-gray-700">
            <CardTitle className="text-xs font-medium text-gray-700 dark:text-gray-300">
              Métricas por Domínio
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-100 dark:border-gray-800">
                  {["Domínio", "Status", "Execuções", "Confiança Média", "Falha Tools", "Iterações", "Duração (ms)", "Última Execução"].map((h) => (
                    <th key={h} className="text-left px-4 py-2.5 text-gray-500 dark:text-gray-400 font-medium">
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
                      className="border-b border-gray-50 dark:border-gray-800/50 hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors"
                    >
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">
                        <span className="flex items-center gap-1.5">
                          <Zap className="h-3 w-3 text-gray-400" />
                          {label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <Badge className={`${cfg.color} border-0 text-xs font-normal gap-1`}>
                          <StatusIcon className="h-3 w-3" />
                          {cfg.label}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-gray-700 dark:text-gray-300">
                        {domain.total_executions.toLocaleString("pt-BR")}
                      </td>
                      <td className="px-4 py-3 text-gray-700 dark:text-gray-300">
                        <span className={domain.avg_confidence < 0.5 ? "text-red-600 dark:text-red-400" : ""}>
                          {(domain.avg_confidence * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-700 dark:text-gray-300">
                        <span className={domain.tool_failure_rate > 0.1 ? "text-yellow-600 dark:text-yellow-400" : ""}>
                          {(domain.tool_failure_rate * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-700 dark:text-gray-300">
                        {domain.avg_iterations.toFixed(1)}
                      </td>
                      <td className="px-4 py-3 text-gray-700 dark:text-gray-300">
                        {domain.avg_duration_ms > 0 ? domain.avg_duration_ms.toFixed(0) : "—"}
                      </td>
                      <td className="px-4 py-3 text-gray-500 dark:text-gray-400">
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
