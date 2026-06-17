/**
 * Canonical funnel stages — single source of truth for the recruiter funnel
 * vocabulary (labels, icons, colors, navigation paths).
 *
 * Consumed by ChatWorkflowReels (chat home empty-state, dock-magnified).
 *
 * The keys here intentionally match the existing chat translation namespace
 * (`chat.workflowReels.stages.<id>`) so we can reuse all PT-BR/EN labels
 * without duplicating them.
 */

import {
  Briefcase,
  Search,
  UserCheck,
  Calendar,
  FileText,
  TrendingUp,
  BarChart3,
  Sparkles,
  Settings,
  type LucideIcon,
} from "lucide-react"

export type CanonicalStageId =
  | "definir-vaga"
  | "sourcing"
  | "triagem"
  | "entrevista"
  | "oferta"
  | "contratacao"

export type CanonicalUtilityId = "analytics" | "ia-automacoes" | "configuracoes"

export interface CanonicalStageColor {
  /** Solid accent (used for active node, ring, label). */
  accent: string
  /** Soft tinted background. */
  accentBg: string
  /** Border color when node has data. */
  nodeBorder: string
  /** Subtle border for surrounding card surfaces. */
  cardBorder: string
}

export interface CanonicalStage {
  key: CanonicalStageId | CanonicalUtilityId
  /** i18n key for the long label. */
  labelKey: string
  /** i18n key for the short/compact label. */
  shortLabelKey: string
  Icon: LucideIcon
  color: CanonicalStageColor
  /** Locale-relative target path when the chip is clicked. */
  navPath: string
  /** Position in the linear funnel (1-based). Utility nodes use a higher band. */
  order: number
}

const COLOR_CYAN: CanonicalStageColor = {
  accent: "var(--wedo-cyan)",
  accentBg: "color-mix(in srgb, var(--wedo-cyan) 10%, transparent)",
  nodeBorder: "var(--wedo-cyan)",
  cardBorder: "color-mix(in srgb, var(--wedo-cyan) 25%, transparent)",
}
const COLOR_GREEN: CanonicalStageColor = {
  accent: "var(--wedo-green)",
  accentBg: "color-mix(in srgb, var(--wedo-green) 10%, transparent)",
  nodeBorder: "var(--wedo-green)",
  cardBorder: "color-mix(in srgb, var(--wedo-green) 25%, transparent)",
}
const COLOR_ORANGE: CanonicalStageColor = {
  accent: "var(--wedo-orange)",
  accentBg: "color-mix(in srgb, var(--wedo-orange) 10%, transparent)",
  nodeBorder: "var(--wedo-orange)",
  cardBorder: "color-mix(in srgb, var(--wedo-orange) 25%, transparent)",
}
const COLOR_PURPLE: CanonicalStageColor = {
  accent: "var(--wedo-purple)",
  accentBg: "color-mix(in srgb, var(--wedo-purple) 10%, transparent)",
  nodeBorder: "var(--wedo-purple)",
  cardBorder: "color-mix(in srgb, var(--wedo-purple) 25%, transparent)",
}
const COLOR_AMBER: CanonicalStageColor = {
  accent: "var(--wedo-amber)",
  accentBg: "color-mix(in srgb, var(--wedo-amber) 10%, transparent)",
  nodeBorder: "var(--wedo-amber)",
  cardBorder: "color-mix(in srgb, var(--wedo-amber) 25%, transparent)",
}
const COLOR_GRAY: CanonicalStageColor = {
  accent: "var(--lia-text-secondary)",
  accentBg: "color-mix(in srgb, var(--lia-text-secondary) 10%, transparent)",
  nodeBorder: "var(--lia-text-secondary)",
  cardBorder: "color-mix(in srgb, var(--lia-text-secondary) 25%, transparent)",
}

/** Ordered funnel stages. The footer bar renders these in this order. */
export const CANONICAL_FUNNEL_STAGES: CanonicalStage[] = [
  {
    key: "definir-vaga",
    labelKey: "chat.workflowReels.stages.definir-vaga.label",
    shortLabelKey: "chat.workflowReels.stages.definir-vaga.shortLabel",
    Icon: Briefcase,
    color: COLOR_CYAN,
    navPath: "/jobs",
    order: 1,
  },
  {
    key: "sourcing",
    labelKey: "chat.workflowReels.stages.sourcing.label",
    shortLabelKey: "chat.workflowReels.stages.sourcing.shortLabel",
    Icon: Search,
    color: COLOR_GREEN,
    navPath: "/visao-do-funil?view=candidatos&stage=sourcing",
    order: 2,
  },
  {
    key: "triagem",
    labelKey: "chat.workflowReels.stages.triagem.label",
    shortLabelKey: "chat.workflowReels.stages.triagem.shortLabel",
    Icon: UserCheck,
    color: COLOR_GREEN,
    navPath: "/visao-do-funil?view=candidatos&stage=screening",
    order: 3,
  },
  {
    key: "entrevista",
    labelKey: "chat.workflowReels.stages.entrevista.label",
    shortLabelKey: "chat.workflowReels.stages.entrevista.shortLabel",
    Icon: Calendar,
    color: COLOR_ORANGE,
    navPath: "/visao-do-funil?view=candidatos&stage=interview",
    order: 4,
  },
  {
    key: "oferta",
    labelKey: "chat.workflowReels.stages.oferta.label",
    shortLabelKey: "chat.workflowReels.stages.oferta.shortLabel",
    Icon: FileText,
    color: COLOR_PURPLE,
    navPath: "/visao-do-funil?view=candidatos&stage=offer",
    order: 5,
  },
  {
    key: "contratacao",
    labelKey: "chat.workflowReels.stages.contratacao.label",
    shortLabelKey: "chat.workflowReels.stages.contratacao.shortLabel",
    Icon: TrendingUp,
    color: COLOR_PURPLE,
    navPath: "/visao-do-funil?view=candidatos&stage=hired",
    order: 6,
  },
]

/** Utility nodes shown after the main funnel (analytics, AI). */
export const CANONICAL_UTILITY_STAGES: CanonicalStage[] = [
  {
    key: "analytics",
    labelKey: "chat.workflowReels.stages.analytics.label",
    shortLabelKey: "chat.workflowReels.stages.analytics.shortLabel",
    Icon: BarChart3,
    color: COLOR_AMBER,
    navPath: "/visao-do-funil",
    order: 7,
  },
  {
    key: "ia-automacoes",
    labelKey: "chat.workflowReels.stages.ia-automacoes.label",
    shortLabelKey: "chat.workflowReels.stages.ia-automacoes.shortLabel",
    Icon: Sparkles,
    color: COLOR_CYAN,
    navPath: "/agent-studio",
    order: 8,
  },
  {
    key: "configuracoes",
    labelKey: "chat.workflowReels.stages.configuracoes.label",
    shortLabelKey: "chat.workflowReels.stages.configuracoes.shortLabel",
    Icon: Settings,
    color: COLOR_GRAY,
    navPath: "/configuracoes",
    order: 9,
  },
]

/** Convenience union of every canonical stage (funnel + utility). */
export const CANONICAL_ALL_STAGES: CanonicalStage[] = [
  ...CANONICAL_FUNNEL_STAGES,
  ...CANONICAL_UTILITY_STAGES,
]

/** Look up a canonical stage by its key. */
export function getCanonicalStage(key: string): CanonicalStage | undefined {
  return CANONICAL_ALL_STAGES.find((s) => s.key === key)
}
