'use client'

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import {
  Mail, Save, Bell, Loader2, RefreshCw, Activity,
  AlertTriangle, AlertCircle, Globe, Webhook
} from "lucide-react"
import type { TechnicalAlert } from './types'
import { severityColors } from './constants'

interface AlertsSectionProps {
  technicalAlerts: TechnicalAlert[]
  technicalAlertsLoading: boolean
  savingTechnicalAlerts: boolean
  technicalAlertsHasChanges: boolean
  fetchTechnicalAlerts: () => void
  saveTechnicalAlerts: () => void
  handleToggleAlert: (id: string) => void
  handleToggleAlertChannel: (alertId: string, channel: 'email' | 'slack' | 'webhook') => void
  handleUpdateAlertThreshold: (id: string, threshold: number) => void
}

export function AlertsSection({
  technicalAlerts,
  technicalAlertsLoading,
  savingTechnicalAlerts,
  technicalAlertsHasChanges,
  fetchTechnicalAlerts,
  saveTechnicalAlerts,
  handleToggleAlert,
  handleToggleAlertChannel,
  handleUpdateAlertThreshold
}: AlertsSectionProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium text-lia-text-secondary dark:text-lia-text-tertiary" >
            Alertas Técnicos de Comunicação
          </h3>
          <p className="text-xs mt-1 text-lia-text-tertiary dark:text-lia-text-secondary" >
            Configure alertas para monitorar a saúde das comunicações e integrações
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchTechnicalAlerts}
            disabled={technicalAlertsLoading}
          >
            <RefreshCw className={`w-4 h-4 ${technicalAlertsLoading ? 'animate-spin motion-reduce:animate-none' : ''}`} />
          </Button>
          {technicalAlertsHasChanges && (
            <Button
              onClick={saveTechnicalAlerts}
              disabled={savingTechnicalAlerts}
              className="bg-lia-btn-primary-bg dark:bg-lia-bg-secondary hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active"
              size="sm"
            >
              {savingTechnicalAlerts ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />
              ) : (
                <Save className="w-4 h-4 mr-2" />
              )}
              Salvar Alterações
            </Button>
          )}
          <Badge variant="outline" className="text-xs">
            <Activity className="w-3 h-3 mr-1" />
            {technicalAlerts.filter(a => a.enabled).length} ativos
          </Badge>
        </div>
      </div>

      {technicalAlertsLoading ? (
        <div className="flex items-center justify-center py-12" role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="w-8 h-8 animate-spin motion-reduce:animate-none text-lia-text-primary dark:text-lia-text-secondary" />
          <span className="ml-3 text-sm text-lia-text-secondary dark:text-lia-text-tertiary" >
            Carregando alertas técnicos...
          </span>
        </div>
      ) : technicalAlerts.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12">
          <Bell className="w-12 h-12 text-lia-text-disabled mb-4" />
          <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
            Nenhum alerta técnico configurado
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {technicalAlerts.map(alert => (
            <Card key={alert.id} className={`transition-opacity motion-reduce:transition-none ${!alert.enabled ? 'opacity-60' : ''}`}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <AlertTriangle className={`w-4 h-4 ${alert.enabled ? 'text-status-warning' : 'lia-text-400 dark:text-lia-text-secondary'}`} />
                      <h4 className="font-medium text-sm text-lia-text-primary dark:text-lia-text-primary" >
                        {alert.name}
                      </h4>
                      <Badge className={`text-xs ${severityColors[alert.severity]}`}>
                        {alert.severity === 'low' ? 'Baixa' : 
                         alert.severity === 'medium' ? 'Média' : 
                         alert.severity === 'high' ? 'Alta' : 'Crítica'}
                      </Badge>
                    </div>
                    <p className="text-xs mb-3 text-lia-text-tertiary dark:text-lia-text-secondary" >
                      {alert.description}
                    </p>
                    
                    {alert.threshold !== undefined && (
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-xs font-medium text-lia-text-secondary dark:text-lia-text-tertiary" >Limite:</span>
                        <Input
                          type="number"
                          value={alert.threshold}
                          onChange={(e) => handleUpdateAlertThreshold(alert.id, parseInt(e.target.value) || 0)}
                          className="w-20 h-7 text-xs"
                          min={0}
                        />
                        <span className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >
                          {alert.thresholdUnit}
                        </span>
                      </div>
                    )}
                    
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-lia-text-secondary dark:text-lia-text-tertiary" >Canais:</span>
                      {(['email', 'slack', 'webhook'] as const).map(channel => (
                        <Badge
                          key={channel}
                          variant={alert.channels.includes(channel) ? 'default' : 'outline'}
                          className={`text-xs cursor-pointer transition-transform motion-reduce:transition-none hover:scale-105 ${
                            alert.channels.includes(channel) 
                              ? channel === 'email' ? 'bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:hover:bg-lia-interactive-active' 
                                : channel === 'slack' ? 'bg-wedo-purple hover:bg-wedo-purple' 
                                : 'bg-status-success hover:bg-status-success'
                              : ''
                          }`}
                          onClick={() => handleToggleAlertChannel(alert.id, channel)}
                        >
                          {channel === 'email' && <Mail className="w-3 h-3 mr-1" />}
                          {channel === 'slack' && <Globe className="w-3 h-3 mr-1" />}
                          {channel === 'webhook' && <Webhook className="w-3 h-3 mr-1" />}
                          {channel === 'email' ? 'Email' : channel === 'slack' ? 'Slack' : 'Webhook'}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <Switch
                      checked={alert.enabled}
                      onCheckedChange={() => handleToggleAlert(alert.id)}
                    />
                    <span className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >
                      {alert.enabled ? 'Ativo' : 'Inativo'}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {technicalAlertsHasChanges && (
        <div className="fixed bottom-6 right-6 z-50">
          <Card className="border-lia-border-default/30 dark:border-lia-border-default/30">
            <CardContent className="p-4 flex items-center gap-4">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-lia-text-primary dark:text-lia-text-secondary" />
                <span className="text-sm font-medium">Alterações não salvas</span>
              </div>
              <Button
                onClick={saveTechnicalAlerts}
                disabled={savingTechnicalAlerts}
                className="bg-lia-btn-primary-bg dark:bg-lia-bg-secondary hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active"
                size="sm"
              >
                {savingTechnicalAlerts ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />
                ) : (
                  <Save className="w-4 h-4 mr-2" />
                )}
                Salvar
              </Button>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
