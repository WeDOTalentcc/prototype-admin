"use client"

import React, { useState, useEffect, useCallback } from "react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import {
  Brain,
  Users,
  Mic,
  TrendingUp,
  Heart,
  Rocket,
  BarChart3,
  Loader2,
  CheckCircle,
  Clock,
  Lock,
  Sparkles,
  ArrowRight,
  Layers,
} from "lucide-react"
import { BetaBadge } from "@/components/ui/beta-badge"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/contexts/auth-context"

type ModuleStatusType = "beta" | "trial" | "active" | "expired" | "disabled" | "coming_soon"

interface ModuleInfo {
  module_name: string
  label: string
  description: string
  status: ModuleStatusType
  tier?: string
  features: string[]
  icon: React.ElementType
}

const MODULE_ICONS: Record<string, React.ElementType> = {
  talent_intelligence_pro: Brain,
  internal_mobility: Users,
  interview_intelligence: Mic,
  workforce_planning: TrendingUp,
  candidate_nurture: Heart,
  onboarding_suite: Rocket,
  predictive_analytics: BarChart3,
}

const MODULE_FEATURE_KEYS: Record<string, string[]> = {
  talent_intelligence_pro: [
    "features.talentIntelligence.onet",
    "features.talentIntelligence.gapAnalysis",
    "features.talentIntelligence.marketIntelligence",
    "features.talentIntelligence.adjacentSkills",
    "features.talentIntelligence.marketSnapshot",
  ],
  internal_mobility: [
    "features.internalMobility.talentMatching",
    "features.internalMobility.readinessScore",
    "features.internalMobility.developmentPlan",
    "features.internalMobility.successionMapping",
  ],
  interview_intelligence: [
    "features.interviewIntelligence.autoTranscription",
    "features.interviewIntelligence.biasAnalysis",
    "features.interviewIntelligence.wsiReport",
    "features.interviewIntelligence.profileScore",
  ],
  workforce_planning: [
    "features.workforcePlanning.demandForecast",
    "features.workforcePlanning.growthScenarios",
    "features.workforcePlanning.capacityDashboard",
    "features.workforcePlanning.funnelBottlenecks",
  ],
  candidate_nurture: [
    "features.candidateNurture.autoSequences",
    "features.candidateNurture.engagementTracking",
    "features.candidateNurture.passiveCRM",
    "features.candidateNurture.customTemplates",
  ],
  onboarding_suite: [
    "features.onboarding.postHireWorkflow",
    "features.onboarding.documentChecklist",
    "features.onboarding.hrisIntegration",
    "features.onboarding.probationTracking",
  ],
  predictive_analytics: [
    "features.predictiveAnalytics.turnoverRisk",
    "features.predictiveAnalytics.exitPatterns",
    "features.predictiveAnalytics.retentionScore",
    "features.predictiveAnalytics.proactiveAlerts",
  ],
}

const STATUS_DISPLAY: Record<ModuleStatusType, { labelKey: string; variant: "lilac" | "success" | "info" | "default" | "secondary"; icon: React.ElementType }> = {
  beta: { labelKey: "status.beta", variant: "lilac", icon: Sparkles },
  trial: { labelKey: "status.trial", variant: "info", icon: Clock },
  active: { labelKey: "status.active", variant: "success", icon: CheckCircle },
  expired: { labelKey: "status.expired", variant: "default", icon: Clock },
  disabled: { labelKey: "status.disabled", variant: "secondary", icon: Lock },
  coming_soon: { labelKey: "status.comingSoon", variant: "secondary", icon: Clock },
}

function ModuleCard({ module }: { module: ModuleInfo }) {
  const t = useTranslations('modules')
  const statusConfig = STATUS_DISPLAY[module.status]
  const isBeta = module.status === "beta"
  const isComingSoon = module.status === "coming_soon"
  const isAccessible = ["beta", "trial", "active"].includes(module.status)
  const Icon = module.icon
  const featureKeys = MODULE_FEATURE_KEYS[module.module_name] || []

  return (
    <div
      className={cn(
        "relative flex flex-col rounded-xl border bg-lia-bg-secondary transition-all duration-200",
        isAccessible
          ? "border-lia-border-subtle hover:border-lia-border-medium hover:shadow-md"
          : "border-lia-border-subtle/60 opacity-75",
      )}
    >
      <div className="p-5 flex-1 flex flex-col">
        <div className="flex items-start justify-between mb-3">
          <div
            className={cn(
              "w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0",
              isBeta
                ? "bg-wedo-purple/10"
                : isComingSoon
                  ? "bg-lia-bg-tertiary"
                  : "bg-wedo-cyan/10",
            )}
          >
            <Icon
              className={cn(
                "w-5 h-5",
                isBeta
                  ? "text-wedo-purple"
                  : isComingSoon
                    ? "text-lia-text-disabled"
                    : "text-wedo-cyan",
              )}
            />
          </div>
          {isBeta ? (
            <BetaBadge size="md" />
          ) : (
            <Badge variant={statusConfig.variant}>{t(statusConfig.labelKey)}</Badge>
          )}
        </div>

        <h3 className="text-sm font-semibold text-lia-text-primary mb-1">
          {module.label}
        </h3>
        <p className="text-xs text-lia-text-secondary mb-4 leading-relaxed">
          {module.description}
        </p>

        <div className="flex-1">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-lia-text-disabled mb-2">
            {t('featuresLabel')}
          </p>
          <ul className="space-y-1.5">
            {featureKeys.map((key, idx) => (
              <li key={idx} className="flex items-start gap-1.5">
                <CheckCircle className="w-3 h-3 text-lia-text-disabled flex-shrink-0 mt-0.5" />
                <span className="text-[11px] text-lia-text-secondary leading-tight">
                  {t(key)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="px-5 pb-4 pt-2 border-t border-lia-border-subtle">
        {isBeta && (
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-wedo-purple font-medium">
              {t('card.freeDuringBeta')}
            </span>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs gap-1 text-wedo-purple hover:text-wedo-purple hover:bg-wedo-purple/10"
            >
              {t('card.explore')}
              <ArrowRight className="w-3 h-3" />
            </Button>
          </div>
        )}
        {module.status === "active" && (
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-lia-text-secondary font-medium">
              {t('card.activeModule')}
            </span>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs gap-1 text-lia-text-primary"
            >
              {t('card.manage')}
              <ArrowRight className="w-3 h-3" />
            </Button>
          </div>
        )}
        {module.status === "trial" && (
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-lia-text-secondary font-medium">
              {t('card.trialPeriod')}
            </span>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs gap-1 text-wedo-cyan hover:text-wedo-cyan-dark hover:bg-wedo-cyan/10"
            >
              {t('card.activate')}
              <ArrowRight className="w-3 h-3" />
            </Button>
          </div>
        )}
        {isComingSoon && (
          <div className="flex items-center justify-center">
            <span className="text-[10px] text-lia-text-disabled font-medium">
              {t('card.inDevelopment')}
            </span>
          </div>
        )}
        {(module.status === "expired" || module.status === "disabled") && (
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-lia-text-disabled font-medium">
              {t('card.accessUnavailable')}
            </span>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs gap-1 text-lia-text-secondary"
            >
              {t('card.reactivate')}
              <ArrowRight className="w-3 h-3" />
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

const FALLBACK_MODULE_DEFS = [
  { module_name: "talent_intelligence_pro", labelKey: "catalog.talentIntelligence.label", descKey: "catalog.talentIntelligence.description", status: "beta" as ModuleStatusType, icon: Brain },
  { module_name: "internal_mobility", labelKey: "catalog.internalMobility.label", descKey: "catalog.internalMobility.description", status: "beta" as ModuleStatusType, icon: Users },
  { module_name: "interview_intelligence", labelKey: "catalog.interviewIntelligence.label", descKey: "catalog.interviewIntelligence.description", status: "beta" as ModuleStatusType, icon: Mic },
  { module_name: "workforce_planning", labelKey: "catalog.workforcePlanning.label", descKey: "catalog.workforcePlanning.description", status: "beta" as ModuleStatusType, icon: TrendingUp },
  { module_name: "candidate_nurture", labelKey: "catalog.candidateNurture.label", descKey: "catalog.candidateNurture.description", status: "beta" as ModuleStatusType, icon: Heart },
  { module_name: "onboarding_suite", labelKey: "catalog.onboarding.label", descKey: "catalog.onboarding.description", status: "coming_soon" as ModuleStatusType, icon: Rocket },
  { module_name: "predictive_analytics", labelKey: "catalog.predictiveAnalytics.label", descKey: "catalog.predictiveAnalytics.description", status: "coming_soon" as ModuleStatusType, icon: BarChart3 },
]

export function ModulesPage() {
  const t = useTranslations('modules')
  const fallbackModules: ModuleInfo[] = FALLBACK_MODULE_DEFS.map(def => ({
    module_name: def.module_name,
    label: t(def.labelKey),
    description: t(def.descKey),
    status: def.status,
    features: (MODULE_FEATURE_KEYS[def.module_name] || []).map(k => t(k)),
    icon: def.icon,
  }))

  const [modules, setModules] = useState<ModuleInfo[]>(fallbackModules)
  const [isLoading, setIsLoading] = useState(true)
  const { user } = useAuth()
  const companyId = user?.company || "demo_company"

  const loadModules = useCallback(async () => {
    setIsLoading(true)
    try {
      const res = await fetch(
        `/api/backend-proxy/modules/${companyId}?include_catalog=true`,
      )
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data?.modules) && data.modules.length > 0) {
          const mapped: ModuleInfo[] = data.modules.map(
            (m: Record<string, unknown>) => ({
              module_name: m.module_name as string,
              label: (m.label as string) || (m.module_name as string),
              description: (m.description as string) || "",
              status: (m.status as ModuleStatusType) || "beta",
              tier: m.tier as string | undefined,
              features:
                (MODULE_FEATURE_KEYS[m.module_name as string] || []).map(k => t(k)),
              icon:
                MODULE_ICONS[m.module_name as string] || Brain,
            }),
          )
          setModules(mapped)
          return
        }
      }
      setModules(fallbackModules)
    } catch {
      setModules(fallbackModules)
    } finally {
      setIsLoading(false)
    }
  }, [companyId])

  useEffect(() => {
    loadModules()
  }, [loadModules])

  const betaModules = modules.filter((m) => m.status === "beta")
  const activeModules = modules.filter(
    (m) => m.status === "active" || m.status === "trial",
  )
  const comingSoonModules = modules.filter((m) => m.status === "coming_soon")
  const otherModules = modules.filter(
    (m) =>
      !["beta", "active", "trial", "coming_soon"].includes(m.status),
  )

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-lia-bg-primary">
      <div className="flex-shrink-0 px-6 pt-5 pb-4">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-9 h-9 rounded-xl bg-wedo-purple/10 flex items-center justify-center">
            <Layers className="w-5 h-5 text-wedo-purple" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-lia-text-primary">
              {t('title')}
            </h1>
            <p className="text-xs text-lia-text-secondary">
              {t('subtitle')}
            </p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto px-6 pb-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="w-6 h-6 animate-spin text-lia-text-disabled" />
              <span className="text-xs text-lia-text-secondary">
                {t('loading')}
              </span>
            </div>
          </div>
        ) : (
          <div className="space-y-8">
            {betaModules.length > 0 && (
              <section>
                <div className="flex items-center gap-2 mb-4">
                  <Sparkles className="w-4 h-4 text-wedo-purple" />
                  <h2 className="text-sm font-semibold text-lia-text-primary">
                    {t('sections.availableInBeta')}
                  </h2>
                  <span className="text-[10px] text-wedo-purple bg-wedo-purple/10 px-2 py-0.5 rounded-full font-medium">
                    {t('sections.free')}
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {betaModules.map((m) => (
                    <ModuleCard key={m.module_name} module={m} />
                  ))}
                </div>
              </section>
            )}

            {activeModules.length > 0 && (
              <section>
                <div className="flex items-center gap-2 mb-4">
                  <CheckCircle className="w-4 h-4 text-wedo-green" />
                  <h2 className="text-sm font-semibold text-lia-text-primary">
                    {t('sections.activeModules')}
                  </h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {activeModules.map((m) => (
                    <ModuleCard key={m.module_name} module={m} />
                  ))}
                </div>
              </section>
            )}

            {comingSoonModules.length > 0 && (
              <section>
                <div className="flex items-center gap-2 mb-4">
                  <Clock className="w-4 h-4 text-lia-text-disabled" />
                  <h2 className="text-sm font-semibold text-lia-text-primary">
                    {t('sections.comingSoon')}
                  </h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {comingSoonModules.map((m) => (
                    <ModuleCard key={m.module_name} module={m} />
                  ))}
                </div>
              </section>
            )}

            {otherModules.length > 0 && (
              <section>
                <div className="flex items-center gap-2 mb-4">
                  <Lock className="w-4 h-4 text-lia-text-disabled" />
                  <h2 className="text-sm font-semibold text-lia-text-primary">
                    {t('sections.others')}
                  </h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {otherModules.map((m) => (
                    <ModuleCard key={m.module_name} module={m} />
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
