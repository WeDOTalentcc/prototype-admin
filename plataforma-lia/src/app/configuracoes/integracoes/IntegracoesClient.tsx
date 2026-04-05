"use client"

import { useState, useEffect, useMemo } from "react"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import {
  Search,
  Brain,
  Briefcase,
  Calendar,
  MessageCircle,
  Building,
  Code,
  Plug,
  ArrowLeft,
} from "lucide-react"
import {
  categories,
  integrations,
  type Integration,
  type IntegrationCategory,
} from "./integration-data"
import { IntegrationCard } from "./IntegrationCard"
import { IntegrationDetailDrawer } from "./IntegrationDetailDrawer"

const categoryIcons: Record<IntegrationCategory, React.ReactNode> = {
  ai_models: <Brain className="w-4 h-4" />,
  ats: <Briefcase className="w-4 h-4" />,
  calendar: <Calendar className="w-4 h-4" />,
  communication: <MessageCircle className="w-4 h-4" />,
  crm_hris: <Building className="w-4 h-4" />,
  mcps_apis: <Code className="w-4 h-4" />,
}

export default function IntegracoesPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [activeCategory, setActiveCategory] = useState<IntegrationCategory | "all">("all")
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)

  const [googleStatus, setGoogleStatus] = useState<"idle" | "loading" | "connected" | "error">("idle")
  const [microsoftStatus, setMicrosoftStatus] = useState<"loading" | "connected" | "not_configured">("loading")
  const [teamsStatus, setTeamsStatus] = useState<"loading" | "configured" | "not_configured">("loading")
  const [activeProvider, setActiveProvider] = useState<string>("gemini")
  const [atsConnections, setAtsConnections] = useState<Array<{ provider: string; is_active: boolean }>>([])
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    fetch("/api/backend-proxy/calendar/health")
      .then((r) => r.json())
      .then((data) => {
        setMicrosoftStatus(data.graph_configured ? "connected" : "not_configured")
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

  const totalCount = enrichedIntegrations.length
  const connectedCount = enrichedIntegrations.filter((i) => i.status === "connected").length

  const handleCardClick = (integration: Integration) => {
    setSelectedIntegration(integration)
    setDrawerOpen(true)
  }

  return (
    <div className="flex flex-col lg:flex-row min-h-[calc(100vh-64px)]">
      <aside className="w-full lg:w-56 flex-shrink-0 border-b lg:border-b-0 lg:border-r border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary">
        <div className="p-4 lg:p-5">
          <button
            onClick={() => window.location.href = '/'}
            className="flex items-center gap-1.5 text-xs text-lia-text-secondary hover:text-lia-text-primary transition-colors font-['Open_Sans',sans-serif] mb-3"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Voltar ao menu
          </button>
          <div className="flex items-center gap-2 mb-4">
            <Plug className="w-4 h-4 text-wedo-cyan dark:text-wedo-cyan" />
            <h1 className="text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif]">
              Integrações
            </h1>
          </div>
          <p className="text-[10px] text-lia-text-secondary dark:text-lia-text-secondary font-['Open_Sans',sans-serif] mb-4">
            {connectedCount} de {totalCount} conectadas
          </p>

          <nav className="flex lg:flex-col gap-1 overflow-x-auto lg:overflow-x-visible pb-2 lg:pb-0">
            <button
              onClick={() => setActiveCategory("all")}
              className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-md text-xs font-medium font-['Open_Sans',sans-serif] transition-colors whitespace-nowrap",
                activeCategory === "all"
                  ? "bg-lia-btn-primary-bg text-lia-btn-primary-text dark:bg-lia-bg-tertiary dark:text-lia-text-primary"
                  : "text-lia-text-secondary hover:bg-lia-bg-tertiary dark:text-lia-text-secondary dark:hover:bg-lia-bg-primary"
              )}
            >
              <Plug className="w-3.5 h-3.5 flex-shrink-0" />
              Todas
            </button>

            {categories.map((cat) => {
              const count = enrichedIntegrations.filter((i) => i.category === cat.id).length
              return (
                <button
                  key={cat.id}
                  onClick={() => setActiveCategory(cat.id)}
                  className={cn(
                    "flex items-center gap-2 px-3 py-2 rounded-md text-xs font-medium font-['Open_Sans',sans-serif] transition-colors whitespace-nowrap",
                    activeCategory === cat.id
                      ? "bg-lia-btn-primary-bg text-lia-btn-primary-text dark:bg-lia-bg-tertiary dark:text-lia-text-primary"
                      : "text-lia-text-secondary hover:bg-lia-bg-tertiary dark:text-lia-text-secondary dark:hover:bg-lia-bg-primary"
                  )}
                >
                  <span className="flex-shrink-0">{categoryIcons[cat.id]}</span>
                  <span className="truncate">{cat.label}</span>
                  <span className="ml-auto text-[10px] opacity-60 flex-shrink-0">{count}</span>
                </button>
              )
            })}
          </nav>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <div className="p-4 lg:p-6 max-w-4xl">
          <div className="mb-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-tertiary" />
              <Input
                placeholder="Buscar integrações..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 h-9 text-xs font-['Open_Sans',sans-serif]"
              />
            </div>
          </div>

          {filteredIntegrations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Search className="w-8 h-8 text-lia-text-tertiary mb-3" />
              <p className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif]">
                Nenhuma integração encontrada
              </p>
              <p className="text-[10px] text-lia-text-secondary dark:text-lia-text-secondary font-['Open_Sans',sans-serif] mt-1">
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
                        {categoryIcons[group.category as IntegrationCategory]}
                      </span>
                      <h2 className="text-xs font-semibold text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif]">
                        {getCategoryLabel(group.category as IntegrationCategory)}
                      </h2>
                      <span className="text-[10px] text-lia-text-tertiary font-['Inter',sans-serif]">
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
        </div>
      </main>

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
