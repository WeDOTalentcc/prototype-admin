export type StageType = 'active' | 'final' | 'standby'
export type StatusCategory = 'qualification' | 'cultural' | 'logistics' | 'compensation' | 'process' | 'business_decision'

export interface RecruitmentStage {
  name: string
  displayName: string
  stageOrder: number
  color: string
  icon: string
  stageType: StageType
  isInitial: boolean
  isFinal: boolean
  isHired?: boolean
  isRejection?: boolean
  isStandby?: boolean
  stageCategory: 'system' | 'default' | 'custom'
  allowedTransitions: string[]
}

export interface CompanyPipelineStage {
  name: string
  displayName: string
  stageOrder: number
  color: string
  icon: string
  stageType: StageType
  stageCategory: 'system' | 'default' | 'custom'
  isInitial: boolean
  isFinal: boolean
  isHired?: boolean
  isRejection?: boolean
  isStandby?: boolean
  isActive: boolean
  isEditable: boolean
  isRemovable: boolean
  isReorderable: boolean
  defaultSlaDays: number
  liaAssisted: boolean
}

export const LIA_ASSISTED_STAGES = [
  'sourcing',
  'screening',
  'interview_hr',
  'hired',
  'rejected',
]

export const LIA_ASSISTED_STAGE_NAMES = [
  'Funil',
  'Triagem',
  'Entrevista RH',
  'Contratado',
  'Reprovado',
]

export const DEFAULT_SLA_DAYS: Record<string, number> = {
  sourcing: 5,
  screening: 3,
  long_list: 3,
  short_list: 2,
  interview_hr: 3,
  technical_test: 5,
  english_test: 3,
  interview_technical: 3,
  interview_manager: 3,
  interview_manager2: 3,
  interview_final: 3,
  references: 3,
  offer: 2,
  hired: 1,
  rejected: 1,
  offer_declined: 1,
}

export const RECRUITMENT_STAGES: RecruitmentStage[] = [
  {
    name: 'sourcing',
    displayName: 'Funil',
    stageOrder: 1,
    color: 'var(--lia-border-subtle)',
    icon: 'search',
    stageType: 'active',
    isInitial: true,
    isFinal: false,
    stageCategory: 'system',
    allowedTransitions: ['screening', 'rejected'],
  },
  {
    name: 'screening',
    displayName: 'Triagem',
    stageOrder: 2,
    color: 'var(--lia-border-subtle)',
    icon: 'file-text',
    stageType: 'active',
    isInitial: false,
    isFinal: false,
    stageCategory: 'system',
    allowedTransitions: ['long_list', 'short_list', 'interview_hr', 'interview_technical', 'rejected'],
  },
  {
    name: 'long_list',
    displayName: 'Long List',
    stageOrder: 3,
    color: 'var(--lia-border-default)',
    icon: 'list',
    stageType: 'active',
    isInitial: false,
    isFinal: false,
    stageCategory: 'custom',
    allowedTransitions: ['short_list', 'interview_hr', 'rejected', 'standby'],
  },
  {
    name: 'short_list',
    displayName: 'Short List',
    stageOrder: 4,
    color: 'var(--lia-border-default)',
    icon: 'list-checks',
    stageType: 'active',
    isInitial: false,
    isFinal: false,
    stageCategory: 'custom',
    allowedTransitions: ['interview_hr', 'interview_technical', 'rejected'],
  },
  {
    name: 'interview_hr',
    displayName: 'Entrevista RH',
    stageOrder: 5,
    color: 'var(--lia-text-tertiary)',
    icon: 'users',
    stageType: 'active',
    isInitial: false,
    isFinal: false,
    stageCategory: 'system',
    allowedTransitions: ['technical_test', 'english_test', 'interview_technical', 'interview_manager', 'rejected'],
  },
  {
    name: 'technical_test',
    displayName: 'Teste Técnico',
    stageOrder: 6,
    color: 'var(--lia-text-tertiary)',
    icon: 'code-2',
    stageType: 'active',
    isInitial: false,
    isFinal: false,
    stageCategory: 'custom',
    allowedTransitions: ['english_test', 'interview_technical', 'interview_manager', 'rejected'],
  },
  {
    name: 'english_test',
    displayName: 'Teste de Inglês',
    stageOrder: 7,
    color: 'var(--lia-text-tertiary)',
    icon: 'languages',
    stageType: 'active',
    isInitial: false,
    isFinal: false,
    stageCategory: 'custom',
    allowedTransitions: ['interview_technical', 'interview_manager', 'rejected'],
  },
  {
    name: 'interview_technical',
    displayName: 'Entrevista Técnica',
    stageOrder: 8,
    color: 'var(--lia-text-secondary)',
    icon: 'code',
    stageType: 'active',
    isInitial: false,
    isFinal: false,
    stageCategory: 'custom',
    allowedTransitions: ['interview_manager', 'interview_final', 'offer', 'rejected'],
  },
  {
    name: 'interview_manager',
    displayName: 'Entrevista Gestor',
    stageOrder: 9,
    color: 'var(--lia-text-secondary)',
    icon: 'briefcase',
    stageType: 'active',
    isInitial: false,
    isFinal: false,
    stageCategory: 'custom',
    allowedTransitions: ['interview_manager2', 'interview_final', 'offer', 'rejected'],
  },
  {
    name: 'interview_manager2',
    displayName: 'Entrevista Gestor 2',
    stageOrder: 10,
    color: 'var(--lia-text-secondary)',
    icon: 'briefcase',
    stageType: 'active',
    isInitial: false,
    isFinal: false,
    stageCategory: 'custom',
    allowedTransitions: ['interview_final', 'offer', 'rejected'],
  },
  {
    name: 'interview_final',
    displayName: 'Entrevista Final',
    stageOrder: 11,
    color: 'var(--lia-text-secondary)',
    icon: 'award',
    stageType: 'active',
    isInitial: false,
    isFinal: false,
    stageCategory: 'custom',
    allowedTransitions: ['references', 'offer', 'rejected'],
  },
  {
    name: 'references',
    displayName: 'Referências',
    stageOrder: 12,
    color: 'var(--lia-text-secondary)',
    icon: 'phone',
    stageType: 'active',
    isInitial: false,
    isFinal: false,
    stageCategory: 'custom',
    allowedTransitions: ['offer', 'rejected'],
  },
  {
    name: 'offer',
    displayName: 'Proposta',
    stageOrder: 13,
    color: 'var(--lia-text-primary)',
    icon: 'file-check',
    stageType: 'active',
    isInitial: false,
    isFinal: false,
    stageCategory: 'default',
    allowedTransitions: ['hired', 'rejected', 'offer_declined'],
  },
  {
    name: 'hired',
    displayName: 'Contratado',
    stageOrder: 14,
    color: 'var(--status-success)',
    icon: 'check-circle',
    stageType: 'final',
    isInitial: false,
    isFinal: true,
    isHired: true,
    stageCategory: 'system',
    allowedTransitions: [],
  },
  {
    name: 'rejected',
    displayName: 'Reprovado',
    stageOrder: 15,
    color: 'var(--lia-border-subtle)',
    icon: 'x-circle',
    stageType: 'final',
    isInitial: false,
    isFinal: true,
    isRejection: true,
    stageCategory: 'system',
    allowedTransitions: [],
  },
  {
    name: 'offer_declined',
    displayName: 'Proposta Recusada',
    stageOrder: 16,
    color: 'var(--lia-border-subtle)',
    icon: 'x',
    stageType: 'final',
    isInitial: false,
    isFinal: true,
    stageCategory: 'default',
    allowedTransitions: [],
  },
  {
    name: 'standby',
    displayName: 'Stand By',
    stageOrder: 17,
    color: 'var(--lia-border-default)',
    icon: 'pause-circle',
    stageType: 'standby',
    isInitial: false,
    isFinal: false,
    isStandby: true,
    stageCategory: 'custom',
    allowedTransitions: ['sourcing', 'screening', 'interview_hr'],
  },
]

// =====================================================================
// WT-2022 P0.STAGES — Adapter canonical para unificar 2 shapes de stage
// =====================================================================
//
// Contexto: existem 2 tipos RecruitmentStage no codebase:
//
//  1. ESTE arquivo (legacy, camelCase):
//     { name, displayName, stageOrder, stageType, stageCategory, color,
//       icon, isInitial, isFinal, isHired?, isRejection?, isStandby?,
//       allowedTransitions }
//     — consumido por: stage-transition-*, kanban utils, bulk-action-modal,
//       cell-renderers, etc. (10 consumers em src/components/**).
//
//  2. @/components/settings/recruitment-journey.types (hook canonical,
//     snake_case, vindo do backend Rails /company-pipeline):
//     { id, name, display_name, order, isActive, notes, sla, type,
//       color?, icon?, action_behavior?, default_channel?,
//       stage_category?, catalog_id?, sub_statuses?, data_fields? }
//     — consumido por: useRecruitmentStages hook + settings UI.
//
// Sessao anterior tentou wire 10 consumers contra hook canonical mas
// foram revertidos por TypeScript union conflict (campos diferentes,
// casing diferente). Adapter abaixo normaliza shape do hook para
// shape legacy preservando back-compat.
//
// Pattern canonical pra consumer React migrar:
//   const { legacyStages } = useRecruitmentStages()
//   // legacyStages: RecruitmentStage[] (camelCase, drop-in pra utils)
//
// Sensor lint em scripts/check-no-direct-recruitment-stages-import.ts
// detecta novos imports diretos de RECRUITMENT_STAGES em componentes
// React e sugere migracao pro hook.
// =====================================================================

/**
 * Shape MINIMO do hook canonical (snake_case). Definido localmente em vez
 * de importar  pra evitar
 * dependencia circular (settings UI ja importa ).
 *
 * Mantenha em sincronia com  em
 * .
 * Schema-sync TS pattern: campo novo num lado exige campo no outro.
 */
export interface HookRecruitmentStage {
  id?: string
  name: string
  display_name?: string
  order?: number
  isActive?: boolean
  notes?: string
  sla?: number
  type?: "system" | "default" | "custom"
  color?: string
  icon?: string
  action_behavior?: string
  default_channel?: string
  stage_category?: string
  catalog_id?: string
  // sub_statuses / data_fields nao mapeados — legacy shape nao os usa.
}

/**
 * Resolve isInitial/isFinal/isHired/isRejection/isStandby a partir do
 * nome canonical do stage. Pra stages custom (sem match na lista
 * canonical), fallback conservador: isInitial=false, isFinal=false.
 */
function resolveStageFlags(name: string, stageType?: StageType): {
  isInitial: boolean
  isFinal: boolean
  isHired?: boolean
  isRejection?: boolean
  isStandby?: boolean
} {
  const canonical = RECRUITMENT_STAGES.find((s) => s.name === name)
  if (canonical) {
    return {
      isInitial: canonical.isInitial,
      isFinal: canonical.isFinal,
      isHired: canonical.isHired,
      isRejection: canonical.isRejection,
      isStandby: canonical.isStandby,
    }
  }
  // Fallback heuristica por nome (custom stages do tenant)
  const lower = name.toLowerCase()
  return {
    isInitial: lower === "sourcing" || lower === "funil",
    isFinal: stageType === "final",
    isHired: lower === "hired" || lower === "contratado",
    isRejection: lower === "rejected" || lower === "reprovado",
    isStandby: stageType === "standby" || lower === "standby",
  }
}

/**
 * Mapeia  do hook (system|default|custom) →  legacy
 * (active|final|standby). Pra stages canonical, usa o stageType da
 * lista canonical; pra custom, default = "active".
 */
function resolveStageType(
  name: string,
  hookType?: "system" | "default" | "custom",
): StageType {
  const canonical = RECRUITMENT_STAGES.find((s) => s.name === name)
  if (canonical) return canonical.stageType
  // Heuristica por nome custom
  const lower = name.toLowerCase()
  if (lower === "standby" || lower.includes("stand")) return "standby"
  if (lower === "hired" || lower === "rejected" || lower === "offer_declined") {
    return "final"
  }
  return "active"
}

/**
 * Normaliza um stage do hook (snake_case) pro shape legacy (camelCase).
 *
 * Campos nao-presentes no hook recebem fallback canonical (lookup em
 * RECRUITMENT_STAGES por ) ou defaults seguros.
 *
 * @example
 *   const { stages } = useRecruitmentStages()
 *   const legacy = stages.map(normalizeStageFromHook)
 *   // legacy[0].displayName, legacy[0].stageOrder, ...
 */
export function normalizeStageFromHook(s: HookRecruitmentStage): RecruitmentStage {
  const canonical = RECRUITMENT_STAGES.find((c) => c.name === s.name)
  const stageType = resolveStageType(s.name, s.type)
  const flags = resolveStageFlags(s.name, stageType)

  // stageCategory: hook expoe  (string livre vinda do
  // backend) e . Legacy quer system|default|custom.
  const stageCategory: "system" | "default" | "custom" =
    s.type === "system" || s.type === "default" || s.type === "custom"
      ? s.type
      : (canonical?.stageCategory ?? "custom")

  return {
    name: s.name,
    displayName: s.display_name ?? canonical?.displayName ?? s.name,
    stageOrder: s.order ?? canonical?.stageOrder ?? 0,
    color: s.color ?? canonical?.color ?? "var(--lia-border-default)",
    icon: s.icon ?? canonical?.icon ?? "circle",
    stageType,
    isInitial: flags.isInitial,
    isFinal: flags.isFinal,
    isHired: flags.isHired,
    isRejection: flags.isRejection,
    isStandby: flags.isStandby,
    stageCategory,
    allowedTransitions: canonical?.allowedTransitions ?? [],
  }
}

/**
 * Batch helper — normaliza array inteiro.
 */
export function normalizeStagesFromHook(
  stages: HookRecruitmentStage[],
): RecruitmentStage[] {
  return stages.map(normalizeStageFromHook)
}
