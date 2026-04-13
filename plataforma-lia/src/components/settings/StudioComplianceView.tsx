"use client"

import React, { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Bot, ShieldCheck, AlertTriangle, Activity, TrendingDown, Loader2 } from "lucide-react"
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts"
import { textStyles, cardStyles } from "@/lib/design-tokens"

interface StudioComplianceData {
  period_days: number
  total_executions: number
  blocked_executions: number
  block_rate_pct: number
  avg_confidence: number
  active_agents: number
  by_status: Record<string, number>
  top_blocked_agents: Array<{ agent_id: string; agent_name: string; blocked_count: number }>
  trend: Array<{ day: string; executions: number; blocked: number }>
}

export function StudioComplianceView() {
  const [period, setPeriod] = useState("30")
  const [data, setData] = useState<StudioComplianceData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      setError(null)
      try {
        const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
        const res = await fetch(
          `/api/backend-proxy/custom-agents/studio-compliance-summary?period_days=${period}`,
          { headers: token ? { Authorization: `Bearer ${token}` } : {} },
        )
        if (!res.ok) throw new Error("Erro ao carregar dados")
        const json = await res.json()
        setData(json)
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Erro ao carregar")
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [period])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12 gap-2 text-sm text-lia-text-secondary">
        <Loader2 className="w-4 h-4 animate-spin" /> Carregando metricas do Studio...
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="w-10 h-10 text-status-error mx-auto mb-3" />
        <p className={textStyles.subtitle}>{error}</p>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="space-y-4">
      {/* Header with period selector */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-wedo-cyan-dark" />
          <h2 className={textStyles.title}>Compliance do Agent Studio</h2>
        </div>
        <Select value={period} onValueChange={setPeriod}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7">Ultimos 7 dias</SelectItem>
            <SelectItem value="30">Ultimos 30 dias</SelectItem>
            <SelectItem value="90">Ultimos 90 dias</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card className={cardStyles.default}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <Activity className="w-4 h-4 text-lia-text-secondary" />
              <span className="text-xs text-lia-text-secondary">Execucoes</span>
            </div>
            <p className="text-2xl font-bold font-inter text-lia-text-primary">{data.total_executions}</p>
          </CardContent>
        </Card>

        <Card className={cardStyles.default}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <ShieldCheck className="w-4 h-4 text-emerald-500" />
              <span className="text-xs text-lia-text-secondary">Aprovadas</span>
            </div>
            <p className="text-2xl font-bold font-inter text-emerald-600">
              {data.total_executions - data.blocked_executions}
            </p>
          </CardContent>
        </Card>

        <Card className={cardStyles.default}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="w-4 h-4 text-status-warning" />
              <span className="text-xs text-lia-text-secondary">Bloqueadas</span>
            </div>
            <p className="text-2xl font-bold font-inter text-status-warning">{data.blocked_executions}</p>
            <p className="text-[10px] text-lia-text-disabled mt-0.5">{data.block_rate_pct}% do total</p>
          </CardContent>
        </Card>

        <Card className={cardStyles.default}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <Bot className="w-4 h-4 text-wedo-cyan-dark" />
              <span className="text-xs text-lia-text-secondary">Agents ativos</span>
            </div>
            <p className="text-2xl font-bold font-inter text-lia-text-primary">{data.active_agents}</p>
            <p className="text-[10px] text-lia-text-disabled mt-0.5">
              Confianca media: {(data.avg_confidence * 100).toFixed(0)}%
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Trend chart */}
      {data.trend.length > 0 && (
        <Card className={cardStyles.default}>
          <CardHeader>
            <CardTitle className="text-sm">Execucoes por dia</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={data.trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="executions" stroke="#60BED1" strokeWidth={2} name="Total" />
                <Line type="monotone" dataKey="blocked" stroke="#DC2626" strokeWidth={2} name="Bloqueadas" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Top blocked agents */}
      {data.top_blocked_agents.length > 0 && (
        <Card className={cardStyles.default}>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <TrendingDown className="w-4 h-4 text-status-warning" />
              Agents com mais bloqueios
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.top_blocked_agents.map((a, i) => (
                <div key={a.agent_id} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-lia-text-disabled font-inter">{i + 1}.</span>
                    <span className="text-lia-text-primary">{a.agent_name}</span>
                  </div>
                  <Badge className="bg-status-warning/15 text-status-warning text-xs">
                    {a.blocked_count} bloqueio{a.blocked_count !== 1 ? "s" : ""}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty state */}
      {data.total_executions === 0 && (
        <Card className={cardStyles.default}>
          <CardContent className="py-8 text-center">
            <Bot className="w-10 h-10 text-lia-text-disabled mx-auto mb-3" />
            <p className={textStyles.subtitle}>Sem execucoes no periodo</p>
            <p className="text-xs text-lia-text-disabled mt-1">
              Crie agents no Studio e vincule a vagas para ver metricas aqui
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
