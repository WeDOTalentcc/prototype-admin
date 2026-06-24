"use client"

/**
 * useIntegrationsData — canonical hook for IntegrationsHub server state.
 *
 * Fetches calendar health, integration status, LLM config, and ATS connections
 * via React Query. Derives enriched integration list combining dynamic catalog
 * entries with live connection statuses.
 *
 * Extraction: Task 3.3 (2026-05-26) — reduced IntegrationsHub to ≤200 LOC.
 * Performance fix 2026-06-21: 4 separate fetches consolidated into 1 via
 * GET /api/backend-proxy/integrations/summary (asyncio.gather on backend).
 */

import { useMemo } from "react"
import { useQuery } from "@tanstack/react-query"
import {
  integrations,
  type Integration,
} from "@/components/settings/integrations/integration-data"
import { useIntegrationCatalog, flattenEntries, type FlatIntegration } from "@/hooks/integrations/use-integration-catalog"
import { apiFetch } from "@/lib/api/api-fetch"

// ---------------------------------------------------------------------------
// Summary response types (mirrors IntegrationsSummaryResponse on backend)
// ---------------------------------------------------------------------------

interface CalendarSummary {
  graph_configured: boolean
  google_configured: boolean
}

interface TeamsSummary {
  configured: boolean
  source: string
}

interface LLMConfigSummary {
  company_id: string
  primary_provider: string
  fallback_order: string[]
  providers: Record<string, { api_key?: string; model?: string; is_active?: boolean }>
  routing: Record<string, string>
  is_active: boolean
}

interface ATSConnectionSummary {
  provider: string
  is_active: boolean
}

interface IntegrationsSummaryData {
  calendar: CalendarSummary
  teams: TeamsSummary
  llm_config: LLMConfigSummary
  ats_connections: ATSConnectionSummary[]
}

const ATS_PROVIDER_MAP: Record<string, string> = { gupy: "gupy", pandape: "pandape", merge: "merge" }  // P1-13 audit: merge e provider ATS valido (backend SUPPORTED_PROVIDERS)
const AI_PROVIDER_MAP: Record<string, string> = { gemini: "gemini", claude: "claude", openai: "openai" }

export function useIntegrationsData() {
  // Single fetch aggregating: calendar health + teams status + LLM config + ATS connections
  const {
    data: summaryData,
    refetch: refetchSummary,
  } = useQuery<IntegrationsSummaryData>({
    queryKey: ["integrations-summary"],
    queryFn: () =>
      apiFetch("/api/backend-proxy/integrations/summary").then((r) => {
        if (!r.ok) throw new Error("Failed to fetch integrations summary: " + r.status)
        return r.json()
      }),
    staleTime: 30_000,
    retry: 1,
  })

  const { entries: catalogEntries, isLoading: catalogLoading } = useIntegrationCatalog({ includeMaster: true })

  const baseIntegrations = useMemo<Integration[]>(() => {
    const flat: FlatIntegration[] = catalogEntries.length > 0 ? flattenEntries(catalogEntries) : []
    return flat.length > 0 ? (flat as unknown as Integration[]) : integrations
  }, [catalogEntries])

  // Derived values from consolidated summary
  const calendarHealth = summaryData?.calendar
  const teamsStatusData = summaryData?.teams
  const llmConfig = summaryData?.llm_config ?? null
  const atsConnections = summaryData?.ats_connections ?? []

  const googleStatus = calendarHealth?.google_configured ? "connected" : ("idle" as const)
  const microsoftStatus = calendarHealth?.graph_configured ? "connected" : ("not_configured" as const)
  const teamsConfigured = teamsStatusData?.configured ?? false
  const teamsStatus = teamsConfigured ? "configured" : ("not_configured" as const)
  const activeProvider = llmConfig?.primary_provider ?? "gemini"

  const enrichedIntegrations = useMemo<Integration[]>(() => {
    return baseIntegrations.map((integration) => {
      if (integration.id === "google-calendar") {
        return { ...integration, status: googleStatus === "connected" ? ("connected" as const) : integration.status }
      }
      if (integration.id === "microsoft-calendar") {
        return { ...integration, status: microsoftStatus === "connected" ? ("connected" as const) : integration.status }
      }
      if (integration.id === "teams") {
        return { ...integration, status: teamsStatus === "configured" ? ("connected" as const) : ("not_configured" as const) }
      }
      if (integration.category === "ai_models") {
        const provKey = AI_PROVIDER_MAP[integration.id]
        const hasOwnKey = !!(llmConfig?.providers?.[provKey]?.api_key)
        const isActive = provKey === activeProvider
        const usingSystemKey = isActive && !hasOwnKey
        return {
          ...integration,
          isActiveProvider: isActive,
          usingSystemKey,
          status: (hasOwnKey || usingSystemKey ? "connected" : integration.status) as "connected" | "not_configured" | "coming_soon",
        }
      }
      if (integration.category === "ats" && ATS_PROVIDER_MAP[integration.id]) {
        const conn = atsConnections.find((c) => c.provider?.toLowerCase() === ATS_PROVIDER_MAP[integration.id])
        if (conn?.is_active) return { ...integration, status: "connected" as const }
      }
      return integration
    })
  }, [baseIntegrations, googleStatus, microsoftStatus, teamsStatus, activeProvider, atsConnections, llmConfig])

  // Backward-compatible refetch: single refetch triggers summary reload
  const refetchTeamsStatus = refetchSummary
  const refetchLlmConfig = refetchSummary

  return {
    enrichedIntegrations,
    catalogLoading,
    googleStatus,
    microsoftStatus,
    teamsStatus,
    refetchTeamsStatus,
    llmConfig,
    refetchLlmConfig,
  }
}
