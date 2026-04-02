"use client"

import React, { useState, useEffect, useCallback } from "react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import {
  Shield,
  FileCheck,
  Lock,
  AlertTriangle,
  Award,
  Download,
  Calendar,
  ChevronRight,
  CheckCircle2,
  Clock,
  TrendingUp,
  Scale,
  XCircle,
  RefreshCw,
  Loader2
} from "lucide-react"
import { toast } from "sonner"
import { complianceService, ComplianceDashboard } from '@/services/admin/compliance-service'
import { biasAuditService, BiasAuditSummary, BiasAuditReport } from '@/services/admin/bias-service'
import { lgpdService, LGPDStats } from '@/services/admin/lgpd-service'

interface FrameworkDisplay {
  key: string
  name: string
  progress: number
  status: 'active' | 'implementing' | 'planned'
  controls: number
  implemented: number
}

interface Alert {
  id: string
  title: string
  description: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  type: 'compliance' | 'bias' | 'lgpd'
  timestamp: string
  status: 'pending' | 'resolved' | 'investigating'
}

const ADMIN_CLIENT_ID = 'demo_company'

const FRAMEWORK_NAME_MAP: Record<string, string> = {
  'ISO27001': 'ISO 27001:2022',
  'SOC2': 'SOC 2 Type II',
  'SOX': 'SOX',
  'BCB498': 'BCB 498/2025'
}

function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'critical':
      return 'text-status-error dark:text-status-error'
    case 'high':
      return 'text-wedo-orange dark:text-wedo-orange'
    case 'medium':
      return 'text-status-warning dark:text-status-warning'
    case 'low':
      return 'text-status-success dark:text-status-success'
    default:
      return 'text-lia-text-secondary'
  }
}

function getSeverityBadgeVariant(severity: string): "destructive" | "warning" | "success" | "default" {
  switch (severity) {
    case 'critical':
      return 'destructive'
    case 'high':
      return 'warning'
    case 'medium':
      return 'warning'
    case 'low':
      return 'success'
    default:
      return 'default'
  }
}

function getAlertIcon(alert: Alert) {
  if (alert.status === 'resolved') {
    return <CheckCircle2 className="w-5 h-5 text-status-success shrink-0" />
  }
  if (alert.severity === 'critical' || alert.severity === 'high') {
    return <XCircle className={`w-5 h-5 ${getSeverityColor(alert.severity)} shrink-0`} />
  }
  return <AlertTriangle className={`w-5 h-5 ${getSeverityColor(alert.severity)} shrink-0`} />
}

function formatTimeAgo(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) return 'Hoje'
  if (diffDays === 1) return 'Há 1 dia'
  if (diffDays < 7) return `Há ${diffDays} dias`
  if (diffDays < 30) return `Há ${Math.floor(diffDays / 7)} semanas`
  return `Há ${Math.floor(diffDays / 30)} meses`
}

async function fetchAlerts(): Promise<Alert[]> {
  try {
    const response = await fetch('/api/backend-proxy/alerts?limit=10')
    if (!response.ok) {
      throw new Error('Failed to fetch alerts')
    }
    const data = await response.json()
    return (data || []).map((item: Record<string, unknown>) => ({
      id: item.id || String(Math.random()),
      title: item.title || item.message || 'Alerta',
      description: item.description || item.details || '',
      severity: item.severity || 'medium',
      type: item.type || item.category || 'compliance',
      timestamp: item.created_at || item.timestamp || new Date().toISOString(),
      status: item.status || 'pending'
    }))
  } catch (error) {
    return []
  }
}

export default function ComplianceDashboardPage() {
  const [complianceDashboard, setComplianceDashboard] = useState<ComplianceDashboard | null>(null)
  const [biasSummary, setBiasSummary] = useState<BiasAuditSummary | null>(null)
  const [latestBiasAudit, setLatestBiasAudit] = useState<BiasAuditReport | null>(null)
  const [lgpdStats, setLgpdStats] = useState<LGPDStats | null>(null)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const fetchData = useCallback(async () => {
    setIsRefreshing(true)

    try {
      const [dashboardData, biasData, latestBias, lgpdData, alertsData] = await Promise.all([
        complianceService.getDashboard(ADMIN_CLIENT_ID).catch(() => null),
        biasAuditService.getSummary(ADMIN_CLIENT_ID).catch(() => null),
        biasAuditService.getLatest(ADMIN_CLIENT_ID).catch(() => null),
        lgpdService.getStats(ADMIN_CLIENT_ID).catch(() => null),
        fetchAlerts().catch(() => [])
      ])

      if (dashboardData) setComplianceDashboard(dashboardData)
      if (biasData) setBiasSummary(biasData)
      if (latestBias) setLatestBiasAudit(latestBias)
      if (lgpdData) setLgpdStats(lgpdData)
      setAlerts(alertsData)
    } catch (err) {
      toast.error('Erro ao carregar dados de compliance')
    } finally {
      setIsRefreshing(false)
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const totalControls = complianceDashboard?.totalControls || 0
  const implementedControls = complianceDashboard?.totalImplemented || 0
  const upcomingReviews = complianceDashboard?.upcomingReviews || 0
  const overdueReviews = complianceDashboard?.overdueReviews || 0

  const biasAlertCount = biasSummary 
    ? (biasSummary.byStatus.concern + biasSummary.byStatus.consider) 
    : 0

  const lgpdStatus = lgpdStats?.dpoActive 
    ? 'Conforme' 
    : lgpdStats?.dpoRegistered 
      ? 'Em revisão' 
      : 'Pendente'

  const lgpdBadgeVariant = lgpdStats?.dpoActive 
    ? 'success' 
    : lgpdStats?.dpoRegistered 
      ? 'warning' 
      : 'destructive'

  const displayFrameworks: FrameworkDisplay[] = complianceDashboard?.byFramework
    ? Object.entries(complianceDashboard.byFramework).map(([key, stats]) => ({
        key,
        name: FRAMEWORK_NAME_MAP[key] || key,
        progress: stats.compliancePercentage,
        status: stats.compliancePercentage > 30 ? 'active' : 'implementing' as const,
        controls: stats.totalControls,
        implemented: stats.implemented + stats.verified
      }))
    : []

  if (isLoading) {
    return (
      <div className="p-6" role="status" aria-live="polite" aria-label="Carregando...">
        <div className="max-w-7xl mx-auto flex items-center justify-center py-12" role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="w-8 h-8 animate-spin motion-reduce:animate-none text-lia-text-secondary dark:text-lia-text-tertiary" />
          <span className="ml-3 text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
            Carregando dados de compliance...
          </span>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30"
            >
              <Shield className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
            </div>
            <div>
              <h1 
                className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary"
                
              >
                Dashboard de Compliance Global
              </h1>
              <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                Visão consolidada de conformidade, riscos e controles
              </p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={fetchData} disabled={isRefreshing}>
            <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin motion-reduce:animate-none' : ''}`} />
            {isRefreshing ? 'Atualizando...' : 'Atualizar'}
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Total de Controles
                  </p>
                  <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary" >
                    {totalControls}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <TrendingUp className="w-3 h-3 text-status-success" />
                    <span className="text-xs text-status-success">{implementedControls} implementados</span>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30">
                  <FileCheck className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                </div>
              </div>
              <div className="mt-3">
                <Progress value={(implementedControls / totalControls) * 100} className="h-1.5" />
                <p className="text-xs mt-1 text-lia-text-tertiary dark:text-lia-text-secondary" >
                  {Math.round((implementedControls / totalControls) * 100)}% de cobertura
                </p>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                    LGPD Compliance
                  </p>
                  <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary" >
                    {lgpdStatus}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant={lgpdBadgeVariant as "default" | "secondary" | "destructive" | "outline"} className="text-micro">
                      {lgpdStats?.dpoActive ? 'DPO Ativo' : 'Verificar'}
                    </Badge>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-green-500/10">
                  <Lock className="w-5 h-5 text-status-success" />
                </div>
              </div>
              {lgpdStats && lgpdStats.openBreaches > 0 && (
                <div className="mt-3 p-2 rounded-md bg-status-error/10 dark:bg-status-error/20">
                  <p className="text-xs text-status-error dark:text-status-error">
                    {lgpdStats.openBreaches} incidente(s) em aberto
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Auditorias de Bias
                  </p>
                  <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary" >
                    {biasAlertCount} alertas
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge 
                      variant={biasAlertCount > 0 ? 'warning' : 'success'} 
                      className="text-micro"
                    >
                      {biasAlertCount > 0 ? 'Atenção' : 'OK'}
                    </Badge>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{backgroundColor: biasAlertCount > 0 ? 'var(--status-warning-bg-amber)' : 'var(--status-success-bg)'}}>
                  <Scale className={`w-5 h-5 ${biasAlertCount > 0 ? 'text-status-warning' : 'text-status-success'}`} />
                </div>
              </div>
              {latestBiasAudit && (
                <div className="mt-3">
                  <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Última auditoria: {new Date(latestBiasAudit.auditDate).toLocaleDateString('pt-BR')}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Próximas Revisões
                  </p>
                  <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary" >
                    {upcomingReviews}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Clock className="w-3 h-3 text-lia-text-tertiary dark:text-lia-text-secondary"  />
                    <span className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >Próximos 30 dias</span>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30">
                  <Calendar className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                </div>
              </div>
              {overdueReviews > 0 && (
                <div className="mt-3 p-2 rounded-md bg-status-error/10 dark:bg-status-error/20">
                  <p className="text-xs text-status-error dark:text-status-error">
                    {overdueReviews} revisões em atraso
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div>
          <h2 className="text-base font-semibold mb-4 text-lia-text-primary dark:text-lia-text-primary" >
            Conformidade por Framework
          </h2>
          {displayFrameworks.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {displayFrameworks.map((fw) => (
                <Card key={fw.key} >
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary" >
                        {fw.name}
                      </h3>
                      <Badge 
                        variant={fw.status === 'active' ? (fw.progress >= 70 ? 'success' : 'warning') : 'default'}
                        className={`text-micro ${fw.status === 'implementing' ? 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-tertiary dark:text-lia-text-secondary' : ''}`}
                      >
                        {fw.status === 'active' ? `${Math.round(fw.progress)}%` : 'Em impl.'}
                      </Badge>
                    </div>
                    <Progress 
                      value={fw.progress} 
                      className="h-2 mb-2" 
                    />
                    <div className="flex items-center justify-between">
                      <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >
                        {fw.controls > 0 ? `${fw.implemented}/${fw.controls} controles` : 'Configurando...'}
                      </p>
                      {fw.status === 'active' && (
                        <Link 
                          href={`/admin/compliance/controles/${fw.key.toLowerCase().replace(/\s+/g, '-')}`}
                          className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary hover:underline"
                        >
                          Ver detalhes
                        </Link>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card >
              <CardContent className="p-6 text-center">
                <FileCheck className="w-8 h-8 text-lia-text-tertiary mx-auto mb-2" />
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                  Nenhum framework configurado ainda
                </p>
                <p className="text-xs mt-1 text-lia-text-tertiary dark:text-lia-text-secondary" >
                  Configure seus frameworks de compliance para começar
                </p>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="flex flex-wrap gap-3">
          <Button asChild variant="outline">
            <Link href="/admin/compliance/trust-center">
              <Award className="w-4 h-4 mr-2" />
              Ver Trust Center
            </Link>
          </Button>
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Exportar Relatório
          </Button>
          <Button variant="outline">
            <Calendar className="w-4 h-4 mr-2" />
            Agendar Auditoria
          </Button>
        </div>

        <Card >
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary" >
                Alertas Recentes
              </CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/admin/compliance/monitoramento/alertas">
                  Ver todos
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {alerts.length > 0 ? (
              <div className="space-y-3">
                {alerts.slice(0, 5).map((alert) => (
                  <div 
                    key={alert.id}
                    className="flex items-center gap-3 p-3 rounded-md transition-colors motion-reduce:transition-none hover:opacity-90 bg-lia-bg-tertiary dark:bg-lia-bg-secondary"
                    
                  >
                    {getAlertIcon(alert)}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate text-lia-text-primary dark:text-lia-text-primary" >
                        {alert.title}
                      </p>
                      <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >
                        {formatTimeAgo(alert.timestamp)} • {alert.type === 'compliance' ? 'Compliance' : alert.type === 'bias' ? 'Bias' : 'LGPD'}
                      </p>
                    </div>
                    <Badge 
                      variant={
                        alert.status === 'resolved' 
                          ? 'success' 
                          : alert.status === 'investigating' 
                            ? 'warning' 
                            : getSeverityBadgeVariant(alert.severity)
                      }
                      className="text-micro shrink-0"
                    >
                      {alert.status === 'resolved' 
                        ? 'Resolvido' 
                        : alert.status === 'investigating' 
                          ? 'Investigando' 
                          : 'Pendente'
                      }
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6">
                <CheckCircle2 className="w-8 h-8 text-status-success mx-auto mb-2" />
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary"  aria-live="polite" aria-atomic="true">
                  Nenhum alerta encontrado
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
