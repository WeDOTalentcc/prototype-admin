// Onda 1 F5 (2026-05-27) — canonical hook React Query.
//
// CLAUDE.md REGRA 1 settings/: server data via useQuery. Aplica-se aqui também
// porque DecisionTreeDrawer é canonical e será reutilizado em Ondas 2-3.
"use client"

import { useQuery } from "@tanstack/react-query"
import type { ExecutionReasoningResponse } from "./types"

export const DECISION_TREE_QUERY_KEY = (executionId: string | null) =>
  ["agent-monitoring", "executions", executionId, "reasoning"] as const

export interface UseExecutionReasoningResult {
  data: ExecutionReasoningResponse | undefined
  isLoading: boolean
  isError: boolean
  isLegacy: boolean // backend retornou 404 (sem reasoning_payload)
  error: Error | null
  refetch: () => void
}

async function fetchReasoning(executionId: string): Promise<ExecutionReasoningResponse> {
  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  const res = await fetch(
    `/api/backend-proxy/agent-monitoring/executions/${encodeURIComponent(executionId)}/reasoning`,
    {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    },
  )
  if (res.status === 404) {
    // Sentinela canonical para legacy executions (sem reasoning_payload).
    const err = new Error("LEGACY_NO_REASONING") as Error & { status?: number }
    err.status = 404
    throw err
  }
  if (!res.ok) {
    const err = new Error(`Failed to fetch reasoning: ${res.status}`) as Error & {
      status?: number
    }
    err.status = res.status
    throw err
  }
  return res.json()
}

export function useExecutionReasoning(executionId: string | null): UseExecutionReasoningResult {
  const query = useQuery<ExecutionReasoningResponse, Error & { status?: number }>({
    queryKey: DECISION_TREE_QUERY_KEY(executionId),
    queryFn: () => fetchReasoning(executionId as string),
    enabled: executionId !== null,
    staleTime: 60_000, // execuções terminadas não mudam
    retry: (failureCount, error) => {
      // Não retry em 404 (legacy) ou 403 (cross-tenant).
      const status = (error as Error & { status?: number })?.status
      if (status === 404 || status === 403) return false
      return failureCount < 2
    },
  })
  const status = query.error?.status
  return {
    data: query.data,
    isLoading: query.isLoading,
    isError: query.isError && status !== 404,
    isLegacy: status === 404,
    error: query.error,
    refetch: query.refetch,
  }
}
