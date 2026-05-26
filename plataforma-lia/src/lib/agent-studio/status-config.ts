/**
 * Canonical status config for Agent Studio.
 *
 * UX-Sprint-A Batch 3 audit 2026-05-21 sec.5 QW#18: status palette estava
 * duplicada em 3 sites (AgentStudioPage.tsx STATUS_CONFIG_STYLES,
 * CustomAgentsTab.tsx STATUS_CONFIG, AgentCard.tsx STATUS_STYLES). Drift
 * inevitável. Single source of truth aqui.
 *
 * Dois domínios distintos:
 * - **Sourcing agents** (AgentStudioPage): active / paused / completed
 * - **Custom agents** (CustomAgentsTab + AgentCard): draft / active / paused / archived
 *
 * Schema canonical para ambos (subset de campos conforme uso):
 *   { dot, bg, text, badge (badgeStyles ref), pulse }
 */

import { badgeStyles } from "@/lib/design-tokens"

export type AgentStatus = "active" | "paused" | "completed"
export type CustomAgentStatus = "draft" | "active" | "paused" | "archived"

interface StatusVisualConfig {
  /** Tailwind class for status dot (e.g., "bg-emerald-500") */
  dot: string
  /** Tailwind class for background of status pill (e.g., "bg-emerald-50 dark:bg-emerald-950/30") */
  bg: string
  /** Tailwind class for text inside status pill (e.g., "text-emerald-700 dark:text-emerald-400") */
  text: string
  /** Pre-composed badgeStyles ref (canonical from design-tokens) */
  badge: string
  /** Whether the dot should pulse (only "active" by default) */
  pulse: boolean
}

const ACTIVE: StatusVisualConfig = {
  dot: "bg-emerald-500",
  bg: "bg-emerald-50 dark:bg-emerald-950/30",
  text: "text-emerald-700 dark:text-emerald-400",
  badge: badgeStyles.success,
  pulse: true,
}

const PAUSED: StatusVisualConfig = {
  dot: "bg-amber-500",
  bg: "bg-amber-50 dark:bg-amber-950/30",
  text: "text-amber-700 dark:text-amber-400",
  badge: badgeStyles.warning,
  pulse: false,
}

const COMPLETED: StatusVisualConfig = {
  dot: "bg-lia-text-disabled",
  bg: "bg-lia-bg-tertiary",
  text: "text-lia-text-secondary",
  badge: badgeStyles.default,
  pulse: false,
}

const DRAFT: StatusVisualConfig = {
  dot: "bg-lia-text-disabled",
  bg: "bg-lia-bg-secondary dark:bg-lia-bg-inverse/30",
  text: "text-lia-text-secondary dark:text-lia-text-tertiary",
  badge: badgeStyles.default,
  pulse: false,
}

const ARCHIVED: StatusVisualConfig = {
  dot: "bg-red-400",
  bg: "bg-red-50 dark:bg-red-950/30",
  text: "text-red-600 dark:text-red-400",
  badge: badgeStyles.error,
  pulse: false,
}

export const STATUS_MAP: Record<AgentStatus, StatusVisualConfig> = {
  active: ACTIVE,
  paused: PAUSED,
  completed: COMPLETED,
}

const CUSTOM_MAP: Record<CustomAgentStatus, StatusVisualConfig> = {
  draft: DRAFT,
  active: ACTIVE,
  paused: PAUSED,
  archived: ARCHIVED,
}

/**
 * Get visual config for sourcing agent status (active/paused/completed).
 * Returns COMPLETED config as fallback for unknown status.
 */
export function getAgentStatusConfig(status: string): StatusVisualConfig {
  return STATUS_MAP[status as AgentStatus] || COMPLETED
}

/**
 * Get visual config for custom agent status (draft/active/paused/archived).
 * Returns DRAFT config as fallback for unknown status.
 */
export function getCustomAgentStatusConfig(status: string): StatusVisualConfig {
  return CUSTOM_MAP[status as CustomAgentStatus] || DRAFT
}


// Backward-compat aliases pra consumers legacy (Sprint 7B-3a part 2)
// Remover quando todos consumers migrarem pros nomes canonical
export const getSourcingAgentStatusConfig = getAgentStatusConfig
export type SourcingAgentStatus = AgentStatus
export { STATUS_MAP as SOURCING_MAP }
