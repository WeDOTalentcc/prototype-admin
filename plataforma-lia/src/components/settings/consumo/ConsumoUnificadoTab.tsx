"use client"

import { useQuery } from "@tanstack/react-query"
import { useTranslations } from "next-intl"
import { Gauge, Database, Zap, Search, Bot } from "lucide-react"
import { Progress } from "@/components/ui/progress"
import { SETTINGS_QUERY_KEYS } from "@/hooks/settings/useSettingsBroadcast"
import { CreditosIaTab } from "./CreditosIaTab"
import { PearchTab } from "./PearchTab"
import { AgentesTab } from "./AgentesTab"
import type { DrilldownState } from "../ConsumoHub"

interface ConsumoUnificadoTabProps {
  onOpenDrilldown: (state: DrilldownState) => void
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return n.toLocaleString("pt-BR")
}

function UsageBar({
  label,
  icon: Icon,
  used,
  cap,
  unit,
  capReachedText,
  capWarningTemplate,
}: {
  label: string
  icon: React.ElementType
  used: number
  cap: number
  unit: string
  capReachedText: string
  capWarningTemplate: string
}) {
  const isUnlimited = cap === -1
  const pct = isUnlimited ? 0 : cap > 0 ? Math.min((used / cap) * 100, 100) : 0
  const isWarning = !isUnlimited && cap > 0 && used / cap >= 0.8

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <span className="flex items-center gap-1.5 text-lia-text-secondary">
          <Icon className="h-3.5 w-3.5" aria-hidden="true" />
          {label}
        </span>
        <span className="text-lia-text-primary font-medium">
          {formatNumber(used)} / {isUnlimited ? "∞" : formatNumber(cap)} {unit}
        </span>
      </div>
      {!isUnlimited && (
        <Progress
          value={pct}
          className={`h-2 ${isWarning ? "[&>div]:bg-amber-500" : ""}`}
        />
      )}
      {isWarning && (
        <p className="text-xs text-amber-600">
          {pct >= 100
            ? capReachedText
            : capWarningTemplate.replace("{pct}", pct.toFixed(0))}
        </p>
      )}
    </div>
  )
}

function QuotaSummary() {
  const t = useTranslations("settings.billing")

  const subscription = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.billing(),
    queryFn: async () => {
      const res = await fetch("/api/backend-proxy/billing/plan-summary")
      if (!res.ok) throw new Error(t("errors.loadPlan"))
      return res.json()
    },
    staleTime: 60_000,
  })

  const usage = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.billingUsage(),
    queryFn: async () => {
      const res = await fetch("/api/backend-proxy/billing/usage-summary")
      if (!res.ok) throw new Error(t("errors.loadUsage"))
      return res.json()
    },
    staleTime: 30_000,
  })

  if (subscription.isLoading || usage.isLoading) return null
  if (!subscription.data || !usage.data) return null

  const sub = subscription.data
  const u = usage.data
  const llm = sub.llm || {}
  const pearch = sub.pearch || {}
  const apify = sub.apify || {}
  const quotas = sub.agent_quotas || {}
  const capReached = t("capReached")
  const capWarning = t("capWarning")

  return (
    <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-primary p-5 space-y-4">
      <div className="flex items-center gap-2">
        <Gauge className="h-4 w-4 text-lia-text-muted" aria-hidden="true" />
        <p className="text-sm font-medium text-lia-text-primary">{t("usage")}</p>
      </div>

      <div className="space-y-3">
        <UsageBar
          label={t("embeddingTokens")}
          icon={Database}
          used={u.embedding_tokens_used || 0}
          cap={llm.embedding_monthly_cap || 0}
          unit={t("tokens")}
          capReachedText={capReached}
          capWarningTemplate={capWarning}
        />

        {llm.byok_active ? (
          <div className="flex items-center gap-2 text-sm text-lia-text-secondary">
            <Zap className="h-3.5 w-3.5" aria-hidden="true" />
            <span>
              {t("byokActive")}
              {llm.byok_provider ? ` (${llm.byok_provider})` : ""}
            </span>
          </div>
        ) : (
          <UsageBar
            label={t("llmGeneralTokens")}
            icon={Zap}
            used={u.llm_general_tokens_used || 0}
            cap={llm.general_monthly_cap || 0}
            unit={t("tokens")}
            capReachedText={capReached}
            capWarningTemplate={capWarning}
          />
        )}

        <UsageBar
          label={t("pearchCredits")}
          icon={Search}
          used={u.pearch_credits_used || 0}
          cap={pearch.monthly_included_credits || 0}
          unit={t("credits")}
          capReachedText={capReached}
          capWarningTemplate={capWarning}
        />

        <UsageBar
          label={t("apifyCredits")}
          icon={Database}
          used={u.apify_credits_used || 0}
          cap={apify.monthly_included_credits || 0}
          unit={t("credits")}
          capReachedText={capReached}
          capWarningTemplate={capWarning}
        />

        <UsageBar
          label={t("agentExecutions")}
          icon={Bot}
          used={u.agent_executions_used || 0}
          cap={0}
          unit={t("executions")}
          capReachedText={capReached}
          capWarningTemplate={capWarning}
        />
      </div>

      {quotas && (
        <div className="pt-2 border-t border-lia-border-subtle">
          <p className="text-xs text-lia-text-tertiary">
            {t("agentsSummary")
              .replace("{custom}", String(quotas.custom_agents ?? 0))
              .replace("{sourcing}", String(quotas.sourcing_agents ?? 0))
              .replace("{twins}", String(quotas.digital_twins ?? 0))
              .replace("{campaigns}", String(quotas.campaigns ?? 0))}
          </p>
        </div>
      )}
    </div>
  )
}

export function ConsumoUnificadoTab({ onOpenDrilldown }: ConsumoUnificadoTabProps) {
  return (
    <div className="space-y-6">
      <QuotaSummary />
      <CreditosIaTab onOpenDrilldown={onOpenDrilldown} />
      <PearchTab />
      <AgentesTab onOpenDrilldown={onOpenDrilldown} />
    </div>
  )
}
