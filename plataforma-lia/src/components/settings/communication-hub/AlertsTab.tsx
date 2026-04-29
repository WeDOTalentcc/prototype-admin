import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Edit, Save, Bell, Clock, Calendar, RefreshCw, Brain, Loader2, AlertCircle, CheckCircle, MessageSquare, BarChart3 } from "lucide-react"
import { useTranslations } from "next-intl"
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
  const t = useTranslations("settings.communication")
  return (
    <div className="space-y-4">
      {successMessage && (
        <div className="px-2 py-1.5 rounded-xl flex items-center gap-2 bg-status-success/15 border border-status-success/30 text-status-success dark:bg-status-success dark:border-status-success/30 dark:text-status-success">
          <CheckCircle className="w-3.5 h-3.5 text-status-success dark:text-status-success" />
          <span className="text-xs">{successMessage}</span>
        </div>
      )}
      {error && (
        <div className="bg-status-error/10 border border-status-error/30 text-status-error px-2 py-1.5 rounded-xl flex items-center gap-2">
          <AlertCircle className="w-3.5 h-3.5" />
          <span className="text-xs">{error}</span>
        </div>
      )}
      <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-lia-bg-primary/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-xl">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
                <Bell className="w-3.5 h-3.5 text-lia-text-secondary" />
                {t("alertsSection.title")}
              </CardTitle>
              <p className="text-xs text-lia-text-secondary mt-0.5">
                {t("alertsSection.subtitle")}
              </p>
            </div>
            {!isEditingAlerts ? (
              <button onClick={() => setIsEditingAlerts(true)} className={actionButtonStyles.smOutline}>
                <Edit className={actionButtonStyles.icon} />
                {t("common.edit")}
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <button onClick={() => setIsEditingAlerts(false)} className={actionButtonStyles.smSecondary}>
                  {t("common.cancel")}
                </button>
                <button
                  onClick={async () => { await saveAlertsConfig(); setIsEditingAlerts(false) }}
                  disabled={savingAlerts}
                  className={actionButtonStyles.smPrimary}
                >
                  {savingAlerts ? <Loader2 className={actionButtonStyles.icon} /> : <Save className={actionButtonStyles.icon} />}
                  {t("common.saveChanges")}
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
                    <option value="email">{t("alertsSection.channelEmail")}</option>
                    <option value="teams">{t("alertsSection.channelTeams")}</option>
                    <option value="both">{t("alertsSection.channelBoth")}</option>
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

      <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-lia-bg-primary/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-xl">
        <CardHeader className="pb-2">
          <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
            <MessageSquare className="w-3.5 h-3.5 text-lia-text-secondary" />
            {t("alertsSection.briefingTitle")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-2">
            {([
              { key: 'twice_daily' as const, label: t("alertsSection.briefingTwiceDaily"), desc: t("alertsSection.briefingTwiceDailyDesc"), icon: RefreshCw },
              { key: 'daily' as const, label: t("alertsSection.briefingDaily"), desc: t("alertsSection.briefingDailyDesc"), icon: Clock },
              { key: 'weekly' as const, label: t("alertsSection.briefingWeekly"), desc: t("alertsSection.briefingWeeklyDesc"), icon: Calendar },
              { key: 'monthly' as const, label: t("alertsSection.briefingMonthly"), desc: t("alertsSection.briefingMonthlyDesc"), icon: Calendar },
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
                <p className={`${textStyles.subtitle} text-lia-text-primary`}>{t("alertsSection.liaLearnsTitle")}</p>
                <p className="text-xs text-lia-text-secondary mt-0.5">
                  {t("alertsSection.liaLearnsDesc")}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-lia-bg-primary/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-xl">
        <CardHeader className="pb-2">
          <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
            <BarChart3 className="w-3.5 h-3.5 text-lia-text-secondary" />
            {t("alertsSection.weeklyDigestTitle")}
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
                    {t("alertsSection.weeklyInsightsTitle")}
                  </p>
                  <p className="text-xs text-lia-text-secondary mt-0.5">
                    {t("alertsSection.weeklyInsightsDesc")}
                  </p>
                </div>
              </div>
              <button
                onClick={handleToggleWeeklyDigest}
                disabled={savingWeeklyDigest}
                role="switch"
                aria-checked={weeklyDigestEnabled}
                aria-label={t("alertsSection.weeklyDigestToggle")}
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
            <span>{t("alertsSection.deliveryNote")}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
