"use client"

import React, { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Shield, AlertTriangle, TrendingDown, Download } from "lucide-react"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts"
import { useTranslations } from "next-intl"
import { textStyles, cardStyles } from "@/lib/design-tokens"
import { CHART_DANGER, CHART_WARNING } from "@/lib/chart-colors"
import { apiFetch } from "@/lib/api/api-fetch"

/**
 * FairnessDashboard — staff WeDOTalent only.
 *
 * Movido de `src/components/settings/FairnessComplianceHub.tsx` em 2026-05-25
 * (plan canonical: ~/.claude/plans/jolly-roaming-moler.md, seção PR 2).
 *
 * Inclui:
 * - Sumário de eventos/bloqueios/alertas por período (Feature 1)
 * - Gráfico por categoria (Feature 1)
 * - Export CSV/JSON (Feature 4)
 * - Tabela de incidentes recentes
 *
 * Acessado APENAS via `/wedo-admin/fairness/` (gate role=wedotalent_admin).
 * Backend services intactos: continua chamando os mesmos proxy routes
 * `/api/backend-proxy/fairness-report/*` e `/api/backend-proxy/fairness/audit/logs`.
 */

interface FairnessSummary {
  total_blocks: number
  total_events: number
  by_category: CategorySummary[]
}

interface CategorySummary {
  category: string
  total_blocks: number
  total_warnings: number
  last_occurrence: string | null
}

interface AuditLogEntry {
  id: string
  category: string
  is_blocked: boolean
  blocked_terms: string[]
  soft_warnings: string[]
  context: string | null
  created_at: string
}

const CATEGORY_KEY_MAP: Record<string, string> = {
  gender: "categoryGender",
  age: "categoryAge",
  race: "categoryRace",
  disability: "categoryDisability",
  religion: "categoryReligion",
  sexual_orientation: "categorySexualOrientation",
  nationality: "categoryNationality",
  marital_status: "categoryMaritalStatus",
  appearance: "categoryAppearance",
}

export function FairnessDashboard() {
  const t = useTranslations("wedo_admin.fairness.dashboard")
  const [period, setPeriod] = useState("30")
  const [summary, setSummary] = useState<FairnessSummary | null>(null)
  const [logs, setLogs] = useState<AuditLogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const translateCategory = React.useCallback((cat: string): string => {
    const key = CATEGORY_KEY_MAP[cat]
    if (key) return t(key)
    return cat.charAt(0).toUpperCase() + cat.slice(1)
  }, [t])

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      setError(null)
      try {
        const [summaryRes, logsRes] = await Promise.all([
          apiFetch(`/api/backend-proxy/fairness-report/summary?days=${period}`),
          apiFetch(`/api/backend-proxy/fairness/audit/logs?days=${period}`),
        ])
        if (!summaryRes.ok || !logsRes.ok) throw new Error(t("errorLoadingData"))
        const summaryData = await summaryRes.json()
        const logsData = await logsRes.json()
        setSummary(summaryData)
        setLogs(logsData.items || [])
      } catch (err) {
        setError(err instanceof Error ? err.message : t("errorLoadingFairnessData"))
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [period, t])

  const handleExport = (format: "csv" | "json") => {
    window.open(`/api/backend-proxy/fairness-report/export?format=${format}&days=${period}`, "_blank")
  }

  const totalEvents = summary?.total_events ?? 0
  const totalBlocks = summary?.total_blocks ?? 0
  const totalWarnings = Math.max(0, totalEvents - totalBlocks)

  const chartData = (summary?.by_category ?? []).map((c) => ({
    name: translateCategory(c.category),
    bloqueios: c.total_blocks ?? 0,
    alertas: c.total_warnings ?? 0,
  }))

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="w-10 h-10 text-status-error mx-auto mb-3" />
        <h3 className={textStyles.subtitle}>{t("errorLoading")}</h3>
        <p className={textStyles.description}>{error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6" data-testid="fairness-dashboard">
      <div className="flex items-center justify-between">
        <div>
          <h2 className={textStyles.subtitle}>{t("title")}</h2>
          <p className={textStyles.description}>{t("description")}</p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-[140px]" data-testid="fairness-period-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">{t("period7")}</SelectItem>
              <SelectItem value="30">{t("period30")}</SelectItem>
              <SelectItem value="90">{t("period90")}</SelectItem>
              <SelectItem value="365">{t("period365")}</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm" onClick={() => handleExport("csv")} data-testid="fairness-export-csv">
            <Download className="w-4 h-4 mr-1.5" /> {t("exportCsv")}
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleExport("json")} data-testid="fairness-export-json">
            <Download className="w-4 h-4 mr-1.5" /> {t("exportJson")}
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className={cardStyles.default}>
              <CardContent className="p-5">
                <div className="animate-pulse space-y-3">
                  <div className="h-4 bg-lia-bg-tertiary rounded w-2/3" />
                  <div className="h-8 bg-lia-bg-tertiary rounded w-1/3" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className={cardStyles.default}>
            <CardContent className="p-5">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-9 h-9 rounded-md bg-wedo-cyan/10 flex items-center justify-center">
                  <Shield className="w-5 h-5 text-wedo-cyan" />
                </div>
                <span className={textStyles.description}>{t("totalEvents")}</span>
              </div>
              <p className="text-2xl font-semibold text-lia-text-primary">{totalEvents}</p>
            </CardContent>
          </Card>
          <Card className={cardStyles.default}>
            <CardContent className="p-5">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-9 h-9 rounded-md bg-status-error/10 flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5 text-status-error" />
                </div>
                <span className={textStyles.description}>{t("blocks")}</span>
              </div>
              <p className="text-2xl font-semibold text-status-error">{totalBlocks}</p>
            </CardContent>
          </Card>
          <Card className={cardStyles.default}>
            <CardContent className="p-5">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-9 h-9 rounded-md bg-status-warning/10 flex items-center justify-center">
                  <TrendingDown className="w-5 h-5 text-status-warning" />
                </div>
                <span className={textStyles.description}>{t("alerts")}</span>
              </div>
              <p className="text-2xl font-semibold text-status-warning">{totalWarnings}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {!loading && chartData.length > 0 && (
        <Card className={cardStyles.default} data-testid="fairness-drilldown">
          <CardHeader className="pb-2">
            <CardTitle className={textStyles.subtitle}>{t("eventsByCategory")}</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="bloqueios" fill={CHART_DANGER} radius={[4, 4, 0, 0]} name={t("blocksChart")} />
                <Bar dataKey="alertas" fill={CHART_WARNING} radius={[4, 4, 0, 0]} name={t("alertsChart")} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {!loading && logs.length > 0 && (
        <Card className={cardStyles.default} data-testid="fairness-incidents">
          <CardHeader className="pb-2">
            <CardTitle className={textStyles.subtitle}>{t("recentIncidents")}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-lia-border-default">
                    <th className="text-left py-2 px-3 font-medium text-lia-text-secondary">{t("categoryColumn")}</th>
                    <th className="text-left py-2 px-3 font-medium text-lia-text-secondary">{t("typeColumn")}</th>
                    <th className="text-left py-2 px-3 font-medium text-lia-text-secondary">{t("termsColumn")}</th>
                    <th className="text-left py-2 px-3 font-medium text-lia-text-secondary">{t("dateColumn")}</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id} className="border-lia-border-default/50 hover:bg-lia-bg-tertiary/50">
                      <td className="py-2.5 px-3">
                        <Badge variant="outline" className="text-xs">
                          {translateCategory(log.category)}
                        </Badge>
                      </td>
                      <td className="py-2.5 px-3">
                        {log.is_blocked ? (
                          <Badge className="bg-status-error/15 text-status-error text-xs">{t("blocked")}</Badge>
                        ) : (
                          <Badge className="bg-status-warning/15 text-status-warning text-xs">{t("alert")}</Badge>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-lia-text-secondary max-w-[200px] truncate">
                        {log.is_blocked
                          ? (log.blocked_terms || []).join(",")
                          : (log.soft_warnings || []).join(",")}
                      </td>
                      <td className="py-2.5 px-3 text-lia-text-secondary whitespace-nowrap">
                        {new Date(log.created_at).toLocaleDateString(t("dateLocale"), {
                          day: "2-digit",
                          month: "short",
                          year: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {!loading && logs.length === 0 && !error && (
        <Card className={cardStyles.default}>
          <CardContent className="py-8 text-center">
            <Shield className="w-10 h-10 text-status-success mx-auto mb-3" />
            <p className={textStyles.subtitle}>{t("noIncidents")}</p>
            <p className={textStyles.description}>{t("noIncidentsDesc")}</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
