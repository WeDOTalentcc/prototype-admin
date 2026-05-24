"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { InteractiveSurface } from "@/components/ui/interactive-surface"
import { ChevronDown, ChevronRight, Loader2, Gauge } from "lucide-react"
import type { RecruitmentStage } from "./recruitment-journey.types"
import { apiFetch } from "@/lib/api/api-fetch"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"

interface SaturationSettings {
  threshold_web: number
  threshold_sourcing: number
  unlock_increment: number
  unlock_hours: number
}

const DEFAULT_SATURATION: SaturationSettings = {
  threshold_web: 20,
  threshold_sourcing: 20,
  unlock_increment: 10,
  unlock_hours: 24,
}

export function SaturationControlPanel({ stage, isEditMode }: { stage: RecruitmentStage; isEditMode: boolean }) {
  const t = useTranslations("settings.recruitment.saturation")
  const [expanded, setExpanded] = React.useState(false)
  const [settings, setSettings] = React.useState<SaturationSettings>(DEFAULT_SATURATION)
  const [loading, setLoading] = React.useState(false)
  const [saving, setSaving] = React.useState(false)
  const [loaded, setLoaded] = React.useState(false)
  const [dirty, setDirty] = React.useState(false)

  const isScreening = stage.name === 'screening' || stage.action_behavior === 'screening'
  if (!isScreening) return null

  const handleExpand = () => {
    if (!expanded && !loaded) {
      setLoading(true)
      apiFetch('/api/backend-proxy/settings/saturation')
        .then(r => r.ok ? r.json() : null)
        .then(data => {
          if (data) {
            setSettings({
              threshold_web: data.threshold_web ?? DEFAULT_SATURATION.threshold_web,
              threshold_sourcing: data.threshold_sourcing ?? DEFAULT_SATURATION.threshold_sourcing,
              unlock_increment: data.unlock_increment ?? DEFAULT_SATURATION.unlock_increment,
              unlock_hours: data.unlock_hours ?? DEFAULT_SATURATION.unlock_hours,
            })
          }
          setLoaded(true)
        })
        .catch(() => { setLoaded(true) })
        .finally(() => setLoading(false))
    }
    setExpanded(v => !v)
  }

  const handleChange = (field: keyof SaturationSettings, value: number) => {
    setSettings(prev => ({ ...prev, [field]: value }))
    setDirty(true)
  }

  const handleSave = () => {
    setSaving(true)
    apiFetch('/api/backend-proxy/settings/saturation', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    })
      .then(r => {
        if (r.ok) {
          setDirty(false)
          notifyChatOfSettingsUpdate({
            actionId: "configure_saturation",
            section: "saturation",
          })
        }
      })
      .catch((err) => { console.warn('[SaturationControlPanel] settings save failed', err) })
      .finally(() => setSaving(false))
  }

  const inputClassName = "w-full px-2 py-1.5 text-xs text-lia-text-primary border border-lia-border-subtle dark:border-lia-border-default rounded-md bg-lia-bg-primary dark:bg-lia-bg-secondary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg dark:focus:ring-lia-border-subtle focus:border-transparent transition-opacity motion-reduce:transition-none disabled:opacity-50"

  return (
    <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle mt-3 pt-2" data-testid="saturation-control-panel">
      <InteractiveSurface
        variant="accordion"
        onClick={handleExpand}
        className="flex items-center gap-1.5 justify-start text-xs text-lia-text-secondary hover:text-lia-text-primary !bg-transparent hover:!bg-transparent"
        aria-expanded={expanded}
        data-testid="saturation-control-toggle"
      >
        {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        <Gauge className="h-3.5 w-3.5" />
        <span className="font-medium">{t("title")}</span>
      </InteractiveSurface>

      {expanded && (
        <div className="mt-2 space-y-3" role="status" aria-live="polite" aria-label={t("loading")}>
          {loading && (
            <div className="flex items-center gap-2 px-1 py-2" role="status" aria-live="polite" aria-label={t("loading")}>
              <Loader2 className="h-3.5 w-3.5 animate-spin motion-reduce:animate-none text-lia-text-tertiary" />
              <span className="text-xs text-lia-text-tertiary">{t("loading")}</span>
            </div>
          )}

          {!loading && (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <Label className="text-xs text-lia-text-secondary">
                    {t("thresholdWeb")}
                  </Label>
                  <input
                    type="number"
                    data-field="threshold_web"
                    data-testid="saturation-threshold-web"
                    value={settings.threshold_web}
                    onChange={(e) => handleChange('threshold_web', parseInt(e.target.value) || 0)}
                    disabled={!isEditMode}
                    min={1}
                    max={999}
                    className={inputClassName}
                  />
                </div>

                <div className="flex flex-col gap-1">
                  <Label className="text-xs text-lia-text-secondary">
                    {t("thresholdSourcing")}
                  </Label>
                  <input
                    type="number"
                    data-field="threshold_sourcing"
                    data-testid="saturation-threshold-sourcing"
                    value={settings.threshold_sourcing}
                    onChange={(e) => handleChange('threshold_sourcing', parseInt(e.target.value) || 0)}
                    disabled={!isEditMode}
                    min={1}
                    max={999}
                    className={inputClassName}
                  />
                </div>

                <div className="flex flex-col gap-1">
                  <Label className="text-xs text-lia-text-secondary">
                    {t("unlockIncrement")}
                  </Label>
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-lia-text-tertiary">+</span>
                    <input
                      type="number"
                      data-field="unlock_increment"
                      data-testid="saturation-unlock-increment"
                      value={settings.unlock_increment}
                      onChange={(e) => handleChange('unlock_increment', parseInt(e.target.value) || 0)}
                      disabled={!isEditMode}
                      min={1}
                      max={100}
                      className={inputClassName}
                    />
                  </div>
                </div>

                <div className="flex flex-col gap-1">
                  <Label className="text-xs text-lia-text-secondary">
                    {t("unlockHours")}
                  </Label>
                  <div className="flex items-center gap-1.5">
                    <input
                      type="number"
                      data-field="unlock_hours"
                      data-testid="saturation-unlock-hours"
                      value={settings.unlock_hours}
                      onChange={(e) => handleChange('unlock_hours', parseInt(e.target.value) || 0)}
                      disabled={!isEditMode}
                      min={1}
                      max={168}
                      className={inputClassName}
                    />
                    <span className="text-xs text-lia-text-tertiary whitespace-nowrap">{t("hours")}</span>
                  </div>
                </div>
              </div>

              {isEditMode && dirty && (
                <div className="flex justify-end">
                  <Button
                    data-testid="saturation-save"
                    size="sm"
                    onClick={handleSave}
                    disabled={saving}
                    className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active rounded-md px-3 py-1 text-xs font-medium"
                  >
                    {saving ? (
                      <>
                        <Loader2 className="h-3 w-3 animate-spin motion-reduce:animate-none mr-1" />
                        {t("saving")}
                      </>
                    ) : (
                      t("saveSaturation")
                    )}
                  </Button>
                </div>
              )}

              <p className="text-micro text-lia-text-tertiary px-1" aria-live="polite" aria-atomic="true">
                {t("helpText")}
              </p>
            </>
          )}
        </div>
      )}
    </div>
  )
}
