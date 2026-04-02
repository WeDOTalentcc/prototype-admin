"use client"

import React, { useState, useEffect } from "react"
import {
  DollarSign,
  TrendingUp,
  Users,
  UserMinus,
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
import { MetricCard } from "@/components/admin/dashboard/MetricCard"

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

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className="animate-pulse motion-reduce:animate-none">
            <CardHeader className="pb-2">
              <div className="h-4 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-md w-24" />
            </CardHeader>
            <CardContent>
              <div className="h-8 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-md w-32 mb-2" />
              <div className="h-3 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-md w-20" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Array.from({ length: 2 }).map((_, i) => (
          <Card key={i} className="animate-pulse motion-reduce:animate-none">
            <CardHeader>
              <div className="h-5 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-md w-40" />
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Array.from({ length: 3 }).map((_, j) => (
                  <div key={j} className="h-12 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-md" />
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
      <div className="min-h-screen bg-lia-bg-primary dark:bg-lia-bg-primary p-8">
        <LoadingSkeleton />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-lia-bg-primary dark:bg-lia-bg-primary">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary">
              Métricas da Plataforma
            </h1>
            <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary mt-1">
              Visão consolidada de todos os clientes • Atualizado em tempo real
            </p>
          </div>
          <div className="flex items-center gap-3">
            {metrics?.lastUpdated && (
              <span className="text-xs text-lia-text-secondary">
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
                className={`w-4 h-4 mr-2 ${isLoading ? "animate-spin motion-reduce:animate-none" : ""}`}
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
              <h2 className="text-lg font-medium text-lia-text-primary dark:text-lia-text-primary mb-4 flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                Métricas de Receita
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard
                  title="MRR (Receita Recorrente Mensal)"
                  value={formatCurrency(metrics.revenue.mrr)}
                  icon={DollarSign}
                  trend={metrics.revenue.growthRate}
                  trendLabel="vs mês anterior"
                  accentColor="var(--lia-text-tertiary)"
                />
                <MetricCard
                  title="ARR (Receita Recorrente Anual)"
                  value={formatCurrency(metrics.revenue.arr)}
                  icon={DollarSign}
                  subtitle="MRR × 12"
                  accentColor="var(--lia-text-tertiary)"
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
              <h2 className="text-lg font-medium text-lia-text-primary dark:text-lia-text-primary mb-4 flex items-center gap-2">
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
                  icon={UserMinus}
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
                    <Zap className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                    Métricas de Uso
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
                    <div>
                      <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                        Consumo Total de IA
                      </p>
                      <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                        Claude + Gemini (tokens)
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-lia-text-primary dark:text-lia-text-primary">
                        {formatNumber(metrics.usage.totalAITokens)}
                      </p>
                      <Badge variant="info">este mês</Badge>
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
                    <div>
                      <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                        Usuários Totais
                      </p>
                      <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                        Todos os clientes
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-lia-text-primary dark:text-lia-text-primary">
                        {metrics.usage.totalUsers}
                      </p>
                      <Badge variant="success">
                        ~{(metrics.usage.totalUsers / metrics.clients.activeClients).toFixed(1)} por cliente
                      </Badge>
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
                    <div>
                      <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                        Sessões Ativas Hoje
                      </p>
                      <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                        Usuários conectados
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-lia-text-primary dark:text-lia-text-primary">
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
                  <div className="flex items-center justify-between p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
                    <div>
                      <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                        Custo de Infraestrutura
                      </p>
                      <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
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

                  <div className="flex items-center justify-between p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
                    <div>
                      <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                        Custo de APIs de IA
                      </p>
                      <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
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

                  <div className="flex items-center justify-between p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md border border-lia-border-default dark:border-lia-border-default">
                    <div>
                      <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                        Custo Total Mensal
                      </p>
                      <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                        Infra + IA
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-lia-text-primary dark:text-lia-text-primary">
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
                  <div className="p-4 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-md text-center">
                    <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-1">
                      ARPU (Receita por Cliente)
                    </p>
                    <p className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">
                      {formatCurrency(metrics.revenue.mrr / metrics.clients.activeClients)}
                    </p>
                    <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary mt-1">
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
