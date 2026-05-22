"use client"

/**
 * WT-2022 Camada IA Proativa: hook canonical para consumir hints
 * scheduler-driven (1x/hora via Celery beat task).
 *
 * Diferente do `useProactiveActions` (actions candidato-especificas), este
 * hook le hints ENVIRONMENTAIS: profile incompleto, DSR vencido, pipeline
 * stuck, etc.
 *
 * Polling: 60s. Razao: hints sao gerados 1x/hora, polling 60s da janela
 * de UX ~60s pos-detection sem stressar backend.
 *
 * Endpoint backend: /api/v1/proactive-hints/ (proxy via
 * /api/backend-proxy/proactive-hints/).
 */
import useSWR from "swr"
import { useCallback } from "react"

export type ProactiveHintSeverity = "low" | "medium" | "high" | "critical"

export interface ProactiveHint {
  id: string
  detector: string
  title: string
  message: string
  severity: ProactiveHintSeverity
  action: string | null
  action_params: Record<string, unknown>
  related_job_id: string | null
  related_candidate_id: string | null
  created_at: string | null
  expires_at: string | null
}

export interface ProactiveHintsResponse {
  hints: ProactiveHint[]
  count: number
}

const fetcher = async (url: string): Promise<ProactiveHintsResponse> => {
  const res = await fetch(url, {
    method: "GET",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
  })
  if (!res.ok) {
    throw new Error(`proactive-hints fetch failed: ${res.status}`)
  }
  return res.json() as Promise<ProactiveHintsResponse>
}

export interface UseProactiveHintsResult {
  hints: ProactiveHint[]
  count: number
  isLoading: boolean
  isError: boolean
  dismiss: (hintId: string) => Promise<void>
  refresh: () => Promise<ProactiveHintsResponse | undefined>
}

const SEVERITY_ORDER: Record<ProactiveHintSeverity, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
}

export function useProactiveHints(): UseProactiveHintsResult {
  const { data, error, isLoading, mutate } = useSWR<ProactiveHintsResponse>(
    "/api/backend-proxy/proactive-hints",
    fetcher,
    {
      refreshInterval: 60_000,
      revalidateOnFocus: true,
      shouldRetryOnError: true,
      errorRetryCount: 3,
    },
  )

  const dismiss = useCallback(
    async (hintId: string): Promise<void> => {
      // Optimistic update — remove imediato + revalida.
      await mutate(
        (current) => {
          if (!current) return current
          return {
            hints: current.hints.filter((h) => h.id !== hintId),
            count: Math.max(0, current.count - 1),
          }
        },
        { revalidate: false },
      )

      try {
        const res = await fetch(
          `/api/backend-proxy/proactive-hints/${encodeURIComponent(hintId)}/dismiss`,
          {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
          },
        )
        if (!res.ok) {
          throw new Error(`dismiss failed: ${res.status}`)
        }
      } finally {
        // Em qualquer caso (success ou erro), revalida do servidor.
        await mutate()
      }
    },
    [mutate],
  )

  const sortedHints = (data?.hints ?? [])
    .slice()
    .sort(
      (a, b) =>
        SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity] ||
        (a.created_at ?? "").localeCompare(b.created_at ?? ""),
    )

  return {
    hints: sortedHints,
    count: data?.count ?? sortedHints.length,
    isLoading,
    isError: Boolean(error),
    dismiss,
    refresh: () => mutate(),
  }
}
