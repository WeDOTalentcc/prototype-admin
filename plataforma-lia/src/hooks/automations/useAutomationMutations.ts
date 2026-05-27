"use client"

/**
 * useAutomationMutations — P2-2 Sprint A.4 canonical hook.
 *
 * Wraps React Query mutations sobre endpoints CRUD de automations.
 * Inclui optimistic update + invalidation + error handling fail-CLOSED.
 *
 * Audit ref: AUTOMATIONS_FRONTEND_AUDIT.md P1-4 (zero useMutation) +
 * AUTOMATIONS_SPRINT_PLAN_ADR.md Sprint A.4.
 */

import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query"
import { apiFetch } from "@/lib/api/api-fetch"

const QUERY_KEY_AUTOMATIONS = ["automations"] as const
const QUERY_KEY_TRIGGER_TYPES = ["automations", "trigger-types"] as const
const QUERY_KEY_ACTION_TYPES = ["automations", "action-types"] as const
const QUERY_KEY_OPERATORS = ["automations", "operators"] as const
const QUERY_KEY_CONDITION_FIELDS = ["automations", "condition-fields"] as const

export interface AutomationCondition {
  field: string
  operator: string
  value: unknown
}

export interface AutomationPayload {
  id?: string
  name?: string
  trigger_type: string
  trigger_data?: Record<string, unknown>
  action_type: string
  action_data?: Record<string, unknown>
  conditions?: AutomationCondition[]
  is_active?: boolean
}

export interface AutomationResponse extends AutomationPayload {
  id: string
  is_active: boolean
  executions_count: number
  last_executed_at: string | null
  success_rate: number | null
  created_at: string
  updated_at: string
}

// ─── Query hooks ────────────────────────────────────────────────────

export function useAutomationsList() {
  return useQuery({
    queryKey: QUERY_KEY_AUTOMATIONS,
    queryFn: async (): Promise<AutomationResponse[]> => {
      const res = await apiFetch("/api/backend-proxy/automations")
      if (!res.ok) {
        // P1-4 audit: fail-CLOSED (NUNCA silent fallback)
        throw new Error(`Falha ao carregar automacoes: ${res.status}`)
      }
      const data = await res.json()
      if (Array.isArray(data)) return data as AutomationResponse[]
      if (data && Array.isArray(data.automations)) return data.automations as AutomationResponse[]
      if (data && Array.isArray(data.items)) return data.items as AutomationResponse[]
      return []
    },
    staleTime: 30_000,
  })
}

export function useTriggerTypes() {
  return useQuery({
    queryKey: QUERY_KEY_TRIGGER_TYPES,
    queryFn: async () => {
      const res = await apiFetch("/api/backend-proxy/automations/trigger-types/available")
      if (!res.ok) throw new Error(`Falha trigger-types: ${res.status}`)
      return (await res.json()) as unknown
    },
    staleTime: 5 * 60_000,
  })
}

export function useActionTypes() {
  return useQuery({
    queryKey: QUERY_KEY_ACTION_TYPES,
    queryFn: async () => {
      const res = await apiFetch("/api/backend-proxy/automations/action-types/available")
      if (!res.ok) throw new Error(`Falha action-types: ${res.status}`)
      return (await res.json()) as unknown
    },
    staleTime: 5 * 60_000,
  })
}

export function useOperators() {
  return useQuery({
    queryKey: QUERY_KEY_OPERATORS,
    queryFn: async () => {
      const res = await apiFetch("/api/backend-proxy/automations/operators/available")
      if (!res.ok) throw new Error(`Falha operators: ${res.status}`)
      return (await res.json()) as unknown
    },
    staleTime: 5 * 60_000,
  })
}

export function useConditionFields() {
  return useQuery({
    queryKey: QUERY_KEY_CONDITION_FIELDS,
    queryFn: async () => {
      const res = await apiFetch("/api/backend-proxy/automations/condition-fields/available")
      if (!res.ok) throw new Error(`Falha condition-fields: ${res.status}`)
      return (await res.json()) as unknown
    },
    staleTime: 5 * 60_000,
  })
}


export function useAutomationLogs(id: string | null) {
  return useQuery({
    queryKey: ["automation", id, "logs"] as const,
    queryFn: async () => {
      const res = await apiFetch(
        `/api/backend-proxy/automations/${encodeURIComponent(id!)}/logs`,
      )
      if (!res.ok) throw new Error(`Falha logs: ${res.status}`)
      return (await res.json()) as unknown
    },
    enabled: !!id,
    staleTime: 10_000,
  })
}

// ─── Mutations ──────────────────────────────────────────────────────

export function useCreateAutomation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: AutomationPayload): Promise<AutomationResponse> => {
      const res = await apiFetch("/api/backend-proxy/automations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.text().catch(() => "")
        throw new Error(`Falha ao criar automacao: ${res.status} ${err}`)
      }
      return (await res.json()) as AutomationResponse
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY_AUTOMATIONS })
    },
  })
}

export function useUpdateAutomation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      id,
      ...payload
    }: AutomationPayload & { id: string }): Promise<AutomationResponse> => {
      const res = await apiFetch(
        `/api/backend-proxy/automations/${encodeURIComponent(id)}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        },
      )
      if (!res.ok) {
        const err = await res.text().catch(() => "")
        throw new Error(`Falha update: ${res.status} ${err}`)
      }
      return (await res.json()) as AutomationResponse
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY_AUTOMATIONS })
      queryClient.invalidateQueries({ queryKey: ["automation", variables.id] })
    },
  })
}

interface DeleteContext {
  previous: AutomationResponse[] | undefined
}

export function useDeleteAutomation() {
  const queryClient = useQueryClient()
  return useMutation<void, Error, string, DeleteContext>({
    mutationFn: async (id: string): Promise<void> => {
      const res = await apiFetch(
        `/api/backend-proxy/automations/${encodeURIComponent(id)}`,
        { method: "DELETE" },
      )
      if (!res.ok) throw new Error(`Falha delete: ${res.status}`)
    },
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: QUERY_KEY_AUTOMATIONS })
      const previous = queryClient.getQueryData<AutomationResponse[]>(QUERY_KEY_AUTOMATIONS)
      queryClient.setQueryData<AutomationResponse[]>(
        QUERY_KEY_AUTOMATIONS,
        (old) => (old ?? []).filter((a) => a.id !== id),
      )
      return { previous }
    },
    onError: (_err, _id, context) => {
      if (context?.previous) {
        queryClient.setQueryData(QUERY_KEY_AUTOMATIONS, context.previous)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY_AUTOMATIONS })
    },
  })
}

export function useTestAutomation() {
  return useMutation({
    mutationFn: async ({
      id,
      dryRunPayload,
    }: {
      id: string
      dryRunPayload?: Record<string, unknown>
    }) => {
      const res = await apiFetch(
        `/api/backend-proxy/automations/${encodeURIComponent(id)}/test`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(dryRunPayload ?? {}),
        },
      )
      if (!res.ok) throw new Error(`Falha test: ${res.status}`)
      return (await res.json()) as unknown
    },
  })
}

interface ToggleContext {
  previous: AutomationResponse[] | undefined
}

export function useToggleAutomationActive() {
  const queryClient = useQueryClient()
  return useMutation<
    AutomationResponse,
    Error,
    { id: string; isActive: boolean },
    ToggleContext
  >({
    mutationFn: async ({ id, isActive }) => {
      const res = await apiFetch(
        `/api/backend-proxy/automations/${encodeURIComponent(id)}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ is_active: isActive }),
        },
      )
      if (!res.ok) throw new Error(`Falha toggle: ${res.status}`)
      return (await res.json()) as AutomationResponse
    },
    onMutate: async ({ id, isActive }) => {
      await queryClient.cancelQueries({ queryKey: QUERY_KEY_AUTOMATIONS })
      const previous = queryClient.getQueryData<AutomationResponse[]>(QUERY_KEY_AUTOMATIONS)
      queryClient.setQueryData<AutomationResponse[]>(
        QUERY_KEY_AUTOMATIONS,
        (old) => (old ?? []).map((a) => (a.id === id ? { ...a, is_active: isActive } : a)),
      )
      return { previous }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(QUERY_KEY_AUTOMATIONS, context.previous)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY_AUTOMATIONS })
    },
  })
}

export function useTriggerAutomation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: Record<string, unknown>) => {
      const res = await apiFetch("/api/backend-proxy/automations/trigger", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error(`Falha trigger: ${res.status}`)
      return (await res.json()) as unknown
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY_AUTOMATIONS })
    },
  })
}
