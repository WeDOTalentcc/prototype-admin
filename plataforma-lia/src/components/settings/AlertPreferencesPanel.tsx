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
  CheckCircle,
  Loader2,
  UserCog,
  UserRound,
} from "lucide-react"
import { useTranslations } from "next-intl"
import { textStyles, actionButtonStyles } from "@/lib/design-tokens"
import {
  useAlertPreferences,
  type AlertPreference,
  type AlertPreferenceChannel,
  type AlertPreferenceUpdate,
} from "@/hooks/settings/use-alert-preferences"

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
    return (
      <div
        key={pref.id ?? pref.alert_type}
        data-component="alert-preference-card"
        data-alert-type={pref.alert_type}
        className={`p-3 rounded-md border transition-colors motion-reduce:transition-none ${
          pref.is_enabled
            ? "bg-lia-bg-primary border-lia-border-subtle"
            : "bg-lia-bg-secondary border-lia-border-subtle"
        }`}
      >
        {/* Linha 1: identidade + toggle */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-2 min-w-0">
            <div className="w-7 h-7 rounded-md flex items-center justify-center bg-lia-bg-secondary text-lia-text-secondary shrink-0">
              <Bell className="w-3.5 h-3.5" />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium text-lia-text-primary">
                {pref.name ?? pref.alert_type}
              </p>
              {pref.description && (
                <p className="text-xs text-lia-text-secondary mt-0.5">
                  {pref.description}
                </p>
              )}
            </div>
          </div>

          <button
            type="button"
            onClick={() => handleUpdate(pref, { is_enabled: !pref.is_enabled })}
            disabled={isSaving}
            role="switch"
            aria-checked={pref.is_enabled}
            aria-label={t("alertPreferences.toggleAria", { type: pref.alert_type })}
            data-toggle={`alert_pref_${pref.alert_type}_enabled`}
            data-testid={`alert-pref-toggle-${pref.alert_type}`}
            className={`relative w-9 h-5 rounded-full transition-colors motion-reduce:transition-none disabled:opacity-60 shrink-0 ${
              pref.is_enabled ? "bg-lia-text-secondary" : "bg-lia-border-subtle"
            }`}
          >
            <span
              className={`absolute top-0.5 w-4 h-4 bg-lia-bg-secondary rounded-full transition-transform motion-reduce:transition-none ${
                pref.is_enabled ? "left-4" : "left-0.5"
              }`}
            />
          </button>
        </div>

        {/* Linha 2: configuração — só quando habilitado */}
        {pref.is_enabled ? (
          <div className="mt-2.5 pl-9 space-y-2">
            {/* Frase legível do gatilho */}
            <div className="flex items-center gap-1.5 flex-wrap text-xs text-lia-text-secondary">
              <span>{meta.before}</span>
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
                disabled={isSaving}
                className="font-data tabular-nums text-xs w-16 border border-lia-border-subtle rounded-md px-1.5 py-1 bg-lia-bg-primary text-lia-text-primary disabled:opacity-60"
                data-field="threshold"
                data-testid={`alert-pref-threshold-${pref.alert_type}`}
                aria-label={t("alertPreferences.thresholdAria", { type: pref.alert_type })}
              />
              {meta.after && <span data-field="threshold_unit">{meta.after}</span>}
            </div>

            {/* Frase legível do intervalo de repetição (cooldown) */}
            <div className="flex items-center gap-1.5 flex-wrap text-xs text-lia-text-secondary">
              <span>{t("alertPreferences.cooldownLabel")}</span>
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
                disabled={isSaving}
                className="font-data tabular-nums text-xs w-16 border border-lia-border-subtle rounded-md px-1.5 py-1 bg-lia-bg-primary text-lia-text-primary disabled:opacity-60"
                data-field="cooldown_hours"
                data-testid={`alert-pref-cooldown-${pref.alert_type}`}
                aria-label={t("alertPreferences.cooldownAria", { type: pref.alert_type })}
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
          </div>
        ) : (
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
