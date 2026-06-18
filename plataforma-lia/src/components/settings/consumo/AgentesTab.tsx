'use client'

import useSWR from 'swr'
import { useTranslations } from 'next-intl'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Chip } from '@/components/ui/chip'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  LineChart,
  Line,
  Legend,
} from 'recharts'
import type { Payload } from 'recharts/types/component/DefaultTooltipContent'
import type { ComponentProps } from 'react'
import { useMemo } from 'react'
import { getAgentColor, getAgentLabel, type AgentChartEntry, type AgentTrendDayEntry } from './CreditosIaTab'

const jsonFetcher = (url: string) => fetch(url).then(r => r.json())

function formatTokens(tokens: number | null | undefined): string {
  if (tokens == null || Number.isNaN(tokens)) return "—"
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(1)}M`
  if (tokens >= 1_000) return `${(tokens / 1_000).toFixed(1)}K`
  return tokens.toString()
}

function formatCost(cents: number | null | undefined): string {
  if (cents == null || Number.isNaN(cents)) return "—"
  return `$${(cents / 100).toFixed(2)}`
}

interface AgentUsage {
  agent_type: string
  total_tokens: number
  total_cost_cents: number
  total_operations?: number
  operation_count?: number
}

interface AgentDailyTrend {
  date: string
  agent_type: string
  total_tokens: number
}

function parseAgentData(raw: unknown): AgentUsage[] {
  if (!raw) return []
  if (Array.isArray(raw)) return raw as AgentUsage[]
  const r = raw as Record<string, unknown>
  return (r.data ?? r.usage_by_agent ?? []) as AgentUsage[]
}

function parseTrendData(raw: unknown): AgentDailyTrend[] {
  if (!raw) return []
  if (Array.isArray(raw)) return raw as AgentDailyTrend[]
  const r = raw as Record<string, unknown>
  return (r.data ?? []) as AgentDailyTrend[]
}

function agentBreakdownTooltipFormatter(
  value: unknown,
  _name: unknown,
  entry: Payload<number, string>,
): [string, string] {
  const v = typeof value === 'number' ? value : Number(value ?? 0)
  const payload = entry.payload as AgentChartEntry | undefined
  const pct = payload?.percentage ?? 0
  return [`${formatTokens(v)} tokens (${pct}%)`, 'Consumo']
}

/**
 * Onda 5.2 / CF-B B6 (2026-05-29) — drilldown e 100% owned pelo ConsumoHub.
 * AgentesTab apenas emite o request via onOpenDrilldown (prop obrigatoria).
 * O fallback de modal local foi removido para eliminar risco de double-mount
 * (AUDIT 4 P2-12).
 */
export interface AgentesTabProps {
  onOpenDrilldown: (state: {
    agentType: string | null
    studioAgentId: string | null
  }) => void
}

export function AgentesTab({ onOpenDrilldown }: AgentesTabProps) {
  const t = useTranslations('settings.consumption.agentes')

  function openDrilldown(agentType: string) {
    onOpenDrilldown({ agentType, studioAgentId: null })
  }

  const { data: agentRaw, isLoading: agentLoading } =
    useSWR('/api/backend-proxy/ai-credits?endpoint=by-agent', jsonFetcher)

  const { data: trendRaw, isLoading: trendLoading } =
    useSWR('/api/backend-proxy/ai-credits?endpoint=agent-trend&days=30', jsonFetcher)

  const byAgent: AgentUsage[] = parseAgentData(agentRaw)
  const agentTrend: AgentDailyTrend[] = parseTrendData(trendRaw)

  const totalAgentTokens = byAgent.reduce((sum, a) => sum + a.total_tokens, 0)
  const agentChartData: AgentChartEntry[] = [...byAgent]
    .sort((a, b) => b.total_tokens - a.total_tokens)
    .map((agent) => ({
      name: getAgentLabel(agent.agent_type),
      agentType: agent.agent_type,
      tokens: agent.total_tokens,
      cost: agent.total_cost_cents,
      operations: agent.total_operations ?? agent.operation_count ?? 0,
      percentage:
        totalAgentTokens > 0
          ? +((agent.total_tokens / totalAgentTokens) * 100).toFixed(1)
          : 0,
    }))

  const { trendChartData, trendAgentTypes } = useMemo(() => {
    if (agentTrend.length === 0)
      return { trendChartData: [] as AgentTrendDayEntry[], trendAgentTypes: [] as string[] }

    const agentTypes = [...new Set(agentTrend.map((tr) => tr.agent_type))]
    const byDate = new Map<string, { isoDate: string; entry: AgentTrendDayEntry }>()

    for (const item of agentTrend) {
      const displayDate = item.date.slice(5)
      if (!byDate.has(item.date)) {
        byDate.set(item.date, { isoDate: item.date, entry: { date: displayDate } })
      }
      const row = byDate.get(item.date)!
      row.entry[item.agent_type] = Math.round(item.total_tokens / 1000)
    }

    const sorted = [...byDate.values()]
      .sort((a, b) => a.isoDate.localeCompare(b.isoDate))
      .map((v) => v.entry)

    return { trendChartData: sorted, trendAgentTypes: agentTypes }
  }, [agentTrend])

  if (agentLoading || trendLoading) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-lia-text-tertiary">
        {t('loading')}
      </div>
    )
  }

  if (agentChartData.length === 0) {
    return (
      <Card className="border border-lia-border-subtle shadow-none">
        <CardHeader className="pb-2 pt-4">
          <CardTitle className="text-xs font-medium text-lia-text-tertiary">
            {t('breakdownTitle')}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex h-48 flex-col items-center justify-center gap-2">
          <p className="text-sm text-lia-text-muted">{t('empty')}</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {trendChartData.length > 0 && (
        <Card className="border border-lia-border-subtle shadow-none">
          <CardHeader className="pb-2 pt-4">
            <CardTitle className="text-xs font-medium text-lia-text-tertiary">
              {t('trendTitle')}
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            {/* Onda 5.5 — wrapper a11y: chart vira role=img com descricao contextual. */}
            <div
              role="img"
              aria-label={t('trendAriaLabel', { count: trendAgentTypes.length })}
              data-testid="agentes-trend-chart"
            >
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={trendChartData} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--lia-border-subtle)" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 10, fill: 'var(--lia-text-tertiary)' }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: 'var(--lia-text-tertiary)' }}
                    tickLine={false}
                    axisLine={false}
                    unit="K"
                  />
                  <Tooltip
                    contentStyle={{ fontSize: 11, borderRadius: 6, border: '1px solid var(--lia-border-subtle)' }}
                    formatter={(value, name) => {
                      const v = Number(value ?? 0)
                      return [`${v}K tokens`, getAgentLabel(String(name))] as [string, string]
                    }}
                  />
                  <Legend
                    formatter={(value: string) => getAgentLabel(value)}
                    wrapperStyle={{ fontSize: 11 }}
                  />
                  {trendAgentTypes.map((agentType) => (
                    <Line
                      key={agentType}
                      type="monotone"
                      dataKey={agentType}
                      stroke={getAgentColor(agentType)}
                      strokeWidth={2}
                      dot={false}
                      connectNulls
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="border border-lia-border-subtle shadow-none">
        <CardHeader className="pb-2 pt-4">
          <CardTitle className="text-xs font-medium text-lia-text-tertiary">
            {t('breakdownTitle')}
          </CardTitle>
        </CardHeader>
        <CardContent className="pb-4">
          {/* Onda 5.5 — wrapper a11y para BarChart breakdown. */}
          <div
            role="img"
            aria-label={t('breakdownAriaLabel', {
              count: agentChartData.length,
              top: agentChartData[0]?.name ?? '—',
            })}
            data-testid="agentes-breakdown-chart"
          >
            <ResponsiveContainer width="100%" height={Math.max(200, agentChartData.length * 48)}>
              <BarChart
                data={agentChartData}
                layout="vertical"
                margin={{ top: 4, right: 60, bottom: 0, left: 90 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="var(--lia-border-subtle)" horizontal={false} />
                <XAxis
                  type="number"
                  tick={{ fontSize: 10, fill: 'var(--lia-text-tertiary)' }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v: number) => formatTokens(v)}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fontSize: 11, fill: 'var(--lia-text-secondary)' }}
                  tickLine={false}
                  axisLine={false}
                  width={85}
                />
                <Tooltip
                  contentStyle={{ fontSize: 11, borderRadius: 6, border: '1px solid var(--lia-border-subtle)' }}
                  formatter={
                    agentBreakdownTooltipFormatter as NonNullable<ComponentProps<typeof Tooltip>['formatter']>
                  }
                />
                <Bar
                  dataKey="tokens"
                  radius={[0, 4, 4, 0]}
                  barSize={24}
                  cursor="pointer"
                  onClick={(payload: unknown) => {
                    const entry = payload as { agentType?: string } | undefined
                    if (entry?.agentType) openDrilldown(entry.agentType)
                  }}
                >
                  {agentChartData.map((entry) => (
                    <Cell key={entry.agentType} fill={getAgentColor(entry.agentType)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-4 space-y-1">
            {agentChartData.map((agent) => (
              <button
                key={agent.agentType}
                type="button"
                onClick={() => openDrilldown(agent.agentType)}
                aria-label={t('viewExecutionsAria', { agentName: agent.name })}
                className="flex w-full items-center justify-between rounded-md px-3 py-2 text-sm text-left transition-colors hover:bg-lia-bg-secondary focus:bg-lia-bg-secondary focus:outline-none"
              >
                <div className="flex items-center gap-2">
                  <div
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: getAgentColor(agent.agentType) }}
                  />
                  <span className="font-medium text-lia-text-secondary">{agent.name}</span>
                </div>
                <div className="flex items-center gap-4 text-xs text-lia-text-tertiary">
                  <span>{formatTokens(agent.tokens)} tokens</span>
                  <span>{formatCost(agent.cost)}</span>
                  <span>{agent.operations} ops</span>
                  <Chip variant="neutral" className="text-xs font-normal">
                    {agent.percentage}%
                  </Chip>
                </div>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
