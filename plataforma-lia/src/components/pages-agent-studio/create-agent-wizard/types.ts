/**
 * CreateAgentWizard — types canonical
 *
 * UX_AUDIT_ESTUDIO_AGENTES_2026-05-21 T1+T3:
 * - T1: unifica os ~9 CTAs "Criar Agente" espalhados nas tabs do Estudio
 *   em um único wizard goal-first.
 * - T3: promove "Criar com IA" de BETA-escondido para hero CTA do passo 2,
 *   chamando POST /api/backend-proxy/custom-agents/generate (que mapeia
 *   pra POST /api/v1/custom-agents/generate-from-description no FastAPI).
 *
 * Os modais existentes (CreateAgentModal sourcing, CreateDigitalTwinModal,
 * TemplatePreviewModal) seguem montados como entry-points alternativos.
 */

import type { AgentTemplate } from "@/components/pages-agent-studio/custom-agents/types"

export type AgentGoal =
  | "triagem_inicial"
  | "sourcing_ativo"
  | "screening_cultural"
  | "voz_whatsapp"
  | "outro"

export type AgentApproach = "ai" | "template" | "manual"

export interface WizardConfig {
  name: string
  description: string
  templateId: string | null
  aiDescription: string
}

export interface GeneratedConfigPreview {
  suggested_name?: string
  suggested_role?: string
  suggested_domain?: string
  suggested_tools?: string[]
  suggested_prompt?: string
  suggested_context_level?: string
  suggested_max_steps?: number
  suggested_temperature?: number
  reasoning?: string
}

export interface CreateAgentWizardProps {
  open: boolean
  onClose: () => void
  /** Called with the created agent id (custom agent OR sourcing) when the wizard finishes. */
  onCreated?: (agentId: string) => void
  /** Optional pre-selected goal — when opened from a goal-specific CTA. */
  initialGoal?: AgentGoal
}

/**
 * Goals → recommended template categories.
 *
 * Used by ApproachStep to filter the 15 canonical templates from
 * `lib/agent-templates-data.ts` so the recruiter sees only templates
 * that match what they want to do.
 *
 * Categories come from `AgentCategory` union: screening | sourcing |
 * communication | analytics | job_management | automation | general.
 */
export const GOAL_TO_CATEGORIES: Record<AgentGoal, readonly string[]> = {
  triagem_inicial: ["screening"],
  sourcing_ativo: ["sourcing"],
  screening_cultural: ["screening"],
  voz_whatsapp: ["communication"],
  outro: ["screening", "sourcing", "communication", "analytics", "job_management", "automation"],
}

/**
 * Goal → template tag hints (additional filter on top of category).
 *
 * Some goals are narrower than the whole category (eg. "screening_cultural"
 * is a subset of screening). We surface templates whose `tags` overlap.
 */
export const GOAL_TO_TAG_HINTS: Record<AgentGoal, readonly string[]> = {
  triagem_inicial: ["triagem", "screening", "tech", "volume"],
  sourcing_ativo: ["sourcing", "passivo", "linkedin", "pool"],
  screening_cultural: ["cultura", "valores", "soft-skills"],
  voz_whatsapp: ["whatsapp", "voz", "voice", "comunicacao"],
  outro: [],
}

/**
 * Pick relevant templates for a goal — category-first, then tag-narrowed.
 *
 * Behavior:
 * - "outro" returns all templates (user wants to browse everything).
 * - Other goals: keep templates whose category matches AND (if tag hints
 *   exist) whose tags overlap with any hint. If filtering produces zero
 *   results, fall back to the unfiltered category set so the UI never
 *   shows an empty grid.
 */
export function filterTemplatesByGoal(
  templates: AgentTemplate[],
  goal: AgentGoal,
): AgentTemplate[] {
  if (goal === "outro") return templates

  const categories = GOAL_TO_CATEGORIES[goal]
  const tagHints = GOAL_TO_TAG_HINTS[goal]
  const inCategory = templates.filter((t) => categories.includes(t.category))

  if (tagHints.length === 0) return inCategory

  const tagFiltered = inCategory.filter((t) =>
    t.tags.some((tag) => tagHints.includes(tag.toLowerCase())),
  )

  return tagFiltered.length > 0 ? tagFiltered : inCategory
}
