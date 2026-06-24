/**
 * useDigestSchedule — hook para frequência de digest por usuário (Fatia 2 — Decisão 3).
 *
 * Lê/escreve a frequência efetiva do usuário autenticado via
 * /api/backend-proxy/notifications/digest-schedule.
 *
 * Precedência (gerida no backend): user override > company default > HiringPolicy.
 *
 * Multi-tenancy: company_id NUNCA enviado no payload (REGRA 2).
 * Dispatch broadcast: dispatchSettingsUpdate após PUT.
 */
"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { SETTINGS_QUERY_KEYS, dispatchSettingsUpdate } from "@/hooks/settings/useSettingsBroadcast"

export type DigestFrequency = "daily" | "twice_daily" | "weekly" | "monthly"
export type DigestScheduleSource = "user" | "company_default" | "policy_fallback"

export interface DigestSchedule {
  frequency: DigestFrequency
  preferred_time_morning: string | null
  preferred_time_afternoon: string | null
  quiet_hours_start: number | null
  quiet_hours_end: number | null
  source: DigestScheduleSource
  user_id: string | null
}

export interface DigestScheduleRequest {
  frequency: DigestFrequency
  preferred_time_morning?: string | null
  preferred_time_afternoon?: string | null
  quiet_hours_start?: number | null
  quiet_hours_end?: number | null
}

const USER_SCHEDULE_URL = "/api/backend-proxy/notifications/digest-schedule"
const COMPANY_SCHEDULE_URL = "/api/backend-proxy/notifications/digest-schedule/company"

async function fetchSchedule(url: string): Promise<DigestSchedule> {
  const r = await fetch(url)
  if (!r.ok) throw new Error(`digest-schedule fetch failed: ${r.status}`)
  return r.json()
}

async function putSchedule(url: string, body: DigestScheduleRequest): Promise<DigestSchedule> {
  const r = await fetch(url, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    // company_id NUNCA no payload (multi-tenancy via JWT)
    body: JSON.stringify(body),
  })
  if (!r.ok) {
    const err = await r.json().catch(() => ({}))
    throw new Error(err?.detail ?? `digest-schedule update failed: ${r.status}`)
  }
  return r.json()
}

// ---------------------------------------------------------------------------
// Hook: per-user override
// ---------------------------------------------------------------------------

export function useDigestSchedule() {
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.digestSchedule(),
    queryFn: () => fetchSchedule(USER_SCHEDULE_URL),
    staleTime: 30_000,
  })

  const mutation = useMutation({
    mutationFn: (body: DigestScheduleRequest) => putSchedule(USER_SCHEDULE_URL, body),
    onSuccess: (updated) => {
      queryClient.setQueryData(SETTINGS_QUERY_KEYS.digestSchedule(), updated)
      dispatchSettingsUpdate({ actionId: "configure_notifications", section: "notifications", source: "ui", ts: Date.now() })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async () => {
      const r = await fetch(USER_SCHEDULE_URL, { method: "DELETE" })
      if (!r.ok) throw new Error(`digest-schedule delete failed: ${r.status}`)
      return r.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.digestSchedule() })
      dispatchSettingsUpdate({ actionId: "configure_notifications", section: "notifications", source: "ui", ts: Date.now() })
    },
  })

  const frequency: DigestFrequency = data?.frequency ?? "weekly"
  const source: DigestScheduleSource = data?.source ?? "policy_fallback"
  const hasPersonalOverride = source === "user"

  return {
    frequency,
    source,
    hasPersonalOverride,
    schedule: data ?? null,
    isLoading,
    error,
    setFrequency: (freq: DigestFrequency) => mutation.mutateAsync({ frequency: freq }),
    updateSchedule: (body: DigestScheduleRequest) => mutation.mutateAsync(body),
    resetToCompanyDefault: () => deleteMutation.mutateAsync(),
    isSaving: mutation.isPending || deleteMutation.isPending,
  }
}

// ---------------------------------------------------------------------------
// Hook: company default (admin-only write, qualquer papel lê)
// ---------------------------------------------------------------------------

export function useCompanyDigestSchedule() {
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.digestScheduleCompany(),
    queryFn: () => fetchSchedule(COMPANY_SCHEDULE_URL),
    staleTime: 60_000,
  })

  const mutation = useMutation({
    mutationFn: (body: DigestScheduleRequest) => putSchedule(COMPANY_SCHEDULE_URL, body),
    onSuccess: (updated) => {
      queryClient.setQueryData(SETTINGS_QUERY_KEYS.digestScheduleCompany(), updated)
      dispatchSettingsUpdate({ actionId: "configure_notifications", section: "notifications", source: "ui", ts: Date.now() })
    },
  })

  return {
    frequency: data?.frequency ?? "weekly",
    source: data?.source ?? "policy_fallback",
    schedule: data ?? null,
    isLoading,
    error,
    setCompanyFrequency: (freq: DigestFrequency) => mutation.mutateAsync({ frequency: freq }),
    isSaving: mutation.isPending,
  }
}
