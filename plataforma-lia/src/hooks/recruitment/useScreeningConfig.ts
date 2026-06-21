"use client"

import { useState, useEffect, useCallback } from 'react'
import { useLoadingWatchdog } from '@/hooks/shared/use-loading-watchdog'
import { WSI_DECISION_CUTOFFS, wsiPresetToScore } from '@/lib/wsi/visual'

/**
 * Canonical screening channel keys — Task #425 (4 Canais MVP).
 * Legacy aliases (`phone`, `voip_web`) are normalized to canonical at read time
 * and mirrored back at write time so older readers keep working.
 */
export type ScreeningChannelKey = 'chat_web' | 'whatsapp' | 'phone_pstn' | 'voice_web'
export type LegacyScreeningChannelKey = 'phone' | 'voip_web'
export type AnyScreeningChannelKey = ScreeningChannelKey | LegacyScreeningChannelKey

export interface ScreeningChannelConfig {
  primary_channel: ScreeningChannelKey
  fallback_order: ScreeningChannelKey[]
}

export interface ChannelToggle {
  enabled: boolean
  label?: string
  // Task #425 — WhatsApp delivery mode (only used by the `whatsapp` channel).
  // 'wa_link' = wa.me link only (legacy);
  // 'twilio_direct' = direct send via Twilio WA Business API;
  // 'both' = link + Twilio direct send.
  mode?: 'wa_link' | 'twilio_direct' | 'both'
}

export interface ScreeningConfig {
  status?: {
    enabled: boolean
    paused_at?: string | null
    paused_by?: string | null
    pause_reason?: string | null
    scheduled_end_date?: string | null
    last_updated?: string | null
  }
  /**
   * Master toggle: when false, the screening flow is disabled regardless of
   * individual channel toggles. Defaults to true. Independent of `status.enabled`
   * which is the global pause/resume flag controlled by auto-approval limits.
   */
  channels_master_enabled?: boolean
  channels?: {
    whatsapp?: ChannelToggle
    chat_web?: ChannelToggle
    phone_pstn?: ChannelToggle
    voice_web?: ChannelToggle
    /** @deprecated use phone_pstn — kept as legacy mirror for backward compat */
    phone?: ChannelToggle
    /** @deprecated use voice_web — kept as legacy mirror for backward compat */
    voip_web?: ChannelToggle
  }
  screening_channels?: ScreeningChannelConfig
  settings?: {
    min_score?: number
    min_score_preset?: 'rigorous' | 'recommended' | 'flexible'
    response_timeout_hours?: number
    max_retries?: number
    auto_approval_limit?: number
    auto_approval_preset?: 'conservative' | 'recommended' | 'autonomous'
    auto_approvals_count?: number
    auto_approval_paused?: boolean
  }
  metrics?: {
    screened_count?: number
    completion_rate?: number
    average_rating?: number
  }
  scheduling?: {
    auto_enabled?: boolean
    min_score_for_auto?: number
    min_score_for_auto_preset?: 'rigorous' | 'recommended' | 'flexible'
    calendar_provider?: string
    available_hours?: string
    available_hours_inherited?: boolean
    interview_duration_min?: number
  }
  feedback_templates?: {
    approved?: string
    rejected?: string
  }
  wsi_skills?: string[]
  job_id?: string
  is_default?: boolean
}

export function normalizeChannelKey(k: string | undefined | null): ScreeningChannelKey {
  if (k === 'phone') return 'phone_pstn'
  if (k === 'voip_web') return 'voice_web'
  if (k === 'chat_web' || k === 'whatsapp' || k === 'phone_pstn' || k === 'voice_web') return k
  return 'chat_web'
}

const DEFAULT_CONFIG: ScreeningConfig = {
  status: {
    enabled: true,
    last_updated: null
  },
  channels_master_enabled: true,
  channels: {
    whatsapp: { enabled: true, label: 'WhatsApp' },
    chat_web: { enabled: true, label: 'Chat Web' },
    phone_pstn: { enabled: false, label: 'Ligação (PSTN)' },
    voice_web: { enabled: true, label: 'Voz no Navegador' },
    phone: { enabled: false, label: 'Ligação (PSTN)' },
    voip_web: { enabled: true, label: 'Voz no Navegador' },
  },
  screening_channels: {
    primary_channel: 'chat_web',
    fallback_order: ['whatsapp']
  },
  settings: {
    min_score: 3.8,
    min_score_preset: 'recommended',
    response_timeout_hours: 48,
    max_retries: 2,
    auto_approval_limit: 10,
    auto_approval_preset: 'recommended',
    auto_approvals_count: 0,
    auto_approval_paused: false
  },
  metrics: {
    screened_count: 0,
    completion_rate: 0,
    average_rating: 4.2
  },
  scheduling: {
    auto_enabled: true,
    min_score_for_auto: WSI_DECISION_CUTOFFS.humanReview,
    min_score_for_auto_preset: 'recommended',
    calendar_provider: 'Microsoft',
    available_hours: '9h-18h',
    available_hours_inherited: true,
    interview_duration_min: 60
  },
  wsi_skills: []
}

export function scoreToPreset(score: number | undefined): 'rigorous' | 'recommended' | 'flexible' {
  // Escala WSI 0-10 (Task #512). Cutoffs canônicos em `lib/wsi/visual.ts`.
  if (score === undefined) return 'recommended'
  if (score >= WSI_DECISION_CUTOFFS.approved) return 'rigorous'
  if (score >= WSI_DECISION_CUTOFFS.humanReview) return 'recommended'
  return 'flexible'
}

export function limitToApprovalPreset(limit: number | undefined): 'conservative' | 'recommended' | 'autonomous' {
  if (limit === undefined) return 'recommended'
  if (limit <= 5) return 'conservative'
  if (limit <= 10) return 'recommended'
  return 'autonomous'
}

export function approvalPresetToLimit(preset: 'conservative' | 'recommended' | 'autonomous'): number {
  switch (preset) {
    case 'conservative': return 5
    case 'recommended': return 10
    case 'autonomous': return 25
  }
}

interface UseScreeningConfigResult {
  config: ScreeningConfig
  isLoading: boolean
  error: string | null
  loadError: string | null
  isDefault: boolean
  mutate: () => Promise<void>
  updateConfig: (updates: Partial<ScreeningConfig>) => Promise<boolean>
}

/**
 * Normalize a raw channels object: ensure all 4 canonical keys are populated,
 * absorbing legacy `phone`/`voip_web` data, and write the legacy mirrors back
 * so older readers keep functioning during the migration window.
 */
function mergeToggle(
  base: ChannelToggle | undefined,
  override: ChannelToggle | undefined,
  defaultEnabled: boolean,
  defaultLabel: string
): ChannelToggle {
  return {
    enabled: override?.enabled ?? base?.enabled ?? defaultEnabled,
    label: override?.label ?? base?.label ?? defaultLabel,
  }
}

function normalizeChannels(
  raw: ScreeningConfig['channels'] | undefined
): ScreeningConfig['channels'] {
  const r = raw || {}
  const d = DEFAULT_CONFIG.channels || {}
  const phonePstn = r.phone_pstn ?? r.phone
  const voiceWeb = r.voice_web ?? r.voip_web
  const phoneToggle = mergeToggle(d.phone_pstn, phonePstn, false, 'Ligação (PSTN)')
  const voiceToggle = mergeToggle(d.voice_web, voiceWeb, true, 'Voz no Navegador')
  // Task #425 — preserve WhatsApp delivery mode (mergeToggle drops unknown fields).
  const whatsappBase = mergeToggle(d.whatsapp, r.whatsapp, true, 'WhatsApp')
  const waMode = r.whatsapp?.mode ?? d.whatsapp?.mode
  const whatsapp: ChannelToggle = waMode
    ? { ...whatsappBase, mode: waMode === 'twilio_direct' || waMode === 'both' ? waMode : 'wa_link' }
    : whatsappBase
  return {
    whatsapp,
    chat_web: mergeToggle(d.chat_web, r.chat_web, true, 'Chat Web'),
    phone_pstn: phoneToggle,
    voice_web: voiceToggle,
    phone: phoneToggle,
    voip_web: voiceToggle,
  }
}

function normalizeScreeningChannels(
  raw: ScreeningChannelConfig | undefined
): ScreeningChannelConfig {
  const base = DEFAULT_CONFIG.screening_channels as ScreeningChannelConfig
  if (!raw) return base
  return {
    primary_channel: normalizeChannelKey(raw.primary_channel as unknown as string),
    fallback_order: (raw.fallback_order || []).map(k => normalizeChannelKey(k as unknown as string)),
  }
}

export function useScreeningConfig(jobId: string | number | null): UseScreeningConfigResult {
  const [config, setConfig] = useState<ScreeningConfig>(DEFAULT_CONFIG)
  const [isLoading, setIsLoading] = useState(false)
  const [isInitialLoading, setIsInitialLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [isDefault, setIsDefault] = useState(true)

  useLoadingWatchdog(isInitialLoading, () => {
    setIsInitialLoading(false)
    setIsLoading(false)
    setLoadError('Tempo limite de carregamento excedido')
  }, 20_000)

  const fetchConfig = useCallback(async () => {
    if (!jobId) {
      setConfig(DEFAULT_CONFIG)
      setIsDefault(true)
      return
    }

    setIsInitialLoading(true)
    setIsLoading(true)
    setLoadError(null)

    try {
      const response = await fetch(`/api/backend-proxy/jobs/${jobId}/screening-config`)
      
      if (!response.ok) {
        // Don't throw for expected cases - just use defaults
        setConfig(DEFAULT_CONFIG)
        setIsDefault(true)
        setIsInitialLoading(false)
        setIsLoading(false)
        return
      }

      const data = await response.json()
      
      const mergedSettings = { ...DEFAULT_CONFIG.settings, ...data.settings }
      if (!mergedSettings.min_score_preset && mergedSettings.min_score !== undefined) {
        mergedSettings.min_score_preset = scoreToPreset(mergedSettings.min_score)
      }
      const mergedScheduling = { ...DEFAULT_CONFIG.scheduling, ...data.scheduling }
      if (!mergedScheduling.min_score_for_auto_preset && mergedScheduling.min_score_for_auto !== undefined) {
        mergedScheduling.min_score_for_auto_preset = scoreToPreset(mergedScheduling.min_score_for_auto)
      }

      const mergedConfig: ScreeningConfig = {
        status: { ...DEFAULT_CONFIG.status, ...data.status },
        channels_master_enabled: data.channels_master_enabled ?? DEFAULT_CONFIG.channels_master_enabled,
        channels: normalizeChannels(data.channels),
        screening_channels: normalizeScreeningChannels(data.screening_channels),
        settings: mergedSettings,
        metrics: { ...DEFAULT_CONFIG.metrics, ...data.metrics },
        scheduling: mergedScheduling,
        feedback_templates: { ...DEFAULT_CONFIG.feedback_templates, ...data.feedback_templates },
        wsi_skills: data.wsi_skills || DEFAULT_CONFIG.wsi_skills,
        job_id: data.job_id,
        is_default: data.is_default
      }

      setConfig(mergedConfig)
      setIsDefault(data.is_default ?? true)
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : 'Unknown error')
      setConfig(DEFAULT_CONFIG)
      setIsDefault(true)
    } finally {
      setIsInitialLoading(false)
      setIsLoading(false)
    }
  }, [jobId])

  useEffect(() => {
    fetchConfig()
  }, [fetchConfig])

  const updateConfig = useCallback(async (updates: Partial<ScreeningConfig>): Promise<boolean> => {
    if (!jobId) {
      setError('No job ID provided')
      return false
    }

    setIsLoading(true)
    setError(null)

    try {
      const newConfig: ScreeningConfig = {
        ...config,
        ...updates,
        channels: normalizeChannels(updates.channels ?? config.channels),
        screening_channels: normalizeScreeningChannels(updates.screening_channels ?? config.screening_channels),
        status: {
          enabled: config.status?.enabled ?? true,
          ...config.status,
          ...updates.status,
          last_updated: new Date().toISOString()
        }
      }

      const response = await fetch(`/api/backend-proxy/jobs/${jobId}/screening-config`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newConfig),
      })

      if (!response.ok) {
        throw new Error(`Failed to update screening config: ${response.status}`)
      }

      setConfig(newConfig)
      setIsDefault(false)
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      return false
    } finally {
      setIsLoading(false)
    }
  }, [jobId, config])

  return {
    config,
    isLoading,
    error,
    loadError,
    isDefault,
    mutate: fetchConfig,
    updateConfig
  }
}

export default useScreeningConfig