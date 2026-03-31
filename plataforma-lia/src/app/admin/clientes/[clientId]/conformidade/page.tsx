// @ts-nocheck
"use client"

import React, { use } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"
import {
  Shield,
  Lock,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  TrendingUp,
  Calendar,
  AlertCircle,
  RefreshCw,
  ChevronRight,
  Loader2,
  FileText,
  Users,
  Activity
} from "lucide-react"
import { useLGPDCompliance } from '@/hooks/admin/useLGPDCompliance'
import { useComplianceControls } from '@/hooks/admin/useComplianceControls'
import { useBiasAudits } from '@/hooks/admin/useBiasAudits'

interface TabLink {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
}

const internalTabs: TabLink[] = [
  { name: 'Visão Geral', href: '', icon: Shield },
  { name: 'LGPD', href: '/lgpd', icon: Lock },
  { name: 'Controles', href: '/controles', icon: CheckCircle2 },
  { name: 'Incidentes', href: '/incidentes', icon: AlertTriangle },
]

function LoadingSpinner({ size = 'sm' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClass = size === 'lg' ? 'w-8 h-8' : size === 'md' ? 'w-6 h-6' : 'w-4 h-4'
  return <Loader2 className={`${sizeClass} animate-spin motion-reduce:animate-none lia-text-600`} />
}

export default function ConformidadePage({ params }: { params: Promise<{ clientId: string }> }) {
  const { clientId } = use(params)
  const pathname = usePathname()
  const basePath = `/admin/clientes/${clientId}/conformidade`
  
  const { dashboard, controls, isLoading: controlsLoading, error: controlsError, refetch: refetchControls } = useComplianceControls(clientId)
  const { stats: lgpdStats, breaches, isLoading: lgpdLoading, error: lgpdError } = useLGPDCompliance(clientId)
  const { summary: biasSummary, isLoading: biasLoading } = useBiasAudits(clientId)

  const isLoading = controlsLoading || lgpdLoading || biasLoading
  const error = controlsError || lgpdError

  const formatDate = (dateStr: string | undefined | null) => {
    if (!dateStr) return '-'
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
    } catch {
      return dateStr
    }
  }

  const isTabActive = (tabHref: string) => {
    const fullPath = basePath + tabHref
    if (tabHref === '') {
      return pathname === basePath
    }
    return pathname === fullPath
  }

  const overallCompliance = dashboard?.overallCompliance ?? 0
  const totalControls = dashboard?.totalControls ?? 0
  const implementedControls = dashboard?.totalImplemented ?? 0
  const pendingControls = dashboard?.totalNotStarted ?? 0
  const inProgressControls = dashboard?.totalInProgress ?? 0
  const upcomingReviews = dashboard?.upcomingReviews ?? 0
  const overdueReviews = dashboard?.overdueReviews ?? 0
  
  const openIncidents = breaches.filter(b => b.status !== 'closed').length
  const dsrPending = lgpdStats?.pendingDSRs ?? 0
  const consentRate = lgpdStats?.consentComplianceRate ?? 0

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-1 border-b pb-px -mb-px border-lia-border-subtle dark:border-lia-border-subtle">
          {internalTabs.map((tab) => {
            const Icon = tab.icon
            return (
              <Link
                key={tab.href}
                href={basePath + tab.href}
                className={cn(
                  "flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                  "border-transparent",
                  "lia-text-500 dark:text-lia-text-tertiary"
                )}
              >
                <Icon className="w-4 h-4" />
                {tab.name}
              </Link>
            )
          })}
        </div>
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="lg" />
          <span className="ml-3 text-sm lia-text-400 dark:lia-text-500">Carregando dados de conformidade...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-1 border-b pb-px -mb-px border-lia-border-subtle dark:border-lia-border-subtle">
          {internalTabs.map((tab) => {
            const Icon = tab.icon
            return (
              <Link
                key={tab.href}
                href={basePath + tab.href}
                className={cn(
                  "flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                  "border-transparent",
                  "lia-text-500 dark:text-lia-text-tertiary"
                )}
              >
                <Icon className="w-4 h-4" />
                {tab.name}
              </Link>
            )
          })}
        </div>
        <div className="p-6 text-center">
          <AlertCircle className="w-8 h-8 text-status-error mx-auto mb-2" />
          <p className="text-sm text-status-error">Erro ao carregar dados de conformidade</p>
          <Button variant="outline" size="sm" onClick={refetchControls} className="mt-3">
            <RefreshCw className="w-4 h-4 mr-2" />
            Tentar novamente
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-1 border-b pb-px -mb-px border-lia-border-subtle dark:border-lia-border-subtle">
        {internalTabs.map((tab) => {
          const isActive = isTabActive(tab.href)
          const Icon = tab.icon
          return (
            <Link
              key={tab.href}
              href={basePath + tab.href}
              className={cn(
                "flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                isActive
                  ? "border-gray-900 dark:lia-border-50 lia-text-900 dark:lia-text-50"
                  : "border-transparent hover:border-lia-border-default dark:hover:border-gray-600 lia-text-500 dark:text-lia-text-tertiary"
              )}
            >
              <Icon className="w-4 h-4" />
              {tab.name}
            </Link>
          )
        })}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm lia-text-400 dark:lia-text-500">Conformidade Geral</p>
                <p className="text-2xl font-semibold mt-1 lia-text-800 dark:text-lia-text-primary">{overallCompliance.toFixed(0)}%</p>
                <Progress value={overallCompliance} className="h-2 mt-2 w-24" />
              </div>
              <div className="w-10 h-10 rounded-md bg-status-success/10 dark:bg-status-success/20 flex items-center justify-center">
                <Shield className="w-5 h-5 text-status-success dark:text-status-success" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm lia-text-400 dark:lia-text-500">Controles Ativos</p>
                <p className="text-2xl font-semibold mt-1 lia-text-800 dark:text-lia-text-primary">{implementedControls}/{totalControls}</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-status-success" />
                  <span className="text-xs text-status-success">{pendingControls} pendentes</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-gray-50 dark:bg-lia-bg-secondary/50 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm lia-text-400 dark:lia-text-500">Taxa de Consentimento</p>
                <p className="text-2xl font-semibold mt-1 lia-text-800 dark:text-lia-text-primary">{consentRate.toFixed(0)}%</p>
                <div className="flex items-center gap-1 mt-1">
                  <Users className="w-3 h-3 lia-text-600 dark:text-lia-text-tertiary" />
                  <span className="text-xs lia-text-400 dark:lia-text-500">{dsrPending} DSRs pendentes</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-wedo-purple/10 dark:bg-wedo-purple/20 flex items-center justify-center">
                <Lock className="w-5 h-5 text-wedo-purple dark:text-wedo-purple" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm lia-text-400 dark:lia-text-500">Incidentes Abertos</p>
                <p className="text-2xl font-semibold mt-1 lia-text-800 dark:text-lia-text-primary">{openIncidents}</p>
                <div className="flex items-center gap-1 mt-1">
                  {openIncidents > 0 ? (
                    <>
                      <AlertTriangle className="w-3 h-3 text-status-warning" />
                      <span className="text-xs text-status-warning">Requer atenção</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-3 h-3 text-status-success" />
                      <span className="text-xs text-status-success">Tudo em ordem</span>
                    </>
                  )}
                </div>
              </div>
              <div className={cn(
                "w-10 h-10 rounded-md flex items-center justify-center",
                openIncidents > 0 ? "bg-status-warning/10 dark:bg-status-warning/20" : "bg-status-success/10 dark:bg-status-success/20"
              )}>
                <AlertTriangle className={cn(
                  "w-5 h-5",
                  openIncidents > 0 ? "text-status-warning dark:text-status-warning" : "text-status-success dark:text-status-success"
                )} />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium lia-text-800 dark:text-lia-text-primary">
                Frameworks de Conformidade
              </CardTitle>
              <Link href={`${basePath}/controles`}>
                <Button variant="ghost" size="sm">
                  Ver todos
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {dashboard?.byFramework && Object.keys(dashboard.byFramework).length > 0 ? (
              <div className="space-y-4">
                {Object.entries(dashboard.byFramework).slice(0, 4).map(([key, stats]) => {
                  const frameworkName = key === 'ISO27001' ? 'ISO 27001' : key === 'SOC2' ? 'SOC 2 Type II' : key
                  return (
                    <div key={key}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium lia-text-800 dark:text-lia-text-primary">{frameworkName}</span>
                        <Badge variant={stats.compliancePercentage >= 80 ? 'success' : stats.compliancePercentage >= 50 ? 'warning' : 'destructive'}>
                          {stats.compliancePercentage.toFixed(0)}%
                        </Badge>
                      </div>
                      <Progress value={stats.compliancePercentage} className="h-2" />
                      <div className="flex items-center gap-4 mt-1">
                        <span className="text-xs lia-text-400 dark:lia-text-500">
                          {stats.implemented + stats.verified} implementados
                        </span>
                        <span className="text-xs lia-text-400 dark:lia-text-500">
                          {stats.inProgress} em progresso
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="text-center py-6">
                <Shield className="w-8 h-8 lia-text-400 mx-auto mb-2" />
                <p className="text-sm lia-text-400 dark:lia-text-500">Nenhum framework configurado</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium lia-text-800 dark:text-lia-text-primary">
                LGPD - Resumo
              </CardTitle>
              <Link href={`${basePath}/lgpd`}>
                <Button variant="ghost" size="sm">
                  Ver detalhes
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {lgpdStats ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 rounded-md bg-status-success/10 dark:bg-status-success/20">
                    <p className="text-lg font-semibold text-status-success dark:text-status-success">{lgpdStats.totalConsents || 0}</p>
                    <p className="text-xs text-status-success dark:text-status-success">Consentimentos Ativos</p>
                  </div>
                  <div className="p-3 rounded-md bg-status-warning/10 dark:bg-status-warning/20">
                    <p className="text-lg font-semibold text-status-warning dark:text-status-warning">{lgpdStats.pendingDSRs || 0}</p>
                    <p className="text-xs text-status-warning dark:text-status-warning">DSRs Pendentes</p>
                  </div>
                </div>
                
                <div className="pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm lia-text-500 dark:text-lia-text-tertiary">Taxa de Retenção de Dados</span>
                    <span className="text-sm font-medium lia-text-800 dark:text-lia-text-primary">{lgpdStats.dataRetentionCompliance?.toFixed(0) || 0}%</span>
                  </div>
                  <Progress value={lgpdStats.dataRetentionCompliance || 0} className="h-2" />
                </div>

                {lgpdStats.lastAuditDate && (
                  <div className="flex items-center gap-2 text-xs lia-text-400 dark:lia-text-500">
                    <Calendar className="w-3 h-3" />
                    Última auditoria: {formatDate(lgpdStats.lastAuditDate)}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-6">
                <Lock className="w-8 h-8 lia-text-400 mx-auto mb-2" />
                <p className="text-sm lia-text-400 dark:lia-text-500">Dados LGPD não disponíveis</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {(upcomingReviews > 0 || overdueReviews > 0) && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium lia-text-800 dark:text-lia-text-primary">
              Revisões Agendadas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              {overdueReviews > 0 && (
                <div className="p-4 rounded-md bg-status-error/10 dark:bg-status-error/20 border border-status-error/30 dark:border-status-error/30 flex-1">
                  <div className="flex items-center gap-3">
                    <AlertCircle className="w-5 h-5 text-status-error" />
                    <div>
                      <p className="text-sm font-medium text-status-error dark:text-status-error">
                        {overdueReviews} revisões em atraso
                      </p>
                      <p className="text-xs text-status-error mt-1">Requer ação imediata</p>
                    </div>
                  </div>
                </div>
              )}
              {upcomingReviews > 0 && (
                <div className="p-4 rounded-md bg-gray-50 dark:bg-lia-bg-secondary/50 border border-lia-border-default dark:border-lia-border-default flex-1">
                  <div className="flex items-center gap-3">
                    <Calendar className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
                    <div>
                      <p className="text-sm font-medium lia-text-900 dark:lia-text-50">
                        {upcomingReviews} revisões agendadas
                      </p>
                      <p className="text-xs lia-text-600 dark:text-lia-text-tertiary mt-1">Próximos 30 dias</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {biasSummary && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium lia-text-800 dark:text-lia-text-primary">
              Auditoria de Bias - IA
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-md bg-gray-50 dark:bg-lia-bg-primary">
                <div className="flex items-center gap-3">
                  <Activity className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
                  <div>
                    <p className="text-sm font-medium lia-text-800 dark:text-lia-text-primary">{biasSummary.totalAudits || 0}</p>
                    <p className="text-xs lia-text-400 dark:lia-text-500">Auditorias Realizadas</p>
                  </div>
                </div>
              </div>
              <div className="p-4 rounded-md bg-gray-50 dark:bg-lia-bg-primary">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 text-status-success" />
                  <div>
                    <p className="text-sm font-medium lia-text-800 dark:text-lia-text-primary">{biasSummary.passedAudits || 0}</p>
                    <p className="text-xs lia-text-400 dark:lia-text-500">Aprovadas</p>
                  </div>
                </div>
              </div>
              <div className="p-4 rounded-md bg-gray-50 dark:bg-lia-bg-primary">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="w-5 h-5 text-status-warning" />
                  <div>
                    <p className="text-sm font-medium lia-text-800 dark:text-lia-text-primary">{biasSummary.concernAudits || 0}</p>
                    <p className="text-xs lia-text-400 dark:lia-text-500">Com Alertas</p>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
