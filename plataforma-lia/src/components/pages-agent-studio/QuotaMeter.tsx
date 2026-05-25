"use client"

/**
 * QuotaMeter — feedforward visual de uso vs limit por recurso.
 *
 * Audit harness 2026-05-23: backend já expunha GET /studio/quota mas frontend
 * nunca consumia. Recrutador só descobria limit quando batia parede (feedback
 * puro). QuotaMeter transforma em feedforward — mostra "8 / 10" com semáforo
 * antes do bloqueio. Pesquisa concorrencial confirmou: ninguém no nicho
 * (Phenom/Paradox/Eightfold/HireVue) faz isso bem — oportunidade real.
 *
 * Modelo canonical WeDOTalent (pay-first sales-led): quando bate amarelo/vermelho,
 * CTA é "Falar com seu Account Manager" → mailto:sucesso@wedotalent.cc.
 * NÃO há self-service upgrade.
 *
 * Posicionamento: header do AgentStudioPage. Compact mode tem 4 cards em row,
 * full mode opcional pra páginas dedicadas.
 */
import React, { useState } from "react"
import { Bot, Brain, Megaphone, Search, Zap } from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { useStudioQuota, type QuotaResource, type QuotaResourceStatus } from "@/hooks/agent-studio/use-studio-quota"
import { UpgradeRequestModal, type UpgradeRequestContext } from "./UpgradeRequestModal"

const RESOURCE_ICONS: Record<QuotaResource, React.ComponentType<{ className?: string }>> = {
  custom_agents: Bot,
  sourcing_agents: Search,
  digital_twins: Brain,
  campaigns: Megaphone,
}

// Cores tokenizadas via design-system (sem hardcoded).
// green = lia-success, yellow = lia-warning, red = lia-error/status-error.
const TIER_STYLES: Record<QuotaResourceStatus["tier"], { bar: string; text: string; bg: string }> = {
  green: {
    bar: "bg-emerald-500/70",
    text: "text-lia-text-primary",
    bg: "bg-emerald-50 dark:bg-emerald-950/20",
  },
  yellow: {
    bar: "bg-amber-500/80",
    text: "text-amber-700 dark:text-amber-400",
    bg: "bg-amber-50 dark:bg-amber-950/20",
  },
  red: {
    bar: "bg-status-error/80",
    text: "text-status-error",
    bg: "bg-status-error/10",
  },
}

export interface QuotaMeterProps {
  /** Quando true, mostra 4 cards em row compacta no header. Default true. */
  compact?: boolean
  className?: string
}

export function QuotaMeter({ compact = true, className }: QuotaMeterProps) {
  const t = useTranslations("agents.studio.quotaMeter")
  const tResources = useTranslations("agents.studio.quotaMeter.resources")
  const { data, resources, isLoading, error } = useStudioQuota()
  const [upgradeContext, setUpgradeContext] = useState<UpgradeRequestContext | null>(null)

  const openUpgradeModal = (worstResource?: QuotaResourceStatus) => {
    if (!data) return
    // Pega o primeiro recurso yellow/red, ou o primeiro no geral
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

  // Quando NENHUM recurso está perto do limit (todos green), mostramos versão
  // ultra-compacta — só plano atual. Quando algum está yellow/red, abre detalhes.
  const hasWarning = resources.some((r) => r.tier !== "green" && !r.isUnlimited)

  return (
    <div
      className={cn(
        "rounded-md border border-lia-border-subtle bg-lia-bg-secondary/50 px-3 py-2",
        hasWarning && "border-amber-500/30",
        className,
      )}
      role="region"
      aria-label={t("regionLabel")}
      data-testid="quota-meter"
    >
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
        <div className="mt-2 flex items-center justify-between gap-2 pt-1.5 border-t border-amber-500/20">
          <span className="text-[10px] text-amber-700 dark:text-amber-400">
            {t("warning")}
          </span>
          <button
            type="button"
            onClick={() => openUpgradeModal()}
            className="inline-flex items-center gap-1 text-[10px] font-medium text-amber-700 dark:text-amber-400 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500/30 rounded"
            data-testid="quota-meter-contact-am"
          >
            {t("contactAm")}
            <Zap className="w-2.5 h-2.5" aria-hidden="true" />
          </button>
        </div>
      )}

      <UpgradeRequestModal
        isOpen={upgradeContext !== null}
        onClose={() => setUpgradeContext(null)}
        context={upgradeContext}
      />
    </div>
  )
}
