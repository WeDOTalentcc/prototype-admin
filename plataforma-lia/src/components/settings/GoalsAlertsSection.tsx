"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Bell, Edit, Save, Calendar, Clock, Brain,
  RefreshCw, Loader2, CheckCircle, AlertCircle, MessageSquare
} from "lucide-react"
import { textStyles, cardStyles, badgeStyles, buttonStyles } from '@/lib/design-tokens'
import type { AlertConfig } from "./goalsPlanningConstants"

interface GoalsAlertsSectionProps {
  alerts: AlertConfig[]
  briefingFrequency: 'twice_daily' | 'daily' | 'weekly' | 'monthly'
  setBriefingFrequency: (freq: 'twice_daily' | 'daily' | 'weekly' | 'monthly') => void
  isEditingAlerts: boolean
  setIsEditingAlerts: (editing: boolean) => void
  saving: boolean
  successMessage: string | null
  error: string | null
  handleToggleAlert: (id: string) => void
  handleChangeChannel: (id: string, channel: 'email' | 'teams' | 'both') => void
  saveAlertsConfig: () => Promise<void>
}

export function GoalsAlertsSection({
  alerts,
  briefingFrequency,
  setBriefingFrequency,
  isEditingAlerts,
  setIsEditingAlerts,
  saving,
  successMessage,
  error,
  handleToggleAlert,
  handleChangeChannel,
  saveAlertsConfig,
}: GoalsAlertsSectionProps) {
  return (
    <div className="space-y-3">
      {successMessage && (
        <div className={`${badgeStyles.success} px-3 py-2 flex items-center gap-2 w-full`}>
          <CheckCircle className="w-3.5 h-3.5 flex-shrink-0" />
          <span className={textStyles.body}>{successMessage}</span>
        </div>
      )}
      {error && (
        <div className={`${badgeStyles.error} px-3 py-2 flex items-center gap-2 w-full`}>
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
          <span className={textStyles.body}>{error}</span>
        </div>
      )}
      <Card className={cardStyles.default}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className={`${textStyles.h3} flex items-center gap-2`}>
                <Bell className="w-3.5 h-3.5 text-lia-text-secondary" />
                Configuração de Alertas
              </CardTitle>
              <p className={`${textStyles.description} mt-1`}>
                A LIA aprende com seus padrões e ajusta os alertas automaticamente
              </p>
            </div>
            {!isEditingAlerts ? (
              <button
                onClick={() => setIsEditingAlerts(true)}
                className={buttonStyles.outline}
              >
                <Edit className="w-3 h-3" />
                Editar
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsEditingAlerts(false)}
                  className={buttonStyles.secondary}
                >
                  Cancelar
                </button>
                <button
                  onClick={async () => {
                    await saveAlertsConfig()
                    setIsEditingAlerts(false)
                  }}
                  disabled={saving}
                  className={buttonStyles.primary}
                >
                  {saving ? <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" /> : <Save className="w-3 h-3" />}
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
                    className={`w-7 h-7 rounded-md flex items-center justify-center transition-colors motion-reduce:transition-none ${
                      alert.enabled 
                        ? 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary' 
                        : 'bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-secondary'
                    }`}
                  >
                    <Bell className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <p className={`${textStyles.subtitle} ${alert.enabled ? '' : 'text-lia-text-secondary'}`}>
                      {alert.name}
                    </p>
                    <p className={textStyles.description}>{alert.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <select
                    value={alert.channel}
                    onChange={(e) => handleChangeChannel(alert.id, e.target.value as 'email' | 'teams' | 'both')}
                    disabled={!isEditingAlerts || !alert.enabled}
                    className={`${textStyles.caption} border border-lia-border-subtle rounded-md px-2 py-1 bg-lia-bg-primary dark:bg-lia-bg-elevated disabled:bg-lia-bg-secondary dark:disabled:bg-lia-btn-primary-hover disabled:text-lia-text-secondary dark:disabled:text-lia-text-tertiary dark:border-lia-border-default`}
                  >
                    <option value="email">Email</option>
                    <option value="teams">Teams</option>
                    <option value="both">Ambos</option>
                  </select>
                  <button
                    onClick={() => isEditingAlerts && handleToggleAlert(alert.id)}
                    disabled={!isEditingAlerts}
                    className={`relative w-10 h-5 rounded-full transition-colors motion-reduce:transition-none disabled:opacity-60 ${alert.enabled ? 'bg-lia-btn-primary-bg' : 'bg-lia-border-subtle'}`}
                  >
                    <span className={`absolute top-0.5 w-4 h-4 bg-lia-bg-primary rounded-full transition-transform motion-reduce:transition-none ${
                      alert.enabled ? 'left-5' : 'left-0.5'
                    }`} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className={cardStyles.default}>
        <CardHeader className="pb-2">
          <CardTitle className={`${textStyles.h3} flex items-center gap-2`}>
            <MessageSquare className="w-3.5 h-3.5 text-lia-text-secondary" />
            Frequência do Briefing da LIA
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => setBriefingFrequency('twice_daily')}
              disabled={!isEditingAlerts}
              className={`p-2.5 rounded-md border-2 transition-colors motion-reduce:transition-none text-left ${!isEditingAlerts ? 'opacity-60 cursor-not-allowed' : ''} ${
                briefingFrequency === 'twice_daily'
                  ? 'border-lia-btn-primary-bg dark:border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-primary'
                  : 'border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary'
              }`}
            >
              <div className="flex items-center gap-1.5 mb-0.5">
                <RefreshCw className="w-3 h-3 text-lia-text-secondary" />
                <span className={textStyles.subtitle}>2x ao Dia</span>
              </div>
              <p className={textStyles.description}>Resumo às 8h e às 14h</p>
            </button>
            <button
              onClick={() => setBriefingFrequency('daily')}
              disabled={!isEditingAlerts}
              className={`p-2.5 rounded-md border-2 transition-colors motion-reduce:transition-none text-left ${!isEditingAlerts ? 'opacity-60 cursor-not-allowed' : ''} ${
                briefingFrequency === 'daily'
                  ? 'border-lia-btn-primary-bg dark:border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-primary'
                  : 'border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary'
              }`}
            >
              <div className="flex items-center gap-1.5 mb-0.5">
                <Clock className="w-3 h-3 text-lia-text-secondary" />
                <span className={textStyles.subtitle}>Diário</span>
              </div>
              <p className={textStyles.description}>Resumo todas as manhãs às 8h</p>
            </button>
            <button
              onClick={() => setBriefingFrequency('weekly')}
              disabled={!isEditingAlerts}
              className={`p-2.5 rounded-md border-2 transition-colors motion-reduce:transition-none text-left ${!isEditingAlerts ? 'opacity-60 cursor-not-allowed' : ''} ${
                briefingFrequency === 'weekly'
                  ? 'border-lia-btn-primary-bg dark:border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-primary'
                  : 'border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary'
              }`}
            >
              <div className="flex items-center gap-1.5 mb-0.5">
                <Calendar className="w-3 h-3 text-lia-text-secondary" />
                <span className={textStyles.subtitle}>Semanal</span>
              </div>
              <p className={textStyles.description}>Resumo toda segunda-feira</p>
            </button>
            <button
              onClick={() => setBriefingFrequency('monthly')}
              disabled={!isEditingAlerts}
              className={`p-2.5 rounded-md border-2 transition-colors motion-reduce:transition-none text-left ${!isEditingAlerts ? 'opacity-60 cursor-not-allowed' : ''} ${
                briefingFrequency === 'monthly'
                  ? 'border-lia-btn-primary-bg dark:border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-primary'
                  : 'border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary'
              }`}
            >
              <div className="flex items-center gap-1.5 mb-0.5">
                <Calendar className="w-3 h-3 text-lia-text-secondary" />
                <span className={textStyles.subtitle}>Mensal</span>
              </div>
              <p className={textStyles.description}>Resumo no 1º dia útil do mês</p>
            </button>
          </div>

          <div className="rounded-xl p-2.5 bg-lia-bg-tertiary dark:bg-lia-bg-secondary dark:bg-lia-bg-secondary border border-lia-border-default dark:border-lia-border-default">
            <div className="flex items-start gap-2">
              <Brain className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-wedo-cyan" />
              <div>
                <p className={`${textStyles.subtitle} text-lia-text-primary`}>A LIA aprende com você</p>
                <p className={`${textStyles.description} mt-0.5`}>
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
