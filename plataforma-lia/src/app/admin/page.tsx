"use client"

import React, { useState } from "react"
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
    iconColor: "var(--gray-600)",
    title: "Adicionar Cliente",
    subtitle: "Nova organização",
  },
  {
    href: "/admin/configuracoes",
    icon: Zap,
    iconColor: "var(--gray-600)",
    title: "Configurar Integração",
    subtitle: "Pearch, OpenMic, ATS",
  },
  {
    href: "/admin/metricas-plataforma",
    icon: TrendingUp,
    iconColor: "#16a34a",
    title: "Ver Métricas Detalhadas",
    subtitle: "Consumo, custos, analytics",
  },
]

function formatCurrency(value: number): string {
  if (value >= 1000000) {
    return `R$ ${(value / 1000000).toFixed(2)}M`
  }
  if (value >= 1000) {
    return `R$ ${(value / 1000).toFixed(1)}k`
  }
  return `R$ ${value.toFixed(2)}`
}

function formatDate(dateString?: string): string {
  if (!dateString) return "-"
  const date = new Date(dateString)
  return date.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" })
}

function getDaysRemainingColor(days?: number): string {
  if (days === undefined) return "text-gray-500"
  if (days <= 3) return "text-status-error"
  if (days <= 7) return "text-wedo-orange"
  return "text-status-success"
}

function getPlanBadgeColor(plan: string): string {
  const planLower = plan.toLowerCase()
  if (planLower.includes("enterprise")) return "bg-wedo-purple/15 text-wedo-purple"
  if (planLower.includes("professional") || planLower.includes("pro")) return "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-50"
  if (planLower.includes("starter") || planLower.includes("basic")) return "bg-gray-100 text-gray-800 dark:text-gray-200"
  return "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-50"
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
      value: isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : formatCurrency(kpis?.mrr || 0),
      icon: DollarSign,
      subtitle: `ARR: ${formatCurrency(kpis?.arr || 0)}`,
      trend: kpis?.mrr ? "+12.5% vs mês anterior" : undefined,
      trendDirection: "up" as const,
    },
    {
      title: "Clientes Ativos",
      value: isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : (kpis?.activeClients ?? 0).toString(),
      icon: Building,
      subtitle: `${kpis?.totalClients || 0} total`,
      trend: kpis?.newClientsPeriod ? `+${kpis.newClientsPeriod} novos no período` : undefined,
      trendDirection: "up" as const,
    },
    {
      title: "Em Trial",
      value: isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : (kpis?.trialClients ?? 0).toString(),
      icon: Clock,
      subtitle: "Aguardando conversão",
    },
    {
      title: "Churn Rate",
      value: isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : `${(kpis?.churnRate ?? 0).toFixed(1)}%`,
      icon: TrendingDown,
      subtitle: `${kpis?.churnedClients || 0} cliente(s) churned`,
      trend: (kpis?.churnRate ?? 0) > 5 ? "Atenção: acima da meta" : "Dentro da meta",
      trendDirection: (kpis?.churnRate ?? 0) > 5 ? "down" as const : "up" as const,
    },
  ]

  const serviceItems: ServiceItem[] = [
    {
      icon: Zap,
      iconColor: "var(--gray-600)",
      title: "Consumo de IA (Claude + Gemini)",
      subtitle: "1.2M tokens este mês",
      value: "R$ 850",
      trend: "+8% vs média",
      trendDirection: "up",
    },
    {
      icon: Globe,
      iconColor: "#2563eb",
      title: "Buscas Globais (Base Global)",
      subtitle: "3.500 buscas (850 créditos)",
      value: "R$ 420",
      trend: "-5% vs média",
      trendDirection: "down",
    },
    {
      icon: Database,
      iconColor: "#9333ea",
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
            className="text-3xl font-semibold mb-2 text-gray-800 dark:text-gray-100"
            
          >
            Dashboard Administrativo
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400" >
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
          <MetricCard key={index} {...metric} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Card className="p-6 bg-white dark:bg-gray-950" >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <UserPlus className="w-5 h-5 text-green-600" />
              <h3 className="font-semibold text-gray-950 dark:text-gray-50">Novos Clientes</h3>
            </div>
            <span className="text-sm px-2 py-0.5 rounded-full bg-status-success/15 text-status-success">
              {newClients.length} no período
            </span>
          </div>
          
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : newClients.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-8">
              Nenhum novo cliente no período
            </p>
          ) : (
            <div className="space-y-3">
              {newClients.slice(0, 5).map((client) => (
                <Link 
                  key={client.id}
                  href={`/admin/clientes/${client.id}`}
                  className="flex items-center justify-between p-3 rounded-md border border-gray-100 hover:border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:bg-gray-800/50 transition-colors group"
                >
                  <div>
                    <p className="font-medium text-gray-950 dark:text-gray-50 group-hover:text-gray-900 dark:group-hover:text-gray-50 transition-colors">
                      {client.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      Criado em {formatDate(client.createdAt)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${getPlanBadgeColor(client.plan)}`}>
                      {client.plan}
                    </span>
                    <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-gray-900 dark:group-hover:text-gray-50 transition-colors" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </Card>

        <Card className="p-6 bg-white dark:bg-gray-950" >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5" style={{color: "var(--status-warning)"}} />
              <h3 className="font-semibold text-gray-950 dark:text-gray-50">Clientes em Trial</h3>
            </div>
            <span className="text-sm px-2 py-0.5 rounded-full bg-wedo-orange/15 text-wedo-orange">
              {trialClients.length} ativos
            </span>
          </div>
          
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : trialClients.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-8">
              Nenhum cliente em trial
            </p>
          ) : (
            <div className="space-y-3">
              {trialClients.slice(0, 5).map((client) => (
                <Link 
                  key={client.id}
                  href={`/admin/clientes/${client.id}`}
                  className="flex items-center justify-between p-3 rounded-md border border-gray-100 hover:border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:bg-gray-800/50 transition-colors group"
                >
                  <div>
                    <p className="font-medium text-gray-950 dark:text-gray-50 group-hover:text-gray-900 dark:group-hover:text-gray-50 transition-colors">
                      {client.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      Expira em {formatDate(client.trialEndDate)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-semibold ${getDaysRemainingColor(client.daysRemaining)}`}>
                      {client.daysRemaining} dias
                    </span>
                    <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-gray-900 dark:group-hover:text-gray-50 transition-colors" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </Card>

        <Card className="p-6 bg-white dark:bg-gray-950" >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <UserMinus className="w-5 h-5 text-red-600" />
              <h3 className="font-semibold text-gray-950 dark:text-gray-50">Churned</h3>
            </div>
            <span className="text-sm px-2 py-0.5 rounded-full bg-status-error/15 text-status-error">
              {churnedClients.length} no período
            </span>
          </div>
          
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : churnedClients.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <CheckCircle className="w-8 h-8 text-status-success mb-2" />
              <p className="text-sm text-gray-500">
                Nenhum churn no período
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {churnedClients.slice(0, 5).map((client) => (
                <div 
                  key={client.id}
                  className="p-3 rounded-md border border-gray-100 bg-status-error/10/30"
                >
                  <div className="flex items-center justify-between mb-1">
                    <p className="font-medium text-gray-950 dark:text-gray-50">
                      {client.name}
                    </p>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${getPlanBadgeColor(client.plan)}`}>
                      {client.plan}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500">
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
