"use client"

import React, { useState } from "react"
import {  DEMO_VALUES , formatBRL, formatBRLCompact } from "@/lib/pricing"
import {
  Users,
  Building,
  DollarSign,
  Activity,
  TrendingUp,
  TrendingDown,
  Zap,
  Database,
  Globe,
  CheckCircle,
  AlertCircle,
  Loader2,
  UserPlus,
  Clock,
  UserMinus,
  ExternalLink
} from "lucide-react"
import {
  MetricCard,
  ServiceConsumption,
  ActivityFeed,
  QuickActions,
  PeriodFilter,
  type ServiceItem,
  type Activity as ActivityType,
  type QuickAction,
  type PeriodFilterValue
} from "@/components/admin/dashboard"
import { Card } from "@/components/ui/card"
import { useDashboardSummary } from "@/hooks/admin/useDashboardSummary"
import Link from "next/link"

const quickActions: QuickAction[] = [
  {
    href: "/admin/clientes",
    icon: Building,
    iconColor: "var(--lia-text-secondary)",
    title: "Adicionar Cliente",
    subtitle: "Nova organização",
  },
  {
    href: "/admin/configuracoes",
    icon: Zap,
    iconColor: "var(--lia-text-secondary)",
    title: "Configurar Integração",
    subtitle: "Pearch, OpenMic, ATS",
  },
  {
    href: "/admin/metricas-plataforma",
    icon: TrendingUp,
    iconColor: "var(--status-success)",
    title: "Ver Métricas Detalhadas",
    subtitle: "Consumo, custos, analytics",
  },
]

function formatCurrency(value: number): string {
  return formatBRLCompact(value)
}

function formatDate(dateString?: string): string {
  if (!dateString) return "-"
  const date = new Date(dateString)
  return date.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" })
}

function getDaysRemainingColor(days?: number): string {
  if (days === undefined) return "text-lia-text-secondary"
  if (days <= 3) return "text-status-error"
  if (days <= 7) return "text-wedo-orange"
  return "text-status-success"
}

function getPlanBadgeColor(plan: string): string {
  const planLower = plan.toLowerCase()
  if (planLower.includes("enterprise")) return "bg-wedo-purple/15 text-wedo-purple"
  if (planLower.includes("professional") || planLower.includes("pro")) return "bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-primary"
  if (planLower.includes("starter") || planLower.includes("basic")) return "bg-lia-bg-tertiary text-lia-text-primary dark:text-lia-text-primary"
  return "bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-primary"
}

export default function AdminDashboard() {
  const [periodFilter, setPeriodFilter] = useState<PeriodFilterValue>(() => {
    const today = new Date()
    const startDate = new Date(today)
    startDate.setDate(startDate.getDate() - 29)
    startDate.setHours(0, 0, 0, 0)
    const endDate = new Date(today)
    endDate.setHours(23, 59, 59, 999)
    return { startDate, endDate, periodLabel: "30 dias" }
  })

  const { data: dashboardData, isLoading, error, refetch } = useDashboardSummary(
    periodFilter.startDate,
    periodFilter.endDate
  )

  const kpis = dashboardData?.kpis
  const newClients = dashboardData?.newClients || []
  const trialClients = dashboardData?.trialClients || []
  const churnedClients = dashboardData?.churnedClients || []

  const metricsCards = [
    {
      title: "MRR",
      value: isLoading ? <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none" /> : formatCurrency(kpis?.mrr || 0),
      icon: DollarSign,
      subtitle: `ARR: ${formatCurrency(kpis?.arr || 0)}`,
      trend: kpis?.mrr ? "+12.5% vs mês anterior" : undefined,
      trendDirection: "up" as const,
    },
    {
      title: "Clientes Ativos",
      value: isLoading ? <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none" /> : (kpis?.activeClients ?? 0).toString(),
      icon: Building,
      subtitle: `${kpis?.totalClients || 0} total`,
      trend: kpis?.newClientsPeriod ? `+${kpis.newClientsPeriod} novos no período` : undefined,
      trendDirection: "up" as const,
    },
    {
      title: "Em Trial",
      value: isLoading ? <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none" /> : (kpis?.trialClients ?? 0).toString(),
      icon: Clock,
      subtitle: "Aguardando conversão",
    },
    {
      title: "Churn Rate",
      value: isLoading ? <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none" /> : `${(kpis?.churnRate ?? 0).toFixed(1)}%`,
      icon: TrendingDown,
      subtitle: `${kpis?.churnedClients || 0} cliente(s) churned`,
      trend: (kpis?.churnRate ?? 0) > 5 ? "Atenção: acima da meta" : "Dentro da meta",
      trendDirection: (kpis?.churnRate ?? 0) > 5 ? "down" as const : "up" as const,
    },
  ]

  const serviceItems: ServiceItem[] = [
    {
      icon: Zap,
      iconColor: "var(--lia-text-secondary)",
      title: "Consumo de IA (Claude + Gemini)",
      subtitle: "1.2M tokens este mês",
      value: DEMO_VALUES.AI_CONSUMPTION_MONTHLY,
      trend: "+8% vs média",
      trendDirection: "up",
    },
    {
      icon: Globe,
      iconColor: "var(--wedo-blue)",
      title: "Buscas Globais (Base Global)",
      subtitle: "3.500 buscas (850 créditos)",
      value: DEMO_VALUES.GLOBAL_SEARCH_MONTHLY,
      trend: "-5% vs média",
      trendDirection: "down",
    },
    {
      icon: Database,
      iconColor: "var(--wedo-purple)",
      title: "Armazenamento PostgreSQL",
      subtitle: "4.2 GB / 10 GB",
      badge: "42% usado",
    },
  ]

  const recentActivities: ActivityType[] = [
    {
      type: "success",
      title: "Novo cliente cadastrado",
      subtitle: newClients[0]?.name || "TechCorp Brasil",
      timestamp: "há 2 horas",
    },
    {
      type: "upgrade",
      title: "Upgrade de plano",
      subtitle: "Inovação RH → Professional",
      timestamp: "há 5 horas",
    },
    {
      type: "warning",
      title: "Trial expirando",
      subtitle: trialClients[0]?.name || "Empresa Alpha",
      timestamp: "há 1 dia",
    },
  ]

  return (
    <div className="p-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1
            className="text-3xl font-semibold mb-2 text-lia-text-primary dark:text-lia-text-primary"
            
          >
            Dashboard Administrativo
          </h1>
          <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary" >
            Visão geral da plataforma WedoTalent • {isLoading ? 'Carregando...' : 'Atualizado em tempo real'}
          </p>
        </div>
        <PeriodFilter
          value={periodFilter}
          onChange={setPeriodFilter}
        />
      </div>

      {error && (
        <div className="mb-6 p-4 bg-status-error/10 border border-status-error/30 rounded-md flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-status-error" />
          <span className="text-status-error">{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {metricsCards.map((metric, index) => (
          <MetricCard key={`metric-${index}`} {...metric} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Card className="p-6 bg-lia-bg-primary dark:bg-lia-bg-primary" >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <UserPlus className="w-5 h-5 text-green-600" />
              <h3 className="font-semibold text-lia-text-primary dark:text-lia-text-primary">Novos Clientes</h3>
            </div>
            <span className="text-sm px-2 py-0.5 rounded-full bg-status-success/15 text-status-success">
              {newClients.length} no período
            </span>
          </div>
          
          {isLoading ? (
            <div className="flex items-center justify-center py-8" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none text-lia-text-tertiary" />
            </div>
          ) : newClients.length === 0 ? (
            <p className="text-sm text-lia-text-secondary text-center py-8">
              Nenhum novo cliente no período
            </p>
          ) : (
            <div className="space-y-3">
              {newClients.slice(0, 5).map((client) => (
                <Link 
                  key={client.id}
                  href={`/admin/clientes/${client.id}`}
                  className="flex items-center justify-between p-3 rounded-md border border-lia-border-subtle hover:border-lia-border-default dark:border-lia-border-default hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 transition-colors motion-reduce:transition-none group"
                >
                  <div>
                    <p className="font-medium text-lia-text-primary dark:text-lia-text-primary group-hover:text-lia-text-primary dark:group-hover:text-lia-text-primary transition-colors motion-reduce:transition-none">
                      {client.name}
                    </p>
                    <p className="text-xs text-lia-text-secondary">
                      Criado em {formatDate(client.createdAt)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${getPlanBadgeColor(client.plan)}`}>
                      {client.plan}
                    </span>
                    <ExternalLink className="w-4 h-4 text-lia-text-tertiary group-hover:text-lia-text-primary dark:group-hover:text-lia-text-primary transition-colors motion-reduce:transition-none" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </Card>

        <Card className="p-6 bg-lia-bg-primary dark:bg-lia-bg-primary" >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-status-warning" />
              <h3 className="font-semibold text-lia-text-primary dark:text-lia-text-primary">Clientes em Trial</h3>
            </div>
            <span className="text-sm px-2 py-0.5 rounded-full bg-wedo-orange/15 text-wedo-orange">
              {trialClients.length} ativos
            </span>
          </div>
          
          {isLoading ? (
            <div className="flex items-center justify-center py-8" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none text-lia-text-tertiary" />
            </div>
          ) : trialClients.length === 0 ? (
            <p className="text-sm text-lia-text-secondary text-center py-8">
              Nenhum cliente em trial
            </p>
          ) : (
            <div className="space-y-3">
              {trialClients.slice(0, 5).map((client) => (
                <Link 
                  key={client.id}
                  href={`/admin/clientes/${client.id}`}
                  className="flex items-center justify-between p-3 rounded-md border border-lia-border-subtle hover:border-lia-border-default dark:border-lia-border-default hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 transition-colors motion-reduce:transition-none group"
                >
                  <div>
                    <p className="font-medium text-lia-text-primary dark:text-lia-text-primary group-hover:text-lia-text-primary dark:group-hover:text-lia-text-primary transition-colors motion-reduce:transition-none">
                      {client.name}
                    </p>
                    <p className="text-xs text-lia-text-secondary">
                      Expira em {formatDate(client.trialEndDate)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-semibold ${getDaysRemainingColor(client.daysRemaining)}`}>
                      {client.daysRemaining} dias
                    </span>
                    <ExternalLink className="w-4 h-4 text-lia-text-tertiary group-hover:text-lia-text-primary dark:group-hover:text-lia-text-primary transition-colors motion-reduce:transition-none" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </Card>

        <Card className="p-6 bg-lia-bg-primary dark:bg-lia-bg-primary" >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <UserMinus className="w-5 h-5 text-red-600" />
              <h3 className="font-semibold text-lia-text-primary dark:text-lia-text-primary">Churned</h3>
            </div>
            <span className="text-sm px-2 py-0.5 rounded-full bg-status-error/15 text-status-error">
              {churnedClients.length} no período
            </span>
          </div>
          
          {isLoading ? (
            <div className="flex items-center justify-center py-8" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none text-lia-text-tertiary" />
            </div>
          ) : churnedClients.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <CheckCircle className="w-8 h-8 text-status-success mb-2" />
              <p className="text-sm text-lia-text-secondary">
                Nenhum churn no período
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {churnedClients.slice(0, 5).map((client) => (
                <div 
                  key={client.id}
                  className="p-3 rounded-md border border-lia-border-subtle bg-status-error/10/30"
                >
                  <div className="flex items-center justify-between mb-1">
                    <p className="font-medium text-lia-text-primary dark:text-lia-text-primary">
                      {client.name}
                    </p>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${getPlanBadgeColor(client.plan)}`}>
                      {client.plan}
                    </span>
                  </div>
                  <p className="text-xs text-lia-text-secondary">
                    Churned em {formatDate(client.churnedAt)}
                  </p>
                  {client.reason && (
                    <p className="text-xs text-status-error mt-1">
                      Motivo: {client.reason}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <ServiceConsumption
          title="Consumo de Serviços"
          items={serviceItems}
        />
        <ActivityFeed
          title="Atividades Recentes"
          activities={recentActivities}
        />
      </div>

      <QuickActions
        title="Ações Rápidas"
        actions={quickActions}
        columns={3}
      />
    </div>
  )
}
