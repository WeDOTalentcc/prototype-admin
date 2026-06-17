/**
 * useSettingsBroadcast.ts — canonical event broadcast hook (Sprint 2.2, 2026-05-26)
 *
 * Extraído de use-company-settings-cards.ts. Responsabilidade única:
 * dispatch de eventos lia:settings-updated / lia:settings-success e
 * escuta de atualizações externas (LIA chat, outras superfícies).
 *
 * GAP-09-005 (Sprint 5D): cross-tab sync via BroadcastChannel API.
 * When settings change in TAB A, all other tabs invalidate their
 * React Query caches and refetch fresh data automatically.
 *
 * Substitui o hack lastSelfDispatchRef: React Query invalida queries
 * em onSuccess — sem dedup manual necessário. O listener agora só
 * dispara invalidateQueries (não loadAll) evitando double-fetch.
 */

"use client"

import { useEffect, useCallback } from "react"
import { useQueryClient, QueryClient } from "@tanstack/react-query"

const BROADCAST_CHANNEL_NAME = "lia-settings-sync"

export const SETTINGS_QUERY_KEYS = {
  companyProfile: () => ["company-profile"] as const,
  cultureProfile: (companyId: string) => ["culture-profile", companyId] as const,
  benefits: (companyId: string) => ["company-benefits", companyId] as const,
  hiringPolicy: () => ["hiring-policy"] as const,
  settingsProgress: () => ["settings-progress"] as const,
  automations: (companyId: string) => ["automations", companyId] as const,
  digestSchedule: () => ["digest-schedule"] as const,
  digestScheduleCompany: () => ["digest-schedule-company"] as const,
  offerRules: () => ["offer-rules"] as const,
  billing: () => ["billing"] as const,
  billingUsage: () => ["billing-usage"] as const,
  billingInvoices: () => ["billing-invoices"] as const,
  billingPaymentMethods: () => ["billing-payment-methods"] as const,
} as const

export type SettingsBroadcastDetail = {
  actionId: string
  section: string
  field?: string
  value?: unknown
  source: "ui" | "chat" | "external"
  ts: number
}

function invalidateAllSettingsQueries(queryClient: QueryClient): void {
  queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.companyProfile() })
  queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.hiringPolicy() })
  queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.settingsProgress() })
  queryClient.invalidateQueries({ queryKey: ["culture-profile"] })
  queryClient.invalidateQueries({ queryKey: ["company-benefits"] })
}

function broadcastCrossTab(detail: SettingsBroadcastDetail): void {
  if (typeof window === "undefined" || !("BroadcastChannel" in window)) return
  try {
    const ch = new BroadcastChannel(BROADCAST_CHANNEL_NAME)
    ch.postMessage(detail)
    ch.close()
  } catch {
    // BroadcastChannel blocked or unsupported — degrade silently
  }
}

/** Dispatches lia:settings-success + lia:settings-updated with canonical detail. */
export function dispatchSettingsUpdate(detail: SettingsBroadcastDetail): void {
  if (typeof window === "undefined") return
  window.dispatchEvent(new CustomEvent("lia:settings-success", { detail }))
  window.dispatchEvent(new CustomEvent("lia:settings-updated", { detail }))
  if (detail.source === "ui") {
    broadcastCrossTab(detail)
  }
}

/**
 * Hook that installs listeners for settings updates:
 * 1. Same-tab: lia:settings-updated CustomEvent (chat, external sources)
 * 2. Cross-tab: BroadcastChannel "lia-settings-sync" (GAP-09-005)
 *
 * Own-dispatch events (source="ui") are intentionally NOT re-fetched here
 * because React Query's mutation onSuccess already invalidates those queries.
 * Cross-tab messages always trigger invalidation (they originate from a
 * different tab's "ui" source).
 */
export function useSettingsBroadcast(): void {
  const queryClient = useQueryClient()

  useEffect(() => {
    const handler = (ev: Event) => {
      const detail = (ev as CustomEvent<SettingsBroadcastDetail>).detail
      if (detail?.source === "ui") return
      invalidateAllSettingsQueries(queryClient)
    }

    window.addEventListener("lia:settings-updated", handler)
    return () => window.removeEventListener("lia:settings-updated", handler)
  }, [queryClient])

  useEffect(() => {
    if (typeof window === "undefined" || !("BroadcastChannel" in window)) return

    const channel = new BroadcastChannel(BROADCAST_CHANNEL_NAME)
    channel.onmessage = () => {
      invalidateAllSettingsQueries(queryClient)
    }
    return () => channel.close()
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
        policy: { section: "hiring_policies", actionId: "configure_hiring_policy" },
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

      invalidateAllSettingsQueries(queryClient)
    },
    [queryClient],
  )
}
