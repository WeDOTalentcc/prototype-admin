"use client"

/**
 * useIntegrationCatalog — canonical hook para o catalogo dinamico per-tenant.
 *
 * Audit 2026-05-20 Sprint 4 F3: substitui o catalogo hardcoded
 * `src/components/settings/integrations/integration-data.ts` (370 linhas, 16
 * entradas) por fetch dinamico via API endpoints F2
 * (GET/POST /api/backend-proxy/integration-catalog).
 *
 * Decisões Paulo 2026-05-20:
 * - A1: customize cria cópia total no DB (não override por field)
 * - B1: customize é snapshot canonical (não sincroniza com master após)
 * - C: admin tudo, recrutador create-novos OK mas não delete/update-de-outros
 *
 * Performance fix 2026-06-21: migrado para React Query com staleTime: 60_000.
 * Elimina re-fetch a cada navegação para a aba Integrações (CAUSA #2).
 */

import { useCallback } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"

export type IntegrationCategory =
  | "ai_models"
  | "ats"
  | "calendar"
  | "communication"
  | "crm_hris"
  | "mcps_apis"
  | "job_board"

export type IntegrationStatus = "production" | "coming_soon" | "deprecated"

export type ConnectAction = "oauth" | "config" | "webhook" | "none"

export interface IntegrationCapability {
  name: string
  description: string
}

export interface IntegrationMetadata {
  icon_bg?: string
  icon_color?: string
  icon_letter?: string
  is_active_provider?: boolean
  connect_action?: ConnectAction
  capabilities?: IntegrationCapability[]
  config_fields?: string[]
}

export interface IntegrationCatalogData {
  provider: string
  label: string
  category: IntegrationCategory
  logo_url?: string | null
  description: string
  full_description?: string | null
  status: IntegrationStatus
  industries_recommended?: string[]
  metadata?: IntegrationMetadata | null
}

export interface IntegrationCatalogEntry {
  id: string
  company_id: string | null
  is_master_template: boolean
  parent_template_id: string | null
  data: IntegrationCatalogData
  created_at: string
  updated_at: string
  created_by: string | null
  deleted_at: string | null
}

export interface IntegrationCatalogListResponse {
  items: IntegrationCatalogEntry[]
  total: number
  master_count: number
  custom_count: number
}

interface UseIntegrationCatalogResult {
  entries: IntegrationCatalogEntry[]
  masterCount: number
  customCount: number
  total: number
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  createCustom: (
    data: IntegrationCatalogData,
  ) => Promise<IntegrationCatalogEntry | null>
  updateEntry: (
    id: string,
    data: IntegrationCatalogData,
  ) => Promise<IntegrationCatalogEntry | null>
  deleteEntry: (id: string) => Promise<boolean>
  customizeMaster: (
    masterId: string,
    overrides?: IntegrationCatalogData,
  ) => Promise<IntegrationCatalogEntry | null>
}

const CATALOG_QUERY_KEY = "integration-catalog" as const

export function useIntegrationCatalog(
  options: {
    includeMaster?: boolean
    category?: IntegrationCategory | null
  } = {},
): UseIntegrationCatalogResult {
  const { includeMaster = true, category = null } = options
  const queryClient = useQueryClient()

  const queryKey = [CATALOG_QUERY_KEY, includeMaster, category] as const

  const {
    data,
    isLoading,
    error: queryError,
    refetch: queryRefetch,
  } = useQuery<IntegrationCatalogListResponse>({
    queryKey,
    queryFn: async () => {
      const params: Record<string, string> = {
        include_master: String(includeMaster),
      }
      if (category) params.category = category
      const qs = new URLSearchParams(params).toString()
      const res = await fetch(
        `/api/backend-proxy/integration-catalog?${qs}`,
      )
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }
      return res.json()
    },
    staleTime: 60_000,
    retry: 1,
  })

  const entries = data?.items ?? []
  const masterCount = data?.master_count ?? 0
  const customCount = data?.custom_count ?? 0
  const total = data?.total ?? 0
  const error = queryError instanceof Error
    ? queryError.message
    : queryError
      ? "Erro ao carregar catalogo"
      : null

  const refetch = useCallback(async () => {
    await queryRefetch()
  }, [queryRefetch])

  const invalidate = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: [CATALOG_QUERY_KEY] })
  }, [queryClient])

  const createCustom = useCallback(
    async (data: IntegrationCatalogData) => {
      try {
        const res = await fetch("/api/backend-proxy/integration-catalog", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ data }),
        })
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || err.error || `HTTP ${res.status}`)
        }
        const created: IntegrationCatalogEntry = await res.json()
        invalidate()
        return created
      } catch (e) {
        return null
      }
    },
    [invalidate],
  )

  const updateEntry = useCallback(
    async (id: string, data: IntegrationCatalogData) => {
      try {
        const res = await fetch(
          `/api/backend-proxy/integration-catalog/${encodeURIComponent(id)}`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ data }),
          },
        )
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || err.error || `HTTP ${res.status}`)
        }
        const updated: IntegrationCatalogEntry = await res.json()
        invalidate()
        return updated
      } catch (e) {
        return null
      }
    },
    [invalidate],
  )

  const deleteEntry = useCallback(
    async (id: string) => {
      try {
        const res = await fetch(
          `/api/backend-proxy/integration-catalog/${encodeURIComponent(id)}`,
          { method: "DELETE" },
        )
        if (!res.ok && res.status !== 204) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || err.error || `HTTP ${res.status}`)
        }
        invalidate()
        return true
      } catch (e) {
        return false
      }
    },
    [invalidate],
  )

  const customizeMaster = useCallback(
    async (masterId: string, overrides?: IntegrationCatalogData) => {
      try {
        const res = await fetch(
          `/api/backend-proxy/integration-catalog/${encodeURIComponent(masterId)}/customize`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(overrides ? { overrides } : {}),
          },
        )
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || err.error || `HTTP ${res.status}`)
        }
        const custom: IntegrationCatalogEntry = await res.json()
        invalidate()
        return custom
      } catch (e) {
        return null
      }
    },
    [invalidate],
  )

  return {
    entries,
    masterCount,
    customCount,
    total,
    isLoading,
    error,
    refetch,
    createCustom,
    updateEntry,
    deleteEntry,
    customizeMaster,
  }
}

/**
 * Flat-shape canonical compatível com o antigo `Integration` shape do
 * `integration-data.ts` hardcoded. Permite migração incremental dos
 * componentes consumindo o catalogo hardcoded sem reescrever props.
 *
 * server: { id, data: { provider, label, category, ... }, is_master_template, ... }
 * flat:   { id, name, shortDescription, fullDescription, category, status,
 *           iconBg, iconColor, iconLetter, capabilities, configFields, ... }
 */
export interface FlatIntegration {
  id: string // provider slug (canonical hardcoded compat)
  serverId: string // server UUID for mutations
  name: string
  shortDescription: string
  fullDescription: string
  category: IntegrationCategory
  status: "connected" | "not_configured" | "coming_soon"
  iconBg: string
  iconColor: string
  iconLetter: string
  capabilities: IntegrationCapability[]
  configFields?: string[]
  isActiveProvider?: boolean
  connectAction?: ConnectAction
  _isMaster: boolean
}

/**
 * Map canonical status ("production"/"coming_soon") -> legacy display status.
 * Production é mostrado como "connected" OU "not_configured" — o componente
 * consumidor decide com base em runtime checks (env, oauth).
 */
function mapStatusToLegacy(
  status: IntegrationStatus,
  fallback: "connected" | "not_configured" = "not_configured",
): "connected" | "not_configured" | "coming_soon" {
  if (status === "coming_soon") return "coming_soon"
  if (status === "deprecated") return "coming_soon"
  return fallback
}

export function flattenEntry(
  e: IntegrationCatalogEntry,
  statusOverride?: "connected" | "not_configured",
): FlatIntegration {
  const d = e.data
  const md = d.metadata ?? {}
  return {
    id: d.provider,
    serverId: e.id,
    name: d.label,
    shortDescription: d.description,
    fullDescription: d.full_description ?? d.description,
    category: d.category,
    status: mapStatusToLegacy(d.status, statusOverride ?? "not_configured"),
    iconBg: md.icon_bg ?? "bg-gray-500/10",
    iconColor: md.icon_color ?? "text-gray-600",
    iconLetter: md.icon_letter ?? d.label.slice(0, 2).toUpperCase(),
    capabilities: md.capabilities ?? [],
    configFields: md.config_fields,
    isActiveProvider: md.is_active_provider,
    connectAction: md.connect_action,
    _isMaster: e.is_master_template,
  }
}

export function flattenEntries(items: IntegrationCatalogEntry[]): FlatIntegration[] {
  return items.map((e) => flattenEntry(e))
}
