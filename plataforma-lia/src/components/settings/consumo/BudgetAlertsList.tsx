// Onda 4 F5 (2026-05-28) — lista de alertas de orçamento.
//
// Renderiza alerts do endpoint /ai-consumption/budget-alerts (Onda 4 B3).
// Severity: info (azul) / warning (amber) / critical (red) com border-l-4
// canonical.
//
// Decisão: backend tem gap — `limit_cents` é na realidade TOKENS, não cents.
// Renderizamos via helper formatBudgetLimit que rotula "tokens".
//
// projected_to_exceed=true → adicionar texto "Projeção: ultrapassará o limite
// em ~X dias".
"use client"

import { useTranslations } from "next-intl"
import { AlertCircle, AlertTriangle, Info } from "lucide-react"

import { cn } from "@/lib/utils"
import { useBudgetAlerts } from "@/hooks/consumption/use-budget-alerts"
import { getAgentLabel } from "@/components/settings/consumo/CreditosIaTab"
import type { BudgetAlert } from "@/types/consumption/budget-alerts"

interface BudgetAlertsListProps {
  /** Permite consumer escutar request para drilldown (F4 já é por agent_type). */
  onViewExecutions?: (agentType: string | null) => void
}

const SEVERITY_CLASS: Record<
  BudgetAlert["severity"],
  { wrap: string; icon: string }
> = {
  info: {
    wrap:
      "border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-950/30 text-blue-900 dark:text-blue-100",
    icon: "text-blue-500",
  },
  warning: {
    wrap:
      "border-l-4 border-amber-500 bg-amber-50 dark:bg-amber-950/30 text-amber-900 dark:text-amber-100",
    icon: "text-amber-500",
  },
  critical: {
    wrap:
      "border-l-4 border-red-500 bg-red-50 dark:bg-red-950/30 text-red-900 dark:text-red-100",
    icon: "text-red-500",
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
  const { data, isLoading, error } = useBudgetAlerts()

  // Não renderiza nada quando isLoading/error/empty — alerts são "ruído baixo".
  if (isLoading || error || !data || data.alerts.length === 0) {
    return null
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
        {data.alerts.map((alert, idx) => {
          const cls = SEVERITY_CLASS[alert.severity]
          const pct = Math.round(alert.used_pct * 100)
          const projectionDays = alert.days_remaining

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
                {alert.projected_to_exceed && (
                  <p className="text-xs opacity-90">
                    {t("projected", { days: projectionDays })}
                  </p>
                )}
                {alert.scope === "agent" && alert.studio_agent_id && (
                  <button
                    type="button"
                    onClick={() => {
                      // Onda 4 F5 — open drilldown filtered by agent
                      // Default: passa null agent_type para abrir o modal por agent_id se consumer suportar
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
 * Helper canonical para renderizar o "limite" como tokens (não cents).
 * Backend gap: field name é limit_cents mas value é tokens.
 */
export function formatBudgetLimit(limit: number): string {
  if (limit >= 1_000_000) return `${(limit / 1_000_000).toFixed(1)}M tokens`
  if (limit >= 1_000) return `${(limit / 1_000).toFixed(1)}K tokens`
  return `${limit} tokens`
}
