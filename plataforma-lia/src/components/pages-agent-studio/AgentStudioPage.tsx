"use client"

import React, { useState, useEffect } from "react"
import { TwinsList, EvaluateWithTwinModal } from "@/components/pages-agent-studio/DigitalTwinComponents"
import MultiStrategySearchPanel from "@/components/pages-agent-studio/MultiStrategySearchPanel"
import CustomAgentsTab from "@/components/pages-agent-studio/CustomAgentsTab"
import { TemplateGallery, AgentCard as CustomAgentCard, AgentCardSkeleton, AgentDetailsPanel, DeployDialog, ConversationalCreator, TestDebugPanel, ApprovalsList } from "@/components/pages-agent-studio/custom-agents"
import { useCustomAgents } from "@/hooks/agents"
import { useAgentStudioStore } from "@/stores/agent-studio-store"
import type { CustomAgent, AgentTemplate } from "@/components/pages-agent-studio/custom-agents/types"
import MarketplaceTab from "@/components/pages-agent-studio/MarketplaceTab"
import {
  Bot, Plus, Play, Pause, Briefcase, Database,
  Factory, HeartPulse, ShoppingCart, Code, Truck, Brain,
  ChevronRight, Zap, Target, ArrowRight,
  Activity, Eye, ThumbsUp, ThumbsDown, RefreshCw,
  Loader2, Users, Wand2, Search, Store,
  GraduationCap, BarChart3, Clock
} from "lucide-react"
import { cn } from "@/lib/utils"
import { toast } from "@/lib/toast"
import { extractErrorMessage } from "@/lib/api/extract-error-message"
import { Button } from "@/components/ui/button"
import { BetaBadge } from "@/components/ui/beta-badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { PageTabNavigation } from "@/components/ui/page-tab-navigation"
import { useTranslations } from "next-intl"

interface SourcingAgent {
  id: string
  agent_name: string
  status: "active" | "paused" | "completed"
  calibration_v: number
  job_id: string | null
  talent_pool_id: string | null
  search_strategy: Record<string, unknown>
  preferences: Record<string, unknown>
  profiles_viewed: number
  profiles_approved: number
  profiles_rejected: number
  created_at: string
}

interface SectorTemplate {
  id: string
  display_name: string
  description: string
  icon: string
}

const SECTOR_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  factory: Factory,
  heart_pulse: HeartPulse,
  shopping_cart: ShoppingCart,
  code: Code,
  truck: Truck,
}

const SECTOR_COLORS: Record<string, { bg: string; text: string; accent: string; glow: string }> = {
  factory: { bg: "bg-amber-50 dark:bg-amber-950/20", text: "text-amber-700 dark:text-amber-400", accent: "bg-amber-500", glow: "shadow-amber-200/50 dark:shadow-amber-900/30" },
  heart_pulse: { bg: "bg-rose-50 dark:bg-rose-950/20", text: "text-rose-700 dark:text-rose-400", accent: "bg-rose-500", glow: "shadow-rose-200/50 dark:shadow-rose-900/30" },
  shopping_cart: { bg: "bg-violet-50 dark:bg-violet-950/20", text: "text-violet-700 dark:text-violet-400", accent: "bg-violet-500", glow: "shadow-violet-200/50 dark:shadow-violet-900/30" },
  code: { bg: "bg-cyan-50 dark:bg-cyan-950/20", text: "text-cyan-700 dark:text-cyan-400", accent: "bg-cyan-500", glow: "shadow-cyan-200/50 dark:shadow-cyan-900/30" },
  truck: { bg: "bg-emerald-50 dark:bg-emerald-950/20", text: "text-emerald-700 dark:text-emerald-400", accent: "bg-emerald-500", glow: "shadow-emerald-200/50 dark:shadow-emerald-900/30" },
}

const STATUS_CONFIG_STYLES = {
  active: { labelKey: "studio.status.active" as const, dot: "bg-emerald-500", bg: "bg-emerald-50 dark:bg-emerald-950/30", text: "text-emerald-700 dark:text-emerald-400", pulse: true },
  paused: { labelKey: "studio.status.paused" as const, dot: "bg-amber-500", bg: "bg-amber-50 dark:bg-amber-950/30", text: "text-amber-700 dark:text-amber-400", pulse: false },
  completed: { labelKey: "studio.status.completed" as const, dot: "bg-lia-text-disabled", bg: "bg-lia-bg-tertiary", text: "text-lia-text-secondary", pulse: false },
}

const FLOW_STEPS_CONFIG = [
  { icon: Target, titleKey: "studio.flowSteps.chooseProfile" as const, descKey: "studio.flowSteps.chooseProfileDesc" as const, color: "text-cyan-600 dark:text-cyan-400", bg: "bg-cyan-50 dark:bg-cyan-950/30" },
  { icon: Wand2, titleKey: "studio.flowSteps.configureAgent" as const, descKey: "studio.flowSteps.configureAgentDesc" as const, color: "text-violet-600 dark:text-violet-400", bg: "bg-violet-50 dark:bg-violet-950/30" },
  { icon: GraduationCap, titleKey: "studio.flowSteps.teachByEvaluating" as const, descKey: "studio.flowSteps.teachByEvaluatingDesc" as const, color: "text-amber-600 dark:text-amber-400", bg: "bg-amber-50 dark:bg-amber-950/30" },
  { icon: Zap, titleKey: "studio.flowSteps.receiveCandidates" as const, descKey: "studio.flowSteps.receiveCandidatesDesc" as const, color: "text-emerald-600 dark:text-emerald-400", bg: "bg-emerald-50 dark:bg-emerald-950/30" },
]

interface AgentStudioPageProps {
  onNavigateToPool?: (poolId: string) => void
  onNavigateToJob?: (jobId: string) => void
  onStartCalibration?: (agentId: string) => void
}

export default function AgentStudioPage({
  onNavigateToPool,
  onNavigateToJob,
  onStartCalibration,
}: AgentStudioPageProps) {
  const t = useTranslations("agents")
  const [agents, setAgents] = useState<SourcingAgent[]>([])
  const [templates, setTemplates] = useState<SectorTemplate[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [evaluatingTwinId, setEvaluatingTwinId] = useState<string | null>(null)
  const [deployAgent, setDeployAgent] = useState<CustomAgent | null>(null)
  const [testAgent, setTestAgent] = useState<CustomAgent | null>(null)
  const [detailsAgent, setDetailsAgent] = useState<CustomAgent | null>(null)
  const { agents: customAgents, mutate: mutateCustomAgents } = useCustomAgents()
  const { selectTemplate, reset: resetStudio } = useAgentStudioStore()
  const [selectedTemplate, setSelectedTemplate] = useState<SectorTemplate | null>(null)
  const [activeTab, setActiveTab] = useState<"agents" | "custom" | "marketplace" | "twins" | "search">("agents")

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setIsLoading(true)
    try {
      const [agentsRes, templatesRes] = await Promise.allSettled([
        fetch("/api/backend-proxy/sourcing-agents"),
        fetch("/api/backend-proxy/agent-templates/sectors"),
      ])
      let agentsData: Record<string, unknown> = {}
      let templatesData: unknown = []
      if (agentsRes.status === "fulfilled" && agentsRes.value.ok) {
        try { agentsData = await agentsRes.value.json() } catch { /* */ }
      }
      if (templatesRes.status === "fulfilled" && templatesRes.value.ok) {
        try { templatesData = await templatesRes.value.json() } catch { /* */ }
      }
      setAgents(Array.isArray(agentsData?.agents) ? agentsData.agents as SourcingAgent[] : [])
      setTemplates(Array.isArray(templatesData) ? templatesData as SectorTemplate[] : [])
    } catch (err) {
      console.error("Failed to load agent studio data:", err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleToggleStatus = async (agentId: string, currentStatus: string) => {
    const action = currentStatus === "active" ? "pause" : "resume"
    try {
      const res = await fetch(`/api/backend-proxy/sourcing-agents/${agentId}/${action}`, { method: "PATCH" })
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(extractErrorMessage(errData, res.status))
      }
      toast.success(action === "pause" ? t("studio.toast.agentPaused") : t("studio.toast.agentResumed"))
      loadData()
    } catch (err) {
      console.error("Failed to toggle agent:", err)
      toast.error(t("studio.toast.errorToggleStatus"), t("studio.toast.tryAgain"))
    }
  }

  const handleTemplateSelect = async (template: AgentTemplate) => {
    selectTemplate(template)
    try {
      const token = localStorage.getItem("auth_token")
      const res = await fetch("/api/backend-proxy/custom-agents", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
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
      if (!res.ok) throw new Error(t("studio.toast.errorCreating"))
      toast.success(t("studio.toast.agentCreated", { name: template.name }), t("studio.toast.agentCreatedDesc"))
      mutateCustomAgents()
      resetStudio()
      setActiveTab("custom")
    } catch {
      toast.error(t("studio.toast.errorCreating"), t("studio.toast.tryAgainShort"))
    }
  }

  const handleCustomAgentToggle = async (agent: CustomAgent) => {
    const newStatus = agent.status === "active" ? "paused" : "active"
    try {
      const token = localStorage.getItem("auth_token")
      await fetch(`/api/backend-proxy/custom-agents/${agent.id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ status: newStatus }),
      })
      toast.success(newStatus === "active" ? t("studio.toast.agentActivated") : t("studio.toast.agentPaused"))
      mutateCustomAgents()
    } catch {
      toast.error(t("studio.toast.errorStatus"))
    }
  }

  const totalViewed = agents.reduce((s, a) => s + a.profiles_viewed, 0)
  const totalApproved = agents.reduce((s, a) => s + a.profiles_approved, 0)
  const activeCount = agents.filter(a => a.status === "active").length

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-lia-bg-primary">
      <div className="flex-shrink-0 px-4 pt-3 pb-0">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-lg font-semibold text-lia-text-primary">
            {t("studio.title")}
          </h1>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={loadData}
              className="gap-2 text-lia-text-secondary hover:text-lia-text-primary"
            >
              <RefreshCw className="w-4 h-4" />
            </Button>
            {/* BUG-12: CTA explícito para o ConversationalCreator (que estava
                escondido na aba "Custom Agents" sem call-to-action visível).
                Clicar troca para a aba e dá scroll até o componente. */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setActiveTab("custom")
                // Aguarda render da aba antes de scrollar
                setTimeout(() => {
                  document.getElementById("agent-studio-conversational-creator")
                    ?.scrollIntoView({ behavior: "smooth", block: "start" })
                }, 80)
              }}
              className="gap-2"
            >
              <Wand2 className="w-4 h-4" />
              Criar com IA
            </Button>
            <Button
              size="sm"
              onClick={() => setShowCreateModal(true)}
              className="gap-2 bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
            >
              <Plus className="w-4 h-4" />
              {t("studio.createAgent")}
            </Button>
          </div>
        </div>

        <PageTabNavigation
          tabs={[
            { id: "agents", label: t("studio.tabs.sourcingAgents"), icon: Bot, count: agents.length },
            { id: "custom", label: t("studio.tabs.customAgents"), icon: Wand2 },
            { id: "marketplace", label: t("studio.tabs.marketplace"), icon: Store },
            { id: "twins", label: t("studio.tabs.digitalTwins"), icon: Users },
            { id: "search", label: t("studio.tabs.smartSearch"), icon: Search },
          ]}
          activeTab={activeTab}
          onTabChange={(id) => setActiveTab(id as typeof activeTab)}
        />

        {agents.length > 0 && (
          <div className="flex items-center gap-6 mt-2 mb-1">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs font-medium text-lia-text-secondary">
                {t("studio.stats.activeAgents", { count: activeCount })}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <Eye className="w-3.5 h-3.5 text-lia-text-disabled" />
              <span className="text-xs text-lia-text-secondary">
                <span className="font-semibold text-lia-text-primary">{totalViewed}</span> {t("studio.stats.profilesAnalyzed")}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <ThumbsUp className="w-3.5 h-3.5 text-emerald-500" />
              <span className="text-xs text-lia-text-secondary">
                <span className="font-semibold text-lia-text-primary">{totalApproved}</span> {t("studio.stats.approved")}
              </span>
            </div>
            {totalViewed > 0 && (
              <div className="flex items-center gap-1.5">
                <BarChart3 className="w-3.5 h-3.5 text-lia-text-disabled" />
                <span className="text-xs text-lia-text-secondary">
                  <span className="font-semibold text-lia-text-primary">{Math.round((totalApproved / totalViewed) * 100)}%</span> {t("studio.stats.approvalRate")}
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="flex-1 overflow-auto px-4 py-4">
        {activeTab === "agents" && (
          <div className="space-y-8">
            {/* How It Works — show prominently when no agents */}
            {agents.length === 0 && !isLoading && (
              <section className="relative overflow-hidden rounded-xl border border-lia-border-subtle bg-gradient-to-br from-lia-bg-secondary to-lia-bg-primary p-6">
                <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl from-cyan-500/5 to-transparent rounded-full -translate-y-1/2 translate-x-1/4" />
                <div className="relative">
                  <div className="flex items-center gap-2 mb-1">
                    <Brain className="w-4 h-4 text-wedo-cyan" />
                    <span className="text-xs font-semibold uppercase tracking-wider text-wedo-cyan">
                      {t("studio.whatIsAgent")}
                    </span>
                  </div>
                  <h2 className="text-base font-semibold text-lia-text-primary mb-2">
                    {t("studio.virtualRecruiter")}
                  </h2>
                  <p className="text-sm text-lia-text-secondary mb-6 max-w-2xl">
                    {t("studio.virtualRecruiterDesc")}
                  </p>

                  {/* BUG-10: grid responsivo — antes ia direto para 4 colunas em md (768px),
                      o que cortava textos ("PASS" em vez de "PASSO") quando o chat lateral
                      ocupa ~360px. Agora só vai para 4 colunas em xl+ (1280px) e usa 2
                      colunas no intervalo intermediário, permitindo respirar os textos. */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
                    {FLOW_STEPS_CONFIG.map((step, i) => (
                      <div key={i} className="flex items-start gap-3 min-w-0">
                        <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0", step.bg)}>
                          <step.icon className={cn("w-5 h-5", step.color)} />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-1.5 mb-0.5">
                            <span className="text-[10px] font-bold text-lia-text-disabled uppercase whitespace-nowrap">{t("studio.flowSteps.step")} {i + 1}</span>
                            {i < 3 && <ArrowRight className="w-3 h-3 text-lia-text-disabled hidden xl:block" />}
                          </div>
                          <p className="text-xs font-semibold text-lia-text-primary break-words">{t(step.titleKey)}</p>
                          <p className="text-[11px] text-lia-text-secondary leading-relaxed break-words">{t(step.descKey)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </section>
            )}

            {/* Templates */}
            <section>
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h2 className="text-sm font-semibold text-lia-text-primary">
                    {agents.length === 0 ? t("studio.templates.startChoosing") : t("studio.templates.createNew")}
                  </h2>
                  <p className="text-xs text-lia-text-secondary mt-0.5">
                    {t("studio.templates.preConfigured")}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                {templates.map(t => {
                  const Icon = SECTOR_ICONS[t.icon] || Brain
                  const colors = SECTOR_COLORS[t.icon] || SECTOR_COLORS.code
                  return (
                    <button
                      key={t.id}
                      onClick={() => { setSelectedTemplate(t); setShowCreateModal(true) }}
                      className={cn(
                        "group relative flex flex-col items-center gap-2.5 p-5 rounded-xl border border-lia-border-subtle",
                        "bg-lia-bg-secondary hover:border-lia-border-medium transition-all duration-200",
                        "hover:shadow-lg cursor-pointer", colors.glow && `hover:${colors.glow}`
                      )}
                    >
                      <div className={cn(
                        "w-12 h-12 rounded-xl flex items-center justify-center transition-transform group-hover:scale-110",
                        colors.bg
                      )}>
                        <Icon className={cn("w-6 h-6", colors.text)} />
                      </div>
                      <div className="text-center">
                        <p className="text-xs font-semibold text-lia-text-primary">{t.display_name}</p>
                        <p className="text-[10px] text-lia-text-secondary mt-0.5 line-clamp-2">{t.description}</p>
                      </div>
                    </button>
                  )
                })}
                <button
                  onClick={() => { setSelectedTemplate(null); setShowCreateModal(true) }}
                  className={cn(
                    "group flex flex-col items-center gap-2.5 p-5 rounded-xl border-2 border-dashed border-lia-border-subtle",
                    "hover:border-wedo-cyan/40 transition-all duration-200 cursor-pointer"
                  )}
                >
                  <Brain className="w-6 h-6 text-wedo-cyan transition-transform group-hover:scale-110" />
                  <div className="text-center">
                    <p className="text-xs font-semibold text-lia-text-primary">{t("studio.templates.custom")}</p>
                    <p className="text-[10px] text-lia-text-secondary mt-0.5">{t("studio.templates.createFromScratch")}</p>
                  </div>
                </button>
              </div>
            </section>

            {/* Active Agents */}
            <section>
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-lia-text-primary">
                  {t("studio.myAgents")}
                  {agents.length > 0 && (
                    <span className="ml-2 px-2 py-0.5 rounded-full text-[10px] font-bold bg-lia-interactive-active text-lia-text-primary">
                      {agents.length}
                    </span>
                  )}
                </h2>
              </div>

              {isLoading ? (
                <div className="flex items-center justify-center py-16">
                  <div className="flex flex-col items-center gap-3 text-lia-text-secondary">
                    <Loader2 className="w-6 h-6 animate-spin" />
                    <span className="text-xs">{t("studio.loading")}</span>
                  </div>
                </div>
              ) : agents.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 rounded-xl border border-dashed border-lia-border-subtle bg-lia-bg-secondary/50">
                  <div className="w-14 h-14 rounded-2xl bg-lia-bg-tertiary flex items-center justify-center mb-3">
                    <Bot className="w-7 h-7 text-lia-text-disabled" />
                  </div>
                  <p className="text-sm font-medium text-lia-text-secondary">{t("studio.noAgentsYet")}</p>
                  <p className="text-xs text-lia-text-disabled mt-1 mb-4">
                    {t("studio.chooseTemplateAbove")}
                  </p>
                  <Button
                    size="sm"
                    onClick={() => setShowCreateModal(true)}
                    className="gap-2 bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    {t("studio.createFirstAgent")}
                  </Button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {agents.map(agent => (
                    <AgentCard
                      key={agent.id}
                      agent={agent}
                      onToggleStatus={() => handleToggleStatus(agent.id, agent.status)}
                      onCalibrate={() => onStartCalibration?.(agent.id)}
                      onNavigate={() => {
                        if (agent.talent_pool_id) {
                          onNavigateToPool?.(agent.talent_pool_id)
                        } else if (agent.job_id) {
                          onNavigateToJob?.(agent.job_id)
                        } else {
                          toast.warning(
                            t("studio.toast.noLinkTitle"),
                            t("studio.toast.noLinkDesc")
                          )
                        }
                      }}
                    />
                  ))}
                </div>
              )}
            </section>

            {/* How it works — compact version when agents exist */}
            {agents.length > 0 && (
              <section className="rounded-xl border border-lia-border-subtle bg-lia-bg-secondary p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Brain className="w-4 h-4 text-wedo-cyan" />
                  <h2 className="text-sm font-semibold text-lia-text-primary">{t("studio.howItWorks")}</h2>
                </div>
                {/* BUG-10: passa para grid responsivo — em telas apertadas (chat
                    lateral aberto) fica em 2 colunas sem truncar textos; em telas
                    largas mantém a visual horizontal com setas. */}
                <div className="grid grid-cols-1 sm:grid-cols-2 xl:flex xl:items-start xl:gap-2">
                  {FLOW_STEPS_CONFIG.map((step, i) => (
                    <React.Fragment key={i}>
                      <div className="xl:flex-1 flex items-start gap-2.5 min-w-0">
                        <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0", step.bg)}>
                          <step.icon className={cn("w-4 h-4", step.color)} />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-semibold text-lia-text-primary break-words">{t(step.titleKey)}</p>
                          <p className="text-[10px] text-lia-text-secondary leading-relaxed break-words">{t(step.descKey)}</p>
                        </div>
                      </div>
                      {i < 3 && (
                        <ArrowRight className="hidden xl:block w-4 h-4 text-lia-text-disabled flex-shrink-0 mt-2" />
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}

        {activeTab === "custom" && (
          <div className="space-y-6">
            {/* Pending Approvals (admin only — hidden if empty or not admin) */}
            <section>
              <ApprovalsList onReviewed={() => mutateCustomAgents()} />
            </section>

            {/* My Agents */}
            <section>
              <h3 className="text-sm font-semibold text-lia-text-primary mb-3">
                {t("studio.myAgents")} {customAgents.length > 0 && `(${customAgents.length})`}
              </h3>
              {customAgents.length === 0 ? (
                <div className="text-center py-8">
                  <Bot className="w-8 h-8 text-lia-text-disabled mx-auto mb-2" />
                  <p className="text-sm text-lia-text-secondary">{t("studio.noAgentsYet")}</p>
                  <p className="text-xs text-lia-text-disabled mt-1">{t("studio.chooseTemplateOrDescribe")}</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {customAgents.map((agent) => (
                    <div key={agent.id} onClick={() => setDetailsAgent(agent)} className="cursor-pointer">
                      <CustomAgentCard
                        agent={agent}
                        onTest={(a) => { a; setTestAgent(agent) }}
                        onDeploy={(a) => { a; setDeployAgent(agent) }}
                        onToggleStatus={(a) => { handleCustomAgentToggle(a) }}
                      />
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Template Gallery */}
            <TemplateGallery
              onTemplateSelect={handleTemplateSelect}
              onCreateManual={() => setShowCreateModal(true)}
            />

            {/* Conversational Creator (target do CTA "Criar com IA" — BUG-12) */}
            <div id="agent-studio-conversational-creator" className="scroll-mt-4">
              <ConversationalCreator onAgentCreated={() => mutateCustomAgents()} />
            </div>

            {/* Deploy Dialog */}
            <DeployDialog
              agent={deployAgent}
              open={!!deployAgent}
              onClose={() => setDeployAgent(null)}
              onDeployed={() => mutateCustomAgents()}
            />

            {/* Test Debug Panel */}
            <TestDebugPanel
              agent={testAgent}
              open={!!testAgent}
              onClose={() => setTestAgent(null)}
            />

            {/* Agent Details Panel */}
            <AgentDetailsPanel
              agent={detailsAgent}
              open={!!detailsAgent}
              onClose={() => setDetailsAgent(null)}
              onDeploy={(a) => { setDetailsAgent(null); setDeployAgent(a) }}
              onTest={(a) => { setDetailsAgent(null); setTestAgent(a) }}
            />

            {/* Legacy form for advanced editing */}
            <details className="mt-4">
              <summary className="text-xs text-lia-text-disabled cursor-pointer hover:text-lia-text-secondary">
                {t("studio.advancedForm")}
              </summary>
              <div className="mt-3">
                <CustomAgentsTab />
              </div>
            </details>
          </div>
        )}

        {activeTab === "marketplace" && (
          <MarketplaceTab />
        )}

        {activeTab === "twins" && (
          <div className="space-y-4">
            <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-secondary p-5 mb-4">
              <div className="flex items-center gap-2 mb-1">
                <Users className="w-4 h-4 text-wedo-cyan" />
                <span className="text-xs font-semibold uppercase tracking-wider text-wedo-cyan">{t("studio.twins.label")}</span>
              </div>
              <h2 className="text-base font-semibold text-lia-text-primary mb-1">{t("studio.twins.cloneReasoning")}</h2>
              <p className="text-sm text-lia-text-secondary max-w-2xl">
                {t("studio.twins.cloneDesc")}
              </p>
            </div>
            <TwinsList onEvaluate={(id) => setEvaluatingTwinId(id)} />
          </div>
        )}

        {activeTab === "search" && (
          <div className="space-y-4">
            <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-secondary p-5 mb-4">
              <div className="flex items-center gap-2 mb-1">
                <Search className="w-4 h-4 text-wedo-cyan" />
                <span className="text-xs font-semibold uppercase tracking-wider text-wedo-cyan">{t("studio.search.multiStrategy")}</span>
              </div>
              <h2 className="text-base font-semibold text-lia-text-primary mb-1">{t("studio.search.fourStrategies")}</h2>
              <p className="text-sm text-lia-text-secondary max-w-2xl">
                {t("studio.search.searchDesc")}
              </p>
            </div>
            <MultiStrategySearchPanel />
          </div>
        )}
      </div>

      {evaluatingTwinId && (
        <EvaluateWithTwinModal
          twinId={evaluatingTwinId}
          candidateProfile={{}}
          jobContext={{}}
          isOpen
          onClose={() => setEvaluatingTwinId(null)}
        />
      )}

      {showCreateModal && (
        <CreateAgentModal
          initialTemplate={selectedTemplate}
          onClose={() => { setShowCreateModal(false); setSelectedTemplate(null) }}
          onCreated={(agentId) => {
            setShowCreateModal(false)
            setSelectedTemplate(null)
            loadData()
            onStartCalibration?.(agentId)
          }}
        />
      )}
    </div>
  )
}

function AgentCard({
  agent, onToggleStatus, onCalibrate, onNavigate,
}: {
  agent: SourcingAgent
  onToggleStatus: () => void
  onCalibrate: () => void
  onNavigate: () => void
}) {
  const t = useTranslations("agents")
  const status = STATUS_CONFIG_STYLES[agent.status]
  const strategy = agent.search_strategy as { required_skills?: string[]; exclusions?: string[] }
  const totalReviewed = agent.profiles_approved + agent.profiles_rejected
  const approvalRate = totalReviewed > 0 ? Math.round((agent.profiles_approved / totalReviewed) * 100) : 0

  return (
    <div className={cn(
      "group relative rounded-xl border border-lia-border-subtle bg-lia-bg-secondary",
      "hover:border-lia-border-medium hover:shadow-md transition-all duration-200"
    )}>
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/10 to-violet-500/10 flex items-center justify-center">
              <Bot className="w-5 h-5 text-wedo-cyan" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <p className="text-sm font-semibold text-lia-text-primary">{agent.agent_name}</p>
                <BetaBadge />
              </div>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-[10px] text-lia-text-disabled">v{agent.calibration_v}</span>
                <span className="text-lia-text-disabled">·</span>
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3 text-lia-text-disabled" />
                  <span className="text-[10px] text-lia-text-disabled">
                    {new Date(agent.created_at).toLocaleDateString(undefined, { day: "2-digit", month: "short" })}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div className={cn("flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold", status.bg, status.text)}>
            <div className={cn("w-1.5 h-1.5 rounded-full", status.dot, status.pulse && "animate-pulse")} />
            {t(status.labelKey)}
          </div>
        </div>

        {/* Strategy Pills */}
        {strategy.required_skills?.length ? (
          <div className="flex flex-wrap gap-1 mb-3">
            {strategy.required_skills.slice(0, 4).map((skill, i) => (
              <span key={i} className="px-2 py-0.5 rounded-xl bg-lia-bg-tertiary text-[10px] font-medium text-lia-text-secondary">
                {skill}
              </span>
            ))}
            {(strategy.required_skills.length > 4) && (
              <span className="px-2 py-0.5 rounded-xl bg-lia-bg-tertiary text-[10px] text-lia-text-disabled">
                +{strategy.required_skills.length - 4}
              </span>
            )}
          </div>
        ) : null}

        {/* Stats Row */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          <div className="flex flex-col items-center p-2 rounded-lg bg-lia-bg-primary">
            <span className="text-xs font-bold text-lia-text-primary">{agent.profiles_viewed}</span>
            <span className="text-[9px] text-lia-text-disabled uppercase tracking-wider">{t("studio.stats.analyzed")}</span>
          </div>
          <div className="flex flex-col items-center p-2 rounded-lg bg-lia-bg-primary">
            <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">{agent.profiles_approved}</span>
            <span className="text-[9px] text-lia-text-disabled uppercase tracking-wider">{t("studio.stats.approved")}</span>
          </div>
          <div className="flex flex-col items-center p-2 rounded-lg bg-lia-bg-primary">
            <span className="text-xs font-bold text-lia-text-primary">{approvalRate}%</span>
            <span className="text-[9px] text-lia-text-disabled uppercase tracking-wider">{t("studio.stats.rate")}</span>
          </div>
        </div>

        {/* Link indicator */}
        {(agent.talent_pool_id || agent.job_id) ? (
          <div className="flex items-center gap-1.5 mb-3 px-2.5 py-1.5 rounded-lg bg-lia-bg-primary border border-lia-border-subtle">
            {agent.talent_pool_id ? (
              <>
                <Database className="w-3 h-3 text-lia-text-disabled" />
                <span className="text-[10px] text-lia-text-secondary">{t("studio.card.linkedToPool")}</span>
              </>
            ) : (
              <>
                <Briefcase className="w-3 h-3 text-lia-text-disabled" />
                <span className="text-[10px] text-lia-text-secondary">{t("studio.card.linkedToJob")}</span>
              </>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-1.5 mb-3 px-2.5 py-1.5 rounded-lg bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800">
            <Brain className="w-3 h-3 text-amber-500" />
            <span className="text-[10px] text-amber-700 dark:text-amber-400">{t("studio.card.noLink")}</span>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 pt-3 border-t border-lia-border-subtle">
          <button
            onClick={onToggleStatus}
            className={cn(
              "flex items-center justify-center w-8 h-8 rounded-lg border border-lia-border-subtle",
              "hover:bg-lia-bg-tertiary transition-colors"
            )}
            title={agent.status === "active" ? t("studio.card.pause") : t("studio.card.resume")}
          >
            {agent.status === "active" ? (
              <Pause className="w-3.5 h-3.5 text-lia-text-secondary" />
            ) : (
              <Play className="w-3.5 h-3.5 text-emerald-600" />
            )}
          </button>
          <button
            onClick={onCalibrate}
            className="flex-1 flex items-center justify-center gap-1.5 h-8 rounded-lg border border-lia-border-subtle text-xs font-medium text-lia-text-secondary hover:bg-lia-bg-tertiary hover:text-lia-text-primary transition-colors"
          >
            <Activity className="w-3.5 h-3.5" />
            {t("studio.card.recalibrate")}
          </button>
          <button
            onClick={onNavigate}
            className="flex items-center justify-center gap-1 h-8 px-3 rounded-lg bg-lia-btn-primary-bg text-lia-btn-primary-text text-xs font-medium hover:bg-lia-btn-primary-hover transition-colors"
          >
            {t("studio.card.view")}
            <ChevronRight className="w-3 h-3" />
          </button>
        </div>
      </div>
    </div>
  )
}

function CreateAgentModal({ initialTemplate, onClose, onCreated }: {
  initialTemplate: SectorTemplate | null
  onClose: () => void
  onCreated: (agentId: string) => void
}) {
  const t = useTranslations("agents")
  const [agentName, setAgentName] = useState(initialTemplate ? `${initialTemplate.display_name}` : "")
  const [linkType, setLinkType] = useState<"job" | "pool" | "none">("none")
  const [linkId, setLinkId] = useState("")
  const [candidatesPerDay, setCandidatesPerDay] = useState(20)
  const [notifyFrequency, setNotifyFrequency] = useState("daily")
  const [isCreating, setIsCreating] = useState(false)
  const sectorId = initialTemplate?.id || ""

  const [createError, setCreateError] = useState("")

  const handleCreate = async () => {
    setIsCreating(true)
    setCreateError("")
    try {
      let templateId: string | undefined
      if (sectorId) {
        try {
          const templateRes = await fetch(`/api/backend-proxy/agent-templates/sectors/${sectorId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ agent_name: agentName }),
          })
          if (templateRes.ok) {
            const templateData = await templateRes.json()
            templateId = templateData?.template_id
          }
        } catch {
          // template application is optional
        }
      }

      const res = await fetch("/api/backend-proxy/sourcing-agents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          agent_name: agentName,
          job_id: linkType === "job" ? linkId : null,
          talent_pool_id: linkType === "pool" ? linkId : null,
          agent_template_id: templateId || null,
          preferences: {
            candidates_per_day: candidatesPerDay,
            notify_frequency: notifyFrequency,
            channels: ["internal", "linkedin"],
          },
        }),
      })
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(extractErrorMessage(errData, res.status))
      }
      const data = await res.json()
      if (data?.agent_id) onCreated(data.agent_id)
      else onCreated(data?.id || "")
    } catch (err) {
      const msg = err instanceof Error ? err.message : t("studio.toast.errorCreating")
      setCreateError(msg)
      console.error("Failed to create agent:", err)
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-lg bg-lia-bg-primary border-lia-border-subtle">
        <DialogHeader>
          <DialogTitle className="text-base font-semibold text-lia-text-primary flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500/10 to-violet-500/10 flex items-center justify-center">
              <Bot className="w-4 h-4 text-wedo-cyan" />
            </div>
            {initialTemplate ? t("studio.modal.createTitleWithTemplate", { name: initialTemplate.display_name }) : t("studio.modal.createTitle")}
          </DialogTitle>
          <DialogDescription className="sr-only">{t("studio.modal.configureDesc")}</DialogDescription>
        </DialogHeader>

        <div className="space-y-5 py-4">
          <div>
            <label className="text-xs font-semibold text-lia-text-primary mb-1.5 block">{t("studio.modal.agentName")}</label>
            <input
              type="text"
              value={agentName}
              onChange={e => setAgentName(e.target.value)}
              placeholder={t("studio.modal.agentNamePlaceholder")}
              className="w-full border border-lia-border-subtle rounded-lg px-3 py-2.5 text-sm bg-lia-bg-secondary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-wedo-cyan/30 focus:border-wedo-cyan/50"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-lia-text-primary mb-1.5 block">{t("studio.modal.linkTo")}</label>
            <div className="flex gap-2">
              {[
                { id: "none" as const, label: t("studio.modal.none"), icon: Brain },
                { id: "job" as const, label: t("studio.modal.job"), icon: Briefcase },
                { id: "pool" as const, label: t("studio.modal.talentPool"), icon: Database },
              ].map(opt => (
                <button
                  key={opt.id}
                  onClick={() => setLinkType(opt.id)}
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border transition-all",
                    linkType === opt.id
                      ? "border-lia-text-primary bg-lia-bg-tertiary text-lia-text-primary"
                      : "border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary"
                  )}
                >
                  <opt.icon className="w-3.5 h-3.5" />
                  {opt.label}
                </button>
              ))}
            </div>
            {linkType === "none" && (
              <div className="mt-2 px-3 py-2 rounded-lg bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800">
                <p className="text-xs text-amber-700 dark:text-amber-400">
                  {t("studio.modal.noLinkWarning")}
                </p>
              </div>
            )}
            {linkType !== "none" && (
              <input
                type="text"
                value={linkId}
                onChange={e => setLinkId(e.target.value)}
                placeholder={linkType === "job" ? t("studio.modal.jobIdPlaceholder") : t("studio.modal.poolIdPlaceholder")}
                className="mt-2 w-full border border-lia-border-subtle rounded-lg px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-wedo-cyan/30"
              />
            )}
          </div>

          <div>
            <label className="text-xs font-semibold text-lia-text-primary mb-1.5 block">{t("studio.modal.candidatesPerDay")}</label>
            <div className="flex gap-2">
              {[10, 20, 30, 50].map(n => (
                <button
                  key={n}
                  onClick={() => setCandidatesPerDay(n)}
                  className={cn(
                    "px-4 py-2 rounded-lg text-xs font-medium border transition-all",
                    candidatesPerDay === n
                      ? "border-lia-text-primary bg-lia-bg-tertiary text-lia-text-primary"
                      : "border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary"
                  )}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-lia-text-primary mb-1.5 block">{t("studio.modal.notificationFrequency")}</label>
            <div className="flex gap-2">
              {[
                { id: "realtime", label: t("studio.modal.perCandidate") },
                { id: "daily", label: t("studio.modal.dailySummary") },
                { id: "weekly", label: t("studio.modal.weeklySummary") },
              ].map(opt => (
                <button
                  key={opt.id}
                  onClick={() => setNotifyFrequency(opt.id)}
                  className={cn(
                    "px-3 py-2 rounded-lg text-xs font-medium border transition-all",
                    notifyFrequency === opt.id
                      ? "border-lia-text-primary bg-lia-bg-tertiary text-lia-text-primary"
                      : "border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary"
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {createError && (
          <div className="mx-6 mb-2 px-3 py-2 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800">
            <p className="text-xs text-red-700 dark:text-red-400">{createError}</p>
          </div>
        )}

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={onClose}
            className="border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary"
          >
            {t("studio.modal.cancel")}
          </Button>
          <Button
            onClick={handleCreate}
            disabled={!agentName.trim() || isCreating}
            className="gap-2 bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
          >
            {isCreating ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                {t("studio.modal.creating")}
              </>
            ) : (
              <>
                <Zap className="w-3.5 h-3.5" />
                {t("studio.modal.createAndCalibrate")}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
