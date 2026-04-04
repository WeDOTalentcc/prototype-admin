"use client"

import { useState, useEffect, useCallback } from 'react'

export type ScreeningChannelKey = 'chat_web' | 'phone' | 'whatsapp' | 'voip_web'

export interface ScreeningChannelConfig {
  primary_channel: ScreeningChannelKey
  fallback_order: ScreeningChannelKey[]
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
  channels?: {
    whatsapp?: { enabled: boolean; label?: string }
    chat_web?: { enabled: boolean; label?: string }
    phone?: { enabled: boolean; label?: string }
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

const DEFAULT_CONFIG: ScreeningConfig = {
  status: {
    enabled: true,
    last_updated: null
  },
  channels: {
    whatsapp: { enabled: true, label: 'WhatsApp' },
    chat_web: { enabled: true, label: 'Chat Web' },
    phone: { enabled: false, label: 'Ligação' }
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
    min_score_for_auto: 3.8,
    min_score_for_auto_preset: 'recommended',
    calendar_provider: 'Microsoft',
    available_hours: '9h-18h',
    available_hours_inherited: true,
    interview_duration_min: 60
  },
  wsi_skills: []
}

export function scoreToPreset(score: number | undefined): 'rigorous' | 'recommended' | 'flexible' {
  if (score === undefined) return 'recommended'
  if (score >= 4.2) return 'rigorous'
  if (score >= 3.8) return 'recommended'
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
  isDefault: boolean
  mutate: () => Promise<void>
  updateConfig: (updates: Partial<ScreeningConfig>) => Promise<boolean>
}

export function useScreeningConfig(jobId: string | number | null): UseScreeningConfigResult {
  const [config, setConfig] = useState<ScreeningConfig>(DEFAULT_CONFIG)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isDefault, setIsDefault] = useState(true)

  const fetchConfig = useCallback(async () => {
    if (!jobId) {
      setConfig(DEFAULT_CONFIG)
      setIsDefault(true)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/backend-proxy/jobs/${jobId}/screening-config`)
      
      if (!response.ok) {
        // Don't throw for expected cases - just use defaults
        setConfig(DEFAULT_CONFIG)
        setIsDefault(true)
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
        channels: {
          whatsapp: { ...DEFAULT_CONFIG.channels?.whatsapp, ...data.channels?.whatsapp },
          chat_web: { ...DEFAULT_CONFIG.channels?.chat_web, ...data.channels?.chat_web },
          phone: { ...DEFAULT_CONFIG.channels?.phone, ...data.channels?.phone },
        },
        screening_channels: data.screening_channels
          ? { ...DEFAULT_CONFIG.screening_channels, ...data.screening_channels }
          : DEFAULT_CONFIG.screening_channels,
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
      setError(err instanceof Error ? err.message : 'Unknown error')
      setConfig(DEFAULT_CONFIG)
      setIsDefault(true)
    } finally {
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
    isDefault,
    mutate: fetchConfig,
    updateConfig
  }
}

export default useScreeningConfig
