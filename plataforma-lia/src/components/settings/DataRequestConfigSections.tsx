"use client"

import React from"react"
import { useTranslations } from "next-intl"
import { Chip } from "@/components/ui/chip"
import { Switch } from"@/components/ui/switch"
import { Label } from"@/components/ui/label"
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from"@/components/ui/select"
import { Shield, Bell, Clock, AlertCircle } from"lucide-react"
import type { DataRequestConfig } from"@/hooks/company/use-data-request-config"

function MessageField({ label, value, isEditing, onChange, rows }: {
  label: string
  value: string
  isEditing: boolean
  onChange: (v: string) => void
  rows: number
}) {
  return (
    <div>
      <Label className="text-micro text-lia-text-secondary mb-1 block">{label}</Label>
      {isEditing ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={rows}
          className="w-full px-2 py-1.5 text-xs border border-lia-border-default dark:border-lia-border-default rounded-xl focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
        />
      ) : (
        <p className="text-xs text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary p-2 rounded-xl whitespace-pre-wrap">
          {value}
        </p>
      )}
    </div>
  )
}

interface GeneralSettingsProps {
  config: DataRequestConfig
  isEditing: boolean
  updateGeneralConfig: (updates: Record<string, unknown>) => void
}

export function GeneralSettingsContent({ config, isEditing, updateGeneralConfig }: GeneralSettingsProps) {
  const t = useTranslations("settings.dataRequest")
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      <div className="flex items-center justify-between p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
        <div className="flex items-center gap-2">
          <Shield className="w-3.5 h-3.5 text-lia-text-secondary" />
          <div>
            <Label className="text-xs font-medium text-lia-text-primary">{t("otpRequired")}</Label>
            <p className="text-micro text-lia-text-secondary">{t("otpDesc")}</p>
          </div>
        </div>
        {isEditing ? (
          <Switch checked={config.otpRequired} onCheckedChange={(checked: boolean) => updateGeneralConfig({ otpRequired: checked })} />
        ) : (
          <Chip variant="neutral" muted className="text-micro">{config.otpRequired ? t("active") : t("inactive")}</Chip>
        )}
      </div>

      <div className="flex items-center justify-between p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
        <div className="flex items-center gap-2">
          <Bell className="w-3.5 h-3.5 text-lia-text-secondary" />
          <div>
            <Label className="text-xs font-medium text-lia-text-primary">{t("autoReminders")}</Label>
            <p className="text-micro text-lia-text-secondary">{t("autoRemindersDesc")}</p>
          </div>
        </div>
        {isEditing ? (
          <Switch checked={config.autoReminders} onCheckedChange={(checked: boolean) => updateGeneralConfig({ autoReminders: checked })} />
        ) : (
          <Chip variant="neutral" muted className="text-micro">{config.autoReminders ? t("active") : t("inactive")}</Chip>
        )}
      </div>

      <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
        <div className="flex items-center gap-2 mb-2">
          <Clock className="w-3.5 h-3.5 text-lia-text-secondary" />
          <Label className="text-xs font-medium text-lia-text-primary">{t("expirationDays")}</Label>
        </div>
        {isEditing ? (
          <Select value={config.expirationDays.toString()} onValueChange={(value) => updateGeneralConfig({ expirationDays: parseInt(value) })}>
            <SelectTrigger className="w-full h-8 text-xs"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="3">3 {t("days")}</SelectItem>
              <SelectItem value="7">7 {t("days")}</SelectItem>
              <SelectItem value="14">14 {t("days")}</SelectItem>
              <SelectItem value="30">30 {t("days")}</SelectItem>
            </SelectContent>
          </Select>
        ) : (
          <p className="text-xs font-medium text-lia-text-primary">{config.expirationDays} {t("days")}</p>
        )}
      </div>

      {config.autoReminders && (
        <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
          <div className="flex items-center gap-2 mb-2">
            <Bell className="w-3.5 h-3.5 text-lia-text-secondary" />
            <Label className="text-xs font-medium text-lia-text-primary">{t("sendReminderAfter")}</Label>
          </div>
          {isEditing ? (
            <Select value={config.reminderDays.toString()} onValueChange={(value) => updateGeneralConfig({ reminderDays: parseInt(value) })}>
              <SelectTrigger className="w-full h-8 text-xs"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="1">1 {t("day")}</SelectItem>
                <SelectItem value="2">2 {t("days")}</SelectItem>
                <SelectItem value="3">3 {t("days")}</SelectItem>
                <SelectItem value="5">5 {t("days")}</SelectItem>
              </SelectContent>
            </Select>
          ) : (
            <p className="text-xs font-medium text-lia-text-primary">{config.reminderDays} {t("daysPlural")}</p>
          )}
        </div>
      )}
    </div>
  )
}

interface LgpdSectionProps {
  config: DataRequestConfig
  isEditing: boolean
  updateLgpdConfig: (updates: Partial<DataRequestConfig['lgpd']>) => void
}

export function LgpdSectionContent({ config, isEditing, updateLgpdConfig }: LgpdSectionProps) {
  const t = useTranslations("settings.dataRequest")
  return (
    <div className="space-y-4">
      <div className="p-3 bg-status-warning/10 dark:bg-status-warning/20 border border-status-warning/30 dark:border-status-warning/30 rounded-xl">
        <div className="flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-status-warning mt-0.5 flex-shrink-0" />
          <p className="text-micro text-status-warning dark:text-status-warning" aria-live="polite" aria-atomic="true">
            {t("lgpdWarning")}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
          <div className="flex items-center justify-between mb-2">
            <Label className="text-xs font-medium text-lia-text-primary">{t("requireConsent")}</Label>
            {isEditing ? (
              <Switch checked={config.lgpd.requireConsent} onCheckedChange={(checked: boolean) => updateLgpdConfig({ requireConsent: checked })} />
            ) : (
              <Chip variant="neutral" muted className="text-micro">{config.lgpd.requireConsent ? t("required") : t("disabled")}</Chip>
            )}
          </div>
          <p className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">{t("consentDesc")}</p>
        </div>

        <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
          <div className="flex items-center justify-between mb-2">
            <Label className="text-xs font-medium text-lia-text-primary">{t("allowDeletion")}</Label>
            {isEditing ? (
              <Switch checked={config.lgpd.allowDataDeletion} onCheckedChange={(checked: boolean) => updateLgpdConfig({ allowDataDeletion: checked })} />
            ) : (
              <Chip variant="neutral" muted className="text-micro">{config.lgpd.allowDataDeletion ? t("enabled") : t("disabled")}</Chip>
            )}
          </div>
          <p className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">{t("deletionDesc")}</p>
        </div>
      </div>

      <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
        <Label className="text-xs font-medium text-lia-text-primary mb-2 block">{t("dataRetention")}</Label>
        {isEditing ? (
          <div className="flex items-center gap-2">
            <input
              type="number"
              value={config.lgpd.dataRetentionDays}
              onChange={(e) => updateLgpdConfig({ dataRetentionDays: parseInt(e.target.value) || 365 })}
              min={30}
              max={1825}
              className="w-20 px-2 py-1 text-xs border border-lia-border-default dark:border-lia-border-default rounded-xl focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-primary text-lia-text-primary"
            />
            <span className="text-micro text-lia-text-secondary">{t("daysAfterProcess")}</span>
          </div>
        ) : (
          <p className="text-xs text-lia-text-secondary">{config.lgpd.dataRetentionDays} {t("daysAfterProcess")}</p>
        )}
      </div>

      <MessageField label={t("consentMessage")} value={config.lgpd.consentMessage} isEditing={isEditing} onChange={(v) => updateLgpdConfig({ consentMessage: v })} rows={4} />
      <MessageField label={t("disclaimerPortal")} value={config.lgpd.disclaimerText} isEditing={isEditing} onChange={(v) => updateLgpdConfig({ disclaimerText: v })} rows={3} />
    </div>
  )
}


 
export function CollectionModelContent(_props: Record<string, any>) {
  return null
}
