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
