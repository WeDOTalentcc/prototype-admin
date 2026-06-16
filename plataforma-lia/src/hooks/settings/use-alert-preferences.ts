/**
 * useAlertPreferences — canonical hook per ADR-WT-2025 Sprint D (2026-05-22).
 *
 * Single source of truth para AlertPreference (canonical) na UI. Substitui
 * `useCommunicationHub.saveAlertsConfig` (legacy AlertConfig blob).
 *
 * Multi-tenancy: `company_id` NUNCA enviado no payload (REGRA 2 Pydantic
 * Conventions). Backend extrai do JWT via `Depends(require_company_id)`.
 *
 * REGRA 4 (anti silent-fallback): erro propagado via throw — UI exibe banner
 * explícito; nunca silenciamos falha de PUT/POST.
 *
 * Endpoint canonical: /api/backend-proxy/alerts/preferences (proxies para
 * /api/v1/alerts/preferences no FastAPI).
 */
"use client"

import { useCallback } from "react"
import useSWR from "swr"
import { apiFetch } from "@/lib/api/api-fetch"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"
import { useJWTAuth } from "@/contexts/auth-context"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { SETTINGS_QUERY_KEYS, dispatchSettingsUpdate } from "@/hooks/settings/useSettingsBroadcast"

export type AlertPreferenceChannel = "email" | "bell" | "teams" | "whatsapp"

export interface AlertPreferenceChannels {
  email: boolean
  bell: boolean
  teams: boolean
  whatsapp: boolean
}

export interface AlertPreference {
  id: string | null
  user_id: string
  alert_type: string
  is_enabled: boolean
  threshold: number | null
  channels: AlertPreferenceChannels
  cooldown_hours: number
  // Campos opcionais vindos do catálogo default
  name?: string
  description?: string
  // company_id NUNCA aparece em payloads de mutation (multi-tenancy via JWT).
  // Aparece apenas em GET response para conferência defensiva no client.
  company_id?: string
}

export interface AlertPreferenceUpdate {
  is_enabled?: boolean
  threshold?: number
  channels?: AlertPreferenceChannels
  cooldown_hours?: number
}

export interface AlertPreferenceCreate {
  user_id: string
  alert_type: string
  is_enabled: boolean
  threshold: number | null
  channels: AlertPreferenceChannels
  cooldown_hours: number
}

interface AlertPreferencesResponse {
  preferences: AlertPreference[]
  user_id: string
  company_id?: string
}

const jsonFetcher = async (url: string): Promise<AlertPreferencesResponse> => {
  const response = await apiFetch(url)
  if (!response.ok) {
    throw new Error(`Falha ao carregar preferências de alerta (HTTP ${response.status})`)
  }
  return response.json()
}

export function useAlertPreferences() {
  const { user } = useJWTAuth()
  const userId = user?.id ?? null

  const swrKey = userId
    ? `/api/backend-proxy/alerts/preferences?user_id=${encodeURIComponent(userId)}`
    : null

  const { data, error, mutate, isLoading } = useSWR<AlertPreferencesResponse>(
    swrKey,
    jsonFetcher,
  )

  const updatePreference = useCallback(
    async (pref: AlertPreference, updates: AlertPreferenceUpdate) => {
      if (!userId) throw new Error("Sessão não autenticada")
      const merged: AlertPreference = {
        ...pref,
        ...updates,
        channels: updates.channels ?? pref.channels,
      }

      // Backend canonical aceita lista (`preferences: AlertPreferenceItem[]`).
      // NUNCA enviar company_id no body (REGRA 2 — JWT-only).
      const payload = {
        preferences: [
          {
            id: merged.id,
            user_id: merged.user_id || userId,
            alert_type: merged.alert_type,
            is_enabled: merged.is_enabled,
            threshold: merged.threshold,
            channels: merged.channels,
            cooldown_hours: merged.cooldown_hours,
          },
        ],
      }

      const optimistic: AlertPreferencesResponse | undefined = data
        ? {
            ...data,
            preferences: data.preferences.map((p) =>
              p.alert_type === merged.alert_type ? merged : p
            ),
          }
        : undefined

      await mutate(
        async (current) => {
          const response = await apiFetch(
            "/api/backend-proxy/alerts/preferences",
            {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload),
            }
          )
          notifyChatOfSettingsUpdate({ actionId: "configure_alert", section: "alerts" })
          if (!response.ok) {
            // REGRA 4: fail-loud — UI vai mostrar banner explícito.
            const text = await response.text().catch(() => "")
            throw new Error(
              `Falha ao salvar preferência (HTTP ${response.status})${text ? `: ${text.slice(0, 120)}` : ""}`
            )
          }
          return optimistic ?? current
        },
        {
          optimisticData: optimistic,
          rollbackOnError: true,
          revalidate: true,
        }
      )
    },
    [data, mutate, userId]
  )

  const createPreference = useCallback(
    async (payload: AlertPreferenceCreate) => {
      if (!userId) throw new Error("Sessão não autenticada")
      const body = {
        preferences: [
          {
            id: null,
            user_id: payload.user_id || userId,
            alert_type: payload.alert_type,
            is_enabled: payload.is_enabled,
            threshold: payload.threshold,
            channels: payload.channels,
            cooldown_hours: payload.cooldown_hours,
          },
        ],
      }
      const response = await apiFetch("/api/backend-proxy/alerts/preferences", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })
      if (!response.ok) {
        const text = await response.text().catch(() => "")
        throw new Error(
          `Falha ao criar preferência (HTTP ${response.status})${text ? `: ${text.slice(0, 120)}` : ""}`
        )
      }
      await mutate()
    },
    [mutate, userId]
  )

  return {
    preferences: data?.preferences ?? [],
    isLoading: isLoading || (!data && !error && !!swrKey),
    error: error instanceof Error ? error.message : (error ? String(error) : null),
    updatePreference,
    createPreference,
    refetch: () => mutate(),
  }
}

export type BriefingFrequency = "daily" | "twice_daily" | "weekly" | "monthly"

export interface BriefingPreferencesData {
  briefingFrequency: BriefingFrequency
  digestEnabled: boolean
}

/**
 * useBriefingPreferences — lê/escreve briefing_frequency e digest_enabled
 * via HiringPolicy.communication_rules (canonical desde migration 174).
 *
 * Leitura: GET /api/backend-proxy/hiring-policy
 * Escrita: PATCH /api/backend-proxy/hiring-policy/block
 * {block: "communication_rules", data: {briefing_frequency|digest_enabled}}
 *
 * Multi-tenancy: company_id do JWT, nunca do payload.
 * REGRA 4: erro propagado via throw — sem silent fallback.
 */
export function useBriefingPreferences() {
  const queryClient = useQueryClient()

  const { data: policyData, isLoading } = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.hiringPolicy(),
    queryFn: async () => {
      const r = await fetch("/api/backend-proxy/hiring-policy")
      if (!r.ok) throw new Error(`Falha ao carregar política (HTTP ${r.status})`)
      return r.json()
    },
    staleTime: 30_000,
  })

  const commRules = (policyData?.communication_rules as Record<string, unknown>) ?? {}
  const briefingFrequency: BriefingFrequency =
    (commRules.briefing_frequency as BriefingFrequency) ?? "daily"
  const digestEnabled: boolean = commRules.digest_enabled !== false  // fail-open: True when absent

  const updateCommunicationRules = useMutation({
    mutationFn: async (data: Record<string, unknown>) => {
      const r = await fetch("/api/backend-proxy/hiring-policy/block", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ block: "communication_rules", data }),
      })
      if (!r.ok) {
        const text = await r.text().catch(() => "")
        throw new Error(
          `Falha ao salvar configuração (HTTP ${r.status})${text ? `: ${text.slice(0, 120)}` : ""}`
        )
      }
      return r.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.hiringPolicy() })
      dispatchSettingsUpdate({ actionId: "update_briefing_preferences", section: "alerts", source: "ui", ts: Date.now() })
    },
  })

  return {
    briefingFrequency,
    digestEnabled,
    isLoading,
    isSaving: updateCommunicationRules.isPending,
    saveError: updateCommunicationRules.error
      ? (updateCommunicationRules.error instanceof Error
          ? updateCommunicationRules.error.message
          : String(updateCommunicationRules.error))
      : null,
    updateBriefingFrequency: (freq: BriefingFrequency) =>
      updateCommunicationRules.mutateAsync({ briefing_frequency: freq }),
    updateDigestEnabled: (enabled: boolean) =>
      updateCommunicationRules.mutateAsync({ digest_enabled: enabled }),
  }
}
