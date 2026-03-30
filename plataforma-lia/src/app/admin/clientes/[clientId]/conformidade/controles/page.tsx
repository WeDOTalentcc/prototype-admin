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
  Calendar,
  AlertCircle,
  RefreshCw,
  Loader2,
  Filter
} from "lucide-react"
import { useComplianceControls } from '@/hooks/admin/useComplianceControls'

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

const statusColors: Record<string, string> = {
  implemented: 'bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success',
  partial: 'bg-status-warning/15 text-status-warning dark:bg-status-warning/30 dark:text-status-warning',
  not_implemented: 'bg-status-error/15 text-status-error dark:bg-status-error/30 dark:text-status-error',
  in_progress: 'bg-status-warning/15 text-status-warning dark:bg-status-warning/30 dark:text-status-warning',
  not_started: 'bg-gray-100 lia-text-800 dark:bg-lia-bg-primary/30 dark:text-lia-text-primary',
  verified: 'bg-gray-100 lia-text-900 dark:bg-lia-bg-secondary dark:lia-text-50',
  not_applicable: 'bg-gray-100 lia-text-500 dark:bg-lia-bg-primary/30 dark:lia-text-500',
}

const statusLabels: Record<string, string> = {
  implemented: 'Implementado',
  partial: 'Parcial',
  not_implemented: 'Não Implementado',
  in_progress: 'Em Progresso',
  not_started: 'Não Iniciado',
  verified: 'Verificado',
  not_applicable: 'N/A',
}

function LoadingSpinner({ size = 'sm' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClass = size === 'lg' ? 'w-8 h-8' : size === 'md' ? 'w-6 h-6' : 'w-4 h-4'
  return <Loader2 className={`${sizeClass} animate-spin lia-text-600`} />
}

export default function ControlesPage({ params }: { params: Promise<{ clientId: string }> }) {
  const { clientId } = use(params)
  const pathname = usePathname()
  const basePath = `/admin/clientes/${clientId}/conformidade`
  
  const { dashboard, controls, soxControls, isLoading, error, refetch } = useComplianceControls(clientId)

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

  const displayControls = controls.map((c) => ({
    id: c.id,
    code: c.control?.controlId || '-',
    name: c.control?.controlName || '-',
    framework: c.control?.framework || '-',
    status: c.status === 'implemented' || c.status === 'verified' ? 'implemented' : c.status === 'in_progress' ? 'partial' : 'not_implemented',
    lastChecked: c.lastReviewedAt || c.updatedAt || '',
    owner: c.ownerName,
  }))

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
                  "border-transparent"
                )}
                className="lia-text-500 dark:text-lia-text-tertiary"
              >
                <Icon className="w-4 h-4" />
                {tab.name}
              </Link>
            )
          })}
        </div>
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="lg" />
          <span className="ml-3 text-sm lia-text-400 dark:lia-text-500">Carregando controles...</span>
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
                  "border-transparent"
                )}
                className="lia-text-500 dark:text-lia-text-tertiary"
              >
                <Icon className="w-4 h-4" />
                {tab.name}
              </Link>
            )
          })}
        </div>
        <div className="p-6 text-center">
          <AlertCircle className="w-8 h-8 text-status-error mx-auto mb-2" />
          <p className="text-sm text-status-error">Erro ao carregar controles</p>
          <Button variant="outline" size="sm" onClick={refetch} className="mt-3">
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

      {dashboard?.byFramework && Object.keys(dashboard.byFramework).length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(dashboard.byFramework).map(([key, stats]) => {
            const frameworkName = key === 'ISO27001' ? 'ISO 27001' : key === 'SOC2' ? 'SOC 2 Type II' : key
            return (
              <Card key={key}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="font-semibold text-base lia-text-800 dark:text-lia-text-primary">
                        {frameworkName}
                      </h3>
                      <p className="text-xs mt-1 lia-text-400 dark:lia-text-500">
                        {stats.totalControls} controles totais
                      </p>
                    </div>
                    <Badge variant={stats.compliancePercentage >= 80 ? 'success' : stats.compliancePercentage >= 50 ? 'warning' : 'destructive'}>
                      {stats.compliancePercentage.toFixed(0)}%
                    </Badge>
                  </div>
                  
                  <Progress value={stats.compliancePercentage} className="h-2 mb-4" />
                  
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="p-2 rounded-md bg-status-success/10 dark:bg-status-success/20">
                      <p className="text-lg font-semibold text-status-success dark:text-status-success">{stats.implemented + stats.verified}</p>
                      <p className="text-micro text-status-success dark:text-status-success">Implementado</p>
                    </div>
                    <div className="p-2 rounded-md bg-status-warning/10 dark:bg-status-warning/20">
                      <p className="text-lg font-semibold text-status-warning dark:text-status-warning">{stats.inProgress}</p>
                      <p className="text-micro text-status-warning dark:text-status-warning">Parcial</p>
                    </div>
                    <div className="p-2 rounded-md bg-status-error/10 dark:bg-status-error/20">
                      <p className="text-lg font-semibold text-status-error dark:text-status-error">{stats.notStarted}</p>
                      <p className="text-micro text-status-error dark:text-status-error">Pendente</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium lia-text-800 dark:text-lia-text-primary">
              Controles de Compliance
            </CardTitle>
            <Button variant="outline" size="sm">
              <Filter className="w-4 h-4 mr-2" />
              Filtrar
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {displayControls.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-lia-border-subtle dark:border-lia-border-subtle">
                    <th className="text-left py-3 px-2 text-xs font-medium lia-text-400 dark:lia-text-500">Código</th>
                    <th className="text-left py-3 px-2 text-xs font-medium lia-text-400 dark:lia-text-500">Controle</th>
                    <th className="text-left py-3 px-2 text-xs font-medium lia-text-400 dark:lia-text-500">Framework</th>
                    <th className="text-left py-3 px-2 text-xs font-medium lia-text-400 dark:lia-text-500">Status</th>
                    <th className="text-left py-3 px-2 text-xs font-medium lia-text-400 dark:lia-text-500">Última Verificação</th>
                    <th className="text-left py-3 px-2 text-xs font-medium lia-text-400 dark:lia-text-500">Responsável</th>
                  </tr>
                </thead>
                <tbody>
                  {displayControls.map((control) => (
                    <tr key={control.id} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800/50 border-lia-border-subtle dark:border-lia-border-subtle">
                      <td className="py-3 px-2 text-sm font-mono lia-text-800 dark:text-lia-text-primary">{control.code}</td>
                      <td className="py-3 px-2 text-sm lia-text-800 dark:text-lia-text-primary">{control.name}</td>
                      <td className="py-3 px-2">
                        <Badge variant="outline" className="text-xs">{control.framework}</Badge>
                      </td>
                      <td className="py-3 px-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${statusColors[control.status] || statusColors.not_implemented}`}>
                          {control.status === 'implemented' && <CheckCircle2 className="w-3 h-3 mr-1" />}
                          {control.status === 'partial' && <AlertTriangle className="w-3 h-3 mr-1" />}
                          {control.status === 'not_implemented' && <XCircle className="w-3 h-3 mr-1" />}
                          {statusLabels[control.status] || control.status}
                        </span>
                      </td>
                      <td className="py-3 px-2 text-sm lia-text-400 dark:lia-text-500">{formatDate(control.lastChecked)}</td>
                      <td className="py-3 px-2 text-sm lia-text-500 dark:text-lia-text-tertiary">{control.owner || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-6">
              <Shield className="w-8 h-8 lia-text-400 mx-auto mb-2" />
              <p className="text-sm lia-text-400 dark:lia-text-500">Nenhum controle encontrado</p>
            </div>
          )}
        </CardContent>
      </Card>

      {soxControls.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium lia-text-800 dark:text-lia-text-primary">
              Controles SOX
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-lia-border-subtle dark:border-lia-border-subtle">
                    <th className="text-left py-3 px-2 text-xs font-medium lia-text-400 dark:lia-text-500">Código</th>
                    <th className="text-left py-3 px-2 text-xs font-medium lia-text-400 dark:lia-text-500">Descrição</th>
                    <th className="text-left py-3 px-2 text-xs font-medium lia-text-400 dark:lia-text-500">Seção</th>
                    <th className="text-left py-3 px-2 text-xs font-medium lia-text-400 dark:lia-text-500">Resultado</th>
                    <th className="text-left py-3 px-2 text-xs font-medium lia-text-400 dark:lia-text-500">Último Teste</th>
                  </tr>
                </thead>
                <tbody>
                  {soxControls.slice(0, 10).map((sox) => (
                    <tr key={sox.id} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800/50 border-lia-border-subtle dark:border-lia-border-subtle">
                      <td className="py-3 px-2 text-sm font-mono lia-text-800 dark:text-lia-text-primary">{sox.controlId}</td>
                      <td className="py-3 px-2 text-sm lia-text-800 dark:text-lia-text-primary">{sox.description}</td>
                      <td className="py-3 px-2">
                        <Badge variant="outline" className="text-xs">{sox.section}</Badge>
                      </td>
                      <td className="py-3 px-2">
                        <Badge variant={sox.testResult === 'pass' ? 'success' : sox.testResult === 'fail' ? 'destructive' : 'warning'}>
                          {sox.testResult === 'pass' ? 'Aprovado' : sox.testResult === 'fail' ? 'Reprovado' : 'Pendente'}
                        </Badge>
                      </td>
                      <td className="py-3 px-2 text-sm lia-text-400 dark:lia-text-500">{formatDate(sox.lastTestedAt)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {dashboard && dashboard.upcomingReviews > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium lia-text-800 dark:text-lia-text-primary">
              Próximas Revisões Agendadas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="p-4 rounded-md bg-gray-50 dark:bg-lia-bg-secondary/50 border border-lia-border-default dark:border-lia-border-default">
              <div className="flex items-center gap-3">
                <Calendar className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
                <div>
                  <p className="text-sm font-medium lia-text-900 dark:lia-text-50">
                    {dashboard.upcomingReviews} revisões agendadas
                  </p>
                  {dashboard.overdueReviews > 0 && (
                    <p className="text-xs text-status-error mt-1">
                      {dashboard.overdueReviews} revisões em atraso
                    </p>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
