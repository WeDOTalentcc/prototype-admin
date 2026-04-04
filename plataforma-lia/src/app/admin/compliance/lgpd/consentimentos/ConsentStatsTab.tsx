"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { CheckSquare, Ban, Clock, AlertCircle, Loader2 } from "lucide-react"
import { ConsentStats } from "@/services/admin/consent-management-service"

const CONSENT_TYPE_LABELS: Record<string, string> = {
  personal_data: 'Dados Pessoais',
  marketing: 'Comunicações Marketing',
  sensitive_data: 'Dados Sensíveis',
  data_sharing: 'Compartilhamento com Clientes',
  cookies: 'Cookies',
  analytics: 'Analytics',
  third_party: 'Terceiros',
}

interface ConsentStatsTabProps {
  stats: ConsentStats | null
  isLoading: boolean
}

export function ConsentStatsTab({ stats, isLoading }: ConsentStatsTabProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
            Taxa de Consentimento por Tipo
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none text-lia-text-secondary dark:text-lia-text-tertiary" />
            </div>
          ) : stats && Object.keys(stats.byType).length > 0 ? (
            <div className="space-y-4">
              {Object.entries(stats.byType).map(([type, data]) => (
                <div key={type} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                      {CONSENT_TYPE_LABELS[type] || type}
                    </span>
                    <span className="text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary">
                      {Math.round(data.rate)}%
                    </span>
                  </div>
                  <Progress value={data.rate} className="h-2" />
                  <div className="flex items-center justify-between text-xs text-lia-text-tertiary dark:text-lia-text-secondary">
                    <span>{data.active} ativos</span>
                    <span>{data.pending} pendentes</span>
                    <span>{data.revoked} revogados</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8">
              <AlertCircle className="w-10 h-10 text-lia-text-disabled mb-3" />
              <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                Nenhuma estatística disponível
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
            Atividade Recente
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none text-lia-text-secondary dark:text-lia-text-tertiary" />
            </div>
          ) : stats ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 rounded-md bg-status-success/10">
                <div className="flex items-center gap-3">
                  <CheckSquare className="w-5 h-5 text-status-success" />
                  <span className="text-sm text-lia-text-primary dark:text-lia-text-primary">
                    Consentimentos Hoje
                  </span>
                </div>
                <span className="text-lg font-semibold text-status-success">
                  {stats.recentActivity.grantsToday}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-md bg-wedo-purple/10">
                <div className="flex items-center gap-3">
                  <Ban className="w-5 h-5 text-wedo-purple" />
                  <span className="text-sm text-lia-text-primary dark:text-lia-text-primary">
                    Revogações Hoje
                  </span>
                </div>
                <span className="text-lg font-semibold text-wedo-purple">
                  {stats.recentActivity.revokesToday}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-md bg-status-warning/10">
                <div className="flex items-center gap-3">
                  <Clock className="w-5 h-5 text-status-warning" />
                  <span className="text-sm text-lia-text-primary dark:text-lia-text-primary">
                    Expirando Esta Semana
                  </span>
                </div>
                <span className="text-lg font-semibold text-status-warning">
                  {stats.recentActivity.expiringThisWeek}
                </span>
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
            Resumo Geral
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 rounded-md bg-lia-bg-secondary">
              <p className="text-3xl font-bold text-lia-text-primary dark:text-lia-text-primary">
                {stats?.totalVersions || 0}
              </p>
              <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">
                Versões de Termos
              </p>
            </div>
            <div className="text-center p-4 rounded-md bg-lia-bg-secondary">
              <p className="text-3xl font-bold text-lia-text-primary dark:text-lia-text-primary">
                {stats?.totalConsents || 0}
              </p>
              <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">
                Total de Consentimentos
              </p>
            </div>
            <div className="text-center p-4 rounded-md bg-lia-bg-secondary">
              <p className="text-3xl font-bold text-status-success">
                {stats?.activeVersions || 0}
              </p>
              <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">
                Versões Ativas
              </p>
            </div>
            <div className="text-center p-4 rounded-md bg-lia-bg-secondary">
              <p className="text-3xl font-bold text-lia-text-primary dark:text-lia-text-primary">
                {Math.round(stats?.consentRate || 0)}%
              </p>
              <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">
                Taxa de Aceite
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
