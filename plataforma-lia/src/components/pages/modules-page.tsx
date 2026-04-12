"use client"

import React, { useState, useEffect, useCallback } from "react"
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

const MODULE_FEATURES: Record<string, string[]> = {
  talent_intelligence_pro: [
    "Skills Ontology com taxonomia O*NET",
    "Gap Analysis por competências",
    "Market Intelligence e benchmarking",
    "Recomendação de skills adjacentes",
    "Snapshot de mercado por cargo",
  ],
  internal_mobility: [
    "Matching de talentos internos",
    "Readiness scoring por posição",
    "Plano de desenvolvimento individual",
    "Mapeamento de sucessão",
  ],
  interview_intelligence: [
    "Transcrição automática de entrevistas",
    "Análise de viés do entrevistador",
    "Parecer estruturado WSI",
    "Score de aderência ao perfil",
  ],
  workforce_planning: [
    "Previsão de demanda de contratação",
    "Cenários de crescimento do time",
    "Dashboard de capacidade",
    "Alerta de gargalos no pipeline",
  ],
  candidate_nurture: [
    "Sequências automatizadas de contato",
    "Tracking de engajamento",
    "CRM de candidatos passivos",
    "Templates personalizáveis",
  ],
  onboarding_suite: [
    "Workflow pós-contratação",
    "Checklist de documentos",
    "Integração com HRIS",
    "Acompanhamento do período de experiência",
  ],
  predictive_analytics: [
    "Previsão de risco de turnover",
    "Análise de padrões de saída",
    "Score de retenção por equipe",
    "Alertas proativos de attrition",
  ],
}

const STATUS_DISPLAY: Record<ModuleStatusType, { label: string; variant: "lilac" | "success" | "info" | "default" | "secondary"; icon: React.ElementType }> = {
  beta: { label: "BETA", variant: "lilac", icon: Sparkles },
  trial: { label: "Trial", variant: "info", icon: Clock },
  active: { label: "Ativo", variant: "success", icon: CheckCircle },
  expired: { label: "Expirado", variant: "default", icon: Clock },
  disabled: { label: "Desabilitado", variant: "secondary", icon: Lock },
  coming_soon: { label: "Em Breve", variant: "secondary", icon: Clock },
}

function ModuleCard({ module }: { module: ModuleInfo }) {
  const statusConfig = STATUS_DISPLAY[module.status]
  const isBeta = module.status === "beta"
  const isComingSoon = module.status === "coming_soon"
  const isAccessible = ["beta", "trial", "active"].includes(module.status)
  const Icon = module.icon

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
            <Badge variant={statusConfig.variant}>{statusConfig.label}</Badge>
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
            Funcionalidades
          </p>
          <ul className="space-y-1.5">
            {module.features.map((feature, idx) => (
              <li key={idx} className="flex items-start gap-1.5">
                <CheckCircle className="w-3 h-3 text-lia-text-disabled flex-shrink-0 mt-0.5" />
                <span className="text-[11px] text-lia-text-secondary leading-tight">
                  {feature}
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
              Gratuito durante o BETA
            </span>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs gap-1 text-wedo-purple hover:text-wedo-purple hover:bg-wedo-purple/10"
            >
              Explorar
              <ArrowRight className="w-3 h-3" />
            </Button>
          </div>
        )}
        {module.status === "active" && (
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-lia-text-secondary font-medium">
              Módulo ativo
            </span>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs gap-1 text-lia-text-primary"
            >
              Gerenciar
              <ArrowRight className="w-3 h-3" />
            </Button>
          </div>
        )}
        {module.status === "trial" && (
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-lia-text-secondary font-medium">
              Período de avaliação
            </span>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs gap-1 text-wedo-cyan hover:text-wedo-cyan-dark hover:bg-wedo-cyan/10"
            >
              Ativar
              <ArrowRight className="w-3 h-3" />
            </Button>
          </div>
        )}
        {isComingSoon && (
          <div className="flex items-center justify-center">
            <span className="text-[10px] text-lia-text-disabled font-medium">
              Em desenvolvimento
            </span>
          </div>
        )}
        {(module.status === "expired" || module.status === "disabled") && (
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-lia-text-disabled font-medium">
              Acesso indisponível
            </span>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs gap-1 text-lia-text-secondary"
            >
              Reativar
              <ArrowRight className="w-3 h-3" />
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

const FALLBACK_MODULES: ModuleInfo[] = [
  {
    module_name: "talent_intelligence_pro",
    label: "Talent Intelligence Pro",
    description: "Skills Ontology + Gap Analysis + Market Intelligence",
    status: "beta",
    features: MODULE_FEATURES.talent_intelligence_pro,
    icon: Brain,
  },
  {
    module_name: "internal_mobility",
    label: "Internal Mobility Suite",
    description: "Matching interno + Readiness scoring",
    status: "beta",
    features: MODULE_FEATURES.internal_mobility,
    icon: Users,
  },
  {
    module_name: "interview_intelligence",
    label: "Interview Intelligence Pro",
    description: "Análise WSI de entrevista + viés + parecer",
    status: "beta",
    features: MODULE_FEATURES.interview_intelligence,
    icon: Mic,
  },
  {
    module_name: "workforce_planning",
    label: "Workforce Planning",
    description: "Previsão + cenários + dashboard",
    status: "beta",
    features: MODULE_FEATURES.workforce_planning,
    icon: TrendingUp,
  },
  {
    module_name: "candidate_nurture",
    label: "Candidate Nurture / CRM",
    description: "Sequências + engajamento + CRM",
    status: "beta",
    features: MODULE_FEATURES.candidate_nurture,
    icon: Heart,
  },
  {
    module_name: "onboarding_suite",
    label: "Onboarding Intelligence",
    description: "Workflow pós-contratação completo",
    status: "coming_soon",
    features: MODULE_FEATURES.onboarding_suite,
    icon: Rocket,
  },
  {
    module_name: "predictive_analytics",
    label: "Predictive Attrition",
    description: "Previsão de risco de turnover com ML",
    status: "coming_soon",
    features: MODULE_FEATURES.predictive_analytics,
    icon: BarChart3,
  },
]

export function ModulesPage() {
  const [modules, setModules] = useState<ModuleInfo[]>(FALLBACK_MODULES)
  const [isLoading, setIsLoading] = useState(true)
  const { user } = useAuth()
  const companyId = user?.company_id || "demo_company"

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
                MODULE_FEATURES[m.module_name as string] || [],
              icon:
                MODULE_ICONS[m.module_name as string] || Brain,
            }),
          )
          setModules(mapped)
          return
        }
      }
      setModules(FALLBACK_MODULES)
    } catch {
      setModules(FALLBACK_MODULES)
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
              Módulos
            </h1>
            <p className="text-xs text-lia-text-secondary">
              Expanda as capacidades da LIA com módulos especializados
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
                Carregando módulos...
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
                    Disponíveis em BETA
                  </h2>
                  <span className="text-[10px] text-wedo-purple bg-wedo-purple/10 px-2 py-0.5 rounded-full font-medium">
                    Gratuito
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
                    Módulos Ativos
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
                    Em Breve
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
                    Outros
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
