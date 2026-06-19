"use client"

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
 */

import React, { useState } from "react"
import { Globe, MessageSquare, Phone, Wifi, Clock, Shield, Settings2 } from "lucide-react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { HubHeader, HubLoadingState, HubErrorState } from "@/components/settings/_shared"
import { SETTINGS_QUERY_KEYS, dispatchSettingsUpdate } from "@/hooks/settings/useSettingsBroadcast"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { cn } from "@/lib/utils"

interface ChannelConfig {
  enabled: boolean
  label: string
}

interface ScreeningDefaults {
  settings: {
    min_score: number
    min_score_preset: string
    response_timeout_hours: number
    max_retries: number
    auto_approval_limit: number
    auto_approval_preset: string
    auto_approvals_count: number
    auto_approval_paused: boolean
  }
  channels: {
    chat_web: ChannelConfig
    whatsapp: ChannelConfig
    phone_pstn: ChannelConfig
    voice_web: ChannelConfig
  }
  scheduling: {
    auto_enabled: boolean
    min_score_for_auto: number
    min_score_for_auto_preset: string
    calendar_provider: string
    available_hours: string
    interview_duration_min: number
  }
}

const DEFAULTS: ScreeningDefaults = {
  settings: {
    min_score: 76, min_score_preset: "recommended",
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
  scheduling: {
    auto_enabled: false, min_score_for_auto: 76,
    min_score_for_auto_preset: "recommended",
    calendar_provider: "Microsoft", available_hours: "9h-18h",
    interview_duration_min: 45,
  },
}

const CHANNEL_DEFS = [
  { key: "chat_web" as const, label: "Chat Web", icon: Globe, desc: "Candidato responde via portal web" },
  { key: "whatsapp" as const, label: "WhatsApp", icon: MessageSquare, desc: "Triagem por WhatsApp Business" },
  { key: "phone_pstn" as const, label: "Ligação (PSTN)", icon: Phone, desc: "Ligação de voz automática", comingSoon: true },
  { key: "voice_web" as const, label: "Voz no Navegador", icon: Wifi, desc: "Conversa por voz via Gemini Live", comingSoon: true },
]

const SCORE_PRESETS = [
  { key: "conservative", label: "Rigoroso", score: 85, desc: "Alta exigência" },
  { key: "recommended", label: "Recomendado", score: 76, desc: "Equilíbrio qualidade/volume" },
  { key: "inclusive", label: "Inclusivo", score: 65, desc: "Mais candidatos em revisão" },
]

async function fetchDefaults(companyId: string): Promise<ScreeningDefaults> {
  const res = await fetch(`/api/backend-proxy/company/screening-config-defaults`)
  if (!res.ok) throw new Error("Erro ao buscar configurações de triagem")
  const data = await res.json()
  return (data?.screening_config_defaults ?? DEFAULTS) as ScreeningDefaults
}

async function saveDefaults(companyId: string, updates: Partial<ScreeningDefaults>): Promise<void> {
  const res = await fetch(`/api/backend-proxy/company/screening-config-defaults`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  })
  if (!res.ok) throw new Error("Erro ao salvar configurações de triagem")
}

export function CompanyScreeningConfigHub() {
  const { companyId } = useCompanyId()
  const queryClient = useQueryClient()

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.screeningDefaults(companyId ?? ""),
    queryFn: () => fetchDefaults(companyId ?? ""),
    enabled: !!companyId,
    staleTime: 30_000,
  })

  const [draft, setDraft] = useState<Partial<ScreeningDefaults> | null>(null)
  const effective = draft ? { ...DEFAULTS, ...data, ...draft } : (data ?? DEFAULTS)
  const isDirty = draft !== null

  const { mutate: save, isPending: saving } = useMutation({
    mutationFn: (updates: Partial<ScreeningDefaults>) => saveDefaults(companyId ?? "", updates),
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

  const setScorePreset = (preset: typeof SCORE_PRESETS[0]) => {
    setDraft((prev) => ({
      ...effective,
      ...prev,
      settings: { ...effective.settings, ...prev?.settings, min_score: preset.score, min_score_preset: preset.key },
    }))
  }

  return (
    <div className="space-y-6" data-testid="company-screening-config-hub">
      <HubHeader
        title="Configurações de Triagem"
        description="Defaults empresa: usados ao criar vagas novas. Pode ser sobrescrito por vaga individualmente."
        icon={<Settings2 className="w-5 h-5" />}
      />

      {/* Score WSI */}
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
                <div className="text-lg font-bold">{preset.score}<span className="text-xs font-normal">/100</span></div>
                <div className="text-[10px] mt-0.5 opacity-70">{preset.desc}</div>
              </button>
            )
          })}
        </div>
        <div className="flex items-center gap-2 pt-1">
          <Label className="text-xs text-lia-text-secondary whitespace-nowrap">Score personalizado:</Label>
          <Input
            type="number"
            min={0}
            max={100}
            value={effective.settings.min_score}
            onChange={(e) => {
              const v = parseInt(e.target.value, 10)
              if (!isNaN(v)) updateSettings("min_score", Math.max(0, Math.min(100, v)))
              updateSettings("min_score_preset", "custom")
            }}
            className="w-20 h-7 text-sm"
          />
          <span className="text-xs text-lia-text-tertiary">/ 100</span>
        </div>
      </section>

      {/* Canais */}
      <section className="rounded-xl border border-lia-border-subtle p-4 space-y-3">
        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4 text-wedo-cyan-text" />
          <span className="text-sm font-semibold text-lia-text-primary">Canais de Triagem Ativos</span>
        </div>
        <p className="text-xs text-lia-text-secondary">Defina quais canais a IA usa por padrão para triagem de candidatos.</p>
        <div className="space-y-2">
          {CHANNEL_DEFS.map(({ key, label, icon: Icon, desc, comingSoon }) => (
            <div key={key} className="flex items-center justify-between py-2 border-b border-lia-border-subtle last:border-0">
              <div className="flex items-center gap-2.5">
                <Icon className="w-4 h-4 text-lia-text-secondary" />
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
      </section>

      {/* Prazo de Resposta */}
      <section className="rounded-xl border border-lia-border-subtle p-4 space-y-3">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-wedo-cyan-text" />
          <span className="text-sm font-semibold text-lia-text-primary">Prazo e Tentativas</span>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label className="text-xs">Prazo de resposta (horas)</Label>
            <Input
              type="number"
              min={1}
              max={168}
              value={effective.settings.response_timeout_hours}
              onChange={(e) => {
                const v = parseInt(e.target.value, 10)
                if (!isNaN(v)) updateSettings("response_timeout_hours", Math.max(1, Math.min(168, v)))
              }}
              className="h-8 text-sm"
            />
            <p className="text-[10px] text-lia-text-tertiary">Após esse prazo, candidato vai para revisão manual.</p>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Máx. tentativas de contato</Label>
            <Input
              type="number"
              min={1}
              max={5}
              value={effective.settings.max_retries}
              onChange={(e) => {
                const v = parseInt(e.target.value, 10)
                if (!isNaN(v)) updateSettings("max_retries", Math.max(1, Math.min(5, v)))
              }}
              className="h-8 text-sm"
            />
            <p className="text-[10px] text-lia-text-tertiary">Número de reenvios antes de desistir.</p>
          </div>
        </div>
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
