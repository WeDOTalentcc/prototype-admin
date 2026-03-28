"use client"

import React, { use } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Skeleton } from "@/components/ui/skeleton"
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Users,
  Briefcase,
  Clock,
  Target,
  Download,
  Calendar,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  Zap,
  PieChart,
  Receipt,
  RefreshCw,
  AlertCircle
} from "lucide-react"
import { useClientSaasMetrics } from "@/hooks/admin/useClientSaasMetrics"

const FALLBACK_SAAS_METRICS = {
  revenue: {
    mrr: 4500,
    mrrChange: 500,
    mrrTrend: 'up' as const,
    arr: 54000,
    ltv: 162000,
    ltvMonths: 36,
    planName: 'Professional',
    contractStart: '2024-03-15',
    contractEnd: '2025-03-14',
    billingCycle: 'monthly' as const
  },
  acquisition: {
    cac: 2800,
    paybackMonths: 0.62,
    referralSource: 'Indicação',
    salesCycle: 45
  },
  usage: {
    aiCreditsUsed: 8500,
    aiCreditsLimit: 15000,
    usersActive: 12,
    usersLimit: 20,
    jobsActive: 8,
    jobsLimit: 25,
    storageUsedMB: 2340,
    storageLimitMB: 5000
  },
  health: {
    churnRisk: 'low' as const,
    healthScore: 92,
    lastLoginDays: 1,
    npsScore: 9,
    supportTickets: 2,
    engagementLevel: 'high' as const
  },
  payments: [
    { id: '1', date: '2024-12-01', amount: 4500, status: 'paid' as const, method: 'Cartão' },
    { id: '2', date: '2024-11-01', amount: 4500, status: 'paid' as const, method: 'Cartão' },
    { id: '3', date: '2024-10-01', amount: 4000, status: 'paid' as const, method: 'Boleto' },
    { id: '4', date: '2024-09-01', amount: 4000, status: 'paid' as const, method: 'Boleto' },
    { id: '5', date: '2024-08-01', amount: 4000, status: 'paid' as const, method: 'Pix' }
  ]
}

const metrics = {
  overview: {
    activeVacancies: 8,
    candidatesInPipeline: 342,
    averageTimeToHire: 28,
    conversionRate: 12.5,
    screeningsCompleted: 156,
    interviewsScheduled: 45
  },
  trends: {
    vacancies: { value: 8, change: 2, trend: 'up' },
    candidates: { value: 342, change: 45, trend: 'up' },
    timeToHire: { value: 28, change: -3, trend: 'down' },
    conversion: { value: 12.5, change: 1.2, trend: 'up' }
  },
  funnel: [
    { stage: 'Candidatura', count: 342, percentage: 100 },
    { stage: 'Triagem', count: 156, percentage: 45.6 },
    { stage: 'Entrevista', count: 89, percentage: 26 },
    { stage: 'Avaliação Técnica', count: 45, percentage: 13.2 },
    { stage: 'Proposta', count: 23, percentage: 6.7 },
    { stage: 'Contratado', count: 12, percentage: 3.5 }
  ]
}

function MetricsLoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className="border-l-4 border-l-gray-200">
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="space-y-2 flex-1">
                  <Skeleton className="h-3 w-24" />
                  <Skeleton className="h-8 w-28" />
                  <Skeleton className="h-3 w-16" />
                </div>
                <Skeleton className="w-10 h-10 rounded-md" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader>
            <Skeleton className="h-5 w-32" />
          </CardHeader>
          <CardContent className="space-y-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i}>
                <div className="flex justify-between mb-1">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-24" />
                </div>
                <Skeleton className="h-2 w-full" />
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <Skeleton className="h-5 w-28" />
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-center">
              <Skeleton className="h-10 w-16 mx-auto" />
              <Skeleton className="h-3 w-20 mx-auto mt-2" />
            </div>
            <div className="space-y-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="flex justify-between">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-4 w-16" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default function ClientMetricasPage({
  params
}: {
  params: Promise<{ clientId: string }>
}) {
  const { clientId } = use(params)
  const { metrics: saasMetricsData, isLoading, error, refetch } = useClientSaasMetrics(clientId)

  const saasMetrics = saasMetricsData || FALLBACK_SAAS_METRICS

  const TrendIndicator = ({ change, trend }: { change: number, trend: string }) => {
    const isPositive = trend === 'up'
    return (
      <div className={`flex items-center gap-1 text-xs ${isPositive ? 'text-emerald-600' : 'text-red-600'}`}>
        {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
        <span>{Math.abs(change)}{typeof change === 'number' && change < 1 ? '%' : ''}</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <BarChart3 className="w-6 h-6 text-gray-600 dark:text-gray-400" />
            <h2 
              className="text-lg font-semibold"
              style={{ color: 'var(--eleven-text-primary)' }}
            >
              Métricas
            </h2>
          </div>
          <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
            Indicadores de performance e analytics
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Calendar className="w-4 h-4 mr-2" />
            Últimos 30 dias
          </Button>
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => refetch()}
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Exportar
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <span className="text-sm text-red-700 dark:text-red-300">{error}</span>
        </div>
      )}

      <Tabs defaultValue="financeiro" className="w-full">
        <TabsList className="grid w-full grid-cols-2 max-w-md">
          <TabsTrigger value="financeiro" className="flex items-center gap-2">
            <DollarSign className="w-4 h-4" />
            Financeiro
          </TabsTrigger>
          <TabsTrigger value="recrutamento" className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            Recrutamento
          </TabsTrigger>
        </TabsList>

        <TabsContent value="financeiro" className="space-y-6 mt-6">
          {isLoading ? (
            <MetricsLoadingSkeleton />
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card className="border-l-4 border-l-emerald-500">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                          MRR (Receita Mensal)
                        </p>
                        <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                          R$ {saasMetrics.revenue.mrr.toLocaleString('pt-BR')}
                        </p>
                        <div className="flex items-center gap-1 text-xs text-emerald-600">
                          <TrendingUp className="w-3 h-3" />
                          <span>+R$ {saasMetrics.revenue.mrrChange}</span>
                        </div>
                      </div>
                      <div className="w-10 h-10 rounded-md bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
                        <DollarSign className="w-5 h-5 text-emerald-600" />
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-l-4 border-l-gray-400 dark:border-l-gray-500">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                          ARR (Receita Anual)
                        </p>
                        <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                          R$ {saasMetrics.revenue.arr.toLocaleString('pt-BR')}
                        </p>
                        <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                          Plano: {saasMetrics.revenue.planName}
                        </p>
                      </div>
                      <div className="w-10 h-10 rounded-md bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                        <PieChart className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-l-4 border-l-purple-500">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                          LTV Estimado
                        </p>
                        <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                          R$ {saasMetrics.revenue.ltv.toLocaleString('pt-BR')}
                        </p>
                        <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                          {saasMetrics.revenue.ltvMonths} meses projetados
                        </p>
                      </div>
                      <div className="w-10 h-10 rounded-md bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                        <TrendingUp className="w-5 h-5 text-purple-600" />
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-l-4 border-l-amber-500">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                          CAC (Custo Aquisição)
                        </p>
                        <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                          R$ {saasMetrics.acquisition.cac.toLocaleString('pt-BR')}
                        </p>
                        <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                          Payback: {saasMetrics.acquisition.paybackMonths} meses
                        </p>
                      </div>
                      <div className="w-10 h-10 rounded-md bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                        <Target className="w-5 h-5 text-amber-600" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <Card className="lg:col-span-2">
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2" style={{ color: 'var(--eleven-text-primary)' }}>
                      <Zap className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      Uso vs Contrato
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span style={{ color: 'var(--eleven-text-secondary)' }}>Créditos IA</span>
                        <span style={{ color: 'var(--eleven-text-primary)' }}>
                          {saasMetrics.usage.aiCreditsUsed.toLocaleString()} / {saasMetrics.usage.aiCreditsLimit.toLocaleString()}
                        </span>
                      </div>
                      <Progress value={(saasMetrics.usage.aiCreditsUsed / saasMetrics.usage.aiCreditsLimit) * 100} className="h-2" />
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span style={{ color: 'var(--eleven-text-secondary)' }}>Usuários Ativos</span>
                        <span style={{ color: 'var(--eleven-text-primary)' }}>
                          {saasMetrics.usage.usersActive} / {saasMetrics.usage.usersLimit}
                        </span>
                      </div>
                      <Progress value={(saasMetrics.usage.usersActive / saasMetrics.usage.usersLimit) * 100} className="h-2" />
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span style={{ color: 'var(--eleven-text-secondary)' }}>Vagas Ativas</span>
                        <span style={{ color: 'var(--eleven-text-primary)' }}>
                          {saasMetrics.usage.jobsActive} / {saasMetrics.usage.jobsLimit}
                        </span>
                      </div>
                      <Progress value={(saasMetrics.usage.jobsActive / saasMetrics.usage.jobsLimit) * 100} className="h-2" />
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span style={{ color: 'var(--eleven-text-secondary)' }}>Storage</span>
                        <span style={{ color: 'var(--eleven-text-primary)' }}>
                          {(saasMetrics.usage.storageUsedMB / 1024).toFixed(1)} GB / {(saasMetrics.usage.storageLimitMB / 1024).toFixed(1)} GB
                        </span>
                      </div>
                      <Progress value={(saasMetrics.usage.storageUsedMB / saasMetrics.usage.storageLimitMB) * 100} className="h-2" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2" style={{ color: 'var(--eleven-text-primary)' }}>
                      {saasMetrics.health.churnRisk === 'low' ? (
                        <CheckCircle className="w-4 h-4 text-emerald-500" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-amber-500" />
                      )}
                      Saúde do Cliente
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="text-center">
                      <p className="text-4xl font-bold text-gray-900 dark:text-gray-50">{saasMetrics.health.healthScore}</p>
                      <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Health Score</p>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span style={{ color: 'var(--eleven-text-tertiary)' }}>Risco de Churn</span>
                        <Badge className={
                          saasMetrics.health.churnRisk === 'low' ? 'bg-emerald-100 text-emerald-700' :
                          saasMetrics.health.churnRisk === 'medium' ? 'bg-amber-100 text-amber-700' :
                          'bg-red-100 text-red-700'
                        }>
                          {saasMetrics.health.churnRisk === 'low' ? 'Baixo' : 
                           saasMetrics.health.churnRisk === 'medium' ? 'Médio' : 'Alto'}
                        </Badge>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span style={{ color: 'var(--eleven-text-tertiary)' }}>Último Login</span>
                        <span style={{ color: 'var(--eleven-text-primary)' }}>
                          {saasMetrics.health.lastLoginDays === 0 ? 'Hoje' : 
                           saasMetrics.health.lastLoginDays === 1 ? 'Ontem' : 
                           `${saasMetrics.health.lastLoginDays} dias`}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span style={{ color: 'var(--eleven-text-tertiary)' }}>NPS Score</span>
                        <span style={{ color: 'var(--eleven-text-primary)' }}>{saasMetrics.health.npsScore}/10</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span style={{ color: 'var(--eleven-text-tertiary)' }}>Tickets Suporte</span>
                        <span style={{ color: 'var(--eleven-text-primary)' }}>{saasMetrics.health.supportTickets} abertos</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2" style={{ color: 'var(--eleven-text-primary)' }}>
                    <Receipt className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                    Histórico de Pagamentos
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-2 text-xs font-medium" style={{ color: 'var(--eleven-text-tertiary)' }}>Data</th>
                          <th className="text-left py-2 text-xs font-medium" style={{ color: 'var(--eleven-text-tertiary)' }}>Valor</th>
                          <th className="text-left py-2 text-xs font-medium" style={{ color: 'var(--eleven-text-tertiary)' }}>Método</th>
                          <th className="text-left py-2 text-xs font-medium" style={{ color: 'var(--eleven-text-tertiary)' }}>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {saasMetrics.payments.map((payment) => (
                          <tr key={payment.id} className="border-b border-gray-100 dark:border-gray-800">
                            <td className="py-3 text-sm" style={{ color: 'var(--eleven-text-primary)' }}>
                              {new Date(payment.date).toLocaleDateString('pt-BR')}
                            </td>
                            <td className="py-3 text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                              R$ {payment.amount.toLocaleString('pt-BR')}
                            </td>
                            <td className="py-3 text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
                              {payment.method}
                            </td>
                            <td className="py-3">
                              <Badge className={
                                payment.status === 'paid' ? 'bg-emerald-100 text-emerald-700' :
                                payment.status === 'pending' ? 'bg-amber-100 text-amber-700' :
                                payment.status === 'overdue' ? 'bg-red-100 text-red-700' :
                                'bg-gray-100 text-gray-800 dark:text-gray-200'
                              }>
                                {payment.status === 'paid' ? 'Pago' :
                                 payment.status === 'pending' ? 'Pendente' :
                                 payment.status === 'overdue' ? 'Atrasado' : 'Falhou'}
                              </Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Contrato Início</p>
                    <p className="text-lg font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                      {new Date(saasMetrics.revenue.contractStart).toLocaleDateString('pt-BR')}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Contrato Fim</p>
                    <p className="text-lg font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                      {new Date(saasMetrics.revenue.contractEnd).toLocaleDateString('pt-BR')}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Origem</p>
                    <p className="text-lg font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                      {saasMetrics.acquisition.referralSource}
                    </p>
                  </CardContent>
                </Card>
              </div>
            </>
          )}
        </TabsContent>

        <TabsContent value="recrutamento" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                      Vagas Ativas
                    </p>
                    <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                      {metrics.trends.vacancies.value}
                    </p>
                    <TrendIndicator change={metrics.trends.vacancies.change} trend={metrics.trends.vacancies.trend} />
                  </div>
                  <div className="w-10 h-10 rounded-md bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                    <Briefcase className="w-5 h-5 text-purple-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                      Candidatos no Pipeline
                    </p>
                    <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                      {metrics.trends.candidates.value}
                    </p>
                    <TrendIndicator change={metrics.trends.candidates.change} trend={metrics.trends.candidates.trend} />
                  </div>
                  <div className="w-10 h-10 rounded-md bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                    <Users className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                      Tempo Médio de Contratação
                    </p>
                    <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                      {metrics.trends.timeToHire.value}
                      <span className="text-sm font-normal ml-1">dias</span>
                    </p>
                    <TrendIndicator change={metrics.trends.timeToHire.change} trend={metrics.trends.timeToHire.trend} />
                  </div>
                  <div className="w-10 h-10 rounded-md bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                    <Clock className="w-5 h-5 text-amber-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                      Taxa de Conversão
                    </p>
                    <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                      {metrics.trends.conversion.value}%
                    </p>
                    <TrendIndicator change={metrics.trends.conversion.change} trend={metrics.trends.conversion.trend} />
                  </div>
                  <div className="w-10 h-10 rounded-md bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
                    <Target className="w-5 h-5 text-emerald-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base" style={{ color: 'var(--eleven-text-primary)' }}>
                Funil de Recrutamento
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {metrics.funnel.map((stage) => (
                  <div key={stage.stage} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span 
                          className="text-sm font-medium"
                          style={{ color: 'var(--eleven-text-primary)' }}
                        >
                          {stage.stage}
                        </span>
                        <Badge variant="outline" className="text-xs">
                          {stage.count}
                        </Badge>
                      </div>
                      <span 
                        className="text-sm"
                        style={{ color: 'var(--eleven-text-tertiary)' }}
                      >
                        {stage.percentage}%
                      </span>
                    </div>
                    <Progress value={stage.percentage} className="h-2" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base" style={{ color: 'var(--eleven-text-primary)' }}>
                  Triagens Completadas
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <p className="text-4xl font-semibold text-gray-900 dark:text-gray-50">
                    {metrics.overview.screeningsCompleted}
                  </p>
                  <p className="text-sm mt-2" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    nos últimos 30 dias
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base" style={{ color: 'var(--eleven-text-primary)' }}>
                  Entrevistas Agendadas
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <p className="text-4xl font-semibold text-purple-600">
                    {metrics.overview.interviewsScheduled}
                  </p>
                  <p className="text-sm mt-2" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    nos últimos 30 dias
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
