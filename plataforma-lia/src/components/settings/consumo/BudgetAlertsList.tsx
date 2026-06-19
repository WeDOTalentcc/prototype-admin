// Onda 4 F5 (2026-05-28) — lista de alertas de orcamento.
//
// Renderiza alerts do endpoint /ai-consumption/budget-alerts (Onda 4 B3).
// Severity: info (wedo-cyan) / warning (status-warning) / critical (status-error)
// com border-l-4 canonical via tokens do Design System.
//
// CF-B B1 (2026-05-29): error state com retry (nao silenciar falha de fetch).
// CF-B B2 (2026-05-29): limite renderizado em TOKENS via resolveBudgetLimitTokens
// (le limit_tokens com fallback para legacy limit_cents) + formatBudgetLimit.
//
// projected_to_exceed=true -> adicionar texto "Projecao: ultrapassara o limite
// em ~X dias".
"use client"

import { useTranslations } from "next-intl"
import { AlertCircle, AlertTriangle, Info, RotateCw } from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useBudgetAlerts } from "@/hooks/consumption/use-budget-alerts"
import {
  resolveBudgetLimitTokens,
  type BudgetAlert,
} from "@/types/consumption/budget-alerts"

interface BudgetAlertsListProps {
  /** Permite consumer escutar request para drilldown (F4 ja e por agent_type). */
  onViewExecutions?: (agentType: string | null) => void
}

const SEVERITY_CLASS: Record<
  BudgetAlert["severity"],
  { wrap: string; icon: string }
> = {
  info: {
    wrap:
      "border-l-4 border-wedo-cyan bg-wedo-cyan/10 text-lia-text-primary",
    icon: "text-lia-text-secondary dark:text-wedo-cyan",
  },
  warning: {
    wrap:
      "border-l-4 border-status-warning bg-status-warning/10 text-lia-text-primary",
    icon: "text-status-warning",
  },
  critical: {
    wrap:
      "border-l-4 border-status-error bg-status-error/10 text-lia-text-primary",
    icon: "text-status-error",
  },
}

function severityIcon(sev: BudgetAlert["severity"]) {
  if (sev === "critical")
    return <AlertCircle className="h-4 w-4" aria-hidden="true" />
  if (sev === "warning")
    return <AlertTriangle className="h-4 w-4" aria-hidden="true" />
  return <Info className="h-4 w-4" aria-hidden="true" />
}

export function BudgetAlertsList({ onViewExecutions }: BudgetAlertsListProps) {
  const t = useTranslations("settings.consumption.budgetAlerts")
  const { data, isLoading, error, refetch } = useBudgetAlerts()

  // Loading/empty sao "ruido baixo" — nao renderiza nada.
  if (isLoading || (!error && (!data || data.alerts.length === 0))) {
    return null
  }

  // CF-B B1 — falha de fetch e visivel + acionavel (nao silenciar).
  if (error) {
    return (
      <section
        aria-label={t("title")}
        className="space-y-2"
        data-testid="budget-alerts-error"
      >
        <h3 className="text-xs font-medium text-lia-text-tertiary">
          {t("title")}
        </h3>
        <div
          role="alert"
          className="flex flex-col items-start gap-2 rounded-md border-l-4 border-status-error bg-status-error/10 p-3 text-sm text-lia-text-primary"
        >
          <p className="font-medium">{t("error.title")}</p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            className="gap-1.5"
            data-testid="budget-alerts-retry"
          >
            <RotateCw className="h-3.5 w-3.5" />
            {t("error.retry")}
          </Button>
        </div>
      </section>
    )
  }

  return (
    <section
      aria-label={t("title")}
      className="space-y-2"
      data-testid="budget-alerts-list"
    >
      <h3 className="text-xs font-medium text-lia-text-tertiary">
        {t("title")}
      </h3>
      <ul className="space-y-2">
        {data!.alerts.map((alert, idx) => {
          const cls = SEVERITY_CLASS[alert.severity]
          const pct = String(Math.round(alert.used_pct * 100))
          const projectionDays = alert.days_remaining
          const limitTokens = resolveBudgetLimitTokens(alert)

          const messageKey =
            alert.scope === "global"
              ? (`${alert.severity}.global` as const)
              : ("perAgent" as const)

          const labelMessage =
            alert.scope === "global"
              ? t(messageKey, { pct })
              : t("perAgent", {
                  agentName: alert.agent_name ?? "—",
                  pct,
                })

          return (
            <li
              key={`${alert.scope}-${alert.studio_agent_id ?? "global"}-${idx}`}
              className={cn(
                "flex items-start gap-3 rounded-md p-3 text-sm",
                cls.wrap,
              )}
              data-testid={`budget-alert-${alert.severity}`}
            >
              <span className={cn("mt-0.5 flex-shrink-0", cls.icon)}>
                {severityIcon(alert.severity)}
              </span>
              <div className="flex-1 space-y-1">
                <p className="font-medium">{labelMessage}</p>
                {limitTokens > 0 && (
                  <p className="text-xs opacity-90">
                    {t("limit", { value: formatBudgetLimit(limitTokens) })}
                  </p>
                )}
                {alert.projected_to_exceed && (
                  <p className="text-xs opacity-90">
                    {t("projected", { days: projectionDays })}
                  </p>
                )}
                {alert.scope === "agent" && alert.studio_agent_id && (
                  <button
                    type="button"
                    onClick={() => {
                      onViewExecutions?.(alert.studio_agent_id)
                    }}
                    className="text-xs font-medium underline-offset-2 hover:underline"
                  >
                    {t("viewExecutions")}
                  </button>
                )}
              </div>
            </li>
          )
        })}
      </ul>
    </section>
  )
}

/**
 * Helper canonical para renderizar o limite como tokens.
 * O valor ja vem em tokens (ver resolveBudgetLimitTokens / type doc).
 */
export function formatBudgetLimit(limit: number): string {
  if (limit >= 1_000_000) return `${(limit / 1_000_000).toFixed(1)}M tokens`
  if (limit >= 1_000) return `${(limit / 1_000).toFixed(1)}K tokens`
  return `${limit} tokens`
}
