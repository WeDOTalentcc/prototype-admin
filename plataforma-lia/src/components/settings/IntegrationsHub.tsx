"use client"

import React, { useState, useEffect, useMemo, useCallback } from "react"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import { tabStyles, textStyles } from "@/lib/design-tokens"
import {
  Search,
  Brain,
  Briefcase,
  Calendar,
  MessageCircle,
  Building,
  Code,
  Plug,
} from "lucide-react"
import { useTranslations } from "next-intl"
import {
  categories,
  integrations,
  type Integration,
  type IntegrationCategory,
} from "./integrations/integration-data"
import { IntegrationCard } from "./integrations/IntegrationCard"
import { IntegrationDetailDrawer } from "./integrations/IntegrationDetailDrawer"
import { useIntegrationCatalog, flattenEntries, type FlatIntegration } from "@/hooks/integrations/use-integration-catalog"
import { useCurrentCompany } from "@/hooks/company/use-current-company"
import { apiFetch } from "@/lib/api/api-fetch"

interface LLMConfigData {
  company_id: string
  primary_provider: string
  fallback_order: string[]
  providers: Record<string, { api_key?: string; model?: string; is_active?: boolean }>
  routing: Record<string, string>
  is_active: boolean
}

const categoryIcons: Record<string, React.ReactNode> = {
  all: <Plug className="w-3.5 h-3.5" />,
  ai_models: <Brain className="w-3.5 h-3.5" />,
  ats: <Briefcase className="w-3.5 h-3.5" />,
  calendar: <Calendar className="w-3.5 h-3.5" />,
  communication: <MessageCircle className="w-3.5 h-3.5" />,
  crm_hris: <Building className="w-3.5 h-3.5" />,
  mcps_apis: <Code className="w-3.5 h-3.5" />,
}

const tabToCategoryMap: Record<string, IntegrationCategory | "all"> = {
  "all": "all",
  "ai-models": "ai_models",
  "ats": "ats",
  "calendar": "calendar",
  "communication": "communication",
  "crm-hris": "crm_hris",
  "mcps-apis": "mcps_apis",
}

interface IntegrationsHubProps {
  activeSubsection: string
}

export function IntegrationsHub({ activeSubsection }: IntegrationsHubProps) {
  const t = useTranslations("settings")
  const { companyId, tenantId } = useCurrentCompany()
  const effectiveCompanyId = tenantId || companyId
  const [activeTab, setActiveTab] = useState(activeSubsection || "all")
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)

  const [googleStatus, setGoogleStatus] = useState<"idle" | "loading" | "connected" | "error">("idle")
  const [microsoftStatus, setMicrosoftStatus] = useState<"loading" | "connected" | "not_configured">("loading")
  const [teamsStatus, setTeamsStatus] = useState<"loading" | "configured" | "not_configured">("loading")
  const [activeProvider, setActiveProvider] = useState<string>("gemini")
  const [llmConfig, setLlmConfig] = useState<LLMConfigData | null>(null)
  const [atsConnections, setAtsConnections] = useState<Array<{ provider: string; is_active: boolean }>>([])
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // Sprint 4 canonical (2026-05-21): fetch dynamic catalog from DB.
  // Falls back to hardcoded `integrations` if API fails (transitional).
  const { entries: catalogEntries, isLoading: catalogLoading, error: catalogError } = useIntegrationCatalog({ includeMaster: true })
  const dynamicIntegrations: FlatIntegration[] = useMemo(
    () => (catalogEntries.length > 0 ? flattenEntries(catalogEntries) : []),
    [catalogEntries],
  )
  const baseIntegrations = useMemo(
    () => (dynamicIntegrations.length > 0 ? (dynamicIntegrations as unknown as Integration[]) : integrations),
    [dynamicIntegrations],
  )

  useEffect(() => {
    setActiveTab(activeSubsection || "all")
  }, [activeSubsection])

  const fetchLlmConfig = useCallback(() => {
    apiFetch("/api/backend-proxy/llm-config")
      .then((r) => {
        if (!r.ok) throw new Error("Failed to fetch LLM config")
        return r.json()
      })
      .then((data: LLMConfigData) => {
        setLlmConfig(data)
        if (data.primary_provider) {
          setActiveProvider(data.primary_provider)
        }
      })
      .catch(() => {
        // Non-fatal: leave llmConfig as null. UI degrada graciosamente.
      })
  }, [])

  useEffect(() => {
    apiFetch("/api/backend-proxy/calendar/health")
      .then((r) => r.json())
      .then((data) => {
        setMicrosoftStatus(data.graph_configured ? "connected" : "not_configured")
        if (data.google_configured) {
          setGoogleStatus("connected")
        }
      })
      .catch(() => setMicrosoftStatus("not_configured"))

    apiFetch("/api/backend-proxy/integrations/status")
      .then((r) => {
        if (!r.ok) throw new Error("Failed to fetch integrations status")
        return r.json()
      })
      .then((data) => {
        if (data.teams?.configured) {
          setTeamsStatus("configured")
        } else {
          setTeamsStatus("not_configured")
        }
      })
      .catch(() => setTeamsStatus("not_configured"))

    fetchLlmConfig()

    apiFetch("/api/backend-proxy/ats/connections")
      .then((r) => {
        if (!r.ok) throw new Error("Failed to fetch ATS connections")
        return r.json()
      })
      .then((data: Array<{ provider: string; is_active: boolean }>) => {
        setAtsConnections(data)
      })
      .catch(() => setAtsConnections([]))
  }, [fetchLlmConfig])


  const handleConnectGoogle = async () => {
    setGoogleStatus("loading")
    setErrorMsg(null)
    try {
      // Audit Wave 3 (2026-05-21) — P0.E: usar useCurrentCompany em vez de literal "current".
      // Backend resolve company_id do JWT via require_company_id_strict_match, mas
      // mandar string canonical evita 400/fallback ambíguo.
      if (!effectiveCompanyId) {
        throw new Error(t("integrations.companyNotIdentified") || "Empresa não identificada — recarregue a página")
      }
      const res = await apiFetch(`/api/backend-proxy/calendar/google/auth-url?company_id=${effectiveCompanyId}`)
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || t("integrations.authUrlError"))
      }
      const { auth_url } = await res.json()
      window.location.href = auth_url
    } catch (err) {
      setGoogleStatus("error")
      setErrorMsg(err instanceof Error ? err.message : t("integrations.googleConnectError"))
    }
  }

  const enrichedIntegrations = useMemo(() => {
    const atsProviderMap: Record<string, string> = {
      gupy: "gupy",
      pandape: "pandape",
    }

    return baseIntegrations.map((integration) => {
      if (integration.id === "google-calendar") {
        return {
          ...integration,
          status: googleStatus === "connected" ? ("connected" as const) : integration.status,
        }
      }
      if (integration.id === "microsoft-calendar") {
        return {
          ...integration,
          status: microsoftStatus === "connected" ? ("connected" as const) : integration.status,
        }
      }
      if (integration.id === "teams") {
        return {
          ...integration,
          status: teamsStatus === "configured" ? ("connected" as const) : integration.status,
        }
      }
      if (integration.category === "ai_models") {
        const providerMap: Record<string, string> = {
          gemini: "gemini",
          claude: "claude",
          openai: "openai",
        }
        const provKey = providerMap[integration.id]
        const hasOwnKey = !!(llmConfig?.providers?.[provKey]?.api_key)
        const isActive = provKey === activeProvider
        // If this is the active provider (the agent is using it) but the
        // tenant has no own key in tenant_llm_configs, the platform is
        // falling back to the global system env var. Surface this in the UI
        // so the user understands they share quota with other tenants.
        const usingSystemKey = isActive && !hasOwnKey
        return {
          ...integration,
          isActiveProvider: isActive,
          usingSystemKey,
          status: ((hasOwnKey || usingSystemKey) ? "connected" : integration.status) as "connected" | "not_configured" | "coming_soon",
        }
      }
      if (integration.category === "ats" && atsProviderMap[integration.id]) {
        const conn = atsConnections.find(
          (c) => c.provider?.toLowerCase() === atsProviderMap[integration.id]
        )
        if (conn?.is_active) {
          return {
            ...integration,
            status: "connected" as const,
          }
        }
      }
      return integration
    })
  }, [baseIntegrations, googleStatus, microsoftStatus, teamsStatus, activeProvider, atsConnections, llmConfig])

  const activeCategory = tabToCategoryMap[activeTab] ?? "all"

  const filteredIntegrations = useMemo(() => {
    let result = enrichedIntegrations

    if (activeCategory !== "all") {
      result = result.filter((i) => i.category === activeCategory)
    }

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      result = result.filter(
        (i) =>
          i.name.toLowerCase().includes(query) ||
          i.shortDescription.toLowerCase().includes(query) ||
          i.category.toLowerCase().includes(query)
      )
    }

    return result
  }, [enrichedIntegrations, activeCategory, searchQuery])

  const groupedIntegrations = useMemo(() => {
    if (activeCategory !== "all") {
      return [{ category: activeCategory, items: filteredIntegrations }]
    }

    return categories
      .map((cat) => ({
        category: cat.id,
        items: filteredIntegrations.filter((i) => i.category === cat.id),
      }))
      .filter((group) => group.items.length > 0)
  }, [filteredIntegrations, activeCategory])

  const getCategoryLabel = (id: IntegrationCategory) =>
    categories.find((c) => c.id === id)?.label ?? id

  const connectedCount = enrichedIntegrations.filter((i) => i.status === "connected").length
  const totalCount = enrichedIntegrations.length

  const handleCardClick = (integration: Integration) => {
    setSelectedIntegration(integration)
    setDrawerOpen(true)
  }

  const tabs = [
    { id: "all", label: t("integrations.tabAll"), icon: Plug },
    { id: "ai-models", label: t("integrations.tabAiModels"), icon: Brain },
    { id: "ats", label: t("integrations.tabAts"), icon: Briefcase },
    { id: "calendar", label: t("integrations.tabCalendar"), icon: Calendar },
    { id: "communication", label: t("integrations.tabCommunication"), icon: MessageCircle },
    { id: "crm-hris", label: t("integrations.tabCrmHris"), icon: Building },
    { id: "mcps-apis", label: t("integrations.tabMcpsApis"), icon: Code },
  ]

  return (
    <div className="space-y-3" data-testid="integrations-hub">
      <div className={tabStyles.pillContainer} data-testid="integrations-category-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={activeTab === tab.id ? tabStyles.pillActive : tabStyles.pill}
            data-testid={`integrations-tab-${tab.id}`}
          >
            <tab.icon className={tabStyles.pillIcon} />
            {tab.label}
          </button>
        ))}
      </div>

      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-tertiary" />
          <Input
            placeholder={t("integrations.searchPlaceholder")}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-9 text-xs"
            data-testid="integrations-search-input"
          />
        </div>
        <p className={textStyles.caption}>
          {t("integrations.connectedCount", { connected: connectedCount, total: totalCount })}
        </p>
      </div>

      {filteredIntegrations.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center" data-testid="integrations-empty-state">
          <Search className="w-8 h-8 text-lia-text-tertiary mb-3" />
          <p className={textStyles.subtitle}>
            {t("integrations.noResults")}
          </p>
          <p className={cn(textStyles.description, "mt-1")}>
            {t("integrations.noResultsHint")}
          </p>
        </div>
      ) : (
        <div className="space-y-8" data-testid="integrations-list">
          {groupedIntegrations.map((group) => (
            <section key={group.category} data-testid={`integrations-group-${group.category}`}>
              {activeCategory === "all" && (
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-lia-text-tertiary">
                    {categoryIcons[group.category]}
                  </span>
                  <h2 className={textStyles.h3}>
                    {getCategoryLabel(group.category as IntegrationCategory)}
                  </h2>
                  <span className={textStyles.metricSmall}>
                    {group.items.length}
                  </span>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {group.items.map((integration) => (
                  <IntegrationCard
                    key={integration.id}
                    integration={integration}
                    onClick={handleCardClick}
                  />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}

      <IntegrationDetailDrawer
        integration={selectedIntegration}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        googleStatus={googleStatus}
        microsoftStatus={microsoftStatus}
        teamsStatus={teamsStatus}
        onConnectGoogle={handleConnectGoogle}
        errorMsg={errorMsg}
        llmConfig={llmConfig}
        onConfigSaved={fetchLlmConfig}
      />
    </div>
  )
}
