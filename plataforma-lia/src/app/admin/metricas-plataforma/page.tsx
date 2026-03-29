"use client"

import React, { useState, useEffect } from "react"
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Users,
  Building,
  Zap,
  Server,
  Activity,
  RefreshCw,
  AlertCircle,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { usePlatformMetrics } from "@/hooks/admin/usePlatformMetrics"

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

function formatNumber(value: number): string {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`
  }
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}k`
  }
  return value.toString()
}

interface MetricCardProps {
  title: string
  value: React.ReactNode
  icon: React.ElementType
  trend?: number
  trendLabel?: string
  subtitle?: string
  accentColor?: string
}

const accentBgMap: Record<string, string> = {
  'var(--gray-400)': 'var(--gray-bg-10)',
  'var(--status-success)': 'var(--status-success-bg)',
  'var(--status-error)': 'var(--status-error-bg)',
  'var(--wedo-orange)': 'var(--wedo-orange-bg-15)',
  'var(--wedo-purple)': 'var(--wedo-purple-bg-10)',
  'var(--wedo-cyan)': 'var(--wedo-cyan-bg-10)',
}

function MetricCard({
  title,
  value,
  icon: Icon,
  trend,
  trendLabel,
  subtitle,
  accentColor,
}: MetricCardProps) {
  const isPositiveTrend = trend !== undefined && trend >= 0
  const bgColor = accentColor ? (accentBgMap[accentColor] || 'var(--gray-bg-10)') : 'var(--gray-bg-10)'

  return (
    <Card className="relative overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle
          className="text-sm font-medium text-gray-500 dark:text-gray-400"
          
        >
          {title}
        </CardTitle>
        <div
          className="p-2 rounded-md"
          style={{backgroundColor: bgColor}}
        >
          <Icon
            className="w-4 h-4"
            style={{color: accentColor || "var(--gray-400)"}}
          />
        </div>
      </CardHeader>
      <CardContent>
        <div
          className="text-2xl font-bold text-gray-800 dark:text-gray-100"
          
        >
          {value}
        </div>
        {(trend !== undefined || subtitle) && (
          <div className="flex items-center gap-2 mt-1">
            {trend !== undefined && (
              <span
                className={`flex items-center text-xs font-medium ${
                  isPositiveTrend ? "text-status-success" : "text-status-error"
                }`}
              >
                {isPositiveTrend ? (
                  <TrendingUp className="w-3 h-3 mr-1" />
                ) : (
                  <TrendingDown className="w-3 h-3 mr-1" />
                )}
                {isPositiveTrend ? "+" : ""}
                {trend.toFixed(1)}%
              </span>
            )}
            {trendLabel && (
              <span
                className="text-xs text-gray-400 dark:text-gray-500"
                
              >
                {trendLabel}
              </span>
            )}
            {subtitle && !trend && (
              <span
                className="text-xs text-gray-400 dark:text-gray-500"
                
              >
                {subtitle}
              </span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader className="pb-2">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded-md w-24" />
            </CardHeader>
            <CardContent>
              <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded-md w-32 mb-2" />
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-md w-20" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Array.from({ length: 2 }).map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader>
              <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded-md w-40" />
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Array.from({ length: 3 }).map((_, j) => (
                  <div key={j} className="h-12 bg-gray-200 dark:bg-gray-700 rounded-md" />
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

export default function MetricasPlataformaPage() {
  const [mounted, setMounted] = useState(false)
  const { metrics, isLoading, error, refetch } = usePlatformMetrics()

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
        <LoadingSkeleton />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-semibold text-gray-950 dark:text-gray-50">
              Métricas da Plataforma
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Visão consolidada de todos os clientes • Atualizado em tempo real
            </p>
          </div>
          <div className="flex items-center gap-3">
            {metrics?.lastUpdated && (
              <span className="text-xs text-gray-500">
                Última atualização:{" "}
                {new Date(metrics.lastUpdated).toLocaleString("pt-BR")}
              </span>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isLoading}
            >
              <RefreshCw
                className={`w-4 h-4 mr-2 ${isLoading ? "animate-spin" : ""}`}
              />
              Atualizar
            </Button>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-status-error/10 dark:bg-status-error/20 border border-status-error/30 dark:border-status-error/30 rounded-md flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-status-error" />
            <span className="text-sm text-status-error dark:text-status-error">{error}</span>
          </div>
        )}

        {isLoading ? (
          <LoadingSkeleton />
        ) : metrics ? (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-medium text-gray-950 dark:text-gray-50 mb-4 flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                Métricas de Receita
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard
                  title="MRR (Receita Recorrente Mensal)"
                  value={formatCurrency(metrics.revenue.mrr)}
                  icon={DollarSign}
                  trend={metrics.revenue.growthRate}
                  trendLabel="vs mês anterior"
                  accentColor="var(--gray-400)"
                />
                <MetricCard
                  title="ARR (Receita Recorrente Anual)"
                  value={formatCurrency(metrics.revenue.arr)}
                  icon={TrendingUp}
                  subtitle="MRR × 12"
                  accentColor="var(--gray-400)"
                />
                <MetricCard
                  title="Crescimento MRR"
                  value={`+${formatCurrency(metrics.revenue.mrrChange)}`}
                  icon={TrendingUp}
                  trend={metrics.revenue.growthRate}
                  trendLabel="taxa de crescimento"
                  accentColor="var(--status-success)"
                />
                <MetricCard
                  title="Taxa de Crescimento"
                  value={`${metrics.revenue.growthRate.toFixed(1)}%`}
                  icon={Activity}
                  subtitle="mês sobre mês"
                  accentColor="var(--status-success)"
                />
              </div>
            </div>

            <div>
              <h2 className="text-lg font-medium text-gray-950 dark:text-gray-50 mb-4 flex items-center gap-2">
                <Building className="w-5 h-5 text-wedo-orange" />
                Métricas de Clientes
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard
                  title="Clientes Ativos"
                  value={metrics.clients.activeClients}
                  icon={Building}
                  subtitle="pagantes atualmente"
                  accentColor="var(--wedo-orange)"
                />
                <MetricCard
                  title="Clientes em Trial"
                  value={metrics.clients.trialClients}
                  icon={Users}
                  subtitle="período de avaliação"
                  accentColor="var(--wedo-purple)"
                />
                <MetricCard
                  title="Clientes Churned"
                  value={metrics.clients.churnedClients}
                  icon={TrendingDown}
                  subtitle="últimos 30 dias"
                  accentColor="var(--status-error)"
                />
                <MetricCard
                  title="Taxa de Churn"
                  value={`${metrics.clients.churnRate.toFixed(1)}%`}
                  icon={Activity}
                  trend={-metrics.clients.churnRate}
                  trendLabel="mensal"
                  accentColor="var(--status-error)"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base font-medium">
                    <Zap className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                    Métricas de Uso
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                    <div>
                      <p className="text-sm font-medium text-gray-950 dark:text-gray-50">
                        Consumo Total de IA
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Claude + Gemini (tokens)
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-gray-900 dark:text-gray-50">
                        {formatNumber(metrics.usage.totalAITokens)}
                      </p>
                      <Badge variant="info">este mês</Badge>
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                    <div>
                      <p className="text-sm font-medium text-gray-950 dark:text-gray-50">
                        Usuários Totais
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Todos os clientes
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-gray-900 dark:text-gray-50">
                        {metrics.usage.totalUsers}
                      </p>
                      <Badge variant="success">
                        ~{(metrics.usage.totalUsers / metrics.clients.activeClients).toFixed(1)} por cliente
                      </Badge>
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                    <div>
                      <p className="text-sm font-medium text-gray-950 dark:text-gray-50">
                        Sessões Ativas Hoje
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Usuários conectados
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-gray-900 dark:text-gray-50">
                        {metrics.usage.activeSessionsToday}
                      </p>
                      <Badge variant="success">online</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base font-medium">
                    <Server className="w-5 h-5 text-wedo-orange" />
                    Métricas de Custo
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                    <div>
                      <p className="text-sm font-medium text-gray-950 dark:text-gray-50">
                        Custo de Infraestrutura
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Servidores, banco de dados
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-wedo-orange">
                        {formatCurrency(metrics.costs.infrastructureCost)}
                      </p>
                      <Badge variant="default">mensal</Badge>
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                    <div>
                      <p className="text-sm font-medium text-gray-950 dark:text-gray-50">
                        Custo de APIs de IA
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Claude, Gemini, OpenAI
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-wedo-orange">
                        {formatCurrency(metrics.costs.aiApiCost)}
                      </p>
                      <Badge variant="warning">
                        {((metrics.costs.aiApiCost / metrics.costs.totalMonthlyCost) * 100).toFixed(0)}% do total
                      </Badge>
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-300 dark:border-gray-600">
                    <div>
                      <p className="text-sm font-medium text-gray-950 dark:text-gray-50">
                        Custo Total Mensal
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Infra + IA
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-gray-900 dark:text-gray-50">
                        {formatCurrency(metrics.costs.totalMonthlyCost)}
                      </p>
                      <Badge variant="info">
                        {formatCurrency(metrics.costs.costPerClient)}/cliente
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base font-medium">
                  <Activity className="w-5 h-5 text-status-success" />
                  Resumo Financeiro
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 bg-status-success/10 dark:bg-status-success/20 rounded-md text-center">
                    <p className="text-sm font-medium text-status-success dark:text-status-success mb-1">
                      Margem Bruta
                    </p>
                    <p className="text-2xl font-bold text-status-success">
                      {(((metrics.revenue.mrr - metrics.costs.totalMonthlyCost) / metrics.revenue.mrr) * 100).toFixed(1)}%
                    </p>
                    <p className="text-xs text-status-success/70 mt-1">
                      {formatCurrency(metrics.revenue.mrr - metrics.costs.totalMonthlyCost)} lucro bruto
                    </p>
                  </div>
                  <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-md text-center">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-50 mb-1">
                      ARPU (Receita por Cliente)
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-gray-50">
                      {formatCurrency(metrics.revenue.mrr / metrics.clients.activeClients)}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                      média mensal por cliente
                    </p>
                  </div>
                  <div className="p-4 bg-wedo-purple/10 dark:bg-wedo-purple/20 rounded-md text-center">
                    <p className="text-sm font-medium text-wedo-purple dark:text-wedo-purple mb-1">
                      LTV Estimado (24 meses)
                    </p>
                    <p className="text-2xl font-bold text-wedo-purple">
                      {formatCurrency((metrics.revenue.mrr / metrics.clients.activeClients) * 24)}
                    </p>
                    <p className="text-xs text-wedo-purple/70 mt-1">
                      valor vitalício do cliente
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : null}
      </div>
    </div>
  )
}
