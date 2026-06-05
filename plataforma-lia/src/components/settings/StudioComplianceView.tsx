"use client"

import React, { useEffect, useState } from "react"
import { useTranslations } from "next-intl"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Bot, ShieldCheck, AlertTriangle, Activity, TrendingDown, Loader2 } from "lucide-react"
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts"
import { textStyles, cardStyles } from "@/lib/design-tokens"
import { cn } from "@/lib/utils"
import { HubHeader, HubLoadingState, HubErrorState } from "./_shared"
import { CHART_GRID, CHART_LIA, CHART_DANGER } from "@/lib/chart-colors"
import { apiFetch } from "@/lib/api/api-fetch"

interface StudioComplianceData {
  period_days?: number
  total_executions?: number
  blocked_executions?: number
  block_rate_pct?: number
  avg_confidence?: number
  active_agents?: number
  by_status?: Record<string, number>
  top_blocked_agents?: Array<{ agent_id: string; agent_name: string; blocked_count: number }>
  trend?: Array<{ day: string; executions: number; blocked: number }>
}

export function StudioComplianceView() {
  const t = useTranslations("settings.studio")
  const [period, setPeriod] = useState("30")
  const [data, setData] = useState<StudioComplianceData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      setError(null)
      try {
        // P1-W4-03: removed localStorage.getItem("auth_token") anti-pattern.
        // apiFetch already handles auth via JWT/session cookies (CLAUDE.md REGRA 6 canonical).
        // Passing a manually extracted token as Bearer header is redundant and creates
        // cross-tenant risk if the stored token differs from the active session JWT.
        const res = await apiFetch(`/api/backend-proxy/custom-agents/studio-compliance-summary?period_days=${period}`)
        if (!res.ok) throw new Error(t("loadError"))
        const json = await res.json()
        setData(json)
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : t("loadErrorGeneric"))
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [period, t])

  if (loading) {
    return <HubLoadingState message={t("loading")} />
  }

  if (error) {
    return <HubErrorState message={error} />
  }

  if (!data) return null

  const trend = data.trend ?? []
  const topBlockedAgents = data.top_blocked_agents ?? []
  const totalExecutions = data.total_executions ?? 0
  const blockedExecutions = data.blocked_executions ?? 0
  const blockRatePct = data.block_rate_pct ?? 0
  const activeAgents = data.active_agents ?? 0
  const avgConfidence = data.avg_confidence ?? 0

  return (
    <div className="space-y-4" data-testid="studio-compliance-view">
      {/* Header with period selector */}
      <HubHeader title={t("title")}>
        <Select value={period} onValueChange={setPeriod}>
          <SelectTrigger className="w-40" data-testid="studio-compliance-period-select">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7">{t("last7")}</SelectItem>
            <SelectItem value="30">{t("last30")}</SelectItem>
            <SelectItem value="90">{t("last90")}</SelectItem>
          </SelectContent>
        </Select>
      </HubHeader>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card className={cardStyles.default}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <Activity className="w-4 h-4 text-lia-text-secondary" />
              <span className="text-xs text-lia-text-secondary">{t("executions")}</span>
            </div>
            <p className={textStyles.kpi}>{totalExecutions}</p>
          </CardContent>
        </Card>

        <Card className={cardStyles.default}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <ShieldCheck className="w-4 h-4 text-status-success" />
              <span className="text-xs text-lia-text-secondary">{t("approved")}</span>
            </div>
            <p className={cn(textStyles.kpi, "text-status-success")}>
              {Math.max(0, totalExecutions - blockedExecutions)}
            </p>
          </CardContent>
        </Card>

        <Card className={cardStyles.default}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="w-4 h-4 text-status-warning" />
              <span className="text-xs text-lia-text-secondary">{t("blocked")}</span>
            </div>
            <p className={cn(textStyles.kpi, "text-status-warning")}>{blockedExecutions}</p>
            <p className="text-[10px] text-lia-text-disabled mt-0.5">{t("blockedPctOfTotal", { pct: blockRatePct })}</p>
          </CardContent>
        </Card>

        <Card className={cardStyles.default}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <Bot className="w-4 h-4 text-wedo-cyan-dark" />
              <span className="text-xs text-lia-text-secondary">{t("activeAgents")}</span>
            </div>
            <p className={textStyles.kpi}>{activeAgents}</p>
            <p className="text-[10px] text-lia-text-disabled mt-0.5">
              {t("avgConfidence", { pct: (avgConfidence * 100).toFixed(0) })}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Trend chart */}
      {trend.length > 0 && (
        <Card className={cardStyles.default}>
          <CardHeader>
            <CardTitle className="text-sm">{t("executionsByDay")}</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="executions" stroke={CHART_LIA} strokeWidth={2} name={t("totalLine")} />
                <Line type="monotone" dataKey="blocked" stroke={CHART_DANGER} strokeWidth={2} name={t("blockedLine")} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Top blocked agents */}
      {topBlockedAgents.length > 0 && (
        <Card className={cardStyles.default}>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <TrendingDown className="w-4 h-4 text-status-warning" />
              {t("topBlockedAgents")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {topBlockedAgents.map((a, i) => (
                <div key={a.agent_id} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-lia-text-disabled font-sans">{i + 1}.</span>
                    <span className="text-lia-text-primary">{a.agent_name}</span>
                  </div>
                  <Chip density="relaxed" variant="neutral" muted className="bg-status-warning/15 text-status-warning">
                    {t("blocks", { count: a.blocked_count })}
                  </Chip>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty state */}
      {totalExecutions === 0 && (
        <Card className={cardStyles.default}>
          <CardContent className="py-8 text-center">
            <Bot className="w-10 h-10 text-lia-text-disabled mx-auto mb-3" />
            <p className={textStyles.subtitle}>{t("noExecutions")}</p>
            <p className="text-xs text-lia-text-disabled mt-1">
              {t("noExecutionsHint")}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
