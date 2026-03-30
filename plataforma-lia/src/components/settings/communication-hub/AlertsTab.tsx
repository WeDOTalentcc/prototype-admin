import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Edit, Save, Bell, Clock, Calendar, RefreshCw, Brain, Loader2, AlertCircle, CheckCircle, MessageSquare } from "lucide-react"
import { textStyles, actionButtonStyles } from '@/lib/design-tokens'
import type { AlertConfig } from './CommunicationHub.types'

interface AlertsTabProps {
  successMessage: string | null
  error: string | null
  alerts: AlertConfig[]
  briefingFrequency: 'twice_daily' | 'daily' | 'weekly' | 'monthly'
  setBriefingFrequency: (v: 'twice_daily' | 'daily' | 'weekly' | 'monthly') => void
  isEditingAlerts: boolean
  setIsEditingAlerts: (v: boolean) => void
  savingAlerts: boolean
  saveAlertsConfig: () => Promise<void>
  handleToggleAlert: (id: string) => void
  handleChangeChannel: (id: string, channel: 'email' | 'teams' | 'both') => void
}

export function AlertsTab({
  successMessage, error,
  alerts, briefingFrequency, setBriefingFrequency,
  isEditingAlerts, setIsEditingAlerts,
  savingAlerts, saveAlertsConfig,
  handleToggleAlert, handleChangeChannel
}: AlertsTabProps) {
  return (
    <div className="space-y-4">
      {successMessage && (
        <div className="px-2 py-1.5 rounded-md flex items-center gap-2 bg-status-success/15 border border-status-success/30 text-status-success dark:bg-status-success dark:border-status-success/30 dark:text-status-success">
          <CheckCircle className="w-3.5 h-3.5 text-status-success dark:text-status-success" />
          <span className="text-xs">{successMessage}</span>
        </div>
      )}
      {error && (
        <div className="bg-status-error/10 border border-status-error/30 text-status-error px-2 py-1.5 rounded-md flex items-center gap-2">
          <AlertCircle className="w-3.5 h-3.5" />
          <span className="text-xs">{error}</span>
        </div>
      )}
      <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-white/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-md">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
                <Bell className="w-3.5 h-3.5 lia-text-600 dark:text-lia-text-tertiary" />
                Configuração de Alertas
              </CardTitle>
              <p className="text-xs lia-text-600 mt-0.5">
                A LIA aprende com seus padrões e ajusta os alertas automaticamente
              </p>
            </div>
            {!isEditingAlerts ? (
              <button onClick={() => setIsEditingAlerts(true)} className={actionButtonStyles.smOutline}>
                <Edit className={actionButtonStyles.icon} />
                Editar
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <button onClick={() => setIsEditingAlerts(false)} className={actionButtonStyles.smSecondary}>
                  Cancelar
                </button>
                <button
                  onClick={async () => { await saveAlertsConfig(); setIsEditingAlerts(false) }}
                  disabled={savingAlerts}
                  className={actionButtonStyles.smPrimary}
                >
                  {savingAlerts ? <Loader2 className={actionButtonStyles.icon} /> : <Save className={actionButtonStyles.icon} />}
                  Salvar Alterações
                </button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-2.5 rounded-md border transition-colors ${
                alert.enabled
                  ? 'bg-white dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle'
                  : 'bg-gray-50 dark:bg-lia-bg-secondary/50 border-lia-border-subtle dark:lia-border-800'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-2">
                  <div
                    className="w-7 h-7 rounded-md flex items-center justify-center"
                    style={{backgroundColor: alert.enabled ? 'var(--gray-600-bg-10)' : undefined, color: alert.enabled ? 'var(--gray-600)' : undefined}}
                  >
                    <Bell className="w-3.5 h-3.5" style={{color: alert.enabled ? 'var(--gray-600)' : undefined}} />
                  </div>
                  <div>
                    <p className={`text-xs font-medium ${alert.enabled ? 'lia-text-950 dark:lia-text-50' : 'lia-text-800'}`}>
                      {alert.name}
                    </p>
                    <p className="text-xs lia-text-600 mt-0.5">{alert.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <select
                    value={alert.channel}
                    onChange={(e) => handleChangeChannel(alert.id, e.target.value as 'email' | 'teams' | 'both')}
                    disabled={!isEditingAlerts || !alert.enabled}
                    className="text-micro border border-lia-border-subtle dark:border-lia-border-subtle rounded-full px-1.5 py-1 bg-white dark:bg-lia-bg-secondary lia-text-900 dark:text-lia-text-primary disabled:bg-gray-50 disabled:lia-text-600"
                  >
                    <option value="email">Email</option>
                    <option value="teams">Teams</option>
                    <option value="both">Ambos</option>
                  </select>
                  <button
                    onClick={() => isEditingAlerts && handleToggleAlert(alert.id)}
                    disabled={!isEditingAlerts}
                    className="relative w-9 h-5 rounded-full transition-colors disabled:opacity-60"
                    style={{backgroundColor: alert.enabled ? 'var(--gray-600)' : 'var(--gray-200)'}}
                  >
                    <span className={`absolute top-0.5 w-4 h-4 bg-lia-bg-secondary rounded-full transition-transform ${alert.enabled ? 'left-4' : 'left-0.5'}`} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-white/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-md">
        <CardHeader className="pb-2">
          <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
            <MessageSquare className="w-3.5 h-3.5 lia-text-600 dark:text-lia-text-tertiary" />
            Frequência do Briefing da LIA
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-2">
            {([
              { key: 'twice_daily' as const, label: '2x ao Dia', desc: 'Resumo às 8h e às 14h', icon: RefreshCw },
              { key: 'daily' as const, label: 'Diário', desc: 'Resumo todas as manhãs às 8h', icon: Clock },
              { key: 'weekly' as const, label: 'Semanal', desc: 'Resumo toda segunda-feira', icon: Calendar },
              { key: 'monthly' as const, label: 'Mensal', desc: 'Resumo no 1º dia útil do mês', icon: Calendar },
            ] as const).map(({ key, label, desc, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setBriefingFrequency(key)}
                disabled={!isEditingAlerts}
                className={`p-2.5 rounded-md border-2 transition-colors text-left ${!isEditingAlerts ? 'opacity-60 cursor-not-allowed' : ''}`}
                style={{
                  borderColor: briefingFrequency === key ? 'var(--gray-600)' : 'var(--gray-200)',
                  backgroundColor: briefingFrequency === key ? 'var(--gray-600-bg-10)' : undefined
                }}
              >
                <div className="flex items-center gap-1.5 mb-0.5">
                  <Icon className="w-3.5 h-3.5" style={{color: briefingFrequency === key ? 'var(--gray-600)' : undefined}} />
                  <span className="text-xs font-medium">{label}</span>
                </div>
                <p className="text-xs lia-text-600">{desc}</p>
              </button>
            ))}
          </div>

          <div className="rounded-md p-2.5 bg-wedo-cyan/[.08]">
            <div className="flex items-start gap-2">
              <Brain className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-wedo-cyan" />
              <div>
                <p className={`${textStyles.subtitle} lia-text-800 dark:text-lia-text-primary`}>A LIA aprende com você</p>
                <p className="text-xs lia-text-600 mt-0.5">
                  Quanto mais você interage, melhor ela entende quais alertas são relevantes.
                  Alertas ignorados consistentemente serão automaticamente desativados.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
