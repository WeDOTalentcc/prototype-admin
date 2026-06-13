"use client"

import React, { useState, useEffect } from "react"
import {
  TwinsList,
  EvaluateWithTwinModal,
  CreateDigitalTwinModal,
} from "@/components/pages-agent-studio/DigitalTwinComponents"
import CustomAgentsTab, { CreateCustomAgentModal } from "@/components/pages-agent-studio/CustomAgentsTab"
import { AgentCard as CustomAgentCard, AgentDetailsPanel, DeployDialog, ConversationalCreator, TestDebugPanel, ApprovalsList } from "@/components/pages-agent-studio/custom-agents"
import { StudioCardShell } from "@/components/pages-agent-studio/StudioCardShell"
import { TemplatePreviewModal } from "@/components/pages-agent-studio/custom-agents/template-preview-modal"
import { useCustomAgents, useStudioAlerts } from "@/hooks/agents"
import { useAgentStudioStore } from "@/stores/agent-studio-store"
import type { CustomAgent, AgentTemplate } from "@/components/pages-agent-studio/custom-agents/types"
import { ServiceFunnelView, StudioOnboarding } from "@/components/pages-agent-studio/ServiceFunnelView"
import type { FunnelServiceData, ServiceSlug, ServiceStatus } from "@/components/pages-agent-studio/ServiceFunnelView"
import { AlignmentStatusCard } from "@/components/pages-agent-studio/AlignmentStatusCard"
import { OfferStatusCard } from "@/components/pages-agent-studio/OfferStatusCard"
import { NpsStatusCard } from "@/components/pages-agent-studio/NpsStatusCard"
import { useRouter, useSearchParams } from "next/navigation"
import { useLocale } from "next-intl"
import { PageTabNavigation, type PageTab } from "@/components/ui/page-tab-navigation"
import { StudioControlRoom } from "@/components/pages-agent-studio/control-room"
import { usePendingApprovals } from "@/hooks/agents/use-approvals"
import {
  Bot, Plus, Play, Pause, Briefcase, Database,
  Factory, HeartPulse, ShoppingCart, Code, Truck, Brain,
  ChevronRight, Zap, Target, ArrowRight,
  Activity, RefreshCw, Workflow,
  Loader2, Users, Wand2, Store,
  GraduationCap, Pencil
} from "lucide-react"
import { cn } from "@/lib/utils"
import { toast } from "@/lib/toast"
import { extractErrorMessage } from "@/lib/api/extract-error-message"
import { Button } from "@/components/ui/button"
import { BetaBadge } from "@/components/ui/beta-badge"
import { TabSectionHeader } from "@/components/pages-agent-studio/TabSectionHeader"
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

const STATUS_CONFIG_STYLES = {
  active:    { labelKey: "studio.status.active" as const,    dot: "bg-wedo-green", bg: "bg-wedo-green/10", text: "text-wedo-green", pulse: true  },
  paused:    { labelKey: "studio.status.paused" as const,    dot: "bg-wedo-orange", bg: "bg-wedo-orange/10", text: "text-wedo-orange", pulse: false },
  completed: { labelKey: "studio.status.completed" as const, dot: "bg-lia-border-default", bg: "bg-lia-bg-tertiary", text: "text-lia-text-tertiary", pulse: false },
}

// Single lia-cyan for all flow step icons — replaces 4-color palette
const FLOW_STEPS_CONFIG = [
  { icon: Target,       titleKey: "studio.flowSteps.chooseProfile" as const,    descKey: "studio.flowSteps.chooseProfileDesc" as const    },
  { icon: Wand2,        titleKey: "studio.flowSteps.configureAgent" as const,   descKey: "studio.flowSteps.configureAgentDesc" as const   },
  { icon: GraduationCap, titleKey: "studio.flowSteps.teachByEvaluating" as const, descKey: "studio.flowSteps.teachByEvaluatingDesc" as const },
  { icon: Zap,          titleKey: "studio.flowSteps.receiveCandidates" as const, descKey: "studio.flowSteps.receiveCandidatesDesc" as const },
]

interface AgentStudioPageProps {
  onNavigateToPool?: (poolId: string) => void
  onNavigateToJob?: (jobId: string) => void
  onStartCalibration?: (agentId: string) => void
}

const SLUG_TO_MARKETPLACE_CATEGORY: Record<string, string> = {
  sourcing: "sourcing",
  screening: "screening",
  calibration: "screening",
  alignment: "communication",
  offer: "communication",
  nps: "analytics",
  intake: "general",
}

// ── Top-level navigation tabs (equal-weight) ────────────────────────────────
// URL-driven via ?tab=. Aliases keep legacy deep links working (the old tab
// layout linked ?tab=control-room / sala-de-controle before the funnel redesign).
type StudioTab = "funil" | "operacao" | "personalizados" | "marketplace" | "gemeos"

const TAB_ALIASES: Record<string, StudioTab> = {
  funil: "funil", funnel: "funil",
  operacao: "operacao", operations: "operacao",
  "control-room": "operacao", "sala-de-controle": "operacao",
  personalizados: "personalizados", custom: "personalizados", "my-agents": "personalizados",
  marketplace: "marketplace",
  gemeos: "gemeos", "digital-twins": "gemeos", twins: "gemeos",
}

function normalizeTab(raw: string | null): StudioTab {
  return (raw ? TAB_ALIASES[raw] : undefined) ?? "funil"
}

export default function AgentStudioPage({
  onNavigateToPool,
  onNavigateToJob,
  onStartCalibration,
}: AgentStudioPageProps) {
  const t = useTranslations("agents")
  const router = useRouter()
  const locale = useLocale()
  const [agents, setAgents] = useState<SourcingAgent[]>([])
  const [templates, setTemplates] = useState<SectorTemplate[]>([])
  const [openJobs, setOpenJobs] = useState<{ id: string; title: string; status: string }[]>([])
  const [studioSummaryServices, setStudioSummaryServices] = useState<Record<string, { status: string; metric?: string }>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [evaluatingTwinId, setEvaluatingTwinId] = useState<string | null>(null)
  const [showCreateTwinModal, setShowCreateTwinModal] = useState(false)
  const [twinListRefreshKey, setTwinListRefreshKey] = useState(0)
  const [deployAgent, setDeployAgent] = useState<CustomAgent | null>(null)
  const [testAgent, setTestAgent] = useState<CustomAgent | null>(null)
  const [detailsAgent, setDetailsAgent] = useState<CustomAgent | null>(null)
  const { agents: customAgents, mutate: mutateCustomAgents } = useCustomAgents()
  const { alerts, alertCount, twinSummary } = useStudioAlerts()
  const { selectTemplate, reset: resetStudio } = useAgentStudioStore()
  const [selectedTemplate, setSelectedTemplate] = useState<SectorTemplate | null>(null)
  const [previewTemplate, setPreviewTemplate] = useState<AgentTemplate | null>(null)
  // Top-level navigation — URL-driven (?tab=) so deep links + back/forward work.
  const searchParams = useSearchParams()
  const [activeTab, setActiveTabState] = useState<StudioTab>(() => normalizeTab(searchParams.get("tab")))
  useEffect(() => {
    const next = normalizeTab(searchParams.get("tab"))
    setActiveTabState(prev => (prev === next ? prev : next))
  }, [searchParams])
  const setActiveTab = (id: StudioTab) => {
    setActiveTabState(id)
    const sp = new URLSearchParams(Array.from(searchParams.entries()))
    sp.set("tab", id)
    router.replace(`?${sp.toString()}`, { scroll: false })
  }
  const { total: pendingApprovals } = usePendingApprovals()
  const [onboardingDismissed, setOnboardingDismissed] = useState(true)

  useEffect(() => {
    loadData()
    setOnboardingDismissed(!!localStorage.getItem("studio_onboarding_done"))
  }, [])

  const loadData = async () => {
    setIsLoading(true)
    try {
      const [agentsRes, templatesRes, jobsRes] = await Promise.allSettled([
        fetch("/api/backend-proxy/sourcing-agents"),
        fetch("/api/backend-proxy/agent-templates/sectors"),
        fetch("/api/backend-proxy/job-vacancies?status=publicada,ao_vivo,rascunho,enriquecida&limit=50", { credentials: "include" }),
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
      if (jobsRes.status === "fulfilled" && jobsRes.value.ok) {
        try {
          const jobsData = await jobsRes.value.json()
          const rawJobs = Array.isArray(jobsData?.jobs) ? jobsData.jobs : Array.isArray(jobsData) ? jobsData : []
          const mapped = rawJobs.map((j: { id: string; title?: string; status?: string }) => ({
            id: String(j.id),
            title: j.title ?? "Vaga",
            status: j.status ?? "rascunho",
          }))
          setOpenJobs(mapped)
          // Fetch studio-summary for first live job to get screening status
          const firstLive = mapped.find((j: { status: string }) => ["publicada", "ao_vivo"].includes(j.status))
            ?? mapped.find((j: { status: string }) => ["rascunho", "enriquecida"].includes(j.status))
          if (firstLive) {
            try {
              const summaryRes = await fetch(
                `/api/backend-proxy/studio-summary?job_id=${encodeURIComponent(firstLive.id)}`,
                { credentials: "include" }
              )
              if (summaryRes.ok) {
                const summaryData = await summaryRes.json()
                if (summaryData?.services && typeof summaryData.services === "object") {
                  setStudioSummaryServices(summaryData.services)
                }
              }
            } catch { /* non-blocking */ }
          }
        } catch { /* */ }
      }
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

  const handleTemplateUse = async (template: AgentTemplate) => {
    selectTemplate(template)
    try {
      const res = await fetch("/api/backend-proxy/custom-agents", {
        method: "POST",
        credentials: "include",
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
      if (!res.ok) throw new Error(t("studio.toast.errorCreating"))
      toast.success(t("studio.toast.agentCreated", { name: template.name }), t("studio.toast.agentCreatedDesc"))
      mutateCustomAgents()
      resetStudio()
      setActiveTab("personalizados")
    } catch {
      toast.error(t("studio.toast.errorCreating"), t("studio.toast.tryAgainShort"))
    }
  }

  // "Ver detalhes" / "Ajustar antes" abrem o preview (revisar + ajustar nome) em vez
  // de criar direto. "Usar agora" cria via handleTemplateUse.
  const handleTemplatePreview = (template: AgentTemplate) => setPreviewTemplate(template)

  const handleCustomAgentToggle = async (agent: CustomAgent) => {
    const newStatus = agent.status === "active" ? "paused" : "active"
    try {
      await fetch(`/api/backend-proxy/custom-agents/${agent.id}`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      })
      toast.success(newStatus === "active" ? t("studio.toast.agentActivated") : t("studio.toast.agentPaused"))
      mutateCustomAgents()
    } catch {
      toast.error(t("studio.toast.errorStatus"))
    }
  }

  const activeCount = agents.filter(a => a.status === "active").length

  // ── Sourcing panel (embedded in funnel row) ──────────────────────────────
  const sourcingPanel = (
    <div className="p-4 space-y-5">
      {/* How it works (show when no agents) */}
      {agents.length === 0 && !isLoading && (
        <div className="rounded-lg border border-lia-border-subtle bg-lia-bg-elevated p-4">
          <div className="flex items-center gap-2 mb-2">
            <Brain className="w-3.5 h-3.5 text-lia-text-primary" />
            <span className="text-micro font-semibold uppercase tracking-widest text-lia-text-primary">
              {t("studio.whatIsAgent")}
            </span>
          </div>
          <p className="text-xs text-lia-text-tertiary mb-3 max-w-2xl">{t("studio.virtualRecruiterDesc")}</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
            {FLOW_STEPS_CONFIG.map((step, i) => (
              <div key={i} className="flex items-start gap-3 min-w-0">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 bg-lia-bg-tertiary">
                  <step.icon className="w-4 h-4 text-lia-text-primary" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span className="text-micro font-medium text-lia-text-tertiary uppercase tracking-wide whitespace-nowrap">
                      {t("studio.flowSteps.step")} {i + 1}
                    </span>
                    {i < 3 && <ArrowRight className="w-3 h-3 text-lia-border-default hidden xl:block" />}
                  </div>
                  <p className="text-xs font-semibold text-lia-text-primary break-words">{t(step.titleKey)}</p>
                  <p className="text-micro text-lia-text-tertiary leading-relaxed break-words">{t(step.descKey)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Templates */}
      <div>
        <p className="text-xs font-semibold text-lia-text-primary mb-2">
          {agents.length === 0 ? t("studio.templates.startChoosing") : t("studio.templates.createNew")}
        </p>
        <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
          {templates.map(tpl => {
            const Icon = SECTOR_ICONS[tpl.icon] || Brain
            return (
              <button
                key={tpl.id}
                onClick={() => { setSelectedTemplate(tpl); setShowCreateModal(true) }}
                className="group flex flex-col items-center gap-2 p-3 rounded-lg border border-lia-border-subtle bg-lia-bg-elevated hover:border-lia-border-medium/40 hover:bg-lia-bg-tertiary/30 transition-colors cursor-pointer"
              >
                <div className="w-9 h-9 rounded-lg flex items-center justify-center bg-lia-bg-tertiary transition-transform group-hover:scale-110">
                  <Icon className="w-5 h-5 text-lia-text-primary" />
                </div>
                <p className="text-micro font-semibold text-lia-text-primary text-center line-clamp-1">{tpl.display_name}</p>
              </button>
            )
          })}
          <button
            onClick={() => { setSelectedTemplate(null); setShowCreateModal(true) }}
            className="group flex flex-col items-center gap-2 p-3 rounded-lg border-2 border-dashed border-lia-border-subtle hover:border-lia-border-medium/40 transition-colors cursor-pointer"
          >
            <Brain className="w-5 h-5 text-lia-text-primary transition-transform group-hover:scale-110" />
            <p className="text-micro font-semibold text-lia-text-tertiary text-center">{t("studio.templates.custom")}</p>
          </button>
        </div>
      </div>

      {/* Agents list */}
      {isLoading ? (
        <div className="flex items-center justify-center py-10">
          <Loader2 className="w-5 h-5 animate-spin text-lia-text-tertiary" />
        </div>
      ) : agents.length === 0 ? (
        <div className="flex flex-col items-center py-8 rounded-lg border border-dashed border-lia-border-subtle">
          <Bot className="w-7 h-7 text-lia-border-default mb-2" />
          <p className="text-xs font-medium text-lia-text-tertiary">{t("studio.noAgentsYet")}</p>
          <p className="text-micro text-lia-text-tertiary mt-1 mb-3">{t("studio.chooseTemplateAbove")}</p>
          <Button size="sm" onClick={() => setShowCreateModal(true)} className="gap-1.5 bg-lia-btn-primary-bg text-white hover:bg-lia-btn-primary-hover">
            <Plus className="w-3.5 h-3.5" />
            {t("studio.createFirstAgent")}
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {agents.map(agent => (
            <AgentCard
              key={agent.id}
              agent={agent}
              onToggleStatus={() => handleToggleStatus(agent.id, agent.status)}
              onCalibrate={() => onStartCalibration?.(agent.id)}
              onEdit={() => router.push(`/${locale}/agent-studio/${agent.id}/edit`)}
              onNavigate={() => {
                if (agent.talent_pool_id) onNavigateToPool?.(agent.talent_pool_id)
                else if (agent.job_id) onNavigateToJob?.(agent.job_id)
                else toast.warning(t("studio.toast.noLinkTitle"), t("studio.toast.noLinkDesc"))
              }}
            />
          ))}
        </div>
      )}
    </div>
  )

  // ── Intake panel (embedded in funnel row) ────────────────────────────────
  const draftJobs = openJobs.filter(j => ["rascunho", "enriquecida", "ats_importada"].includes(j.status))
  const liveJobs = openJobs.filter(j => ["publicada", "ao_vivo"].includes(j.status))
  const intakePanel = (
    <div className="p-4 space-y-4">
      {openJobs.length === 0 ? (
        <div className="text-center py-6 space-y-2">
          <p className="text-sm text-lia-text-tertiary">Nenhuma vaga aberta encontrada.</p>
          <button
            type="button"
            onClick={() => router.push(`/${locale}/jobs/new`)}
            className="flex items-center gap-2 mx-auto text-sm font-medium text-white bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover rounded-lg px-4 py-2 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Criar vaga
          </button>
        </div>
      ) : (
        <>
          {liveJobs.length > 0 && (
            <div className="space-y-1.5">
              <p className="text-micro font-semibold uppercase tracking-widest text-wedo-green">
                {liveJobs.length} vaga{liveJobs.length !== 1 ? "s" : ""} ativa{liveJobs.length !== 1 ? "s" : ""}
              </p>
              {liveJobs.map(j => (
                <button
                  key={j.id}
                  type="button"
                  onClick={() => router.push(`/${locale}/jobs/${j.id}`)}
                  className="w-full flex items-center gap-3 rounded-lg border border-lia-border-subtle hover:border-lia-border-medium/40 px-3 py-2.5 bg-lia-bg-elevated hover:bg-lia-bg-secondary text-left transition-colors group"
                >
                  <div className="w-2 h-2 rounded-full bg-wedo-green flex-shrink-0" />
                  <span className="flex-1 text-sm text-lia-text-primary truncate">{j.title}</span>
                  <ChevronRight className="w-3.5 h-3.5 text-lia-text-tertiary opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              ))}
            </div>
          )}
          {draftJobs.length > 0 && (
            <div className="space-y-1.5">
              <p className="text-micro font-semibold uppercase tracking-widest text-wedo-orange">
                {draftJobs.length} em configuração
              </p>
              {draftJobs.map(j => (
                <button
                  key={j.id}
                  type="button"
                  onClick={() => router.push(`/${locale}/jobs/${j.id}?tab=edit`)}
                  className="w-full flex items-center gap-3 rounded-lg border border-lia-border-subtle hover:border-wedo-orange/40 px-3 py-2.5 bg-lia-bg-elevated hover:bg-wedo-orange/10 text-left transition-colors group"
                >
                  <div className="w-2 h-2 rounded-full bg-wedo-orange flex-shrink-0" />
                  <span className="flex-1 text-sm text-lia-text-primary truncate">{j.title}</span>
                  <span className="text-micro text-wedo-orange opacity-0 group-hover:opacity-100 transition-opacity">Completar →</span>
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )

  // ── Alignment panel (embedded in funnel row) ────────────────────────────
  // Prefer first live job, fall back to first draft — no agent required
  const firstJobId = liveJobs[0]?.id ?? draftJobs[0]?.id ?? agents.find(a => a.job_id)?.job_id ?? null
  // All jobs list for multi-job selector in status cards
  const allJobsList = openJobs.map(j => ({ id: j.id, title: j.title }))
  const alignmentPanel = (
    <div className="p-4 space-y-3">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs font-semibold uppercase tracking-widest text-lia-text-primary">Alinhamento c/ Gestor</span>
      </div>
      {firstJobId ? (
        <AlignmentStatusCard jobId={firstJobId} jobs={allJobsList} />
      ) : (
        <p className="text-xs text-lia-text-tertiary">
          Crie um agente de prospecção vinculado a uma vaga primeiro.
        </p>
      )}
    </div>
  )

  // ── Calibration panel (embedded in funnel row) ───────────────────────────
  const calibrationPanel = (
    <div className="p-4 space-y-4">
      <div className="flex items-center gap-2 mb-1">
        <Users className="w-4 h-4 text-lia-text-primary" />
        <span className="text-xs font-semibold uppercase tracking-widest text-lia-text-primary">{t("studio.twins.label")}</span>
      </div>
      <p className="text-xs text-lia-text-tertiary max-w-2xl">{t("studio.twins.cloneDesc")}</p>
      <TwinsList
        onEvaluate={(id) => setEvaluatingTwinId(id)}
        onCreateTwin={() => setShowCreateTwinModal(true)}
        refreshKey={twinListRefreshKey}
      />
    </div>
  )

  // ── Funnel services array ────────────────────────────────────────────────
  const funnelServices: FunnelServiceData[] = [
    {
      slug: "intake",
      ctaKey: "studio.services.ctaOpenJobs",
      status: liveJobs.length > 0 ? "active" : draftJobs.length > 0 ? "attention" : openJobs.length > 0 ? "configured" : "inactive",
      metric: openJobs.length > 0 ? `${openJobs.length} vaga${openJobs.length !== 1 ? "s" : ""}` : undefined,
      panel: intakePanel,
    },
    {
      slug: "alignment",
      ctaKey: "studio.services.ctaCreateAgent",
      status: firstJobId ? "configured" : "inactive",
      panel: alignmentPanel,
    },
    {
      slug: "sourcing",
      ctaKey: "studio.services.ctaCreateAgent",
      status: activeCount > 0 ? "active" : agents.length > 0 ? "configured" : "inactive",
      metric: agents.length > 0 ? `${activeCount} ${activeCount === 1 ? "ativo" : "ativos"}` : undefined,
      panel: sourcingPanel,
    },
    {
      slug: "screening",
      ctaKey: "studio.services.ctaConfigure",
      status: (studioSummaryServices.screening?.status as ServiceStatus) ?? (openJobs.length > 0 ? "configured" : "inactive"),
      metric: studioSummaryServices.screening?.metric,
    },
    {
      slug: "calibration",
      ctaKey: "studio.services.ctaCreateTwin",
      status: twinSummary.totalTwins > 0
        ? (alerts.some(a => a.type === "TWIN_LOW_ACCURACY") ? "attention" : "active")
        : "inactive",
      metric: twinSummary.totalTwins > 0
        ? twinSummary.avgAccuracy !== null
          ? `${twinSummary.avgAccuracy}% acurácia`
          : `${twinSummary.totalTwins} twin${twinSummary.totalTwins !== 1 ? "s" : ""}`
        : undefined,
      panel: calibrationPanel,
    },
    {
      slug: "offer",
      ctaKey: "studio.services.ctaActivate",
      status: (studioSummaryServices.offer?.status as ServiceStatus) ?? "inactive",
      metric: studioSummaryServices.offer?.metric,
      panel: firstJobId ? (
        <div className="p-4 space-y-3">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold uppercase tracking-widest text-lia-text-primary">Ofertas</span>
          </div>
          <OfferStatusCard jobId={firstJobId} jobs={allJobsList} />
        </div>
      ) : (
        <div className="p-4">
          <p className="text-xs text-lia-text-tertiary">Crie uma vaga primeiro para registrar ofertas.</p>
        </div>
      ),
    },
    {
      slug: "nps",
      ctaKey: "studio.services.ctaOpenJobs",
      status: (studioSummaryServices.nps?.status as ServiceStatus) ?? "inactive",
      metric: studioSummaryServices.nps?.metric,
      panel: firstJobId ? (
        <div className="p-4 space-y-3">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold uppercase tracking-widest text-lia-text-primary">NPS — Satisfação</span>
          </div>
          <NpsStatusCard jobId={firstJobId} jobs={allJobsList} />
        </div>
      ) : (
        <div className="p-4">
          <p className="text-xs text-lia-text-tertiary">Crie uma vaga primeiro para enviar pesquisas NPS.</p>
        </div>
      ),
    },
  ]

  const handleFunnelActivate = (slug: ServiceSlug) => {
    if (slug === "sourcing") setShowCreateModal(true)
    else if (slug === "calibration") setShowCreateTwinModal(true)
    else if (slug === "screening") {
      // Screening (triagem) é configurado por vaga — leva à aba de perguntas.
      router.push(firstJobId ? `/${locale}/jobs/${firstJobId}?tab=edit&section=perguntas` : `/${locale}/jobs`)
    } else if (slug === "intake") {
      router.push(`/${locale}/jobs`)
    } else if (slug === "alignment") {
      // Alinhamento exige um agente de captação vinculado a uma vaga → abre a criação.
      setShowCreateModal(true)
    } else if (slug === "offer") {
    // offer_concierge — navegar para Marketplace para instalar o agente
    setActiveTab("marketplace")
  } else if (slug === "nps") {
    router.push(firstJobId ? `/${locale}/jobs/${firstJobId}` : `/${locale}/jobs`)
  }/jobs/${firstJobId}` : `/${locale}/jobs`)
    }
  }

  const studioTabs: PageTab[] = [
    { id: "funil", label: t("studio.tabs.funnel"), icon: Workflow },
    { id: "operacao", label: t("studio.tabs.operations"), icon: Activity, count: pendingApprovals },
    { id: "personalizados", label: t("studio.tabs.customAgents"), icon: Bot, count: customAgents.length },
    { id: "marketplace", label: t("studio.tabs.marketplace"), icon: Store },
    { id: "gemeos", label: t("studio.tabs.twins"), icon: Users },
  ]

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-lia-bg-primary">
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex-shrink-0 px-4 pt-3 pb-3">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold text-lia-text-primary">
            {t("studio.title")}
          </h1>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={loadData} aria-label={t("studio.refresh")} className="gap-2 text-lia-text-secondary hover:text-lia-text-primary">
              <RefreshCw className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setActiveTab("personalizados")
                setTimeout(() => {
                  document.getElementById("agent-studio-conversational-creator")
                    ?.scrollIntoView({ behavior: "smooth", block: "start" })
                }, 80)
              }}
              className="gap-2"
            >
              <Wand2 className="w-4 h-4" />
              {t("studio.createWithAI") ?? "Criar com IA"}
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
      </div>

      {/* ── Equal-weight tab navigation (URL-driven) ──────────────────────── */}
      <div className="flex-shrink-0 px-4 pb-2">
        <PageTabNavigation
          tabs={studioTabs}
          activeTab={activeTab}
          onTabChange={(id) => {
            // Marketplace é uma rota canônica própria (/agents/marketplace),
            // não um painel inline do Studio — navega em vez de virar tab.
            if (id === "marketplace") { router.push(`/${locale}/agents/marketplace`); return }
            setActiveTab(id as StudioTab)
          }}
        />
      </div>

      <div className="flex-1 overflow-auto px-4 pb-4 space-y-4">
        {/* ── Funil ─────────────────────────────────────────────────────────── */}
        {activeTab === "funil" && (
          <>
            {!onboardingDismissed && (
              <StudioOnboarding
                openJobCount={openJobs.length}
                onActivateSourcing={() => setShowCreateModal(true)}
                onDismiss={() => {
                  localStorage.setItem("studio_onboarding_done", "1")
                  setOnboardingDismissed(true)
                }}
              />
            )}

            {alertCount > 0 && (
              <div className="rounded-xl border border-wedo-orange/40 bg-wedo-orange/10 overflow-hidden">
                <div className="px-4 py-2.5 flex items-center justify-between border-b border-wedo-orange/20">
                  <span className="text-micro font-semibold uppercase tracking-widest text-wedo-orange">
                    {alertCount} alerta{alertCount !== 1 ? "s" : ""} do Studio
                  </span>
                </div>
                <ul className="divide-y divide-wedo-orange/20">
                  {alerts.map((alert, i) => (
                    <li key={i} className="flex items-start gap-3 px-4 py-2.5">
                      <span className={cn(
                        "mt-0.5 w-1.5 h-1.5 rounded-full flex-shrink-0",
                        alert.severity === "error" ? "bg-wedo-orange" : "bg-wedo-orange/60"
                      )} />
                      <span className="text-xs text-lia-text-secondary">{alert.message}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <ServiceFunnelView
              services={funnelServices}
              onActivate={handleFunnelActivate}
              onMarketplaceForSlug={(slug) => {
                const cat = SLUG_TO_MARKETPLACE_CATEGORY[slug] ?? ""
                router.push(`/${locale}/agents/marketplace${cat ? `?category=${cat}` : ""}`)
              }}
            />
          </>
        )}

        {/* ── Operação (centro de controle) ─────────────────────────────────── */}
        {/* Restaura a "Sala de Controle" removida no redesign do funil: agentes
            ao vivo + histórico + auditoria LGPD + digest + reasoning drawer.
            ApprovalsList no topo traz o sistema de aprovação de volta ao Studio. */}
        {activeTab === "operacao" && (
          <div className="space-y-4">
            <ApprovalsList onReviewed={() => mutateCustomAgents()} />
            <StudioControlRoom />
          </div>
        )}

        {/* ── Personalizados ────────────────────────────────────────────────── */}
        {activeTab === "personalizados" && (
          <div className="space-y-6">
            <p className="text-sm text-lia-text-secondary mb-6">
              {t("customAgents.customAgentsSubtitle")}
            </p>

            <div id="agent-studio-conversational-creator" className="scroll-mt-4">
              <ConversationalCreator onAgentCreated={() => mutateCustomAgents()} />
            </div>

            <div className="mt-4">
              <p className="text-sm font-medium text-lia-text-secondary">
                {t("studio.advancedForm")}
              </p>
              <div className="mt-3">
                <CustomAgentsTab />
              </div>
            </div>
          </div>
        )}

        {/* Marketplace não é painel inline — a nav navega para /agents/marketplace. */}

        {/* ── Gêmeos Digitais ───────────────────────────────────────────────── */}
        {activeTab === "gemeos" && (
          <div className="space-y-4">
            <TabSectionHeader
              title={t("studio.twins.label")}
              subtitle={t("studio.twins.cloneDesc")}
              count={twinSummary.totalTwins}
            />
            <TwinsList
              onEvaluate={(id) => setEvaluatingTwinId(id)}
              onCreateTwin={() => setShowCreateTwinModal(true)}
              refreshKey={twinListRefreshKey}
            />
          </div>
        )}
      </div>

      <CreateDigitalTwinModal
        isOpen={showCreateTwinModal}
        onClose={() => setShowCreateTwinModal(false)}
        onCreated={() => {
          setTwinListRefreshKey((k) => k + 1)
          setShowCreateTwinModal(false)
        }}
      />

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
        <CreateCustomAgentModal
          agent={null}
          sourcingCreate
          initialTemplate={selectedTemplate}
          onClose={() => { setShowCreateModal(false); setSelectedTemplate(null) }}
          onSaved={(agentId) => {
            setShowCreateModal(false)
            setSelectedTemplate(null)
            loadData()
            if (agentId) onStartCalibration?.(agentId)
          }}
        />
      )}

      {previewTemplate && (
        <TemplatePreviewModal
          template={previewTemplate}
          open={true}
          onOpenChange={(o) => { if (!o) setPreviewTemplate(null) }}
          onConfirm={async (tpl) => { await handleTemplateUse(tpl); setPreviewTemplate(null) }}
        />
      )}

      <DeployDialog
        agent={deployAgent}
        open={!!deployAgent}
        onClose={() => setDeployAgent(null)}
        onDeployed={() => mutateCustomAgents()}
      />

      <TestDebugPanel
        agent={testAgent}
        open={!!testAgent}
        onClose={() => setTestAgent(null)}
      />

      <AgentDetailsPanel
        agent={detailsAgent}
        open={!!detailsAgent}
        onClose={() => setDetailsAgent(null)}
        onDeploy={(a) => { setDetailsAgent(null); setDeployAgent(a) }}
        onTest={(a) => { setDetailsAgent(null); setTestAgent(a) }}
      />
    </div>
  )
}

function AgentCard({
  agent, onToggleStatus, onCalibrate, onNavigate, onEdit,
}: {
  agent: SourcingAgent
  onToggleStatus: () => void
  onCalibrate: () => void
  onNavigate: () => void
  onEdit: () => void
}) {
  const t = useTranslations("agents")
  const status = STATUS_CONFIG_STYLES[agent.status]
  const strategy = agent.search_strategy as { required_skills?: string[]; exclusions?: string[] }
  const totalReviewed = agent.profiles_approved + agent.profiles_rejected
  const approvalRate = totalReviewed > 0 ? Math.round((agent.profiles_approved / totalReviewed) * 100) : 0

  const statusBadge = (
    <span className={cn("inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-micro font-semibold", status.bg, status.text)}>
      <span className={cn("w-1.5 h-1.5 rounded-full", status.dot, status.pulse && "animate-pulse")} />
      {t(status.labelKey)}
    </span>
  )

  const metricsSlot = (
    <div className="grid grid-cols-3 gap-2">
      <div className="flex flex-col items-center p-2 rounded-md bg-lia-bg-primary">
        <span className="text-xs font-bold text-lia-text-primary">{agent.profiles_viewed}</span>
        <span className="text-micro text-lia-text-disabled uppercase tracking-wider">{t("studio.stats.analyzed")}</span>
      </div>
      <div className="flex flex-col items-center p-2 rounded-md bg-lia-bg-primary">
        <span className="text-xs font-bold text-status-success">{agent.profiles_approved}</span>
        <span className="text-micro text-lia-text-disabled uppercase tracking-wider">{t("studio.stats.approved")}</span>
      </div>
      <div className="flex flex-col items-center p-2 rounded-md bg-lia-bg-primary">
        <span className="text-xs font-bold text-lia-text-primary">{approvalRate}%</span>
        <span className="text-micro text-lia-text-disabled uppercase tracking-wider">{t("studio.stats.rate")}</span>
      </div>
    </div>
  )

  const chipsSlot = strategy.required_skills?.length ? (
    <div className="flex flex-wrap gap-1">
      {strategy.required_skills.slice(0, 4).map((skill, i) => (
        <span key={i} className="px-2 py-0.5 rounded-md bg-lia-bg-tertiary text-micro font-medium text-lia-text-secondary">{skill}</span>
      ))}
      {strategy.required_skills.length > 4 && (
        <span className="px-2 py-0.5 rounded-md bg-lia-bg-tertiary text-micro text-lia-text-disabled">+{strategy.required_skills.length - 4}</span>
      )}
    </div>
  ) : undefined

  const alertSlot = (
    <div className={cn(
      "flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border",
      (agent.talent_pool_id || agent.job_id)
        ? "bg-lia-bg-primary border-lia-border-subtle"
        : "bg-wedo-orange/10 border-wedo-orange/30",
    )}>
      {agent.talent_pool_id ? (
        <>
          <Database className="w-3 h-3 text-lia-text-disabled" />
          <span className="text-micro text-lia-text-secondary">{t("studio.card.linkedToPool")}</span>
        </>
      ) : agent.job_id ? (
        <>
          <Briefcase className="w-3 h-3 text-lia-text-disabled" />
          <span className="text-micro text-lia-text-secondary">{t("studio.card.linkedToJob")}</span>
        </>
      ) : (
        <>
          <Brain className="w-3 h-3 text-wedo-orange" />
          <span className="text-micro text-wedo-orange">{t("studio.card.noLink")}</span>
        </>
      )}
    </div>
  )

  const actionsSlot = (
    <div className="flex items-center gap-2 w-full">
      <button
        onClick={onToggleStatus}
        className="flex items-center justify-center w-8 h-8 rounded-md border border-lia-border-subtle hover:bg-lia-bg-tertiary transition-colors"
        title={agent.status === "active" ? t("studio.card.pause") : t("studio.card.resume")}
      >
        {agent.status === "active" ? (
          <Pause className="w-3.5 h-3.5 text-lia-text-secondary" />
        ) : (
          <Play className="w-3.5 h-3.5 text-emerald-600" />
        )}
      </button>
      <button
        onClick={onEdit}
        className="flex items-center justify-center w-8 h-8 rounded-md border border-lia-border-subtle hover:bg-lia-bg-tertiary transition-colors"
        title={t("studio.card.edit")}
      >
        <Pencil className="w-3.5 h-3.5 text-lia-text-secondary" />
      </button>
      <button
        onClick={onCalibrate}
        className="flex-1 flex items-center justify-center gap-1.5 h-8 rounded-md border border-lia-border-subtle text-xs font-medium text-lia-text-secondary hover:bg-lia-bg-tertiary hover:text-lia-text-primary transition-colors"
      >
        <Activity className="w-3.5 h-3.5" />
        {t("studio.card.recalibrate")}
      </button>
      <button
        onClick={onNavigate}
        className="flex items-center justify-center gap-1 h-8 px-3 rounded-md bg-lia-btn-primary-bg text-lia-btn-primary-text text-xs font-medium hover:bg-lia-btn-primary-hover transition-colors"
      >
        {t("studio.card.view")}
        <ChevronRight className="w-3 h-3" />
      </button>
    </div>
  )

  return (
    <StudioCardShell
      tone="elevated"
      icon={<Bot className="w-4 h-4 text-graphite" />}
      title={agent.agent_name}
      subtitle={`v${agent.calibration_v} \u00b7 ${new Date(agent.created_at).toLocaleDateString(undefined, { day: "2-digit", month: "short" })}`}
      badges={<BetaBadge />}
      statusBadge={statusBadge}
      metricsSlot={metricsSlot}
      alertSlot={alertSlot}
      chipsSlot={chipsSlot}
      actionsSlot={actionsSlot}
    />
  )
}
