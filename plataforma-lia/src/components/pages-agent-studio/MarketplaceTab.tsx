"use client"

import React, { useState, useEffect, useCallback } from "react"
import { toast } from "@/lib/toast"
import { ConfirmAlertDialog } from "@/components/agent-studio/confirm-alert-dialog"
import { useTranslations } from "next-intl"
// Sprint B QW#17 audit 2026-05-22: shadcn Tabs canonical (era <button> custom sem ARIA)
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import {
  Store, Download, Search, Loader2,
  Package, CreditCard, Trash2, TrendingUp, CheckCircle2, Sparkles,
  AlertTriangle, ExternalLink
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { TabSectionHeader } from "@/components/pages-agent-studio/TabSectionHeader"
// White-label canonical 2026-05-29: persona do cliente como fallback de nome
// de agente quando o billing row não traz agent_name (agente deletado etc.).
import { useAiPersona } from "@/hooks/company/use-ai-persona"
// Marketplace redesign 2026-06-09: use first-party agents API + legacy templates hook
import { useLegacyAgentTemplates } from "@/hooks/agents/use-legacy-agent-templates"
import { TemplateCard } from "@/components/pages-agent-studio/custom-agents/TemplateCard"
import { TemplatePreviewModal } from "@/components/pages-agent-studio/custom-agents/template-preview-modal"
import type { AgentTemplate } from "@/components/pages-agent-studio/custom-agents/types"

interface MarketplaceListing {
  id: string
  agent_id: string
  template_id?: string
  title: string
  short_description: string | null
  category: string
  tags: string[]
  status: string
  credits_per_execution: number
  is_free: boolean
  install_count: number
  avg_rating: number
  total_ratings: number
  agent_name: string | null
  agent_role: string | null
  agent_domain: string | null
  published_at: string | null
  listing_type?: "agent" | "template"
  agent_type?: "first_party" | "custom"
  is_installed?: boolean
}

interface Installation {
  id: string
  source_agent_id: string
  installed_agent_id: string | null
  status: string
  total_executions: number
  total_credits_consumed: number
  installed_at: string | null
  agent_name: string | null
}

// Marketplace redesign 2026-06-09: 5 módulos de roadmap (sem agente publicado)
// consolidados aqui como seção "Em breve" display-only. Substituem a antiga
// página "Módulos (beta)" morta. Placeholders — sem API, sem instalação.
const ROADMAP_MODULES: Array<{ id: string; name: string; description: string }> = [
  {
    id: "internal_mobility",
    name: "Mobilidade Interna",
    description: "Correspondência interna + Nota de prontidão",
  },
  {
    id: "workforce_planning",
    name: "Planejamento de Equipe",
    description: "Previsão + cenários + dashboard",
  },
  {
    id: "candidate_nurture",
    name: "Nutrição de Candidatos / CRM",
    description: "Sequências + engajamento + CRM",
  },
  {
    id: "onboarding_suite",
    name: "Inteligência de Integração",
    description: "Workflow pós-contratação completo",
  },
  {
    id: "predictive_analytics",
    name: "Previsão de Rotatividade",
    description: "Previsão de risco de turnover com ML",
  },
]

export default function MarketplaceTab({ initialCategory }: { initialCategory?: string } = {}) {
  const t = useTranslations('agents.marketplace')
  const [activeView, setActiveView] = useState<"browse" | "installed" | "billing">("browse")

  return (
    <div className="space-y-6">
      <TabSectionHeader
        title={t('title')}
        subtitle={t('subtitle')}
        icon={<Store className="w-4 h-4 text-violet-500" />}
      />

      {/* Sprint B QW#17 audit 2026-05-22: shadcn Tabs canonical (Radix com ARIA built-in) */}
      <Tabs value={activeView} onValueChange={(v) => setActiveView(v as "browse" | "installed" | "billing")}>
        <TabsList aria-label={t('viewSwitcher') || 'Visão do marketplace'}>
          <TabsTrigger value="browse" className="gap-1.5">
            <Search className="w-3.5 h-3.5" aria-hidden="true" />
            {t('browse')}
          </TabsTrigger>
          <TabsTrigger value="installed" className="gap-1.5">
            <Package className="w-3.5 h-3.5" aria-hidden="true" />
            {t('installed')}
          </TabsTrigger>
          <TabsTrigger value="billing" className="gap-1.5">
            <CreditCard className="w-3.5 h-3.5" aria-hidden="true" />
            {t('billing')}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="browse" className="mt-4">
          {/* F3 Wave F: onInstallSuccess auto-switch para tab "installed" */}
          <BrowseMarketplace onInstallSuccess={() => setActiveView("installed")} initialCategory={initialCategory} />
        </TabsContent>
        <TabsContent value="installed" className="mt-4">
          <InstalledAgents />
        </TabsContent>
        <TabsContent value="billing" className="mt-4">
          <BillingView />
        </TabsContent>
      </Tabs>
    </div>
  )
}


interface FirstPartyAgent {
  id: string
  name: string
  description: string | null
  icon: string
  domain: string
  role: string
  status: string
  agent_type: string
  system_prompt?: string
  allowed_tools?: string[]
  max_steps?: number
  temperature?: number
}

function BrowseMarketplace({ onInstallSuccess, initialCategory: _initialCategory }: { onInstallSuccess?: () => void; initialCategory?: string }) {
  const t = useTranslations("agents.marketplace")
  const [search, setSearch] = React.useState("")

  // Section 1 — First-party WeDo agents
  const [firstPartyAgents, setFirstPartyAgents] = React.useState<FirstPartyAgent[]>([])
  const [loadingAgents, setLoadingAgents] = React.useState(true)
  const [activating, setActivating] = React.useState<string | null>(null)
  const [activatedIds, setActivatedIds] = React.useState<Set<string>>(new Set())
  const [offerReadiness, setOfferReadiness] = React.useState<{ ready: boolean; score: number; total: number; items: { key: string; label: string; ok: boolean; settings_path: string }[] } | null>(null)

  // Section 2 — Templates via canonical hook
  const { templates, isLoading: loadingTemplates } = useLegacyAgentTemplates()

  // Template preview modal state — "Ajustar antes" e "Ver detalhes"
  const [previewTemplate, setPreviewTemplate] = React.useState<AgentTemplate | null>(null)

  React.useEffect(() => {
    async function load() {
      setLoadingAgents(true)
      try {
        const res = await fetch("/api/backend-proxy/custom-agents?agent_type=first_party&status=active")
        if (res.ok) {
          const data = await res.json()
          // VoiceScreeningChannel is an inert per-tenant config manifest (max_steps:1, no tools/prompt) —
          // voice is a per-agent channel toggle, not a standalone agent. Don't show it as an installable card.
          setFirstPartyAgents(
            (data.agents || []).filter(
              (a: FirstPartyAgent) => a.name !== "VoiceScreeningChannel",
            ),
          )
        }
      } catch (err) {
        console.error("Failed to load first-party agents:", err)
      } finally {
        setLoadingAgents(false)
      }
    }
    load()
  }, [])

  const handleActivate = async (agent: FirstPartyAgent) => {
    setActivating(agent.id)
    try {
      const res = await fetch("/api/backend-proxy/custom-agents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: agent.name,
          role: agent.role,
          description: agent.description || "",
          icon: agent.icon,
          domain: agent.domain,
          system_prompt: agent.system_prompt || "",
          allowed_tools: agent.allowed_tools || [],
          max_steps: agent.max_steps ?? 10,
          temperature: agent.temperature ?? 0.3,
        }),
      })
      if (res.ok) {
        toast.success(t("installSuccess"))
        setActivatedIds(prev => { const s = new Set(prev); s.add(agent.id); return s })
        onInstallSuccess?.()
        if (agent.domain === "offer" || (agent.name || "").toLowerCase().includes("offer")) {
          fetch("/api/backend-proxy/offer-agent-readiness").then(r=>r.json()).then(d=>{if(d&&!d.ready)setOfferReadiness(d)}).catch(()=>{})
        }
      } else {
        const err = await res.json().catch(() => ({ detail: t("errorGeneric") }))
        toast.error(err.detail || t("errorInstalling"))
      }
    } catch {
      toast.error(t("connectionError"))
    } finally {
      setActivating(null)
    }
  }

  const handleUseTemplate = async (template: AgentTemplate) => {
    try {
      const res = await fetch("/api/backend-proxy/custom-agents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: template.name,
          role: template.description,
          description: template.description,
          system_prompt: template.system_prompt,
          allowed_tools: template.allowed_tools,
          domain: template.domain,
          icon: template.icon,
          max_steps: template.max_steps,
          temperature: template.temperature,
          enable_memory: template.enable_memory,
          context_level: template.context_level,
          excluded_tools: template.excluded_tools,
        }),
      })
      if (res.ok) {
        toast.success(t("templateCloneSuccess"))
      } else if (res.status === 404) {
        toast.info(t("templateComingSoon"))
      } else {
        const err = await res.json().catch(() => ({ detail: t("errorGeneric") }))
        toast.error(err.detail || t("errorGeneric"))
      }
    } catch {
      toast.error(t("connectionError"))
    }
  }

  const q = search.trim().toLowerCase()
  const filteredAgents = firstPartyAgents.filter(a =>
    !q || a.name.toLowerCase().includes(q) || (a.description || "").toLowerCase().includes(q)
  )
  const filteredTemplates = templates.filter(tpl =>
    !q || tpl.name.toLowerCase().includes(q) || (tpl.description || "").toLowerCase().includes(q)
  )

  return (
    <div className="space-y-6">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-disabled pointer-events-none" aria-hidden="true" />
        <input
          type="search"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder={t("searchPlaceholder") as string}
          className="w-full pl-10 pr-3 py-2 border border-lia-border-subtle rounded-lg text-sm bg-lia-bg-secondary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30"
        />
      </div>

      <section data-testid="section-wedo-agents">
        <div className="mb-3">
          <h2 className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
            <Store className="w-4 h-4 text-violet-500" aria-hidden="true" />
            {t("sectionAgents")}
          </h2>
          <p className="text-xs text-lia-text-secondary mt-0.5">{t("wedoAgentsSubtitle")}</p>
        </div>

        {loadingAgents ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-5 h-5 animate-spin text-lia-text-muted" aria-hidden="true" />
          </div>
        ) : filteredAgents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-6 rounded-md border border-dashed border-lia-border-subtle bg-lia-bg-secondary/50">
            <Store className="w-8 h-8 text-lia-text-muted mb-2" />
            <p className="text-xs text-lia-text-muted">{t("noAgentsAvailable")}</p>
          </div>
        ) : (
          <>
            {offerReadiness && !offerReadiness.ready ? (
            <div className="mb-4 rounded-md border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/20 p-4">
              <div className="flex items-start gap-2.5">
                <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-amber-800 dark:text-amber-300">
                    Agente ativado! Complete as configuracoes para melhor experiencia
                  </p>
                  <p className="text-xs text-amber-700 dark:text-amber-400 mt-0.5 mb-3">
                    {offerReadiness.score}/{offerReadiness.total} configuracoes prontas. O agente opera em modo basico ate voce completar:
                  </p>
                  <ul className="space-y-1.5">
                    {(offerReadiness.items||[]).filter((i)=>!i.ok).map((item)=>(
                      <li key={item.key} className="flex items-center justify-between gap-2">
                        <span className="text-xs text-amber-700 dark:text-amber-400 flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0" />
                          {item.label}
                        </span>
                        <a href={item.settings_path} className="inline-flex items-center gap-1 text-xs font-medium text-amber-800 dark:text-amber-300 underline underline-offset-2 hover:text-amber-900 flex-shrink-0">
                          Configurar <ExternalLink className="w-3 h-3" />
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
                <button onClick={()=>setOfferReadiness(null)} className="text-amber-500 hover:text-amber-700 text-xs flex-shrink-0" aria-label="Fechar aviso">x</button>
              </div>
            </div>
          ) : null}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredAgents.map(agent => {
              const isActive = activatedIds.has(agent.id)
              return (
                <div
                  key={agent.id}
                  className="rounded-md border border-lia-border-subtle bg-lia-bg-secondary hover:border-violet-300 dark:hover:border-violet-700 hover:shadow-md transition-colors duration-200"
                  data-testid={"wedo-agent-card-" + agent.id}
                >
                  <div className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-powder border border-mist flex items-center justify-center text-lg flex-shrink-0">
                          {agent.icon || "\u{1F916}"}
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-lia-text-primary">{agent.name}</p>
                          {agent.role && <p className="text-[10px] text-lia-text-secondary mt-0.5">{agent.role}</p>}
                        </div>
                      </div>
                      <span
                        className="inline-flex items-center gap-1 text-xs bg-blue-50 dark:bg-blue-950/20 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800 px-2 py-0.5 rounded-full font-medium flex-shrink-0"
                        data-testid="official-wedo-badge"
                      >
                        Oficial WeDo
                      </span>
                    </div>

                    {agent.description && (
                      <p className="text-xs text-lia-text-secondary mb-3 line-clamp-2">{agent.description}</p>
                    )}

                    {isActive ? (
                      <div
                        className="flex items-center justify-center gap-1.5 w-full px-3 py-2 rounded-md bg-emerald-50 dark:bg-emerald-950/20 text-emerald-700 dark:text-emerald-400 text-xs font-medium"
                        data-testid="agent-active-chip"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />
                        {t("active")}
                      </div>
                    ) : (
                      <Button
                        size="sm"
                        onClick={() => handleActivate(agent)}
                        disabled={activating === agent.id}
                        className="w-full gap-2 bg-violet-600 text-white hover:bg-violet-700"
                        data-testid={"activate-btn-" + agent.id}
                      >
                        {activating === agent.id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
                        ) : (
                          <Download className="w-3.5 h-3.5" aria-hidden="true" />
                        )}
                        {t("activate")}
                      </Button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
          </>
        )}
      </section>

      <section data-testid="section-templates">
        <div className="mb-3">
          <h2 className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
            <Package className="w-4 h-4 text-amber-500" aria-hidden="true" />
            {t("sectionTemplates")}
          </h2>
          <p className="text-xs text-lia-text-secondary mt-0.5">{t("templatesSubtitle")}</p>
        </div>

        {loadingTemplates ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-5 h-5 animate-spin text-lia-text-muted" aria-hidden="true" />
          </div>
        ) : filteredTemplates.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-6 rounded-md border border-dashed border-lia-border-subtle bg-lia-bg-secondary/50">
            <Package className="w-8 h-8 text-lia-text-muted mb-2" />
            <p className="text-xs text-lia-text-muted">{t("noAgentsAvailable")}</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {filteredTemplates.map(template => (
              <TemplateCard
                key={template.id}
                template={template}
                onSelect={handleUseTemplate}
                onCustomize={(tpl) => setPreviewTemplate(tpl)}
                onPreview={(tpl) => setPreviewTemplate(tpl)}
              />
            ))}
          </div>
        )}
      </section>

      {/* Modal "Ajustar antes" / "Ver detalhes" — restaurado após commit 742793c13 */}
      <TemplatePreviewModal
        template={previewTemplate}
        open={previewTemplate !== null}
        onOpenChange={(o) => { if (!o) setPreviewTemplate(null) }}
        onConfirm={async (tpl) => { await handleUseTemplate(tpl); setPreviewTemplate(null) }}
      />

      <section data-testid="section-roadmap">
        <div className="mb-3">
          <h2 className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-emerald-500" aria-hidden="true" />
            {t("sectionRoadmap")}
          </h2>
          <p className="text-xs text-lia-text-secondary mt-0.5">{t("roadmapSubtitle")}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {ROADMAP_MODULES.map(mod => (
            <div
              key={mod.id}
              className="rounded-md border border-lia-border-subtle bg-lia-bg-secondary"
              data-testid={"roadmap-module-card-" + mod.id}
            >
              <div className="p-4">
                <div className="flex items-start justify-between mb-2 gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-950/20 flex items-center justify-center flex-shrink-0">
                      <Sparkles className="w-5 h-5 text-emerald-500" aria-hidden="true" />
                    </div>
                    <p className="text-sm font-semibold text-lia-text-primary truncate">{mod.name}</p>
                  </div>
                  <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full font-medium flex-shrink-0">
                    {t("roadmapBadge")}
                  </span>
                </div>
                <p className="text-xs text-lia-text-secondary line-clamp-2">{mod.description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

function InstalledAgents() {
  const t = useTranslations('agents.marketplace')
  const [installations, setInstallations] = useState<Installation[]>([])
  const [isLoading, setIsLoading] = useState(true)

  const load = useCallback(async () => {
    setIsLoading(true)
    try {
      const res = await fetch("/api/backend-proxy/agent-marketplace/installations")
      if (res.ok) {
        const data = await res.json()
        setInstallations(data.installations || [])
      }
    } catch (err) {
      console.error("Failed to load installations:", err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  // Sprint B QW#4 audit 2026-05-22: state-driven confirm via shadcn AlertDialog
  const [uninstallTargetId, setUninstallTargetId] = useState<string | null>(null)

  const handleUninstall = (installationId: string) => {
    setUninstallTargetId(installationId)
  }

  const confirmUninstall = async () => {
    if (!uninstallTargetId) return
    try {
      await fetch(`/api/backend-proxy/agent-marketplace/installations/${uninstallTargetId}`, {
        method: "DELETE",
      })
      load()
    } catch (err) {
      console.error("Failed to uninstall:", err)
    } finally {
      setUninstallTargetId(null)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-6 h-6 animate-spin text-lia-text-muted" aria-hidden="true" />
      </div>
    )
  }

  if (installations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 rounded-md border border-dashed border-lia-border-subtle bg-lia-bg-secondary/50">
        <Package className="w-10 h-10 text-lia-text-muted mb-3" />
        <p className="text-sm font-medium text-lia-text-secondary">{t('noInstalledAgents')}</p>
        <p className="text-xs text-lia-text-muted mt-1">
          {t('exploreMarketplace')}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {installations.map(inst => (
        <div
          key={inst.id}
          className="flex items-center justify-between p-4 rounded-md border border-lia-border-subtle bg-lia-bg-secondary"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-violet-50 dark:bg-violet-950/20 flex items-center justify-center">
              <Package className="w-5 h-5 text-violet-500" />
            </div>
            <div>
              <p className="text-sm font-semibold text-lia-text-primary">{inst.agent_name || t('agent')}</p>
              <div className="flex items-center gap-3 mt-0.5 text-[10px] text-lia-text-secondary">
                <span>{t('executions', { count: inst.total_executions })}</span>
                <span>{t('credits', { count: inst.total_credits_consumed })}</span>
                {inst.installed_at && (
                  <span>
                    {t('installedOn', { date: new Date(inst.installed_at).toLocaleDateString() })}
                  </span>
                )}
              </div>
            </div>
          </div>
          <button
            onClick={() => handleUninstall(inst.id)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            {t('uninstall')}
          </button>
        </div>
      ))}
          {/* Sprint B QW#4 audit 2026-05-22: ConfirmAlertDialog canonical (era native confirm) */}
      <ConfirmAlertDialog
        open={uninstallTargetId !== null}
        onOpenChange={(open) => !open && setUninstallTargetId(null)}
        title={t('confirmUninstallTitle') || 'Desinstalar agente?'}
        description={t('confirmUninstall')}
        onConfirm={confirmUninstall}
        confirmLabel={t('uninstall') || 'Desinstalar'}
        destructive
      />

      </div>
  )
}

function BillingView() {
  const t = useTranslations('agents.marketplace')
  // White-label canonical 2026-05-29: fallback do nome quando agent_name
  // ausente (agente deletado fora do ciclo de billing).
  const { persona: aiPersona } = useAiPersona()
  const [billing, setBilling] = useState<Array<{
    agent_id: string
    agent_name: string
    total_executions: number
    total_credits_consumed: number
  }>>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetch("/api/backend-proxy/agent-marketplace/billing")
      .then(r => r.ok ? r.json() : [])
      .then(d => setBilling(Array.isArray(d) ? d : []))
      .catch(() => {})
      .finally(() => setIsLoading(false))
  }, [])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-6 h-6 animate-spin text-lia-text-muted" aria-hidden="true" />
      </div>
    )
  }

  const totalCredits = billing.reduce((s, b) => s + b.total_credits_consumed, 0)
  const totalExecs = billing.reduce((s, b) => s + b.total_executions, 0)

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-md border border-lia-border-subtle bg-lia-bg-secondary p-4">
          <p className="text-xs text-lia-text-secondary mb-1">{t('totalCredits')}</p>
          <p className="text-2xl font-semibold text-lia-text-primary">{totalCredits.toLocaleString()}</p>
        </div>
        <div className="rounded-md border border-lia-border-subtle bg-lia-bg-secondary p-4">
          <p className="text-xs text-lia-text-secondary mb-1">{t('totalExecutions')}</p>
          <p className="text-2xl font-semibold text-lia-text-primary">{totalExecs.toLocaleString()}</p>
        </div>
      </div>

      {billing.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-8 text-lia-text-disabled">
          <TrendingUp className="w-8 h-8 mb-2" />
          <p className="text-sm">{t('noUsageRecorded')}</p>
        </div>
      ) : (
        <div className="rounded-md border border-lia-border-subtle overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-lia-bg-secondary">
                <th className="text-left px-4 py-3 text-xs font-semibold text-lia-text-secondary">{t('agentColumn')}</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-lia-text-secondary">{t('executionsColumn')}</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-lia-text-secondary">{t('creditsColumn')}</th>
              </tr>
            </thead>
            <tbody>
              {billing.map(b => (
                <tr key={b.agent_id} className="border-t border-lia-border-subtle">
                  <td className="px-4 py-3 font-medium text-lia-text-primary">{b.agent_name || aiPersona?.name || t('agent')}</td>
                  <td className="px-4 py-3 text-right text-lia-text-secondary">{b.total_executions}</td>
                  <td className="px-4 py-3 text-right font-semibold text-lia-text-primary">{b.total_credits_consumed}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
          </div>
  )
}
