"use client"

import React from"react"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Bell, AlertTriangle, AlertCircle, Info, Briefcase, Clock, Brain } from"lucide-react"
import { getAlertSeverityStyle, getSeverityLabel } from"../task-helpers"

interface Alert {
  id: string
  title: string
  description: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  jobId: string
  jobTitle: string
  createdAt: Date
  action: string
}

interface ActiveAlertsCardProps {
  activeAlerts: Alert[]
  onAlertAction: (alert: Alert) => void
  textStyles: { label: string; [key: string]: string }
}

export const ActiveAlertsCard = React.memo(function ActiveAlertsCard({
  activeAlerts,
  onAlertAction,
  textStyles,
}: ActiveAlertsCardProps) {
  return (
    <Card className="border-lia-border-subtle dark:border-lia-border-subtle">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bell className="w-3.5 h-3.5 text-amber-500" />
            <CardTitle className={`${textStyles.label} font-semibold text-lia-text-primary`}>Alertas Ativos</CardTitle>
            <Chip density="relaxed" variant="neutral" className="font-inter">
              {activeAlerts.length}
            </Chip>
          </div>
          <div className="flex items-center gap-1.5">
            <Chip
              variant="danger"
              className="text-xs font-medium"
            >
              {activeAlerts.filter(a => a.severity === 'critical' || a.severity === 'high').length} Alto/Crítico
            </Chip>
            <Chip
              variant="warning"
              className="text-xs font-medium"
            >
              {activeAlerts.filter(a => a.severity === 'medium').length} Médio
            </Chip>
            <Chip
              variant="info"
              className="text-xs font-medium"
            >
              {activeAlerts.filter(a => a.severity === 'low').length} Baixo
            </Chip>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0 pb-2 max-h-[280px] overflow-y-auto">
        <div className="space-y-2">
          {activeAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`border border-lia-border-subtle dark:border-lia-border-subtle rounded-lg p-2.5 hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none ${getAlertSeverityStyle(alert.severity)} bg-opacity-40`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-start gap-2 flex-1">
                  <div
                    className={`w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0 ${getAlertSeverityStyle(alert.severity)}`}
                  >
                    {(alert.severity === 'critical' || alert.severity === 'high') && <AlertTriangle className="w-3.5 h-3.5" />}
                    {alert.severity === 'medium' && <AlertCircle className="w-3.5 h-3.5" />}
                    {(alert.severity === 'low' || alert.severity === 'info') && <Info className="w-3.5 h-3.5" />}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap mb-0.5">
                      <h4 className="text-xs font-inter font-semibold text-lia-text-primary">
                        {alert.title}
                      </h4>
                      <Chip variant="neutral" muted
                        className={`border-0 text-micro py-0 px-1.5 font-medium ${getAlertSeverityStyle(alert.severity)}`}
                      >
                        {getSeverityLabel(alert.severity)}
                      </Chip>
                    </div>
                    <p className="text-xs font-open-sans text-lia-text-primary mb-1 line-clamp-1">
                      {alert.description}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-lia-text-primary">
                      <span className="flex items-center gap-0.5">
                        <Briefcase className="w-2.5 h-2.5" />
                        {alert.jobTitle}
                      </span>
                      <span className="flex items-center gap-0.5">
                        <Clock className="w-2.5 h-2.5" />
                        {alert.createdAt.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })}
                      </span>
                    </div>
                  </div>
                </div>

                <Button
                  size="sm"
                  onClick={() => onAlertAction(alert)}
                  className="h-6 px-2 text-xs gap-1 flex-shrink-0"
                >
                  <Brain className="w-3 h-3 text-wedo-cyan" />
                  {alert.action}
                </Button>
              </div>
            </div>
          ))}

          {activeAlerts.length === 0 && (
            <div className="text-center py-8">
              <Bell className="w-12 h-12 mx-auto text-lia-text-disabled mb-3" />
              <p className="text-sm font-medium text-lia-text-primary mb-1">Nenhum alerta ativo</p>
              <p className="text-xs text-lia-text-secondary">Sem alertas no momento</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
})

export default ActiveAlertsCard
