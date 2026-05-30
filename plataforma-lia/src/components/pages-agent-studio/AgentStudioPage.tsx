"use client"

import React, { useState, useEffect } from "react"
import {
  TwinsList,
  EvaluateWithTwinModal,
  CreateDigitalTwinModal,
} from "@/components/pages-agent-studio/DigitalTwinComponents"
import MultiStrategySearchPanel from "@/components/pages-agent-studio/MultiStrategySearchPanel"
import CustomAgentsTab from "@/components/pages-agent-studio/CustomAgentsTab"
import { TemplateGallery, AgentCard as CustomAgentCard, AgentDetailsPanel, DeployDialog, ConversationalCreator, TestDebugPanel, ApprovalsList } from "@/components/pages-agent-studio/custom-agents"
import { useCustomAgents, useStudioAlerts } from "@/hooks/agents"
import { useAgentStudioStore } from "@/stores/agent-studio-store"
import type { CustomAgent, AgentTemplate } from "@/components/pages-agent-studio/custom-agents/types"
import MarketplaceTab from "@/components/pages-agent-studio/MarketplaceTab"
import { ServiceFunnelView, StudioOnboarding } from "@/components/pages-agent-studio/ServiceFunnelView"
import type { FunnelServiceData, ServiceSlug, ServiceStatus } from "@/components/pages-agent-studio/ServiceFunnelView"
import { AlignmentStatusCard } from "@/components/pages-agent-studio/AlignmentStatusCard"
import { OfferStatusCard } from "@/components/pages-agent-studio/OfferStatusCard"
import { NpsStatusCard } from "@/components/pages-agent-studio/NpsStatusCard"
import { useRouter } from "next/navigation"
import { useLocale } from "next-intl"
import {
  Bot, Plus, Play, Pause, Briefcase, Database,
  Factory, HeartPulse, ShoppingCart, Code, Truck, Brain,
  ChevronRight, Zap, Target, ArrowRight,
  Activity, RefreshCw,
  Loader2, Users, Wand2, Search, Store,
  GraduationCap, Clock
} from "lucide-react"
import { cn } from "@/lib/utils"
import { toast } from "@/lib/toast"
import { extractErrorMessage } from "@/lib/api/extract-error-message"
import { Button } from "@/components/ui/button"
import { BetaBadge } from "@/components/ui/beta-badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
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
  active:    { labelKey: "studio.status.active" as const,    dot: "bg-[#5DA47A]", bg: "bg-[#F0FAF4]", text: "text-[#5DA47A]", pulse: true  },
  paused:    { labelKey: "studio.status.paused" as const,    dot: "bg-[#D19960]", bg: "bg-[#FEF9F0]", text: "text-[#D19960]", pulse: false },
  completed: { labelKey: "studio.status.completed" as const, dot: "bg-[#D1D5DB]", bg: "bg-[#F3F4F6]", text: "text-[#9CA3AF]", pulse: false },
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
  // secondaryView: shown below the funnel when user clicks Advanced Tools links
  const [secondaryView, setSecondaryView] = useState<"custom" | "marketplace" | "search" | null>(null)
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

  const handleTemplateSelect = async (template: AgentTemplate) => {
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
      setSecondaryView("custom")
    } catch {
      toast.error(t("studio.toast.errorCreating"), t("studio.toast.tryAgainShort"))
    }
  }

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
        <div className="rounded-lg border border-[#E5E7EB] bg-white p-4">
          <div className="flex items-center gap-2 mb-2">
            <Brain className="w-3.5 h-3.5 text-[#60BED1]" />
            <span className="text-[10px] font-semibold uppercase tracking-widest text-[#60BED1]">
              {t("studio.whatIsAgent")}
            </span>
          </div>
          <p className="text-xs text-[#6B7280] mb-3 max-w-2xl">{t("studio.virtualRecruiterDesc")}</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
            {FLOW_STEPS_CONFIG.map((step, i) => (
              <div key={i} className="flex items-start gap-3 min-w-0">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 bg-[#EBF8FB]">
                  <step.icon className="w-4 h-4 text-[#60BED1]" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span className="text-[9px] font-medium text-[#9CA3AF] uppercase tracking-wide whitespace-nowrap">
                      {t("studio.flowSteps.step")} {i + 1}
                    </span>
                    {i < 3 && <ArrowRight className="w-3 h-3 text-[#D1D5DB] hidden xl:block" />}
                  </div>
                  <p className="text-xs font-semibold text-[#030712] break-words">{t(step.titleKey)}</p>
                  <p className="text-[10px] text-[#6B7280] leading-relaxed break-words">{t(step.descKey)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Templates */}
      <div>
        <p className="text-xs font-semibold text-[#030712] mb-2">
          {agents.length === 0 ? t("studio.templates.startChoosing") : t("studio.templates.createNew")}
        </p>
        <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
          {templates.map(tpl => {
            const Icon = SECTOR_ICONS[tpl.icon] || Brain
            return (
              <button
                key={tpl.id}
                onClick={() => { setSelectedTemplate(tpl); setShowCreateModal(true) }}
                className="group flex flex-col items-center gap-2 p-3 rounded-lg border border-[#E5E7EB] bg-white hover:border-[#60BED1]/40 hover:bg-[#EBF8FB]/30 transition-all cursor-pointer"
              >
                <div className="w-9 h-9 rounded-lg flex items-center justify-center bg-[#EBF8FB] transition-transform group-hover:scale-110">
                  <Icon className="w-5 h-5 text-[#60BED1]" />
                </div>
                <p className="text-[10px] font-semibold text-[#030712] text-center line-clamp-1">{tpl.display_name}</p>
              </button>
            )
          })}
          <button
            onClick={() => { setSelectedTemplate(null); setShowCreateModal(true) }}
            className="group flex flex-col items-center gap-2 p-3 rounded-lg border-2 border-dashed border-[#E5E7EB] hover:border-[#60BED1]/40 transition-all cursor-pointer"
          >
            <Brain className="w-5 h-5 text-[#60BED1] transition-transform group-hover:scale-110" />
            <p className="text-[10px] font-semibold text-[#6B7280] text-center">{t("studio.templates.custom")}</p>
          </button>
        </div>
      </div>

      {/* Agents list */}
      {isLoading ? (
        <div className="flex items-center justify-center py-10">
          <Loader2 className="w-5 h-5 animate-spin text-[#9CA3AF]" />
        </div>
      ) : agents.length === 0 ? (
        <div className="flex flex-col items-center py-8 rounded-lg border border-dashed border-[#E5E7EB]">
          <Bot className="w-7 h-7 text-[#D1D5DB] mb-2" />
          <p className="text-xs font-medium text-[#6B7280]">{t("studio.noAgentsYet")}</p>
          <p className="text-[10px] text-[#9CA3AF] mt-1 mb-3">{t("studio.chooseTemplateAbove")}</p>
          <Button size="sm" onClick={() => setShowCreateModal(true)} className="gap-1.5 bg-[#030712] text-white hover:bg-[#1F2937]">
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
          <p className="text-sm text-[#6B7280]">Nenhuma vaga aberta encontrada.</p>
          <button
            type="button"
            onClick={() => router.push(`/${locale}/jobs/new`)}
            className="flex items-center gap-2 mx-auto text-sm font-medium text-white bg-[#60BED1] hover:bg-[#4fa8bc] rounded-lg px-4 py-2 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Criar vaga
          </button>
        </div>
      ) : (
        <>
          {liveJobs.length > 0 && (
            <div className="space-y-1.5">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-[#5DA47A]">
                {liveJobs.length} vaga{liveJobs.length !== 1 ? "s" : ""} ativa{liveJobs.length !== 1 ? "s" : ""}
              </p>
              {liveJobs.map(j => (
                <button
                  key={j.id}
                  type="button"
                  onClick={() => router.push(`/${locale}/jobs/${j.id}`)}
                  className="w-full flex items-center gap-3 rounded-lg border border-[#E5E7EB] hover:border-[#60BED1]/40 px-3 py-2.5 bg-white hover:bg-[#F9FAFB] text-left transition-colors group"
                >
                  <div className="w-2 h-2 rounded-full bg-[#5DA47A] flex-shrink-0" />
                  <span className="flex-1 text-sm text-[#030712] truncate">{j.title}</span>
                  <ChevronRight className="w-3.5 h-3.5 text-[#9CA3AF] opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              ))}
            </div>
          )}
          {draftJobs.length > 0 && (
            <div className="space-y-1.5">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-[#D19960]">
                {draftJobs.length} em configuração
              </p>
              {draftJobs.map(j => (
                <button
                  key={j.id}
                  type="button"
                  onClick={() => router.push(`/${locale}/jobs/${j.id}?tab=edit`)}
                  className="w-full flex items-center gap-3 rounded-lg border border-[#E5E7EB] hover:border-[#D19960]/40 px-3 py-2.5 bg-white hover:bg-[#FEF9F0] text-left transition-colors group"
                >
                  <div className="w-2 h-2 rounded-full bg-[#D19960] flex-shrink-0" />
                  <span className="flex-1 text-sm text-[#030712] truncate">{j.title}</span>
                  <span className="text-[10px] text-[#D19960] opacity-0 group-hover:opacity-100 transition-opacity">Completar →</span>
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
        <span className="text-xs font-semibold uppercase tracking-widest text-[#60BED1]">Alinhamento c/ Gestor</span>
      </div>
      {firstJobId ? (
        <AlignmentStatusCard jobId={firstJobId} jobs={allJobsList} />
      ) : (
        <p className="text-xs text-[#6B7280]">
          Crie um agente de prospecção vinculado a uma vaga primeiro.
        </p>
      )}
    </div>
  )

  // ── Calibration panel (embedded in funnel row) ───────────────────────────
  const calibrationPanel = (
    <div className="p-4 space-y-4">
      <div className="flex items-center gap-2 mb-1">
        <Users className="w-4 h-4 text-[#60BED1]" />
        <span className="text-xs font-semibold uppercase tracking-widest text-[#60BED1]">{t("studio.twins.label")}</span>
      </div>
      <p className="text-xs text-[#6B7280] max-w-2xl">{t("studio.twins.cloneDesc")}</p>
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
      status: liveJobs.length > 0 ? "active" : draftJobs.length > 0 ? "attention" : openJobs.length > 0 ? "configured" : "inactive",
      metric: openJobs.length > 0 ? `${openJobs.length} vaga${openJobs.length !== 1 ? "s" : ""}` : undefined,
      panel: intakePanel,
    },
    {
      slug: "alignment",
      status: firstJobId ? "configured" : "inactive",
      panel: alignmentPanel,
    },
    {
      slug: "sourcing",
      status: activeCount > 0 ? "active" : agents.length > 0 ? "configured" : "inactive",
      metric: agents.length > 0 ? `${activeCount} ${activeCount === 1 ? "ativo" : "ativos"}` : undefined,
      panel: sourcingPanel,
    },
    {
      slug: "screening",
      status: (studioSummaryServices.screening?.status as ServiceStatus) ?? (openJobs.length > 0 ? "configured" : "inactive"),
      metric: studioSummaryServices.screening?.metric,
    },
    {
      slug: "calibration",
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
      status: (studioSummaryServices.offer?.status as ServiceStatus) ?? "inactive",
      metric: studioSummaryServices.offer?.metric,
      panel: firstJobId ? (
        <div className="p-4 space-y-3">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold uppercase tracking-widest text-[#60BED1]">Ofertas</span>
          </div>
          <OfferStatusCard jobId={firstJobId} jobs={allJobsList} />
        </div>
      ) : (
        <div className="p-4">
          <p className="text-xs text-[#6B7280]">Crie uma vaga primeiro para registrar ofertas.</p>
        </div>
      ),
    },
    {
      slug: "nps",
      status: (studioSummaryServices.nps?.status as ServiceStatus) ?? "inactive",
      metric: studioSummaryServices.nps?.metric,
      panel: firstJobId ? (
        <div className="p-4 space-y-3">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold uppercase tracking-widest text-[#60BED1]">NPS — Satisfação</span>
          </div>
          <NpsStatusCard jobId={firstJobId} jobs={allJobsList} />
        </div>
      ) : (
        <div className="p-4">
          <p className="text-xs text-[#6B7280]">Crie uma vaga primeiro para enviar pesquisas NPS.</p>
        </div>
      ),
    },
  ]

  const handleFunnelActivate = (slug: ServiceSlug) => {
    if (slug === "sourcing") setShowCreateModal(true)
    else if (slug === "calibration") setShowCreateTwinModal(true)
  }

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-lia-bg-primary">
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex-shrink-0 px-4 pt-3 pb-3">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold text-lia-text-primary">
            {t("studio.title")}
          </h1>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={loadData} className="gap-2 text-lia-text-secondary hover:text-lia-text-primary">
              <RefreshCw className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSecondaryView("custom")
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

      <div className="flex-1 overflow-auto px-4 pb-4 space-y-4">
        {/* ── Onboarding inline wizard ──────────────────────────────────────── */}
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

        {/* ── Smart alerts banner ───────────────────────────────────────────── */}
        {alertCount > 0 && (
          <div className="rounded-xl border border-[#D19960]/40 bg-[#FEF9F0] overflow-hidden">
            <div className="px-4 py-2.5 flex items-center justify-between border-b border-[#D19960]/20">
              <span className="text-[10px] font-semibold uppercase tracking-widest text-[#D19960]">
                {alertCount} alerta{alertCount !== 1 ? "s" : ""} do Studio
              </span>
            </div>
            <ul className="divide-y divide-[#FDE8C8]/60">
              {alerts.map((alert, i) => (
                <li key={i} className="flex items-start gap-3 px-4 py-2.5">
                  <span className={cn(
                    "mt-0.5 w-1.5 h-1.5 rounded-full flex-shrink-0",
                    alert.severity === "error" ? "bg-[#D19960]" : "bg-[#D19960]/60"
                  )} />
                  <span className="text-xs text-[#4B5563]">{alert.message}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* ── Funnel-first view ─────────────────────────────────────────────── */}
        <ServiceFunnelView
          services={funnelServices}
          onActivate={handleFunnelActivate}
          onCustomAgents={() => setSecondaryView(v => v === "custom" ? null : "custom")}
          onMarketplace={() => setSecondaryView(v => v === "marketplace" ? null : "marketplace")}
          onMarketplaceForSlug={() => setSecondaryView(v => v === "marketplace" ? null : "marketplace")}
        />

        {/* ── Secondary views (Custom Agents / Marketplace / Search) ────────── */}
        {secondaryView === "custom" && (
          <div className="space-y-6 rounded-xl border border-[#E5E7EB] bg-white overflow-hidden p-4">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-semibold uppercase tracking-widest text-[#9CA3AF]">
                {t("studio.tabs.customAgents")}
              </span>
              <button onClick={() => setSecondaryView(null)} className="text-xs text-[#9CA3AF] hover:text-[#6B7280] transition-colors">
                {t("studio.close") ?? "Fechar"}
              </button>
            </div>

            <section>
              <ApprovalsList onReviewed={() => mutateCustomAgents()} />
            </section>

            <section>
              <h3 className="text-sm font-semibold text-[#030712] mb-3">
                {t("studio.myAgents")} {customAgents.length > 0 && `(${customAgents.length})`}
              </h3>
              {customAgents.length === 0 ? (
                <div className="text-center py-8">
                  <Bot className="w-8 h-8 text-[#D1D5DB] mx-auto mb-2" />
                  <p className="text-sm text-[#6B7280]">{t("studio.noAgentsYet")}</p>
                  <p className="text-xs text-[#9CA3AF] mt-1">{t("studio.chooseTemplateOrDescribe")}</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {customAgents.map((agent) => (
                    <div key={agent.id} onClick={() => setDetailsAgent(agent)} className="cursor-pointer">
                      <CustomAgentCard
                        agent={agent}
                        onTest={() => setTestAgent(agent)}
                        onDeploy={() => setDeployAgent(agent)}
                        onToggleStatus={(a) => handleCustomAgentToggle(a)}
                      />
                    </div>
                  ))}
                </div>
              )}
            </section>

            <TemplateGallery onTemplateSelect={handleTemplateSelect} onCreateManual={() => setShowCreateModal(true)} />

            <div id="agent-studio-conversational-creator" className="scroll-mt-4">
              <ConversationalCreator onAgentCreated={() => mutateCustomAgents()} />
            </div>

            <details className="mt-4">
              <summary className="text-xs text-[#9CA3AF] cursor-pointer hover:text-[#6B7280]">
                {t("studio.advancedForm")}
              </summary>
              <div className="mt-3">
                <CustomAgentsTab />
              </div>
            </details>
          </div>
        )}

        {secondaryView === "marketplace" && (
          <div className="rounded-xl border border-[#E5E7EB] bg-white overflow-hidden p-4">
            <div className="flex items-center justify-between mb-4">
              <span className="text-[10px] font-semibold uppercase tracking-widest text-[#9CA3AF]">
                {t("studio.tabs.marketplace")}
              </span>
              <button onClick={() => setSecondaryView(null)} className="text-xs text-[#9CA3AF] hover:text-[#6B7280] transition-colors">
                {t("studio.close") ?? "Fechar"}
              </button>
            </div>
            <MarketplaceTab />
          </div>
        )}

        {secondaryView === "search" && (
          <div className="rounded-xl border border-[#E5E7EB] bg-white overflow-hidden p-4">
            <div className="flex items-center justify-between mb-4">
              <span className="text-[10px] font-semibold uppercase tracking-widest text-[#9CA3AF]">
                {t("studio.tabs.smartSearch")}
              </span>
              <button onClick={() => setSecondaryView(null)} className="text-xs text-[#9CA3AF] hover:text-[#6B7280] transition-colors">
                {t("studio.close") ?? "Fechar"}
              </button>
            </div>
            <MultiStrategySearchPanel />
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
            <div className="w-10 h-10 rounded-xl bg-[#EBF8FB] flex items-center justify-center">
              <Bot className="w-5 h-5 text-[#60BED1]" />
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
            <span className="text-xs font-bold text-[#5DA47A]">{agent.profiles_approved}</span>
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
          <div className="flex items-center gap-1.5 mb-3 px-2.5 py-1.5 rounded-lg bg-[#FEF9F0] border border-[#D19960]/30">
            <Brain className="w-3 h-3 text-[#D19960]" />
            <span className="text-[10px] text-[#D19960]">{t("studio.card.noLink")}</span>
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
              <div className="mt-2 px-3 py-2 rounded-lg bg-[#FEF9F0] border border-[#D19960]/30">
                <p className="text-xs text-[#D19960]">
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
