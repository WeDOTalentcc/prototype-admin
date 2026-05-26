"use client"

/**
 * Badge canonical "X/Y agentes" pra sidebar (Sprint 7C / 7B-3b backlog).
 *
 * Consome useAgentsTotalQuota (alias unified das 4 categorias agent).
 * Cor canonical per percentage: verde<70%, amber 70-94%, coral≥95%.
 *
 * PRESERVA QuotaMeter (4 categorias per resource) — esse badge é apenas
 * vista global pra navegação ambient.
 */
import { useAgentsTotalQuota, type QuotaTotalTier } from "@/hooks/agent-studio/use-agents-total-quota"

const TIER_CLASSES: Record<QuotaTotalTier, string> = {
  green: "bg-lia-success-soft text-lia-success",
  amber: "bg-lia-warning-soft text-lia-warning",
  coral: "bg-lia-coral-soft text-lia-coral",
}

export interface AgentsQuotaBadgeProps {
  /** Quando true, esconde texto e mantém apenas dot indicator (sidebar collapsed). */
  compact?: boolean
}

export function AgentsQuotaBadge({ compact = false }: AgentsQuotaBadgeProps) {
  const { data, tier, isLoading, error } = useAgentsTotalQuota()

  if (isLoading || error || !data) return null

  const label = data.is_unlimited
    ? `${data.current_agents_total}/∞`
    : `${data.current_agents_total}/${data.max_agents_total}`

  const cls = TIER_CLASSES[tier]

  if (compact) {
    return (
      <span
        data-testid="agents-quota-badge-dot"
        data-tier={tier}
        className={`inline-block h-2 w-2 rounded-full ${cls}`}
        aria-label={`${label} agentes`}
      />
    )
  }

  return (
    <span
      data-testid="agents-quota-badge"
      data-tier={tier}
      className={`text-micro px-1.5 py-0.5 rounded-full ${cls}`}
    >
      {label}
    </span>
  )
}
