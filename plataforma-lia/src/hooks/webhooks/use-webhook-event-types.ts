"use client"

/**
 * useWebhookEventTypes — canonical hook para o catalogo dinamico per-tenant.
 *
 * Audit 2026-05-20 Sprint 5 F3: substitui o catalogo hardcoded
 * `src/components/pages-agent-studio/custom-agents/webhook-types.ts:WEBHOOK_EVENTS`
 * por fetch dinamico via API endpoints F2
 * (POST /api/backend-proxy/webhook-event-types).
 *
 * Decisões Paulo 2026-05-20:
 * - A1: customize cria cópia total no DB (não override por field)
 * - B1: customize é snapshot canonical (não sincroniza com master após)
 * - C: admin tudo, recrutador create-novos OK mas não delete/update-de-outros
 *
 * Pattern canonical: useState + fetch direto (mesmo pattern de
 * `useEligibilityTemplates` em Sprint 1).
 */

import { useCallback, useEffect, useState } from "react"

export type EventCategory =
  | "candidates"
  | "jobs"
  | "interviews"
  | "offers"
  | "ats"
  | "agents"
  | "system"

export interface WebhookEventTypeData {
  event_type: string // slug canonical "namespace.action"
  label: string
  category: EventCategory
  description?: string
  payload_schema?: Record<string, unknown>
  deprecated?: boolean
  metadata?: Record<string, unknown>
}

export interface WebhookEventType {
  id: string
  company_id: string | null
  is_master_template: boolean
  parent_template_id: string | null
  data: WebhookEventTypeData
  created_at: string
  updated_at: string
  created_by: string | null
  deleted_at: string | null
}

export interface ListResponse {
  items: WebhookEventType[]
  total: number
  master_count: number
  custom_count: number
}

interface UseWebhookEventTypesResult {
  eventTypes: WebhookEventType[]
  masterCount: number
  customCount: number
  total: number
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  createCustom: (
    data: WebhookEventTypeData,
  ) => Promise<WebhookEventType | null>
  updateEventType: (
    id: string,
    data: WebhookEventTypeData,
  ) => Promise<WebhookEventType | null>
  deleteEventType: (id: string) => Promise<boolean>
  customizeMaster: (
    masterId: string,
    overrides?: WebhookEventTypeData,
  ) => Promise<WebhookEventType | null>
}

export function useWebhookEventTypes(
  options: { includeMaster?: boolean } = {},
): UseWebhookEventTypesResult {
  const { includeMaster = true } = options
  const [eventTypes, setEventTypes] = useState<WebhookEventType[]>([])
  const [masterCount, setMasterCount] = useState(0)
  const [customCount, setCustomCount] = useState(0)
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const authHeaders = useCallback((): HeadersInit => {
    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("auth_token")
        : null
    const h: HeadersInit = { "Content-Type": "application/json" }
    if (token) h["Authorization"] = `Bearer ${token}`
    return h
  }, [])

  const fetchAll = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const qs = new URLSearchParams({
        include_master: String(includeMaster),
      }).toString()
      const res = await fetch(
        `/api/backend-proxy/webhook-event-types?${qs}`,
        { headers: authHeaders() },
      )
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }
      const data: ListResponse = await res.json()
      setEventTypes(data.items || [])
      setMasterCount(data.master_count ?? 0)
      setCustomCount(data.custom_count ?? 0)
      setTotal(data.total ?? 0)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar event types")
    } finally {
      setIsLoading(false)
    }
  }, [includeMaster, authHeaders])

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  const createCustom = useCallback(
    async (data: WebhookEventTypeData) => {
      try {
        const res = await fetch("/api/backend-proxy/webhook-event-types", {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({ data }),
        })
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || err.error || `HTTP ${res.status}`)
        }
        const created: WebhookEventType = await res.json()
        await fetchAll()
        return created
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erro ao criar event type")
        return null
      }
    },
    [fetchAll, authHeaders],
  )

  const updateEventType = useCallback(
    async (id: string, data: WebhookEventTypeData) => {
      try {
        const res = await fetch(
          `/api/backend-proxy/webhook-event-types/${encodeURIComponent(id)}`,
          {
            method: "PUT",
            headers: authHeaders(),
            body: JSON.stringify({ data }),
          },
        )
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || err.error || `HTTP ${res.status}`)
        }
        const updated: WebhookEventType = await res.json()
        await fetchAll()
        return updated
      } catch (e) {
        setError(
          e instanceof Error ? e.message : "Erro ao atualizar event type",
        )
        return null
      }
    },
    [fetchAll, authHeaders],
  )

  const deleteEventType = useCallback(
    async (id: string) => {
      try {
        const res = await fetch(
          `/api/backend-proxy/webhook-event-types/${encodeURIComponent(id)}`,
          { method: "DELETE", headers: authHeaders() },
        )
        if (!res.ok && res.status !== 204) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || err.error || `HTTP ${res.status}`)
        }
        await fetchAll()
        return true
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erro ao deletar event type")
        return false
      }
    },
    [fetchAll, authHeaders],
  )

  const customizeMaster = useCallback(
    async (masterId: string, overrides?: WebhookEventTypeData) => {
      try {
        const res = await fetch(
          `/api/backend-proxy/webhook-event-types/${encodeURIComponent(masterId)}/customize`,
          {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify(overrides ? { overrides } : {}),
          },
        )
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || err.error || `HTTP ${res.status}`)
        }
        const custom: WebhookEventType = await res.json()
        await fetchAll()
        return custom
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erro ao customizar master")
        return null
      }
    },
    [fetchAll, authHeaders],
  )

  return {
    eventTypes,
    masterCount,
    customCount,
    total,
    isLoading,
    error,
    refetch: fetchAll,
    createCustom,
    updateEventType,
    deleteEventType,
    customizeMaster,
  }
}

/**
 * Flat-shape canonical compatível com o antigo WEBHOOK_EVENTS (array de strings).
 * Permite migração incremental de componentes consumindo o catalogo hardcoded
 * sem reescrever shape de props.
 */
export interface FlatWebhookEvent {
  id: string // serverId UUID
  event_type: string // slug
  label: string
  category: EventCategory
  description?: string
  payload_schema?: Record<string, unknown>
  deprecated?: boolean
  metadata?: Record<string, unknown>
  _isMaster: boolean
  _serverId: string
}

export function flattenEventType(t: WebhookEventType): FlatWebhookEvent {
  return {
    ...t.data,
    id: t.id,
    _isMaster: t.is_master_template,
    _serverId: t.id,
  }
}

export function flattenEventTypes(
  items: WebhookEventType[],
): FlatWebhookEvent[] {
  return items.map(flattenEventType)
}

/**
 * EVENT_CATEGORIES canonical — labels PT-BR para display.
 */
export const EVENT_CATEGORIES: Record<
  EventCategory,
  { label: string; color: string }
> = {
  candidates: {
    label: "Candidatos",
    color: "bg-wedo-cyan/15 text-wedo-cyan-text",
  },
  jobs: { label: "Vagas", color: "bg-wedo-purple/15 text-wedo-purple-text" },
  interviews: {
    label: "Entrevistas",
    color: "bg-status-success/15 text-status-success",
  },
  offers: {
    label: "Propostas",
    color: "bg-wedo-orange/15 text-wedo-orange-text",
  },
  ats: { label: "ATS", color: "bg-lia-bg-tertiary text-lia-text-primary" },
  agents: {
    label: "Agentes",
    color: "bg-status-warning/15 text-status-warning",
  },
  system: { label: "Sistema", color: "bg-lia-bg-tertiary text-lia-text-primary" },
}
