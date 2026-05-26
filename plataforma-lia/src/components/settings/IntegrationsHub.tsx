"use client"

import React, { useState, useMemo, useCallback } from "react"
import { Input } from "@/components/ui/input"
import { tabStyles, textStyles } from "@/lib/design-tokens"
import { Search, Brain, Briefcase, Calendar, MessageCircle, Building, Code, Plug } from "lucide-react"
import { cn } from "@/lib/utils"
import { useTranslations } from "next-intl"
import { categories, type Integration, type IntegrationCategory } from "./integrations/integration-data"
import { IntegrationDetailDrawer } from "./integrations/IntegrationDetailDrawer"
import { IntegrationGrid } from "./integrations/IntegrationGrid"
import { useIntegrationsData } from "@/hooks/integrations/use-integrations-data"
import { useCurrentCompany } from "@/hooks/company/use-current-company"
import { apiFetch } from "@/lib/api/api-fetch"

const tabToCategoryMap: Record<string, IntegrationCategory | "all"> = {
  all: "all",
  "ai-models": "ai_models",
  ats: "ats",
  calendar: "calendar",
  communication: "communication",
  "crm-hris": "crm_hris",
  "mcps-apis": "mcps_apis",
}

const TAB_DEFS = [
  { id: "all", labelKey: "integrations.tabAll", Icon: Plug },
  { id: "ai-models", labelKey: "integrations.tabAiModels", Icon: Brain },
  { id: "ats", labelKey: "integrations.tabAts", Icon: Briefcase },
  { id: "calendar", labelKey: "integrations.tabCalendar", Icon: Calendar },
  { id: "communication", labelKey: "integrations.tabCommunication", Icon: MessageCircle },
  { id: "crm-hris", labelKey: "integrations.tabCrmHris", Icon: Building },
  { id: "mcps-apis", labelKey: "integrations.tabMcpsApis", Icon: Code },
] as const

interface IntegrationsHubProps {
  activeSubsection: string
}

export function IntegrationsHub({ activeSubsection }: IntegrationsHubProps) {
  const t = useTranslations("settings")
  const { companyId, tenantId } = useCurrentCompany()
  const effectiveCompanyId = tenantId || companyId

  // UI state
  const [activeTab, setActiveTab] = useState(activeSubsection || "all")
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  React.useEffect(() => {
    setActiveTab(activeSubsection || "all")
  }, [activeSubsection])

  // Server data via canonical hook
  const { enrichedIntegrations, catalogLoading, googleStatus, microsoftStatus, teamsStatus, llmConfig, refetchLlmConfig } =
    useIntegrationsData()

  // Filtering + grouping
  const activeCategory = tabToCategoryMap[activeTab] ?? "all"

  const filteredIntegrations = useMemo(() => {
    let result = enrichedIntegrations
    if (activeCategory !== "all") result = result.filter((i) => i.category === activeCategory)
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      result = result.filter(
        (i) => i.name.toLowerCase().includes(q) || i.shortDescription.toLowerCase().includes(q) || i.category.toLowerCase().includes(q),
      )
    }
    return result
  }, [enrichedIntegrations, activeCategory, searchQuery])

  const groupedIntegrations = useMemo(() => {
    if (activeCategory !== "all") return [{ category: activeCategory, items: filteredIntegrations }]
    return categories
      .map((cat) => ({ category: cat.id, items: filteredIntegrations.filter((i) => i.category === cat.id) }))
      .filter((g) => g.items.length > 0)
  }, [filteredIntegrations, activeCategory])

  const getCategoryLabel = useCallback(
    (id: IntegrationCategory) => categories.find((c) => c.id === id)?.label ?? id,
    [],
  )

  const connectedCount = enrichedIntegrations.filter((i) => i.status === "connected").length

  const handleCardClick = useCallback((integration: Integration) => {
    setSelectedIntegration(integration)
    setDrawerOpen(true)
  }, [])

  const handleConnectGoogle = useCallback(async () => {
    setErrorMsg(null)
    try {
      if (!effectiveCompanyId) throw new Error(t("integrations.companyNotIdentified") || "Empresa nao identificada")
      const res = await apiFetch("/api/backend-proxy/calendar/google/auth-url")
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || t("integrations.authUrlError"))
      }
      const { auth_url } = await res.json()
      window.location.href = auth_url
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : t("integrations.googleConnectError"))
    }
  }, [effectiveCompanyId, t])

  const emptyState = (
    <div className="flex flex-col items-center justify-center py-16 text-center" data-testid="integrations-empty-state">
      <Search className="w-8 h-8 text-lia-text-tertiary mb-3" />
      <p className={textStyles.subtitle}>{t("integrations.noResults")}</p>
      <p className={cn(textStyles.description, "mt-1")}>{t("integrations.noResultsHint")}</p>
    </div>
  )

  return (
    <div className="space-y-3" data-testid="integrations-hub">
      <div className={tabStyles.pillContainer} data-testid="integrations-category-tabs">
        {TAB_DEFS.map(({ id, labelKey, Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={activeTab === id ? tabStyles.pillActive : tabStyles.pill}
            data-testid={`integrations-tab-${id}`}
          >
            <Icon className={tabStyles.pillIcon} />
            {t(labelKey)}
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
          {t("integrations.connectedCount", { connected: connectedCount, total: enrichedIntegrations.length })}
        </p>
      </div>

      {filteredIntegrations.length === 0 ? (
        emptyState
      ) : (
        <IntegrationGrid
          groups={groupedIntegrations}
          activeCategory={activeCategory}
          isLoading={catalogLoading}
          emptyState={emptyState}
          onCardClick={handleCardClick}
          getCategoryLabel={getCategoryLabel}
        />
      )}

      <IntegrationDetailDrawer
        integration={selectedIntegration}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        googleStatus={googleStatus as "idle" | "loading" | "connected" | "error"}
        microsoftStatus={microsoftStatus as "loading" | "connected" | "not_configured"}
        teamsStatus={teamsStatus as "loading" | "configured" | "not_configured"}
        onConnectGoogle={handleConnectGoogle}
        errorMsg={errorMsg}
        llmConfig={llmConfig}
        onConfigSaved={() => { void refetchLlmConfig() }}
      />
    </div>
  )
}
