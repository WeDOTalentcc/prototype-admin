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
 * Redesign 2026-06-05 (UX): cada alerta vira uma frase legível ("Avisar após X
 * dias…") em vez de campos numéricos soltos; alertas são agrupados por público
 * (recrutador vs candidato) e os canais são filtrados por aplicabilidade —
 * WhatsApp só aparece em alertas enviados ao candidato. A presentação NÃO altera
 * o contrato do backend (mesmos campos threshold/cooldown_hours/channels); canais
 * não-aplicáveis simplesmente não são renderizados e seu valor armazenado é
 * preservado (sem writes-surpresa no render).
 *
 * Design tokens canonical (00-design-system-v4.2.2.md) — sem cores hardcoded.
 * Rules of Hooks: TODOS os hooks no topo (lição BulkImportModal 2026-05-04).
 *
 * REGRA 4 (anti silent-fallback): erros explícitos via UI banner, sem mascarar
 * com toast efêmero quando o save falha.
 */
"use client"

import React, { useMemo, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  AlertCircle,
  Bell,
  Calendar,
  CheckCircle,
  Loader2,
  ToggleLeft,
  UserCog,
  UserRound,
} from "lucide-react"
import { useTranslations } from "next-intl"
import { textStyles, actionButtonStyles } from "@/lib/design-tokens"
import {
  useAlertPreferences,
  useBriefingPreferences,
  type AlertPreference,
  type AlertPreferenceChannel,
  type AlertPreferenceUpdate,
  type BriefingFrequency,
} from "@/hooks/settings/use-alert-preferences"
import {
  useDigestSchedule,
  type DigestFrequency,
} from "@/hooks/settings/use-digest-schedule"

type Audience = "recruiter" | "candidate"
type ThresholdUnit = "count" | "hours" | "days" | "percent"

interface AlertMeta {
  audience: Audience
  /** Canais aplicáveis a este alerta, na ordem de exibição. */
  channels: AlertPreferenceChannel[]
  unit: ThresholdUnit
  /** Texto antes do campo numérico (compõe a frase legível). */
  before: string
  /** Texto depois do campo numérico (compõe a frase legível). */
  after: string
}

const CHANNEL_LABEL_KEY: Record<AlertPreferenceChannel, string> = {
  email: "channelEmail",
  bell: "channelInApp",
  teams: "channelTeams",
  whatsapp: "channelWhatsapp",
}

const RECRUITER_CHANNELS: AlertPreferenceChannel[] = ["email", "bell", "teams"]
const CANDIDATE_CHANNELS: AlertPreferenceChannel[] = ["email", "whatsapp"]

/**
 * Catálogo de apresentação — espelha DEFAULT_ALERT_PREFERENCES do backend
 * (lia-agent-system/app/api/v1/alerts.py). Frases em PT-BR, mesmo padrão dos
 * `name`/`description` que já vêm do backend sem i18n. WhatsApp só nos alertas
 * de público "candidate".
 */
const ALERT_META: Record<string, AlertMeta> = {
  conversion_rate_low: {
    audience: "recruiter", channels: RECRUITER_CHANNELS, unit: "percent",
    before: "Avisar quando a conversão cair abaixo de", after: "%",
  },
  sla_near_expiration: {
    audience: "recruiter", channels: RECRUITER_CHANNELS, unit: "percent",
    before: "Avisar ao atingir", after: "% do tempo de SLA na etapa",
  },
  candidate_no_interaction: {
    audience: "recruiter", channels: RECRUITER_CHANNELS, unit: "days",
    before: "Avisar após", after: "dias sem contato com o candidato",
  },
  interview_not_confirmed: {
    audience: "candidate", channels: CANDIDATE_CHANNELS, unit: "hours",
    before: "Lembrar o candidato", after: "horas antes da entrevista",
  },
  feedback_pending: {
    audience: "recruiter", channels: RECRUITER_CHANNELS, unit: "hours",
    before: "Cobrar feedback", after: "horas após a entrevista",
  },
  candidates_stagnant: {
    audience: "recruiter", channels: RECRUITER_CHANNELS, unit: "days",
    before: "Avisar quando o candidato ficar", after: "dias parado na mesma etapa",
  },
  offers_pending_long: {
    audience: "candidate", channels: CANDIDATE_CHANNELS, unit: "hours",
    before: "Avisar quando a proposta ficar", after: "horas sem resposta",
  },
  tasks_overdue: {
    audience: "recruiter", channels: RECRUITER_CHANNELS, unit: "count",
    before: "Avisar quando houver", after: "tarefas atrasadas",
  },
  email_delivery_low: {
    audience: "recruiter", channels: RECRUITER_CHANNELS, unit: "percent",
    before: "Avisar quando a entrega de e-mail cair abaixo de", after: "%",
  },
  ideal_candidate_found: {
    audience: "recruiter", channels: RECRUITER_CHANNELS, unit: "percent",
    before: "Avisar quando o match do candidato passar de", after: "%",
  },
  ats_sync_failed: {
    audience: "recruiter", channels: RECRUITER_CHANNELS, unit: "count",
    before: "Avisar após", after: "falhas de sincronização com o ATS",
  },
  company_profile_incomplete: {
    audience: "recruiter", channels: RECRUITER_CHANNELS, unit: "percent",
    before: "Avisar quando o perfil da empresa estiver abaixo de", after: "% completo",
  },
  dsr_overdue: {
    audience: "recruiter", channels: RECRUITER_CHANNELS, unit: "hours",
    before: "Avisar", after: "horas antes do prazo LGPD da solicitação",
  },
  workforce_plan_stale: {
    audience: "recruiter", channels: RECRUITER_CHANNELS, unit: "days",
    before: "Avisar após", after: "dias sem atualizar o plano de workforce",
  },
  credits_low: {
    audience: "recruiter", channels: RECRUITER_CHANNELS, unit: "percent",
    before: "Avisar quando os créditos de IA caírem abaixo de", after: "%",
  },
}

function metaFor(alertType: string): AlertMeta {
  return (
    ALERT_META[alertType] ?? {
      audience: "recruiter",
      // Tipos legados fora do catálogo: oferece todos os canais p/ não perder config.
      channels: ["email", "bell", "teams", "whatsapp"],
      unit: "count",
      before: "Avisar a partir de",
      after: "",
    }
  )
}

// Sprint D: panel se auto-gerencia — zero props.
export function AlertPreferencesPanel() {
  const t = useTranslations("settings.communication")
  const { preferences, isLoading, error: loadError, updatePreference } = useAlertPreferences()
  const [savingId, setSavingId] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [successFor, setSuccessFor] = useState<string | null>(null)

  // B1+B2: briefing frequency + digest toggle (Rules of Hooks: top, before any if/return)
  const {
    briefingFrequency,
    digestEnabled,
    isLoading: isBriefingLoading,
    isSaving: isBriefingSaving,
    saveError: briefingSaveError,
    updateBriefingFrequency,
    updateDigestEnabled,
  } = useBriefingPreferences()

  // Fatia 2 (Decisão 3): frequência per-user override (Rules of Hooks: top)
  const {
    frequency: userFrequency,
    source: userFreqSource,
    hasPersonalOverride,
    isLoading: isDigestScheduleLoading,
    setFrequency: setUserFrequency,
    resetToCompanyDefault,
    isSaving: isDigestScheduleSaving,
  } = useDigestSchedule()

  const groups = useMemo(() => {
    const recruiter: AlertPreference[] = []
    const candidate: AlertPreference[] = []
    for (const pref of preferences) {
      if (metaFor(pref.alert_type).audience === "candidate") candidate.push(pref)
      else recruiter.push(pref)
    }
    return { recruiter, candidate }
  }, [preferences])

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

  function renderCard(pref: AlertPreference) {
    const meta = metaFor(pref.alert_type)
    const isSaving = savingId === (pref.id ?? pref.alert_type)
    const unitLabel = t(`alertPreferences.unit.${meta.unit}`)

    return (
      <div
        key={pref.alert_type}
        className="rounded-xl border border-lia-border-subtle/60 bg-lia-bg-primary/60 p-3 space-y-2"
        data-testid={`alert-card-${pref.alert_type}`}
      >
        {/* Row 1: toggle + frase legível */}
        <div className="flex items-start gap-2.5">
          <button
            type="button"
            role="switch"
            aria-checked={pref.is_enabled}
            aria-label={t("alertPreferences.toggleAria", { type: pref.alert_type })}
            disabled={isSaving}
            onClick={() => handleUpdate(pref, { is_enabled: !pref.is_enabled })}
            className={`relative inline-flex h-4 w-7 shrink-0 mt-0.5 items-center rounded-full transition-colors motion-reduce:transition-none disabled:opacity-60 ${
              pref.is_enabled ? "bg-lia-accent" : "bg-lia-border-subtle"
            }`}
          >
            <span
              className={`inline-block h-3 w-3 transform rounded-full bg-white shadow-sm transition-transform motion-reduce:transition-none ${
                pref.is_enabled ? "translate-x-3.5" : "translate-x-0.5"
              }`}
            />
          </button>

          <div className="flex-1 min-w-0">
            <p className={`text-xs leading-tight ${pref.is_enabled ? "text-lia-text-primary" : "text-lia-text-secondary"}`}>
              {pref.name ?? pref.alert_type.replace(/_/g, " ")}
            </p>
            {pref.description && (
              <p className="text-micro text-lia-text-secondary mt-0.5">{pref.description}</p>
            )}
          </div>
        </div>

        {/* Row 2: threshold + cooldown + channels (só quando ativo) */}
        {pref.is_enabled && (
          <>
            {/* Frase legível com threshold */}
            <div className="flex items-center gap-1.5 pl-9 flex-wrap" data-field="threshold">
              <span className="text-micro text-lia-text-secondary">{meta.before}</span>
              <input
                type="number"
                min={0}
                value={pref.threshold ?? 0}
                onChange={(e) => {
                  const val = parseInt(e.target.value, 10)
                  if (!isNaN(val)) handleUpdate(pref, { threshold: val })
                }}
                disabled={isSaving}
                aria-label={t("alertPreferences.thresholdAria", { type: pref.alert_type })}
                className="w-12 text-micro text-center border border-lia-border-subtle rounded-md px-1 py-0.5 bg-lia-bg-secondary disabled:opacity-60 focus:outline-none focus:ring-1 focus:ring-lia-accent/40"
              />
              <span className="text-micro text-lia-text-secondary">{meta.after} ({unitLabel})</span>
            </div>

            {/* Cooldown */}
            <div className="flex items-center gap-1.5 pl-9 flex-wrap" data-field="cooldown">
              <span className="text-micro text-lia-text-secondary">{t("alertPreferences.cooldownLabel")}</span>
              <input
                type="number"
                min={1}
                value={pref.cooldown_hours}
                onChange={(e) => {
                  const val = parseInt(e.target.value, 10)
                  if (!isNaN(val) && val >= 1) handleUpdate(pref, { cooldown_hours: val })
                }}
                disabled={isSaving}
                aria-label={t("alertPreferences.cooldownAria", { type: pref.alert_type })}
                className="w-12 text-micro text-center border border-lia-border-subtle rounded-md px-1 py-0.5 bg-lia-bg-secondary disabled:opacity-60 focus:outline-none focus:ring-1 focus:ring-lia-accent/40"
              />
              <span>{t("alertPreferences.cooldownUnit")}</span>
            </div>

            {/* Canais — filtrados por aplicabilidade (WhatsApp só p/ candidato) */}
            <div className="flex items-center gap-1.5 flex-wrap" data-field="channels">
              <span className="text-xs text-lia-text-secondary mr-0.5">
                {t("alertPreferences.channelsLabel")}
              </span>
              {meta.channels.map((channel) => {
                const checked = pref.channels[channel]
                const label = t(`alertPreferences.${CHANNEL_LABEL_KEY[channel]}`)
                return (
                  <button
                    key={channel}
                    type="button"
                    onClick={() =>
                      handleUpdate(pref, {
                        channels: { ...pref.channels, [channel]: !checked },
                      })
                    }
                    disabled={isSaving}
                    data-channel={channel}
                    data-testid={`alert-pref-channel-${pref.alert_type}-${channel}`}
                    aria-pressed={checked}
                    aria-label={label}
                    className={`text-micro rounded-full px-2 py-0.5 border transition-colors motion-reduce:transition-none disabled:opacity-60 ${
                      checked
                        ? "bg-lia-text-secondary text-lia-bg-primary border-lia-text-secondary"
                        : "bg-lia-bg-primary text-lia-text-secondary border-lia-border-subtle"
                    }`}
                  >
                    {label}
                  </button>
                )
              })}
              {isSaving && (
                <Loader2 className={`${actionButtonStyles.icon} animate-spin ml-1`} />
              )}
            </div>
          </>
        ) }
        {!pref.is_enabled && (
          <p className="mt-2 pl-9 text-micro text-lia-text-secondary">
            {t("alertPreferences.disabledHint")}
          </p>
        )}
      </div>
    )
  }

  function renderGroup(
    icon: React.ReactNode,
    titleKey: string,
    hintKey: string,
    items: AlertPreference[]
  ) {
    if (items.length === 0) return null
    return (
      <section className="space-y-2" data-component="alert-preference-group">
        <div className="flex items-start gap-2">
          <div className="w-6 h-6 rounded-md flex items-center justify-center bg-lia-bg-secondary text-lia-text-secondary shrink-0">
            {icon}
          </div>
          <div className="min-w-0">
            <h3 className="text-xs font-semibold text-lia-text-primary">
              {t(titleKey)}
            </h3>
            <p className="text-micro text-lia-text-secondary">{t(hintKey)}</p>
          </div>
        </div>
        <div className="space-y-2">{items.map(renderCard)}</div>
      </section>
    )
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
          <span className="text-xs">{loadError ?? saveError}</span>
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

        <CardContent className="space-y-5">
          {/* B1+B2: Configurações gerais de notificação */}
          {!isBriefingLoading && (
            <section className="space-y-3" data-component="notification-general-settings">
              <div className="flex items-start gap-2">
                <div className="w-6 h-6 rounded-md flex items-center justify-center bg-lia-bg-secondary text-lia-text-secondary shrink-0">
                  <Calendar className="w-3.5 h-3.5" />
                </div>
                <div className="min-w-0">
                  <h3 className="text-xs font-semibold text-lia-text-primary">
                    {t("alertPreferences.generalTitle")}
                  </h3>
                  <p className="text-micro text-lia-text-secondary">
                    {t("alertPreferences.generalSubtitle")}
                  </p>
                </div>
              </div>

              {/* B1: Frequência do briefing */}
              <div className="ml-8 space-y-1">
                <label className="text-xs text-lia-text-primary font-medium">
                  {t("alertPreferences.frequencyLabel")}
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {(["daily", "twice_daily", "weekly", "monthly"] as BriefingFrequency[]).map((freq) => (
                    <button
                      key={freq}
                      type="button"
                      disabled={isBriefingSaving}
                      onClick={() => updateBriefingFrequency(freq).catch(() => {})}
                      aria-pressed={briefingFrequency === freq}
                      className={`text-micro rounded-full px-2.5 py-0.5 border transition-colors disabled:opacity-60 ${
                        briefingFrequency === freq
                          ? "bg-lia-accent text-white border-lia-accent"
                          : "bg-lia-bg-primary text-lia-text-secondary border-lia-border-subtle"
                      }`}
                    >
                      {t(`alertPreferences.frequency.${freq}`)}
                    </button>
                  ))}
                  {isBriefingSaving && (
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-lia-text-secondary self-center" />
                  )}
                </div>
              </div>

              {/* B2: Toggle digest semanal */}
              <div className="ml-8 flex items-center justify-between">
                <div>
                  <p className="text-xs text-lia-text-primary font-medium">
                    {t("alertPreferences.digestLabel")}
                  </p>
                  <p className="text-micro text-lia-text-secondary">
                    {t("alertPreferences.digestHint")}
                  </p>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={digestEnabled}
                  disabled={isBriefingSaving}
                  onClick={() => updateDigestEnabled(!digestEnabled).catch(() => {})}
                  className={`relative inline-flex h-4 w-7 shrink-0 items-center rounded-full transition-colors disabled:opacity-60 ${
                    digestEnabled ? "bg-lia-accent" : "bg-lia-border-subtle"
                  }`}
                >
                  <span
                    className={`inline-block h-3 w-3 transform rounded-full bg-white shadow-sm transition-transform ${
                      digestEnabled ? "translate-x-3.5" : "translate-x-0.5"
                    }`}
                  />
                </button>
              </div>

              {briefingSaveError && (
                <p className="ml-8 text-micro text-status-error">{briefingSaveError}</p>
              )}
            </section>
          )}

          {/* Fatia 2: Frequência pessoal do usuário (override per-user) */}
          {!isDigestScheduleLoading && (
            <section className="space-y-3 border border-lia-border-subtle rounded-lg p-3" data-component="personal-digest-schedule">
              <div className="flex items-start gap-2">
                <div className="w-6 h-6 rounded-md flex items-center justify-center bg-lia-bg-secondary text-lia-text-secondary shrink-0">
                  <UserCog className="w-3.5 h-3.5" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-xs font-semibold text-lia-text-primary">
                    {t("alertPreferences.personalFrequencyTitle")}
                  </h3>
                  <p className="text-micro text-lia-text-secondary">
                    {hasPersonalOverride
                      ? t("alertPreferences.personalFrequencyActive")
                      : t("alertPreferences.personalFrequencyDefault")}
                  </p>
                </div>
              </div>

              <div className="ml-8 space-y-2">
                <label className="text-xs text-lia-text-primary font-medium">
                  {t("alertPreferences.personalFrequencyLabel")}
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {(["daily", "twice_daily", "weekly", "monthly"] as DigestFrequency[]).map((freq) => (
                    <button
                      key={freq}
                      type="button"
                      disabled={isDigestScheduleSaving}
                      onClick={() => setUserFrequency(freq).catch(() => {})}
                      aria-pressed={userFrequency === freq}
                      className={`text-micro rounded-full px-2.5 py-0.5 border transition-colors disabled:opacity-60 ${
                        userFrequency === freq
                          ? "bg-lia-accent text-white border-lia-accent"
                          : "bg-lia-bg-primary text-lia-text-secondary border-lia-border-subtle"
                      }`}
                    >
                      {t(`alertPreferences.frequency.${freq}`)}
                    </button>
                  ))}
                  {isDigestScheduleSaving && (
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-lia-text-secondary self-center" />
                  )}
                </div>

                {hasPersonalOverride && (
                  <button
                    type="button"
                    onClick={() => resetToCompanyDefault().catch(() => {})}
                    disabled={isDigestScheduleSaving}
                    className="text-micro text-lia-text-secondary underline hover:text-lia-text-primary disabled:opacity-60"
                  >
                    {t("alertPreferences.resetToCompanyDefault")}
                  </button>
                )}
              </div>
            </section>
          )}

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

          {!isLoading && (
            <>
              {renderGroup(
                <UserCog className="w-3.5 h-3.5" />,
                "alertPreferences.groupRecruiter",
                "alertPreferences.groupRecruiterHint",
                groups.recruiter
              )}
              {renderGroup(
                <UserRound className="w-3.5 h-3.5" />,
                "alertPreferences.groupCandidate",
                "alertPreferences.groupCandidateHint",
                groups.candidate
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
