import type { InsightCategory } from "./job-insights.types"

/** Funnel stage bar colors following lia design tokens */
export const FUNNEL_STAGE_COLORS = [
  "bg-lia-interactive-active",
  "bg-lia-interactive-active",
  "bg-lia-interactive-active",
  "bg-lia-btn-primary-bg",
] as const

/** Status → Tailwind token map for conversion rate cards */
export const CONVERSION_STATUS_COLORS = {
  good: {
    bg: "bg-status-success/10",
    border: "border-status-success/30",
    text: "text-status-success",
    icon: "text-status-success",
    bar: "bg-status-success",
    label: "Dentro do esperado",
  },
  warning: {
    bg: "bg-status-warning/10",
    border: "border-status-warning/30",
    text: "text-status-warning",
    icon: "text-status-warning",
    bar: "bg-status-warning",
    label: "Atenção necessária",
  },
  critical: {
    bg: "bg-status-error/10",
    border: "border-status-error/30",
    text: "text-status-error",
    icon: "text-status-error",
    bar: "bg-status-error",
    label: "Gargalo identificado",
  },
} as const

/** Insight type → visual style map */
export const INSIGHT_TYPE_STYLES = {
  action: {
    bg: "bg-status-warning/10",
    border: "border-status-warning/30",
    iconColor: "text-status-warning",
  },
  analysis: {
    bg: "bg-wedo-purple/10",
    border: "border-wedo-purple/30",
    iconColor: "text-wedo-purple-text",
  },
  comparison: {
    bg: "bg-wedo-purple/10",
    border: "border-wedo-purple/30",
    iconColor: "text-wedo-purple-text",
  },
  attention: {
    bg: "bg-status-error/10",
    border: "border-status-error/30",
    iconColor: "text-status-error",
  },
} as const satisfies Record<InsightCategory["type"], object>

/** Trend chart week labels */
export const TREND_WEEKS = ["Sem 1", "Sem 2", "Sem 3", "Sem 4"] as const
