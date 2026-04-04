"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import {
  Shield,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Calendar,
  AlertCircle,
  RefreshCw,
  Filter,
} from "lucide-react"
import { useComplianceControls } from '@/hooks/admin/useComplianceControls'
import { LoadingSpinner, statusColors, statusLabels, ComplianceFramework, ComplianceControl } from './observabilidade-shared'

export function ComplianceTab({ clientId }: { clientId: string }) {
  const { dashboard, controls, isLoading, error, refetch } = useComplianceControls(clientId)

  const formatDate = (dateStr: string | undefined | null) => {
    if (!dateStr) return '-'
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
    } catch {
      return dateStr
    }
  }

  const frameworks: ComplianceFramework[] = dashboard?.byFramework
    ? Object.entries(dashboard.byFramework).map(([key, stats], index) => ({
        id: String(index + 1),
        name: key === 'ISO27001' ? 'ISO 27001' : key === 'SOC2' ? 'SOC 2 Type II' : key,
        shortName: key,
        progress: stats.compliancePercentage,
        controlsImplemented: stats.implemented + stats.verified,
        controlsPartial: stats.inProgress,
        controlsNotImplemented: stats.notStarted,
        totalControls: stats.totalControls,
        nextReview: undefined }))
    : []

  const displayControls: ComplianceControl[] = controls.map((c) => ({
    id: c.id,
    code: c.control?.controlId || '-',
    name: c.control?.controlName || '-',
    framework: c.control?.framework || '-',
    status: c.status === 'implemented' || c.status === 'verified' ? 'implemented' : c.status === 'in_progress' ? 'partial' : 'not_implemented',
    lastChecked: c.lastReviewedAt || c.updatedAt || '',
    owner: c.ownerName }))

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Carregando dados de compliance...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 text-center">
        <AlertCircle className="w-8 h-8 text-status-error mx-auto mb-2" />
        <p className="text-sm text-status-error">Erro ao carregar dados de compliance</p>
        <Button variant="outline" size="sm" onClick={refetch} className="mt-3">
          <RefreshCw className="w-4 h-4 mr-2" />
          Tentar novamente
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {frameworks.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {frameworks.map((framework) => (
            <Card key={framework.id}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="font-semibold text-base text-lia-text-primary dark:text-lia-text-primary">
                      {framework.name}
                    </h3>
                    <p className="text-xs mt-1 text-lia-text-tertiary dark:text-lia-text-secondary">
                      {framework.totalControls} controles totais
                    </p>
                  </div>
                  <Badge variant={framework.progress >= 80 ? 'success' : framework.progress >= 50 ? 'warning' : 'destructive'}>
                    {framework.progress.toFixed(0)}%
                  </Badge>
                </div>
                
                <Progress value={framework.progress} className="h-2 mb-4" />
                
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="p-2 rounded-md bg-status-success/10 dark:bg-status-success/20">
                    <p className="text-lg font-semibold text-status-success dark:text-status-success">{framework.controlsImplemented}</p>
                    <p className="text-micro text-status-success dark:text-status-success">Implementado</p>
                  </div>
                  <div className="p-2 rounded-md bg-status-warning/10 dark:bg-status-warning/20">
                    <p className="text-lg font-semibold text-status-warning dark:text-status-warning">{framework.controlsPartial}</p>
                    <p className="text-micro text-status-warning dark:text-status-warning">Parcial</p>
                  </div>
                  <div className="p-2 rounded-md bg-status-error/10 dark:bg-status-error/20">
                    <p className="text-lg font-semibold text-status-error dark:text-status-error">{framework.controlsNotImplemented}</p>
                    <p className="text-micro text-status-error dark:text-status-error">Pendente</p>
                  </div>
                </div>

                {framework.nextReview && (
                  <div className="mt-4 pt-4 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-tertiary dark:text-lia-text-secondary">Próxima revisão</span>
                      <span className="font-medium text-lia-text-primary dark:text-lia-text-primary">
                        {formatDate(framework.nextReview)}
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="p-6 text-center">
            <Shield className="w-8 h-8 text-lia-text-tertiary mx-auto mb-2" />
            <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Nenhum framework de compliance configurado</p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
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
                    <th className="text-left py-3 px-2 text-xs font-medium text-lia-text-tertiary dark:text-lia-text-secondary">Código</th>
                    <th className="text-left py-3 px-2 text-xs font-medium text-lia-text-tertiary dark:text-lia-text-secondary">Controle</th>
                    <th className="text-left py-3 px-2 text-xs font-medium text-lia-text-tertiary dark:text-lia-text-secondary">Framework</th>
                    <th className="text-left py-3 px-2 text-xs font-medium text-lia-text-tertiary dark:text-lia-text-secondary">Status</th>
                    <th className="text-left py-3 px-2 text-xs font-medium text-lia-text-tertiary dark:text-lia-text-secondary">Última Verificação</th>
                    <th className="text-left py-3 px-2 text-xs font-medium text-lia-text-tertiary dark:text-lia-text-secondary">Responsável</th>
                  </tr>
                </thead>
                <tbody>
                  {displayControls.map((control) => (
                    <tr key={control.id} className="border-b hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover/50 border-lia-border-subtle dark:border-lia-border-subtle">
                      <td className="py-3 px-2 text-sm font-mono text-lia-text-primary dark:text-lia-text-primary">{control.code}</td>
                      <td className="py-3 px-2 text-sm text-lia-text-primary dark:text-lia-text-primary">{control.name}</td>
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
                      <td className="py-3 px-2 text-sm text-lia-text-tertiary dark:text-lia-text-secondary">{formatDate(control.lastChecked)}</td>
                      <td className="py-3 px-2 text-sm text-lia-text-secondary dark:text-lia-text-tertiary">{control.owner || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-6">
              <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" aria-live="polite" aria-atomic="true">Nenhum controle encontrado</p>
            </div>
          )}
        </CardContent>
      </Card>

      {dashboard && dashboard.upcomingReviews > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
              Próximas Revisões Agendadas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="p-4 rounded-md bg-lia-bg-tertiary dark:bg-lia-bg-secondary border border-lia-border-default dark:border-lia-border-default">
              <div className="flex items-center gap-3">
                <Calendar className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                <div>
                  <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
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
