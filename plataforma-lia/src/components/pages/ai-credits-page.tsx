'use client'

import { useAiCredits, useAiConsumptionHistory } from '@/hooks/use-ai-credits'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { AlertTriangle, Zap, TrendingUp, DollarSign } from 'lucide-react'

function formatTokens(tokens: number): string {
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(1)}M`
  if (tokens >= 1_000) return `${(tokens / 1_000).toFixed(1)}K`
  return tokens.toString()
}

function formatCost(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`
}

function UsageAlert({ percentage }: { percentage: number }) {
  if (percentage >= 100) {
    return (
      <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
        <AlertTriangle className="h-4 w-4 shrink-0" />
        <span>
          <strong>Limite atingido:</strong> O consumo de IA atingiu 100% do limite mensal. Contate o suporte ou atualize seu plano.
        </span>
      </div>
    )
  }
  if (percentage >= 80) {
    return (
      <div className="flex items-center gap-2 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
        <AlertTriangle className="h-4 w-4 shrink-0" />
        <span>
          <strong>Atenção:</strong> {percentage.toFixed(0)}% do limite mensal de IA utilizado. Monitore o consumo para evitar interrupções.
        </span>
      </div>
    )
  }
  return null
}

interface Props {
  companyId?: string
}

export function AiCreditsPage({ companyId }: Props) {
  const { balance, summary, isLoading: balanceLoading, error: balanceError } = useAiCredits()
  const { byDay, byAgent, isLoading: historyLoading } = useAiConsumptionHistory(30)

  if (balanceLoading) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-gray-500">
        Carregando dados de consumo de IA...
      </div>
    )
  }

  if (balanceError) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-red-500">
        {balanceError}
      </div>
    )
  }

  const usagePct = balance?.usage_percentage ?? 0
  const alertVariant =
    usagePct >= 100 ? 'destructive' : usagePct >= 80 ? 'secondary' : 'outline'

  const chartData = byDay.map((d) => ({
    date: d.date.slice(5), // MM-DD
    tokens: Math.round(d.total_tokens / 1000), // em K
    custo: +(d.total_cost_cents / 100).toFixed(2),
  }))

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-gray-900">Consumo de IA</h1>
          <p className="text-xs text-gray-500">Monitoramento de tokens e custos do período mensal</p>
        </div>
        {balance && (
          <Badge variant={alertVariant} className="text-xs">
            {usagePct.toFixed(0)}% utilizado
          </Badge>
        )}
      </div>

      {balance && <UsageAlert percentage={usagePct} />}

      {/* Cards de métricas */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Card className="border border-gray-200 shadow-none">
          <CardHeader className="pb-1 pt-4">
            <CardTitle className="flex items-center gap-2 text-xs font-medium text-gray-500">
              <Zap className="h-3.5 w-3.5" />
              Tokens utilizados
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <p className="text-xl font-semibold text-gray-900">
              {balance ? formatTokens(balance.current_usage) : '—'}
            </p>
            <p className="mt-0.5 text-xs text-gray-400">
              de {balance ? formatTokens(balance.monthly_limit) : '—'} no mês
            </p>
          </CardContent>
        </Card>

        <Card className="border border-gray-200 shadow-none">
          <CardHeader className="pb-1 pt-4">
            <CardTitle className="flex items-center gap-2 text-xs font-medium text-gray-500">
              <TrendingUp className="h-3.5 w-3.5" />
              Tokens restantes
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <p className="text-xl font-semibold text-gray-900">
              {balance ? formatTokens(balance.remaining_tokens) : '—'}
            </p>
            <p className="mt-0.5 text-xs text-gray-400">
              até {balance?.period_end ?? '—'}
            </p>
          </CardContent>
        </Card>

        <Card className="border border-gray-200 shadow-none">
          <CardHeader className="pb-1 pt-4">
            <CardTitle className="flex items-center gap-2 text-xs font-medium text-gray-500">
              <DollarSign className="h-3.5 w-3.5" />
              Custo estimado
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <p className="text-xl font-semibold text-gray-900">
              {summary ? formatCost(summary.total_cost_cents) : '—'}
            </p>
            <p className="mt-0.5 text-xs text-gray-400">no período atual</p>
          </CardContent>
        </Card>

        <Card className="border border-gray-200 shadow-none">
          <CardHeader className="pb-1 pt-4">
            <CardTitle className="flex items-center gap-2 text-xs font-medium text-gray-500">
              <Zap className="h-3.5 w-3.5" />
              Operações
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <p className="text-xl font-semibold text-gray-900">
              {summary ? summary.total_operations.toLocaleString('pt-BR') : '—'}
            </p>
            <p className="mt-0.5 text-xs text-gray-400">chamadas de IA</p>
          </CardContent>
        </Card>
      </div>

      {/* Barra de progresso */}
      {balance && (
        <Card className="border border-gray-200 shadow-none">
          <CardHeader className="pb-2 pt-4">
            <CardTitle className="text-xs font-medium text-gray-500">
              Uso do limite mensal — {usagePct.toFixed(1)}%
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
              <div
                className={`h-full rounded-full transition-all ${
                  usagePct >= 100
                    ? 'bg-red-500'
                    : usagePct >= 80
                    ? 'bg-amber-400'
                    : 'bg-gray-900'
                }`}
                style={{ width: `${Math.min(usagePct, 100)}%` }}
              />
            </div>
            <div className="mt-1.5 flex justify-between text-xs text-gray-400">
              <span>0</span>
              <span>{formatTokens(balance.monthly_limit)}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Gráfico de consumo diário */}
      <Card className="border border-gray-200 shadow-none">
        <CardHeader className="pb-2 pt-4">
          <CardTitle className="text-xs font-medium text-gray-500">
            Consumo diário — últimos 30 dias (tokens em K)
          </CardTitle>
        </CardHeader>
        <CardContent className="pb-4">
          {historyLoading ? (
            <div className="flex h-48 items-center justify-center text-xs text-gray-400">
              Carregando histórico...
            </div>
          ) : chartData.length === 0 ? (
            <div className="flex h-48 items-center justify-center text-xs text-gray-400">
              Sem dados de consumo no período
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 10, fill: '#9ca3af' }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: '#9ca3af' }}
                  tickLine={false}
                  axisLine={false}
                  unit="K"
                />
                <Tooltip
                  contentStyle={{ fontSize: 11, borderRadius: 6, border: '1px solid var(--gray-200)' }}
                  formatter={(value: number, name: string) => [
                    name === 'tokens' ? `${value}K tokens` : `$${value}`,
                    name === 'tokens' ? 'Tokens' : 'Custo',
                  ]}
                />
                <Bar dataKey="tokens" fill="var(--gray-950)" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      {/* Breakdown por agente */}
      {byAgent.length > 0 && (
        <Card className="border border-gray-200 shadow-none">
          <CardHeader className="pb-2 pt-4">
            <CardTitle className="text-xs font-medium text-gray-500">
              Consumo por agente
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <div className="divide-y divide-gray-100">
              {byAgent
                .sort((a, b) => b.total_tokens - a.total_tokens)
                .map((agent) => (
                  <div
                    key={agent.agent_type}
                    className="flex items-center justify-between py-2.5 text-sm"
                  >
                    <span className="font-medium capitalize text-gray-700">
                      {agent.agent_type.replace('_', ' ')}
                    </span>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span>{formatTokens(agent.total_tokens)} tokens</span>
                      <span>{formatCost(agent.total_cost_cents)}</span>
                      <span>{agent.operation_count} ops</span>
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
