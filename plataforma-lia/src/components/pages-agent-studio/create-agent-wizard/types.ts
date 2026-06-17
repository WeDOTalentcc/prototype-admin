/**
 * CreateAgentWizard — types canonical
 *
 * UX_AUDIT_ESTUDIO_AGENTES_2026-05-21 T1+T3+T4:
 * - T1: unifica os ~9 CTAs "Criar Agente" espalhados nas tabs do Estudio
 *   em um único wizard goal-first.
 * - T3: promove "Criar com IA" de BETA-escondido para hero CTA do passo 2,
 *   chamando POST /api/backend-proxy/custom-agents/generate (que mapeia
 *   pra POST /api/v1/custom-agents/generate-from-description no FastAPI).
 * - T4: aceita `initialConfig` (template_id + goal + nome pre-populado)
 *   para o pattern clone-first do TemplateClonePanel. Quando presente,
 *   o wizard pula goal+approach e abre direto no step 3 (Configurar).
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
  /**
   * Channel selection at creation (2026-06-09). All default false/undefined.
   * Channels do NOT flow through the Create schema — after the agent is created,
   * the wizard fires the dedicated PATCH /agents/{id}/{channel}/enabled endpoints
   * for each channel set true here. Adjustable later via the agent card toggles.
   */
  channels?: {
    voice?: boolean
    voip?: boolean
    whatsapp?: boolean
    triagem_invite?: boolean
  }
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

/**
 * T4 — Clone-first pre-population.
 *
 * Passado por TemplateClonePanel quando o recruiter clica "Clonar e customizar".
 * Quando `templateId` está presente, o wizard:
 *   1. Pula step 1 (goal já inferido da categoria do template)
 *   2. Pula step 2 (approach='template' já decidido)
 *   3. Abre direto step 3 (Configurar) com nome "(cópia)" e campos populados
 *
 * Não substitui `initialGoal` — quando ambos vierem, `initialConfig` ganha.
 */
export interface CreateAgentInitialConfig {
  goal?: AgentGoal
  approach?: AgentApproach
  templateId?: string
  name?: string
  description?: string
  aiDescription?: string
  /**
   * Sprint 5 (2026-05-25) — decommission do CreateAgentModal (path #3 sector tile).
   * Sector id canonical (factory | heart_pulse | shopping_cart | code | truck)
   * vindo do FastAPI agent-templates/sectors. Quando setado, sinaliza que a
   * entrada veio de um sector tile e o wizard pode usar isso pra naming/tracking
   * (a criação em si vai por /custom-agents — sectors endpoint nao é mais
   * chamado, dropado junto com o modal legado).
   */
  prefilledSector?: string
}

export interface CreateAgentWizardProps {
  open: boolean
  onClose: () => void
  /** Called with the created agent id (custom agent OR sourcing) when the wizard finishes. */
  onCreated?: (agentId: string) => void
  /** Optional pre-selected goal — when opened from a goal-specific CTA. */
  initialGoal?: AgentGoal
  /**
   * T4 — clone-first pre-population. When `templateId` is set, wizard skips
   * goal+approach and opens at step 3 (Configurar). See {@link CreateAgentInitialConfig}.
   */
  initialConfig?: CreateAgentInitialConfig
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

/**
 * T4 — Infer a goal from a template's category/tags for clone-first flow.
 *
 * When TemplateClonePanel clones a template into the wizard, we pre-populate
 * `goal` so the wizard's downstream steps (config + preview) keep contextual
 * copy + behavior. Falls back to "outro" for ambiguous templates.
 */
export function inferGoalFromTemplate(template: AgentTemplate): AgentGoal {
  const tags = (template.tags ?? []).map((t) => t.toLowerCase())

  // Tag-based heuristics first (more specific than category)
  if (tags.some((t) => ["cultura", "valores", "soft-skills"].includes(t))) {
    return "screening_cultural"
  }
  if (tags.some((t) => ["whatsapp", "voz", "voice", "comunicacao"].includes(t))) {
    return "voz_whatsapp"
  }
  if (tags.some((t) => ["sourcing", "passivo", "linkedin", "pool"].includes(t))) {
    return "sourcing_ativo"
  }
  if (tags.some((t) => ["triagem", "screening", "tech", "volume"].includes(t))) {
    return "triagem_inicial"
  }

  // Category fallback
  switch (template.category) {
    case "screening":
      return "triagem_inicial"
    case "sourcing":
      return "sourcing_ativo"
    case "communication":
      return "voz_whatsapp"
    default:
      return "outro"
  }
}
