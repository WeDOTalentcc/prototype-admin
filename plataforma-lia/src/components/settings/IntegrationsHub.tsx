"use client"

import React, { useState, useEffect, useMemo } from "react"
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
import {
  categories,
  integrations,
  type Integration,
  type IntegrationCategory,
} from "./integrations/integration-data"
import { IntegrationCard } from "./integrations/IntegrationCard"
import { IntegrationDetailDrawer } from "./integrations/IntegrationDetailDrawer"

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
  const [activeTab, setActiveTab] = useState(activeSubsection || "all")
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)

  const [googleStatus, setGoogleStatus] = useState<"idle" | "loading" | "connected" | "error">("idle")
  const [microsoftStatus, setMicrosoftStatus] = useState<"loading" | "connected" | "not_configured">("loading")
  const [teamsStatus, setTeamsStatus] = useState<"loading" | "configured" | "not_configured">("loading")
  const [activeProvider, setActiveProvider] = useState<string>("gemini")
  const [atsConnections, setAtsConnections] = useState<Array<{ provider: string; is_active: boolean }>>([])
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    setActiveTab(activeSubsection || "all")
  }, [activeSubsection])

  useEffect(() => {
    fetch("/api/backend-proxy/calendar/health")
      .then((r) => r.json())
      .then((data) => {
        setMicrosoftStatus(data.graph_configured ? "connected" : "not_configured")
        if (data.google_configured) {
          setGoogleStatus("connected")
        }
      })
      .catch(() => setMicrosoftStatus("not_configured"))

    fetch("/api/backend-proxy/integrations/status")
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

    fetch("/api/backend-proxy/admin/llm-config")
      .then((r) => {
        if (!r.ok) throw new Error("Failed to fetch LLM config")
        return r.json()
      })
      .then((data) => {
        if (data.primary_provider) {
          setActiveProvider(data.primary_provider)
        }
      })
      .catch(() => {})

    fetch("/api/backend-proxy/ats/connections")
      .then((r) => {
        if (!r.ok) throw new Error("Failed to fetch ATS connections")
        return r.json()
      })
      .then((data: Array<{ provider: string; is_active: boolean }>) => {
        setAtsConnections(data)
      })
      .catch(() => setAtsConnections([]))
  }, [])

  const handleConnectGoogle = async () => {
    setGoogleStatus("loading")
    setErrorMsg(null)
    try {
      const companyId = "current"
      const res = await fetch(`/api/backend-proxy/calendar/google/auth-url?company_id=${companyId}`)
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || "Erro ao obter URL de autorização")
      }
      const { auth_url } = await res.json()
      window.location.href = auth_url
    } catch (err) {
      setGoogleStatus("error")
      setErrorMsg(err instanceof Error ? err.message : "Erro ao conectar com Google")
    }
  }

  const enrichedIntegrations = useMemo(() => {
    const atsProviderMap: Record<string, string> = {
      gupy: "gupy",
      pandape: "pandape",
    }

    return integrations.map((integration) => {
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
        return {
          ...integration,
          isActiveProvider: providerMap[integration.id] === activeProvider,
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
  }, [googleStatus, microsoftStatus, teamsStatus, activeProvider, atsConnections])

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
    { id: "all", label: "Todas", icon: Plug },
    { id: "ai-models", label: "Modelos de IA", icon: Brain },
    { id: "ats", label: "ATS", icon: Briefcase },
    { id: "calendar", label: "Calendário", icon: Calendar },
    { id: "communication", label: "Comunicação", icon: MessageCircle },
    { id: "crm-hris", label: "CRM & HRIS", icon: Building },
    { id: "mcps-apis", label: "MCPs & APIs", icon: Code },
  ]

  return (
    <div className="space-y-3">
      <div className={tabStyles.pillContainer}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={activeTab === tab.id ? tabStyles.pillActive : tabStyles.pill}
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
            placeholder="Buscar integrações..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-9 text-xs"
          />
        </div>
        <p className={textStyles.caption}>
          {connectedCount} de {totalCount} conectadas
        </p>
      </div>

      {filteredIntegrations.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <Search className="w-8 h-8 text-lia-text-tertiary mb-3" />
          <p className={textStyles.subtitle}>
            Nenhuma integração encontrada
          </p>
          <p className={cn(textStyles.description, "mt-1")}>
            Tente buscar com outros termos
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {groupedIntegrations.map((group) => (
            <section key={group.category}>
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
      />
    </div>
  )
}
