"use client"
import { WSI_SCORE_PRESETS, wsiPresetToScore } from "@/lib/wsi/visual"

/**
 * CompanyScreeningConfigHub — seção "Configurações de Triagem" em Dados da Empresa.
 *
 * Expõe defaults empresa-level para scoring WSI, canais ativos, prazo de resposta
 * e auto-aprovação. Esses defaults são usados como base ao criar novas vagas
 * (manual ou via wizard). O recrutador pode sobrescrever por vaga individualmente.
 *
 * Padrões canônicos (CLAUDE.md Sprint D 2026-05-26):
 * - REGRA 1: useQuery para server data
 * - REGRA 3: HubHeader / HubLoadingState / HubErrorState de _shared
 * - REGRA 5: dispatchSettingsUpdate após salvar
 * - Multi-tenancy: company_id via JWT (useCompanyId), nunca user input
 *
 * Escala canônica: WSI 0–10 (alinhado com SCMSectionConfiguracoes.tsx e useScreeningConfig.ts)
 * Preset keys canônicos: 'rigorous' | 'recommended' | 'flexible'
 */

import React, { useState } from "react"
import { Globe, MessageSquare, Phone, Wifi, Clock, Shield, Settings2, CalendarCheck, PauseCircle, Star, Layers } from "lucide-react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { HubHeader, HubLoadingState, HubErrorState } from "@/components/settings/_shared"
import { SETTINGS_QUERY_KEYS, dispatchSettingsUpdate } from "@/hooks/settings/useSettingsBroadcast"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { cn } from "@/lib/utils"

interface ChannelConfig {
  enabled: boolean
  label: string
}

interface ScreeningDefaults {
  channels_master_enabled: boolean
  settings: {
    min_score: number
    min_score_preset: 'rigorous' | 'recommended' | 'flexible'
    response_timeout_hours: number
    max_retries: number
    auto_approval_limit: number
    auto_approval_preset: 'conservative' | 'recommended' | 'autonomous'
    auto_approvals_count: number
    auto_approval_paused: boolean
  }
  channels: {
    chat_web: ChannelConfig
    whatsapp: ChannelConfig
    phone_pstn: ChannelConfig
    voice_web: ChannelConfig
  }
  screening_channels: {
    primary_channel: string
    fallback_order: string[]
  }
  scheduling: {
    auto_enabled: boolean
    min_score_for_auto: number
    min_score_for_auto_preset: 'rigorous' | 'recommended' | 'flexible'
    calendar_provider: string
    available_hours: string
    interview_duration_min: number
  }
}

const DEFAULTS: ScreeningDefaults = {
  channels_master_enabled: true,
  settings: {
    min_score: wsiPresetToScore("recommended"), min_score_preset: "recommended",
    response_timeout_hours: 48, max_retries: 2,
    auto_approval_limit: 10, auto_approval_preset: "recommended",
    auto_approvals_count: 0, auto_approval_paused: false,
  },
  channels: {
    chat_web: { enabled: true, label: "Chat Web" },
    whatsapp: { enabled: true, label: "WhatsApp" },
    phone_pstn: { enabled: false, label: "Ligação (PSTN)" },
    voice_web: { enabled: false, label: "Voz no Navegador" },
  },
  screening_channels: {
    primary_channel: "chat_web",
    fallback_order: ["whatsapp"],
  },
  scheduling: {
    auto_enabled: false, min_score_for_auto: wsiPresetToScore('recommended'), // WSI_SCORE_PRESETS canonical
    min_score_for_auto_preset: "recommended",
    calendar_provider: "Microsoft", available_hours: "9h-18h",
    interview_duration_min: 45,
  },
}

// Canônico: alinhado com useScreeningConfig.ts e SCMSectionConfiguracoes.tsx
// SCORE_PRESETS -> WSI_SCORE_PRESETS canonico de @/lib/wsi/visual
const SCORE_PRESETS = WSI_SCORE_PRESETS

const AUTO_APPROVAL_PRESETS = [
  { key: "conservative" as const, label: "Conservador", limit: 5, desc: "Revisão humana frequente" },
  { key: "recommended" as const, label: "Recomendado", limit: 10, desc: "Equilíbrio automação/supervisão" },
  { key: "autonomous" as const, label: "Autônomo", limit: 25, desc: "Máxima automação" },
]

const CHANNEL_DEFS = [
  { key: "chat_web" as const, label: "Chat Web", icon: Globe, desc: "Candidato responde via portal web" },
  { key: "whatsapp" as const, label: "WhatsApp", icon: MessageSquare, desc: "Triagem por WhatsApp Business" },
  { key: "phone_pstn" as const, label: "Ligação (PSTN)", icon: Phone, desc: "Ligação de voz automática", comingSoon: true },
  { key: "voice_web" as const, label: "Voz no Navegador", icon: Wifi, desc: "Conversa por voz via Gemini Live", comingSoon: true },
]

const TIMEOUT_OPTIONS = [12, 24, 48, 72]
const RETRIES_OPTIONS = [1, 2, 3, 4, 5]

async function fetchDefaults(): Promise<ScreeningDefaults> {
  const res = await fetch(`/api/backend-proxy/company/screening-config-defaults`)
  if (!res.ok) throw new Error("Erro ao buscar configurações de triagem")
  const data = await res.json()
  const raw = data?.screening_config_defaults ?? data ?? {}
  return {
    channels_master_enabled: raw.channels_master_enabled ?? DEFAULTS.channels_master_enabled,
    settings: { ...DEFAULTS.settings, ...raw.settings },
    channels: { ...DEFAULTS.channels, ...raw.channels },
    screening_channels: raw.screening_channels ?? DEFAULTS.screening_channels,
    scheduling: { ...DEFAULTS.scheduling, ...raw.scheduling },
  }
}

async function saveDefaults(updates: Partial<ScreeningDefaults>): Promise<void> {
  const res = await fetch(`/api/backend-proxy/company/screening-config-defaults`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  })
  if (!res.ok) throw new Error("Erro ao salvar configurações de triagem")
}

export function CompanyScreeningConfigHub({ showHeader = true }: { showHeader?: boolean } = {}) {
  const t = useTranslations("settings.screening")
  const { companyId } = useCompanyId()
  const queryClient = useQueryClient()

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.screeningDefaults(companyId ?? ""),
    queryFn: fetchDefaults,
    enabled: !!companyId,
    staleTime: 30_000,
  })

  const [draft, setDraft] = useState<Partial<ScreeningDefaults> | null>(null)
  const effective = draft ? { ...DEFAULTS, ...data, ...draft } : (data ?? DEFAULTS)
  const isDirty = draft !== null

  const { mutate: save, isPending: saving } = useMutation({
    mutationFn: (updates: Partial<ScreeningDefaults>) => saveDefaults(updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.screeningDefaults(companyId ?? "") })
      setDraft(null)
      toast.success("Configurações de triagem salvas")
      dispatchSettingsUpdate({ section: "screening_defaults", source: "ui" })
    },
    onError: (e: Error) => toast.error(e.message),
  })

  if (isLoading) return <HubLoadingState />
  if (error) return <HubErrorState onRetry={refetch} />

  const updateSettings = (key: keyof ScreeningDefaults["settings"], val: unknown) => {
    setDraft((prev) => ({
      ...effective,
      ...prev,
      settings: { ...effective.settings, ...prev?.settings, [key]: val },
    }))
  }

  const updateChannel = (ch: keyof ScreeningDefaults["channels"], enabled: boolean) => {
    setDraft((prev) => ({
      ...effective,
      ...prev,
      channels: {
        ...effective.channels,
        ...prev?.channels,
        [ch]: { ...effective.channels[ch], enabled },
      },
    }))
  }

  const updateScheduling = (key: keyof ScreeningDefaults["scheduling"], val: unknown) => {
    setDraft((prev) => ({
      ...effective,
      ...prev,
      scheduling: { ...effective.scheduling, ...prev?.scheduling, [key]: val },
    }))
  }

  const setScorePreset = (preset: typeof WSI_SCORE_PRESETS[number]) => {
    setDraft((prev) => ({
      ...effective,
      ...prev,
      settings: { ...effective.settings, ...prev?.settings, min_score: preset.score, min_score_preset: preset.key },
    }))
  }

  const setSchedulingScorePreset = (preset: typeof WSI_SCORE_PRESETS[number]) => {
    setDraft((prev) => ({
      ...effective,
      ...prev,
      scheduling: { ...effective.scheduling, ...prev?.scheduling, min_score_for_auto: preset.score, min_score_for_auto_preset: preset.key },
    }))
  }

  const setChannelsMasterEnabled = (v: boolean) => {
    setDraft((prev) => ({ ...effective, ...prev, channels_master_enabled: v }))
  }

  const setPrimaryChannel = (channelKey: string) => {
    const prevPrimary = effective.screening_channels.primary_channel
    const prevFallback = effective.screening_channels.fallback_order
    // Move o canal atual primário para início do fallback, remova o novo primário do fallback
    const newFallback = [prevPrimary, ...prevFallback].filter(k => k !== channelKey)
    setDraft((prev) => ({
      ...effective,
      ...prev,
      screening_channels: { primary_channel: channelKey, fallback_order: newFallback },
    }))
  }

  const enabledChannelKeys = CHANNEL_DEFS
    .filter(d => !d.comingSoon && effective.channels[d.key]?.enabled)
    .map(d => d.key)

  return (
    <div className="space-y-6" data-testid="company-screening-config-hub">
      {showHeader && (
        <HubHeader
          title="Configurações de Triagem"
          description="Defaults empresa: usados ao criar vagas novas. Pode ser sobrescrito por vaga individualmente."
          icon={<Settings2 className="w-5 h-5" />}
        />
      )}

      {/* Score Mínimo WSI */}
      <section className="rounded-xl border border-lia-border-subtle p-4 space-y-3">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-wedo-cyan-text" />
          <span className="text-sm font-semibold text-lia-text-primary">Score Mínimo de Aprovação</span>
        </div>
        <p className="text-xs text-lia-text-secondary">Candidatos com score WSI abaixo deste valor vão para revisão manual.</p>
        <div className="flex gap-2 flex-wrap">
          {SCORE_PRESETS.map((preset) => {
            const isSelected = effective.settings.min_score_preset === preset.key
            return (
              <button
                key={preset.key}
                onClick={() => setScorePreset(preset)}
                className={cn(
                  "flex-1 min-w-[100px] p-3 rounded-lg border text-left transition-colors",
                  isSelected
                    ? "border-wedo-cyan bg-wedo-cyan/10 text-wedo-cyan-text"
                    : "border-lia-border-subtle bg-lia-bg-secondary/50 text-lia-text-secondary hover:bg-lia-interactive-hover"
                )}
              >
                <div className="text-xs font-semibold">{preset.label}</div>
                <div className="text-lg font-bold">≥{preset.score}<span className="text-xs font-normal"> WSI</span></div>
                <div className="text-[10px] mt-0.5 opacity-70">{preset.desc}</div>
              </button>
            )
          })}
        </div>
      </section>

      {/* Canais de Triagem */}
      <section className="rounded-xl border border-lia-border-subtle p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4 text-wedo-cyan-text" />
            <span className="text-sm font-semibold text-lia-text-primary">Canais de Triagem</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-lia-text-secondary">
              {effective.channels_master_enabled ? "Triagem ativa" : "Triagem desligada"}
            </span>
            <Switch
              checked={effective.channels_master_enabled}
              onCheckedChange={setChannelsMasterEnabled}
              aria-label="Triagem ativa por padrão"
            />
          </div>
        </div>
        <p className="text-xs text-lia-text-secondary">Defina quais canais a IA usa por padrão e qual é o canal primário.</p>
        <div className="space-y-2">
          {CHANNEL_DEFS.map(({ key, label, icon: Icon, desc, comingSoon }) => (
            <div key={key} className="flex items-center justify-between py-2 border-b border-lia-border-subtle last:border-0">
              <div className="flex items-center gap-2.5">
                <Icon className="w-4 h-4 text-lia-text-secondary" aria-hidden="true" />
                <div>
                  <span className="text-sm text-lia-text-primary">{label}</span>
                  {comingSoon && (
                    <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded bg-lia-bg-tertiary text-lia-text-muted">Em breve</span>
                  )}
                  <p className="text-[10px] text-lia-text-tertiary">{desc}</p>
                </div>
              </div>
              <Switch
                checked={effective.channels[key]?.enabled ?? false}
                onCheckedChange={(v) => updateChannel(key, v)}
                disabled={comingSoon}
                aria-label={`${label} ativo`}
              />
            </div>
          ))}
        </div>

        {/* Canal principal + fallback */}
        {enabledChannelKeys.length > 0 && (
          <div className="pt-2 border-t border-lia-border-subtle space-y-2">
            <div className="flex items-center gap-1.5 mb-1">
              <Layers className="w-3.5 h-3.5 text-lia-text-tertiary" aria-hidden="true" />
              <span className="text-xs font-semibold text-lia-text-tertiary uppercase tracking-wider">Canal principal e fallback</span>
            </div>
            <p className="text-[11px] text-lia-text-secondary">Clique em ★ para definir o canal principal. Os demais são usados como fallback na ordem abaixo.</p>
            <div className="space-y-1.5">
              {enabledChannelKeys.map((channelKey) => {
                const def = CHANNEL_DEFS.find(d => d.key === channelKey)
                if (!def) return null
                const Icon = def.icon
                const isPrimary = effective.screening_channels.primary_channel === channelKey
                const fallbackIdx = effective.screening_channels.fallback_order.indexOf(channelKey)
                return (
                  <div
                    key={channelKey}
                    className={cn(
                      "flex items-center gap-2 px-2.5 py-2 rounded-lg border",
                      isPrimary
                        ? "border-wedo-cyan bg-wedo-cyan/5"
                        : "border-lia-border-subtle bg-lia-bg-secondary/30"
                    )}
                  >
                    <button
                      onClick={() => setPrimaryChannel(channelKey)}
                      aria-label={`Definir ${def.label} como canal principal`}
                      className="flex-shrink-0"
                    >
                      <Star
                        className={cn(
                          "w-3.5 h-3.5 transition-colors",
                          isPrimary ? "fill-wedo-cyan text-wedo-cyan" : "text-lia-text-muted hover:text-wedo-cyan"
                        )}
                        aria-hidden="true"
                      />
                    </button>
                    <Icon className="w-3.5 h-3.5 text-lia-text-secondary" aria-hidden="true" />
                    <span className="text-xs text-lia-text-primary flex-1">{def.label}</span>
                    {isPrimary ? (
                      <span className="text-[10px] font-medium text-wedo-cyan-text">Principal</span>
                    ) : (
                      <span className="text-[10px] text-lia-text-muted">
                        {fallbackIdx === 0 ? "1° fallback" : fallbackIdx === 1 ? "2° fallback" : `${fallbackIdx + 1}° fallback`}
                      </span>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </section>

      {/* Prazo e Tentativas */}
      <section className="rounded-xl border border-lia-border-subtle p-4 space-y-3">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-wedo-cyan-text" />
          <span className="text-sm font-semibold text-lia-text-primary">Prazo e Tentativas</span>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label className="text-xs">Timeout de resposta</Label>
            <select
              value={effective.settings.response_timeout_hours}
              onChange={(e) => updateSettings("response_timeout_hours", Number(e.target.value))}
              className="w-full h-8 text-sm rounded-md border border-lia-border px-2 bg-lia-bg-primary text-lia-text-primary"
            >
              {TIMEOUT_OPTIONS.map(h => (
                <option key={h} value={h}>{h}h</option>
              ))}
            </select>
            <p className="text-[10px] text-lia-text-tertiary">Após esse prazo, candidato vai para revisão manual.</p>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Re-tentativas</Label>
            <select
              value={effective.settings.max_retries}
              onChange={(e) => updateSettings("max_retries", Number(e.target.value))}
              className="w-full h-8 text-sm rounded-md border border-lia-border px-2 bg-lia-bg-primary text-lia-text-primary"
            >
              {RETRIES_OPTIONS.map(n => (
                <option key={n} value={n}>{n}x</option>
              ))}
            </select>
            <p className="text-[10px] text-lia-text-tertiary">Número de reenvios antes de desistir.</p>
          </div>
        </div>
      </section>

      {/* Controle de Paralização */}
      <section className="rounded-xl border border-lia-border-subtle p-4 space-y-3">
        <div className="flex items-center gap-2">
          <PauseCircle className="w-4 h-4 text-wedo-cyan-text" />
          <span className="text-sm font-semibold text-lia-text-primary">{t("sectionPauseControl")}</span>
        </div>
        <p className="text-xs text-lia-text-secondary">
          Pausa a triagem após atingir o limite de aprovações automáticas. Exige revisão humana antes de continuar.
        </p>
        <div className="flex gap-2 flex-wrap">
          {AUTO_APPROVAL_PRESETS.map((preset) => {
            const isSelected = effective.settings.auto_approval_preset === preset.key
            return (
              <button
                key={preset.key}
                onClick={() => {
                  updateSettings("auto_approval_limit", preset.limit)
                  updateSettings("auto_approval_preset", preset.key)
                }}
                className={cn(
                  "flex-1 min-w-[100px] p-3 rounded-lg border text-left transition-colors",
                  isSelected
                    ? "border-wedo-cyan bg-wedo-cyan/10 text-wedo-cyan-text"
                    : "border-lia-border-subtle bg-lia-bg-secondary/50 text-lia-text-secondary hover:bg-lia-interactive-hover"
                )}
              >
                <div className="text-xs font-semibold">{preset.label}</div>
                <div className="text-lg font-bold">{preset.limit} <span className="text-xs font-normal">aprovações</span></div>
                <div className="text-[10px] mt-0.5 opacity-70">{preset.desc}</div>
              </button>
            )
          })}
        </div>
      </section>

      {/* Agendamento Automático */}
      <section className="rounded-xl border border-lia-border-subtle p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CalendarCheck className="w-4 h-4 text-wedo-cyan-text" />
            <span className="text-sm font-semibold text-lia-text-primary">{t("sectionScheduling")}</span>
          </div>
          <Switch
            checked={effective.scheduling.auto_enabled}
            onCheckedChange={(v) => updateScheduling("auto_enabled", v)}
            aria-label="Habilitar agendamento automático"
          />
        </div>
        <p className="text-xs text-lia-text-secondary">
          Quando ativado, candidatos aprovados acima do score mínimo recebem link de agendamento automaticamente.
        </p>
        {effective.scheduling.auto_enabled && (
          <div className="pt-2 space-y-4 border-t border-lia-border-subtle">
            <div className="space-y-2">
              <Label className="text-xs font-medium">Score Mínimo para Agendamento (WSI)</Label>
              <div className="flex gap-2 flex-wrap">
                {SCORE_PRESETS.map((preset) => {
                  const isSelected = effective.scheduling.min_score_for_auto_preset === preset.key
                  return (
                    <button
                      key={preset.key}
                      onClick={() => setSchedulingScorePreset(preset)}
                      className={cn(
                        "flex-1 min-w-[80px] p-2.5 rounded-lg border text-left transition-colors",
                        isSelected
                          ? "border-wedo-cyan bg-wedo-cyan/10 text-wedo-cyan-text"
                          : "border-lia-border-subtle bg-lia-bg-secondary/50 text-lia-text-secondary hover:bg-lia-interactive-hover"
                      )}
                    >
                      <div className="text-[10px] font-semibold">{preset.label}</div>
                      <div className="text-base font-bold">≥{preset.score}<span className="text-[10px] font-normal"> WSI</span></div>
                    </button>
                  )
                })}
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs">Calendário</Label>
                <select
                  value={effective.scheduling.calendar_provider}
                  onChange={(e) => updateScheduling("calendar_provider", e.target.value)}
                  className="w-full h-8 text-sm rounded-md border border-lia-border px-2 bg-lia-bg-primary text-lia-text-primary"
                >
                  <option value="Microsoft">Microsoft</option>
                  <option value="Google">Google</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Horários</Label>
                <input
                  type="text"
                  value={effective.scheduling.available_hours}
                  onChange={(e) => updateScheduling("available_hours", e.target.value)}
                  placeholder="9h-18h"
                  className="w-full h-8 text-sm rounded-md border border-lia-border px-2 bg-lia-bg-primary text-lia-text-primary focus:outline-none focus:border-wedo-cyan"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Duração (min)</Label>
                <select
                  value={effective.scheduling.interview_duration_min}
                  onChange={(e) => updateScheduling("interview_duration_min", Number(e.target.value))}
                  className="w-full h-8 text-sm rounded-md border border-lia-border px-2 bg-lia-bg-primary text-lia-text-primary"
                >
                  {[15, 30, 45, 60, 90, 120].map(m => (
                    <option key={m} value={m}>{m} min</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* Save */}
      {isDirty && (
        <div className="flex items-center gap-3 pt-1">
          <Button
            onClick={() => { if (draft) save(draft) }}
            disabled={saving}
            className="flex-1"
            size="sm"
          >
            {saving ? "Salvando..." : "Salvar padrões da empresa"}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setDraft(null)}
            disabled={saving}
          >
            Cancelar
          </Button>
        </div>
      )}
    </div>
  )
}
