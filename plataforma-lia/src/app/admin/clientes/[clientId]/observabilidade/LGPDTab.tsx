"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  CheckCircle2,
  AlertTriangle,
  Clock,
  TrendingUp,
  Users,
  FileText,
  AlertCircle,
  Filter,
  ChevronRight,
} from "lucide-react"
import { useLGPDCompliance } from '@/hooks/admin/useLGPDCompliance'
import { LoadingSpinner } from './observabilidade-shared'

export function LGPDTab({ clientId }: { clientId: string }) {
  const { stats, dpo, breaches, isLoading } = useLGPDCompliance(clientId)

  const activeConsents = 0
  const pendingDSRs = 0
  const expiredData = 0

  const formatDate = (dateStr: string | undefined | null) => {
    if (!dateStr) return '-'
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
    } catch {
      return dateStr
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Carregando dados LGPD...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">DPO Registrado</p>
                <p className="text-lg font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary">
                  {dpo ? dpo.dpoName : (stats?.dpoRegistered ? 'Sim' : 'Não')}
                </p>
                {dpo && (
                  <p className="text-xs mt-1 text-lia-text-tertiary dark:text-lia-text-secondary">
                    {dpo.dpoEmail}
                  </p>
                )}
              </div>
              <div className="w-10 h-10 rounded-md bg-lia-bg-tertiary dark:bg-lia-bg-secondary flex items-center justify-center">
                <Users className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Consentimentos Ativos</p>
                <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary">{activeConsents}</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-status-success" />
                  <span className="text-xs text-status-success">+8 esta semana</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-status-success/10 dark:bg-status-success/20 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5 text-status-success dark:text-status-success" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Incidentes Abertos</p>
                <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary">
                  {stats?.openBreaches || breaches.filter(b => b.status !== 'resolved').length || 0}
                </p>
                {stats && stats.breachesPendingAnpd > 0 && (
                  <div className="flex items-center gap-1 mt-1">
                    <AlertCircle className="w-3 h-3 text-status-warning" />
                    <span className="text-xs text-status-warning">{stats.breachesPendingAnpd} pendentes ANPD</span>
                  </div>
                )}
              </div>
              <div className="w-10 h-10 rounded-md bg-status-warning/10 dark:bg-status-warning/20 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-status-warning dark:text-status-warning" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Dados Expirados</p>
                <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary">{expiredData}</p>
                <div className="flex items-center gap-1 mt-1">
                  <AlertCircle className="w-3 h-3 text-status-error" />
                  <span className="text-xs text-status-error">Requer ação</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-status-error/10 dark:bg-status-error/20 flex items-center justify-center">
                <Clock className="w-5 h-5 text-status-error dark:text-status-error" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {breaches.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
                Incidentes de Dados (LGPD Art. 48)
              </CardTitle>
              <Badge variant={breaches.some(b => b.status !== 'resolved') ? 'warning' : 'success'}>
                {breaches.filter(b => b.status !== 'resolved').length} abertos
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {breaches.slice(0, 5).map((breach) => (
                <div 
                  key={breach.id}
                  className={`p-4 rounded-md border ${breach.severity === 'critical' || breach.severity === 'high' ? 'bg-status-error/10 dark:bg-status-error/20 border-status-error/30 dark:border-status-error/30' : 'bg-status-warning/10 dark:bg-status-warning/20 border-status-warning/30 dark:border-status-warning/30'}`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                        {breach.breachDescription}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        <Badge variant={breach.severity === 'critical' ? 'destructive' : breach.severity === 'high' ? 'warning' : 'default'}>
                          {breach.severity.toUpperCase()}
                        </Badge>
                        {!breach.notificationSentToAnpd && breach.hoursUntilDeadline !== undefined && (
                          <span className="text-xs text-status-error">
                            {breach.hoursUntilDeadline}h para notificar ANPD
                          </span>
                        )}
                      </div>
                      <p className="text-xs mt-2 text-lia-text-tertiary dark:text-lia-text-secondary">
                        Detectado: {formatDate(breach.breachDetectedAt)}
                      </p>
                    </div>
                    <Badge variant={breach.status === 'resolved' ? 'success' : 'warning'}>
                      {breach.status === 'resolved' ? 'Resolvido' : breach.status === 'notified' ? 'Notificado' : 'Aberto'}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
                Consentimentos por Candidato
              </CardTitle>
              <Button variant="outline" size="sm">
                <Filter className="w-4 h-4 mr-2" />
                Filtrar
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <FileText className="w-8 h-8 mb-3 text-lia-text-tertiary dark:text-lia-text-secondary" />
              <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                Consentimentos gerenciados centralmente
              </p>
              <p className="text-xs mt-1 text-lia-text-tertiary dark:text-lia-text-secondary">
                Acesse a página de Consentimentos para ver e gerenciar os registros.
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
                Solicitações DSR
              </CardTitle>
              <Badge variant={pendingDSRs > 0 ? 'warning' : 'success'}>
                {pendingDSRs} pendentes
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Clock className="w-8 h-8 mb-3 text-lia-text-tertiary dark:text-lia-text-secondary" />
              <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                Solicitações de Titulares (Art. 18 LGPD)
              </p>
              <p className="text-xs mt-1 text-lia-text-tertiary dark:text-lia-text-secondary">
                As DSRs são gerenciadas no Portal do Titular.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
            Alertas de Retenção
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="p-4 rounded-md bg-status-warning/10 dark:bg-status-warning/20 border border-status-warning/30 dark:border-status-warning/30">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-status-warning/15 dark:bg-status-warning/30 flex items-center justify-center">
                <Clock className="w-4 h-4 text-status-warning dark:text-status-warning" />
              </div>
              <div>
                <p className="text-sm font-medium text-status-warning dark:text-status-warning">
                  {expiredData} registros com período de retenção expirado
                </p>
                <p className="text-xs mt-1 text-status-warning dark:text-status-warning">
                  Estes dados devem ser excluídos ou ter seu consentimento renovado de acordo com a LGPD.
                </p>
                <Button variant="outline" size="sm" className="mt-3">
                  Revisar Dados
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
