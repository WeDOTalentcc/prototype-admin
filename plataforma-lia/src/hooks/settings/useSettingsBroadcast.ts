/**
 * useSettingsBroadcast.ts — canonical event broadcast hook (Sprint 2.2, 2026-05-26)
 *
 * Extraído de use-company-settings-cards.ts. Responsabilidade única:
 * dispatch de eventos lia:settings-updated / lia:settings-success e
 * escuta de atualizações externas (LIA chat, outras superfícies).
 *
 * Substitui o hack lastSelfDispatchRef: React Query invalida queries
 * em onSuccess — sem dedup manual necessário. O listener agora só
 * dispara invalidateQueries (não loadAll) evitando double-fetch.
 */

"use client"

import { useEffect, useCallback } from "react"
import { useQueryClient } from "@tanstack/react-query"

export const SETTINGS_QUERY_KEYS = {
  companyProfile: () => ["company-profile"] as const,
  cultureProfile: (companyId: string) => ["culture-profile", companyId] as const,
  benefits: (companyId: string) => ["company-benefits", companyId] as const,
  hiringPolicy: () => ["hiring-policy"] as const,
  settingsProgress: () => ["settings-progress"] as const,
  automations: (companyId: string) => ["automations", companyId] as const,
} as const

export type SettingsBroadcastDetail = {
  actionId: string
  section: string
  field?: string
  value?: unknown
  source: "ui" | "chat" | "external"
  ts: number
}

/** Dispatches lia:settings-success + lia:settings-updated with canonical detail. */
export function dispatchSettingsUpdate(detail: SettingsBroadcastDetail): void {
  if (typeof window === "undefined") return
  window.dispatchEvent(new CustomEvent("lia:settings-success", { detail }))
  window.dispatchEvent(new CustomEvent("lia:settings-updated", { detail }))
}

/**
 * Hook that installs a listener for external lia:settings-updated events.
 * When the event arrives from an external source (chat, other surface),
 * invalidates all settings queries so React Query refetches fresh data.
 *
 * Own-dispatch events (source="ui") are intentionally NOT re-fetched here
 * because React Query's mutation onSuccess already invalidates those queries.
 */
export function useSettingsBroadcast(): void {
  const queryClient = useQueryClient()

  useEffect(() => {
    const handler = (ev: Event) => {
      const detail = (ev as CustomEvent<SettingsBroadcastDetail>).detail
      // Skip our own dispatches — React Query mutation.onSuccess handles those.
      if (detail?.source === "ui") return

      // External update: invalidate all settings caches so next render shows fresh data.
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.companyProfile() })
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.hiringPolicy() })
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.settingsProgress() })
      // culture-profile + benefits use companyId in key; invalidate by prefix.
      queryClient.invalidateQueries({ queryKey: ["culture-profile"] })
      queryClient.invalidateQueries({ queryKey: ["company-benefits"] })
    }

    window.addEventListener("lia:settings-updated", handler)
    return () => window.removeEventListener("lia:settings-updated", handler)
  }, [queryClient])
}

/** Returns a stable broadcast function pre-wired with QueryClient invalidation. */
export function useSettingsBroadcastDispatch() {
  const queryClient = useQueryClient()

  return useCallback(
    (
      block: string,
      field: string,
      value: unknown,
    ): void => {
      const blockToSection: Record<string, { section: string; actionId: string }> = {
        basic: { section: "profile", actionId: "configure_profile" },
        culture: { section: "culture", actionId: "configure_culture" },
        tech: { section: "tech_stack", actionId: "configure_tech_stack" },
        policy: { section: "hiring_policies", actionId: "configure_culture" },
        workforce: { section: "workforce", actionId: "configure_workforce" },
        documents: { section: "profile", actionId: "configure_profile" },
        benefits: { section: "benefits", actionId: "configure_benefits" },
      }
      const mapping = blockToSection[block]
      if (!mapping) return

      dispatchSettingsUpdate({
        actionId: mapping.actionId,
        section: mapping.section,
        field,
        value,
        source: "ui",
        ts: Date.now(),
      })

      // Invalidate queries that were affected by the save.
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.companyProfile() })
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.hiringPolicy() })
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.settingsProgress() })
      queryClient.invalidateQueries({ queryKey: ["culture-profile"] })
      queryClient.invalidateQueries({ queryKey: ["company-benefits"] })
    },
    [queryClient],
  )
}
