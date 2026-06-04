/**
 * AlertPreferencesPanel — canonical UI per ADR-WT-2025 Sprint D (2026-05-22).
 *
 * Substitui AlertsTab.tsx (legacy AlertConfig). Lê e escreve AlertPreference
 * via `useAlertPreferences()` hook canonical. Single source of truth para
 * configuração de alertas DESTE recrutador (per-user, isolado per-tenant).
 *
 * Ownership (P1-10 audit 2026-05-26): AlertPreference table tem company_id E
 * user_id como NOT NULL (composite index). Cada recrutador tem suas próprias
 * preferências; outros recrutadores da mesma company NÃO veem essas
 * configurações. Auditoria considerou mover este panel pra /profile/notifications
 * (mais alinhado com per-user mental model), mas mantido em Configurações por
 * compat com fluxo atual. Decisão de migração pra /profile fica como P2 futuro.
 *
 * Multi-tenancy: nenhum input de `company_id` ou `user_id` (Pydantic REGRA 2 —
 * JWT-only no backend via `Depends(require_company_id)` + user_id do token).
 *
 * Design tokens canonical (00-design-system-v4.2.2.md) — sem cores hardcoded.
 * Rules of Hooks: TODOS os hooks no topo (lição BulkImportModal 2026-05-04).
 *
 * REGRA 4 (anti silent-fallback): erros explícitos via UI banner, sem mascarar
 * com toast efêmero quando o save falha.
 */
"use client"

import React, { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  AlertCircle,
  Bell,
  CheckCircle,
  Loader2,
  Save,
} from "lucide-react"
import { useTranslations } from "next-intl"
import { textStyles, actionButtonStyles } from "@/lib/design-tokens"
import {
  useAlertPreferences,
  type AlertPreference,
  type AlertPreferenceChannel,
  type AlertPreferenceUpdate,
} from "@/hooks/settings/use-alert-preferences"

const CHANNEL_OPTIONS: ReadonlyArray<{ value: AlertPreferenceChannel; labelKey: string }> = [
  { value: "email", labelKey: "channelEmail" },
  { value: "bell", labelKey: "channelInApp" },
  { value: "teams", labelKey: "channelTeams" },
  { value: "whatsapp", labelKey: "channelWhatsapp" },
]

const THRESHOLD_UNITS = ["count", "hours", "days", "percent"] as const
type ThresholdUnit = (typeof THRESHOLD_UNITS)[number]

function inferThresholdUnit(alertType: string): ThresholdUnit {
  // Heurística canonical baseada no catálogo DEFAULT_ALERT_PREFERENCES backend.
  if (alertType.includes("rate") || alertType.includes("percent") || alertType === "credits_low") return "percent"
  if (alertType.includes("hours") || alertType === "interview_not_confirmed" || alertType === "sla_near_expiration") return "hours"
  if (alertType === "candidate_no_interaction" || alertType === "workforce_plan_stale") return "days"
  return "count"
}

// Sprint D: panel se auto-gerencia — zero props.
export function AlertPreferencesPanel() {
  const t = useTranslations("settings.communication")
  const { preferences, isLoading, error: loadError, updatePreference } = useAlertPreferences()
  const [savingId, setSavingId] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [successFor, setSuccessFor] = useState<string | null>(null)

  async function handleUpdate(
    pref: AlertPreference,
    updates: AlertPreferenceUpdate
  ) {
    setSavingId(pref.id ?? pref.alert_type)
    setSaveError(null)
    try {
      await updatePreference(pref, updates)
      setSuccessFor(pref.alert_type)
      // Auto-clear success após 2.5s. REGRA 4: erro NÃO auto-limpa.
      setTimeout(() => setSuccessFor((cur) => (cur === pref.alert_type ? null : cur)), 2500)
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Erro desconhecido ao salvar"
      setSaveError(msg)
    } finally {
      setSavingId(null)
    }
  }

  return (
    <div className="space-y-4" data-component="alert-preferences-panel">
      {/* Success banner */}
      {successFor && (
        <div
          className="px-2 py-1.5 rounded-full flex items-center gap-2 bg-status-success/15 border border-status-success/30 text-status-success"
          role="status"
        >
          <CheckCircle className="w-3.5 h-3.5" />
          <span className="text-xs">{t("alertPreferences.saved")}</span>
        </div>
      )}

      {/* Error banner — explicit per REGRA 4 (no silent fallback) */}
      {(loadError || saveError) && (
        <div
          className="bg-status-error/10 border border-status-error/30 text-status-error px-2 py-1.5 rounded-full flex items-center gap-2"
          role="alert"
          data-testid="alert-preferences-error"
        >
          <AlertCircle className="w-3.5 h-3.5" />
          <span className="text-xs">
            {loadError ?? saveError}
          </span>
        </div>
      )}

      <Card className="border border-lia-border-subtle/50 bg-lia-bg-primary/80 backdrop-blur-sm rounded-xl">
        <CardHeader className="pb-2">
          <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
            <Bell className="w-3.5 h-3.5 text-lia-text-secondary" />
            {t("alertPreferences.title")}
          </CardTitle>
          <p className="text-xs text-lia-text-secondary mt-0.5">
            {t("alertPreferences.subtitle")}
          </p>
        </CardHeader>

        <CardContent className="space-y-2">
          {isLoading && (
            <div
              className="flex items-center gap-2 text-xs text-lia-text-secondary py-4 justify-center"
              data-testid="alert-preferences-loading"
            >
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              {t("alertPreferences.loading")}
            </div>
          )}

          {!isLoading && preferences.length === 0 && !loadError && (
            <div className="text-xs text-lia-text-secondary py-4 text-center">
              {t("alertPreferences.empty")}
            </div>
          )}

          {!isLoading && preferences.map((pref) => {
            const unit = inferThresholdUnit(pref.alert_type)
            const isSaving = savingId === (pref.id ?? pref.alert_type)
            return (
              <div
                key={pref.id ?? pref.alert_type}
                data-component="alert-preference-card"
                data-alert-type={pref.alert_type}
                className={`p-2.5 rounded-md border transition-colors motion-reduce:transition-none ${
                  pref.is_enabled
                    ? "bg-lia-bg-primary border-lia-border-subtle"
                    : "bg-lia-bg-secondary border-lia-border-subtle"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start gap-2 min-w-0">
                    <div className="w-7 h-7 rounded-md flex items-center justify-center bg-lia-bg-secondary text-lia-text-secondary">
                      <Bell className="w-3.5 h-3.5" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-medium text-lia-text-primary truncate">
                        {pref.name ?? pref.alert_type}
                      </p>
                      {pref.description && (
                        <p className="text-xs text-lia-text-secondary mt-0.5">
                          {pref.description}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-wrap justify-end">
                    {/* Threshold input */}
                    <div className="flex items-center gap-1">
                      <input
                        type="number"
                        min={0}
                        max={1000000}
                        value={pref.threshold ?? 0}
                        onChange={(e) => {
                          const next = Number(e.target.value)
                          if (Number.isFinite(next) && next >= 0) {
                            handleUpdate(pref, { threshold: next })
                          }
                        }}
                        disabled={isSaving || !pref.is_enabled}
                        className="text-micro w-16 border border-lia-border-subtle rounded-md px-1.5 py-1 bg-lia-bg-primary text-lia-text-primary disabled:opacity-60"
                        data-field="threshold"
                        data-testid={`alert-pref-threshold-${pref.alert_type}`}
                        aria-label={t("alertPreferences.thresholdAria", { type: pref.alert_type })}
                      />
                      <span className="text-micro text-lia-text-secondary" data-field="threshold_unit">
                        {t(`alertPreferences.unit.${unit}`)}
                      </span>
                    </div>

                    {/* Cooldown hours */}
                    <input
                      type="number"
                      min={1}
                      max={720}
                      value={pref.cooldown_hours ?? 24}
                      onChange={(e) => {
                        const next = Number(e.target.value)
                        if (Number.isFinite(next) && next >= 1 && next <= 720) {
                          handleUpdate(pref, { cooldown_hours: next })
                        }
                      }}
                      disabled={isSaving || !pref.is_enabled}
                      className="text-micro w-16 border border-lia-border-subtle rounded-md px-1.5 py-1 bg-lia-bg-primary text-lia-text-primary disabled:opacity-60"
                      data-field="cooldown_hours"
                      data-testid={`alert-pref-cooldown-${pref.alert_type}`}
                      aria-label={t("alertPreferences.cooldownAria", { type: pref.alert_type })}
                    />

                    {/* Channels multi-select via chips */}
                    <div className="flex items-center gap-1" data-field="channels">
                      {CHANNEL_OPTIONS.map((ch) => {
                        const checked = pref.channels[ch.value]
                        return (
                          <button
                            key={ch.value}
                            type="button"
                            onClick={() =>
                              handleUpdate(pref, {
                                channels: { ...pref.channels, [ch.value]: !checked },
                              })
                            }
                            disabled={isSaving || !pref.is_enabled}
                            data-channel={ch.value}
                            data-testid={`alert-pref-channel-${pref.alert_type}-${ch.value}`}
                            aria-pressed={checked}
                            aria-label={t(`alertPreferences.${ch.labelKey}`)}
                            className={`text-micro rounded-full px-2 py-0.5 border transition-colors motion-reduce:transition-none disabled:opacity-60 ${
                              checked
                                ? "bg-lia-text-secondary text-lia-bg-primary border-lia-text-secondary"
                                : "bg-lia-bg-primary text-lia-text-secondary border-lia-border-subtle"
                            }`}
                          >
                            {t(`alertPreferences.${ch.labelKey}`)}
                          </button>
                        )
                      })}
                    </div>

                    {/* Enable toggle — keep last so it remains visually anchored */}
                    <button
                      type="button"
                      onClick={() =>
                        handleUpdate(pref, { is_enabled: !pref.is_enabled })
                      }
                      disabled={isSaving}
                      role="switch"
                      aria-checked={pref.is_enabled}
                      aria-label={t("alertPreferences.toggleAria", { type: pref.alert_type })}
                      data-toggle={`alert_pref_${pref.alert_type}_enabled`}
                      data-testid={`alert-pref-toggle-${pref.alert_type}`}
                      className={`relative w-9 h-5 rounded-full transition-colors motion-reduce:transition-none disabled:opacity-60 ${
                        pref.is_enabled ? "bg-lia-text-secondary" : "bg-lia-border-subtle"
                      }`}
                    >
                      <span
                        className={`absolute top-0.5 w-4 h-4 bg-lia-bg-secondary rounded-full transition-transform motion-reduce:transition-none ${
                          pref.is_enabled ? "left-4" : "left-0.5"
                        }`}
                      />
                    </button>

                    {isSaving && (
                      <Loader2 className={`${actionButtonStyles.icon} animate-spin`} />
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </CardContent>
      </Card>
    </div>
  )
}
