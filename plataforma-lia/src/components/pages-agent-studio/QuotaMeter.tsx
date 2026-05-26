"use client"

/**
 * QuotaMeter — feedforward visual de uso vs limit por recurso.
 *
 * Sprint visual 2026-05-26: wrapped em <Collapsible defaultOpen={false}>.
 * Antes ocupava ~15% do header (viola 90/10 Rule canonical). Agora vira
 * header compacto "Limite do plano: X% usado" + chevron pra expandir.
 *
 * Audit harness 2026-05-23: backend já expunha GET /studio/quota mas frontend
 * nunca consumia. Recrutador só descobria limit quando batia parede (feedback
 * puro). QuotaMeter transforma em feedforward — mostra "8 / 10" com semáforo
 * antes do bloqueio.
 *
 * Modelo canonical WeDOTalent (pay-first sales-led): quando bate amarelo/vermelho,
 * CTA é "Falar com seu Account Manager" → mailto:sucesso@wedotalent.cc.
 */
import React, { useState } from "react"
import { Bot, Brain, ChevronDown, Megaphone, Search, Zap } from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { useStudioQuota, type QuotaResource, type QuotaResourceStatus } from "@/hooks/agent-studio/use-studio-quota"
import { UpgradeRequestModal, type UpgradeRequestContext } from "./UpgradeRequestModal"

const RESOURCE_ICONS: Record<QuotaResource, React.ComponentType<{ className?: string }>> = {
  custom_agents: Bot,
  sourcing_agents: Search,
  digital_twins: Brain,
  campaigns: Megaphone,
}

// Sprint visual 2026-05-26: barras gradient sutil
//   < 80% → mist neutro (lia-border-subtle equivalente)
//   80-94% → amber-warning/30
//   ≥ 95% → coral-quiet/30 (status-error fallback)
const TIER_STYLES: Record<QuotaResourceStatus["tier"], { bar: string; text: string; bg: string }> = {
  green: {
    bar: "bg-lia-border-medium/70",
    text: "text-lia-text-primary",
    bg: "bg-lia-bg-tertiary",
  },
  yellow: {
    bar: "bg-status-warning/30",
    text: "text-status-warning",
    bg: "bg-status-warning/10",
  },
  red: {
    bar: "bg-status-error/30",
    text: "text-status-error",
    bg: "bg-status-error/10",
  },
}

export interface QuotaMeterProps {
  /** Quando true, mostra 4 cards em row compacta no header. Default true. */
  compact?: boolean
  className?: string
  /** Open by default. Sprint visual 2026-05-26 default false (collapsed). */
  defaultOpen?: boolean
}

export function QuotaMeter({ compact = true, className, defaultOpen = false }: QuotaMeterProps) {
  const t = useTranslations("agents.studio.quotaMeter")
  const tResources = useTranslations("agents.studio.quotaMeter.resources")
  const { data, resources, isLoading, error } = useStudioQuota()
  const [upgradeContext, setUpgradeContext] = useState<UpgradeRequestContext | null>(null)
  const [isOpen, setIsOpen] = useState<boolean>(defaultOpen)

  const openUpgradeModal = (worstResource?: QuotaResourceStatus) => {
    if (!data) return
    const target = worstResource ?? resources.find((r) => r.tier !== "green" && !r.isUnlimited) ?? resources[0]
    if (!target) return
    setUpgradeContext({
      resource: target.resource,
      resourceLabel: tResources(target.resource),
      current: target.active,
      limit: target.limit,
      currentPlan: data.plan_code,
    })
  }

  if (isLoading) {
    return (
      <div
        className={cn(
          "flex items-center gap-2 text-xs text-lia-text-secondary",
          className,
        )}
        data-testid="quota-meter-loading"
      >
        <span className="animate-pulse">{t("loading")}</span>
      </div>
    )
  }

  if (error || !data) {
    // Soft-fail: não bloqueia o usuário, só não mostra meter
    return null
  }

  const hasWarning = resources.some((r) => r.tier !== "green" && !r.isUnlimited)

  // Agregado: pega o maior percent (não-unlimited) pra mostrar no header colapsado.
  const usedResources = resources.filter((r) => !r.isUnlimited)
  const summaryPercent = usedResources.length > 0
    ? Math.max(...usedResources.map((r) => r.percent))
    : 0

  return (
    <Collapsible
      open={isOpen}
      onOpenChange={setIsOpen}
      className={cn(
        "rounded-md border border-lia-border-subtle bg-lia-bg-secondary/50",
        hasWarning && "border-status-warning/30",
        className,
      )}
    >
      <CollapsibleTrigger
        className={cn(
          "group flex items-center justify-between gap-3 w-full px-3 py-2 text-left",
          "hover:bg-lia-bg-tertiary/40 transition-colors rounded-md",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-lia-border-medium/30",
        )}
        data-testid="quota-meter-trigger"
        aria-label={t("regionLabel")}
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-[11px] text-lia-text-secondary truncate">
            {t("collapsed.summary", { percent: summaryPercent })}
          </span>
          <span className="text-[10px] text-lia-text-disabled hidden sm:inline">
            {t("plan", { plan: data.plan_code })}
          </span>
        </div>
        <ChevronDown
          className={cn(
            "w-4 h-4 text-lia-text-disabled flex-shrink-0 transition-transform",
            "group-data-[state=open]:rotate-180",
          )}
          aria-hidden="true"
        />
      </CollapsibleTrigger>

      <CollapsibleContent
        data-testid="quota-meter"
        role="region"
      >
        <div className="px-3 pb-3 pt-1">
          <div className="flex items-center justify-between gap-3 mb-1.5">
            <span className="text-[10px] uppercase tracking-wide font-semibold text-lia-text-secondary">
              {t("title")}
            </span>
            <span className="text-[10px] text-lia-text-secondary">
              {t("plan", { plan: data.plan_code })}
            </span>
          </div>

          <div
            className={cn(
              "grid gap-2",
              compact ? "grid-cols-2 md:grid-cols-4" : "grid-cols-1",
            )}
          >
            {resources.map((r) => {
              const Icon = RESOURCE_ICONS[r.resource]
              const style = TIER_STYLES[r.tier]
              const usageLabel = r.isUnlimited
                ? t("unlimited", { active: r.active })
                : `${r.active} / ${r.limit}`
              return (
                <div
                  key={r.resource}
                  className={cn(
                    "flex flex-col gap-1 rounded-md px-2 py-1.5 transition-colors",
                    style.bg,
                  )}
                  data-testid={`quota-meter-${r.resource}`}
                  data-tier={r.tier}
                >
                  <div className="flex items-center gap-1.5">
                    <Icon className={cn("w-3 h-3 flex-shrink-0", style.text)} aria-hidden="true" />
                    <span className={cn("text-[10px] font-medium truncate", style.text)}>
                      {t(`resources.${r.resource}`)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between gap-2">
                    <span className={cn("text-xs font-semibold tabular-nums", style.text)}>
                      {usageLabel}
                    </span>
                    {!r.isUnlimited && (
                      <span className={cn("text-[10px] tabular-nums", style.text)}>
                        {r.percent}%
                      </span>
                    )}
                  </div>
                  {!r.isUnlimited && (
                    <div className="h-1 rounded-full bg-lia-bg-tertiary overflow-hidden">
                      <div
                        className={cn("h-full transition-all", style.bar)}
                        style={{ width: `${r.percent}%` }}
                        aria-hidden="true"
                      />
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {hasWarning && (
            <div className="mt-2 flex items-center justify-between gap-2 pt-1.5 border-t border-status-warning/20">
              <span className="text-[10px] text-status-warning">
                {t("warning")}
              </span>
              <button
                type="button"
                onClick={() => openUpgradeModal()}
                className="inline-flex items-center gap-1 text-[10px] font-medium text-status-warning hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-status-warning/30 rounded"
                data-testid="quota-meter-contact-am"
              >
                {t("contactAm")}
                <Zap className="w-2.5 h-2.5" aria-hidden="true" />
              </button>
            </div>
          )}
        </div>
      </CollapsibleContent>

      <UpgradeRequestModal
        isOpen={upgradeContext !== null}
        onClose={() => setUpgradeContext(null)}
        context={upgradeContext}
      />
    </Collapsible>
  )
}
