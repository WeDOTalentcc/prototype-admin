"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Bell, Edit, Save, Clock, Calendar,
  AlertCircle, CheckCircle,
  Brain, MessageSquare, RefreshCw, Loader2
} from "lucide-react"
import { textStyles, cardStyles, badgeStyles, buttonStyles } from '@/lib/design-tokens'
import type { UseGoalsPlanningHubReturn } from "./useGoalsPlanningHub"
import { useTranslations } from "next-intl"

interface AlertsSectionProps {
  hub: UseGoalsPlanningHubReturn
}

export function AlertsSection({ hub }: AlertsSectionProps) {
  const t = useTranslations('settings.alerts')
  const {
    alerts, briefingFrequency, setBriefingFrequency,
    saving, error, successMessage,
    isEditingAlerts, setIsEditingAlerts,
    saveAlertsConfig,
    handleToggleAlert, handleChangeChannel,
  } = hub

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
                {t('title')}
              </CardTitle>
              <p className={`${textStyles.description} mt-1`}>
                {t('description')}
              </p>
            </div>
            {!isEditingAlerts ? (
              <button
                onClick={() => setIsEditingAlerts(true)}
                className={buttonStyles.outline}
              >
                <Edit className="w-3 h-3" />
                {t('edit')}
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsEditingAlerts(false)}
                  className={buttonStyles.secondary}
                >
                  {t('cancel')}
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
                  {t('saveChanges')}
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
                    <option value="email">{t('channelEmail')}</option>
                    <option value="teams">{t('channelTeams')}</option>
                    <option value="both">{t('channelBoth')}</option>
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
            {t('briefingTitle')}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <BriefingOption
              value="twice_daily"
              current={briefingFrequency}
              disabled={!isEditingAlerts}
              onClick={() => setBriefingFrequency('twice_daily')}
              icon={<RefreshCw className="w-3 h-3 text-lia-text-secondary" />}
              label={t('twiceDaily')}
              description={t('twiceDailyDesc')}
            />
            <BriefingOption
              value="daily"
              current={briefingFrequency}
              disabled={!isEditingAlerts}
              onClick={() => setBriefingFrequency('daily')}
              icon={<Clock className="w-3 h-3 text-lia-text-secondary" />}
              label={t('daily')}
              description={t('dailyDesc')}
            />
            <BriefingOption
              value="weekly"
              current={briefingFrequency}
              disabled={!isEditingAlerts}
              onClick={() => setBriefingFrequency('weekly')}
              icon={<Calendar className="w-3 h-3 text-lia-text-secondary" />}
              label={t('weekly')}
              description={t('weeklyDesc')}
            />
            <BriefingOption
              value="monthly"
              current={briefingFrequency}
              disabled={!isEditingAlerts}
              onClick={() => setBriefingFrequency('monthly')}
              icon={<Calendar className="w-3 h-3 text-lia-text-secondary" />}
              label={t('monthly')}
              description={t('monthlyDesc')}
            />
          </div>

          <div className="rounded-xl p-2.5 bg-lia-bg-tertiary dark:bg-lia-bg-secondary dark:bg-lia-bg-secondary border border-lia-border-default dark:border-lia-border-default">
            <div className="flex items-start gap-2">
              <Brain className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-wedo-cyan" />
              <div>
                <p className={`${textStyles.subtitle} text-lia-text-primary`}>{t('liaLearns')}</p>
                <p className={`${textStyles.description} mt-0.5`}>
                  {t('liaLearnsDesc')}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

interface BriefingOptionProps {
  value: string
  current: string
  disabled: boolean
  onClick: () => void
  icon: React.ReactNode
  label: string
  description: string
}

function BriefingOption({ value, current, disabled, onClick, icon, label, description }: BriefingOptionProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`p-2.5 rounded-md border-2 transition-colors motion-reduce:transition-none text-left ${disabled ? 'opacity-60 cursor-not-allowed' : ''} ${
        current === value
          ? 'border-lia-btn-primary-bg dark:border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-primary'
          : 'border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary'
      }`}
    >
      <div className="flex items-center gap-1.5 mb-0.5">
        {icon}
        <span className={textStyles.subtitle}>{label}</span>
      </div>
      <p className={textStyles.description}>{description}</p>
    </button>
  )
}
