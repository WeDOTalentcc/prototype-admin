"use client"

import useSWR from "swr"

import type {
  AgentCategory,
  AgentSector,
  AgentTemplateCatalog,
} from "@/types/agent-template-catalog"

/**
 * Hook canonical pra consumir agent_template_catalog do backend
 * (Sprint 3 Caminho B). Substitui o legacy `agent-templates-data.ts`
 * deletado na mesma sprint.
 *
 * Pattern: SWR com dedupingInterval 5min (catálogo é seed read-mostly).
 * Per-tenant write não suportado em V1 (templates globais).
 */

interface UseAgentTemplateCatalogOptions {
  category?: string | null
  sector?: string | null
  activeOnly?: boolean
}

interface UseAgentTemplateCatalogReturn {
  data: AgentTemplateCatalog[]
  isLoading: boolean
  error: string | null
  mutate: () => Promise<unknown>
}

interface UseAgentCategoriesReturn {
  data: AgentCategory[]
  isLoading: boolean
  error: string | null
  mutate: () => Promise<unknown>
}

interface UseAgentSectorsReturn {
  data: AgentSector[]
  isLoading: boolean
  error: string | null
  mutate: () => Promise<unknown>
}

const FIVE_MIN_MS = 5 * 60 * 1000

const jsonFetcher = async (url: string) => {
  const r = await fetch(url)
  if (!r.ok) {
    throw new Error(`HTTP ${r.status}`)
  }
  const payload = await r.json()
  // Pattern canonical do projeto: proxy Next /api/backend-proxy/* wrappa em
  // envelope {ok, data, meta}. Outros hooks (use-ai-credits.ts:137) desempacotam
  // .data. Defensive: tolerante a backend direct (array sem envelope).
  if (
    payload &&
    typeof payload === "object" &&
    !Array.isArray(payload) &&
    "data" in payload &&
    Array.isArray((payload as { data: unknown }).data)
  ) {
    return (payload as { data: unknown[] }).data
  }
  return payload
}

function buildCatalogUrl(opts?: UseAgentTemplateCatalogOptions): string {
  const params = new URLSearchParams()
  if (opts?.category && opts.category !== "all") {
    params.set("category", opts.category)
  }
  if (opts?.sector) {
    params.set("sector", opts.sector)
  }
  if (opts?.activeOnly !== undefined) {
    params.set("active_only", String(opts.activeOnly))
  }
  const qs = params.toString()
  return `/api/backend-proxy/agent-template-catalog${qs ? "?" + qs : ""}`
}

export function useAgentTemplateCatalog(
  options?: UseAgentTemplateCatalogOptions,
): UseAgentTemplateCatalogReturn {
  const { data, error, isLoading, mutate } = useSWR<AgentTemplateCatalog[]>(
    buildCatalogUrl(options),
    jsonFetcher,
    { dedupingInterval: FIVE_MIN_MS },
  )

  return {
    data: data ?? [],
    isLoading,
    error: error ? (error as Error).message : null,
    mutate,
  }
}

export function useAgentCategories(): UseAgentCategoriesReturn {
  const { data, error, isLoading, mutate } = useSWR<AgentCategory[]>(
    "/api/backend-proxy/agent-template-catalog/categories",
    jsonFetcher,
    { dedupingInterval: FIVE_MIN_MS },
  )
  return {
    data: data ?? [],
    isLoading,
    error: error ? (error as Error).message : null,
    mutate,
  }
}

export function useAgentSectors(): UseAgentSectorsReturn {
  const { data, error, isLoading, mutate } = useSWR<AgentSector[]>(
    "/api/backend-proxy/agent-template-catalog/sectors",
    jsonFetcher,
    { dedupingInterval: FIVE_MIN_MS },
  )
  return {
    data: data ?? [],
    isLoading,
    error: error ? (error as Error).message : null,
    mutate,
  }
}
