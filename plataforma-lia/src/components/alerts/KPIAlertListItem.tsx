"use client"

import React from"react"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import {
  AlertTriangle, CheckCircle, TrendingDown, TrendingUp,
  Eye, Send, Archive, AlertCircle, Info,
  Users, Target, Calendar
} from"lucide-react"
import type { KPIAlert } from"./useKPIAlertSystem"

interface KPIAlertListItemProps {
  alert: KPIAlert
  onMarkAsRead: (id: string) => void
  onArchive: (id: string) => void
  onSendNotification: (id: string) => void
  onShowDetails: (alert: KPIAlert) => void
}

function getAlertIcon(type: KPIAlert['type']) {
  switch (type) {
    case 'critical': return <AlertTriangle className="w-5 h-5 text-status-error" />
    case 'warning': return <AlertCircle className="w-5 h-5 text-status-warning" />
    case 'info': return <Info className="w-5 h-5 text-lia-text-secondary" />
    case 'success': return <CheckCircle className="w-5 h-5 text-status-success" />
  }
}

function getAlertBadgeColor(type: KPIAlert['type']) {
  switch (type) {
    case 'critical': return ' border-status-error/30'
    case 'warning': return ' border-status-warning/30'
    case 'info': return 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary border-lia-border-default dark:border-lia-border-default'
    case 'success': return ' border-status-success/30'
  }
}

function getPriorityBadgeColor(priority: KPIAlert['priority']) {
  switch (priority) {
    case 'urgent': return 'bg-status-error text-white'
    case 'high': return 'bg-wedo-orange text-white'
    case 'medium': return 'bg-status-warning text-white'
    case 'low': return 'bg-lia-border-medium text-white'
  }
}

export function KPIAlertListItem({ alert, onMarkAsRead, onArchive, onSendNotification, onShowDetails }: KPIAlertListItemProps) {
  return (
    <div
      data-testid={`kpi-alert-list-item-${alert.id}`}
      className={`p-4 border rounded-md transition-colors motion-reduce:transition-none ${
        alert.isRead ? 'bg-lia-bg-secondary' : 'bg-lia-bg-primary border-l-4'
      } ${
        alert.type === 'critical' ? 'border-l-red-500' :
        alert.type === 'warning' ? 'border-l-yellow-500' :
        alert.type === 'info' ? 'border-l-lia-border-medium dark:border-l-lia-border-medium' :
        'border-l-green-500'
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1">
          <div className="mt-1">{getAlertIcon(alert.type)}</div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h4 className={`font-medium ${alert.isRead ? 'text-lia-text-primary' : 'text-lia-text-primary'}`}>
                {alert.title}
              </h4>
              <Chip variant="neutral" muted className={`text-xs ${getAlertBadgeColor(alert.type)}`}>{alert.type}</Chip>
              <Chip variant="neutral" muted className={`text-xs ${getPriorityBadgeColor(alert.priority)}`}>{alert.priority}</Chip>
            </div>
            <p className="text-sm text-lia-text-secondary mb-3">{alert.description}</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3 p-3 bg-lia-bg-secondary rounded-xl">
              <div className="text-center">
                <div className="text-lg font-semibold text-lia-text-primary">{alert.currentValue}</div>
                <div className="text-xs text-lia-text-secondary">Atual</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-lia-text-secondary">{alert.targetValue}</div>
                <div className="text-xs text-lia-text-secondary">Meta</div>
              </div>
              <div className="text-center">
                <div className={`text-lg font-semibold ${alert.variance > 25 ? 'text-status-error' : 'text-status-warning'}`}>
                  {alert.variance.toFixed(1)}%
                </div>
                <div className="text-xs text-lia-text-secondary">Variação</div>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center">
                  {alert.trend === 'up' ? <TrendingUp className="w-5 h-5 text-status-error" /> : <TrendingDown className="w-5 h-5 text-status-success" />}
                </div>
                <div className="text-xs text-lia-text-secondary">Tendência</div>
              </div>
            </div>
            <div className="flex items-center gap-4 text-xs text-lia-text-secondary mb-3">
              <span className="flex items-center gap-1"><Users className="w-3 h-3" />{alert.department}</span>
              <span className="flex items-center gap-1"><Calendar className="w-3 h-3" />{alert.createdAt.toLocaleDateString('pt-BR')}</span>
              {alert.affectedJobs && <span className="flex items-center gap-1"><Target className="w-3 h-3" />{alert.affectedJobs.length} vagas afetadas</span>}
            </div>
            {alert.suggestedActions.length > 0 && (
              <div className="border-t pt-3">
                <h5 className="text-sm font-medium text-lia-text-primary mb-2">Ações Sugeridas:</h5>
                <ul className="space-y-1">
                  {alert.suggestedActions.slice(0, 2).map((action, index) => (
                    <li key={`action-${index}`} className="text-sm text-lia-text-secondary flex items-start gap-2">
                      <span className="text-lia-text-secondary mt-1">•</span>{action}
                    </li>
                  ))}
                </ul>
                {alert.suggestedActions.length > 2 && (
                  <Button variant="ghost" size="sm" className="mt-2 text-lia-text-secondary h-auto p-0 hover:bg-lia-interactive-hover transition-colors cursor-pointer" onClick={() => onShowDetails(alert)}>
                    Ver todas as {alert.suggestedActions.length} sugestões
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 ml-4">
          {!alert.isRead && (
            <Button variant="ghost" size="sm" onClick={() => onMarkAsRead(alert.id)} className="gap-2 hover:bg-lia-interactive-hover transition-colors cursor-pointer">
              <Eye className="w-3 h-3" />Marcar Lido
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={() => onSendNotification(alert.id)} className="gap-2 hover:bg-lia-interactive-hover transition-colors cursor-pointer">
            <Send className="w-3 h-3" />Notificar
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onArchive(alert.id)} className="gap-2 hover:bg-lia-interactive-hover transition-colors cursor-pointer">
            <Archive className="w-3 h-3" />Arquivar
          </Button>
        </div>
      </div>
    </div>
  )
}
