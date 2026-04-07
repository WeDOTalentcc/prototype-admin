import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Edit, Save, Bell, Clock, Calendar, RefreshCw, Brain, Loader2, AlertCircle, CheckCircle, MessageSquare, BarChart3 } from "lucide-react"
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
  weeklyDigestEnabled: boolean
  savingWeeklyDigest: boolean
  handleToggleWeeklyDigest: () => void
}

export function AlertsTab({
  successMessage, error,
  alerts, briefingFrequency, setBriefingFrequency,
  isEditingAlerts, setIsEditingAlerts,
  savingAlerts, saveAlertsConfig,
  handleToggleAlert, handleChangeChannel,
  weeklyDigestEnabled, savingWeeklyDigest, handleToggleWeeklyDigest
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
      <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-lia-bg-primary/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-md">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
                <Bell className="w-3.5 h-3.5 text-lia-text-secondary" />
                Configuração de Alertas
              </CardTitle>
              <p className="text-xs text-lia-text-secondary mt-0.5">
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
              className={`p-2.5 rounded-md border transition-colors motion-reduce:transition-none ${
                alert.enabled
                  ? 'bg-lia-bg-primary dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle'
                  : 'bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 border-lia-border-subtle dark:border-lia-border-strong'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-2">
                  <div
                    className={`w-7 h-7 rounded-md flex items-center justify-center ${alert.enabled ? 'bg-lia-bg-secondary text-lia-text-secondary' : ''}`}
                  >
                    <Bell className={`w-3.5 h-3.5 ${alert.enabled ? 'text-lia-text-secondary' : ''}`} />
                  </div>
                  <div>
                    <p className={`text-xs font-medium ${alert.enabled ? 'text-lia-text-primary' : 'text-lia-text-primary'}`}>
                      {alert.name}
                    </p>
                    <p className="text-xs text-lia-text-secondary mt-0.5">{alert.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <select
                    value={alert.channel}
                    onChange={(e) => handleChangeChannel(alert.id, e.target.value as 'email' | 'teams' | 'both')}
                    disabled={!isEditingAlerts || !alert.enabled}
                    className="text-micro border border-lia-border-subtle dark:border-lia-border-subtle rounded-full px-1.5 py-1 bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary disabled:bg-lia-bg-secondary disabled:text-lia-text-secondary"
                  >
                    <option value="email">Email</option>
                    <option value="teams">Teams</option>
                    <option value="both">Ambos</option>
                  </select>
                  <button
                    onClick={() => isEditingAlerts && handleToggleAlert(alert.id)}
                    disabled={!isEditingAlerts}
                    className={`relative w-9 h-5 rounded-full transition-colors motion-reduce:transition-none disabled:opacity-60 ${alert.enabled ? 'bg-lia-text-secondary' : 'bg-lia-border-subtle'}`}
                  >
                    <span className={`absolute top-0.5 w-4 h-4 bg-lia-bg-secondary rounded-full transition-transform motion-reduce:transition-none ${alert.enabled ? 'left-4' : 'left-0.5'}`} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-lia-bg-primary/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-md">
        <CardHeader className="pb-2">
          <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
            <MessageSquare className="w-3.5 h-3.5 text-lia-text-secondary" />
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
                className={`p-2.5 rounded-md border-2 transition-colors motion-reduce:transition-none text-left ${!isEditingAlerts ? 'opacity-60 cursor-not-allowed' : ''} ${briefingFrequency === key ? 'border-lia-text-secondary bg-lia-bg-secondary' : 'border-lia-border-subtle'}`}
              >
                <div className="flex items-center gap-1.5 mb-0.5">
                  <Icon className={`w-3.5 h-3.5 ${briefingFrequency === key ? 'text-lia-text-secondary' : ''}`} />
                  <span className="text-xs font-medium">{label}</span>
                </div>
                <p className="text-xs text-lia-text-secondary">{desc}</p>
              </button>
            ))}
          </div>

          <div className="rounded-md p-2.5 bg-wedo-cyan/[.08]">
            <div className="flex items-start gap-2">
              <Brain className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-wedo-cyan" />
              <div>
                <p className={`${textStyles.subtitle} text-lia-text-primary`}>A LIA aprende com você</p>
                <p className="text-xs text-lia-text-secondary mt-0.5">
                  Quanto mais você interage, melhor ela entende quais alertas são relevantes.
                  Alertas ignorados consistentemente serão automaticamente desativados.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-lia-bg-primary/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-md">
        <CardHeader className="pb-2">
          <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
            <BarChart3 className="w-3.5 h-3.5 text-lia-text-secondary" />
            Resumo Semanal
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div
            className={`p-2.5 rounded-md border transition-colors motion-reduce:transition-none ${
              weeklyDigestEnabled
                ? 'bg-lia-bg-primary dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle'
                : 'bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 border-lia-border-subtle dark:border-lia-border-strong'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-2">
                <div
                  className={`w-7 h-7 rounded-md flex items-center justify-center ${weeklyDigestEnabled ? 'bg-lia-bg-secondary text-lia-text-secondary' : ''}`}
                >
                  <BarChart3 className={`w-3.5 h-3.5 ${weeklyDigestEnabled ? 'text-lia-text-secondary' : ''}`} />
                </div>
                <div>
                  <p className={`text-xs font-medium ${weeklyDigestEnabled ? 'text-lia-text-primary' : 'text-lia-text-primary'}`}>
                    Insights Proativos Semanais
                  </p>
                  <p className="text-xs text-lia-text-secondary mt-0.5">
                    Toda segunda-feira às 08h, receba um resumo consolidado com pipeline, compliance, vagas em risco e otimizações via Teams, chat e notificação.
                  </p>
                </div>
              </div>
              <button
                onClick={handleToggleWeeklyDigest}
                disabled={savingWeeklyDigest}
                role="switch"
                aria-checked={weeklyDigestEnabled}
                aria-label="Ativar ou desativar resumo semanal de insights"
                className={`relative w-9 h-5 rounded-full transition-colors motion-reduce:transition-none disabled:opacity-60 flex-shrink-0 mt-0.5 ${weeklyDigestEnabled ? 'bg-lia-text-primary' : 'bg-lia-border-subtle'}`}
              >
                {savingWeeklyDigest ? (
                  <Loader2 className="w-3 h-3 absolute top-1 left-3 animate-spin" />
                ) : (
                  <span className={`absolute top-0.5 w-4 h-4 bg-lia-bg-secondary rounded-full transition-transform motion-reduce:transition-none ${weeklyDigestEnabled ? 'left-4' : 'left-0.5'}`} />
                )}
              </button>
            </div>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-lia-text-secondary">
            <Clock className="w-3 h-3" />
            <span>Entrega: segunda-feira, 08h (Brasília) — Teams + Chat + Bell</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
