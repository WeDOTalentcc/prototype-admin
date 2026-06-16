import type { DynamicStage } from "./types"

export const DYNAMIC_STAGE_COLORS = [
  'var(--lia-text-secondary)', // gray-700
  'var(--lia-text-secondary)', // gray-600
  'var(--lia-text-tertiary)', // gray-500
  'var(--lia-text-tertiary)', // gray-400
  'var(--lia-text-tertiary)', // gray-500
  'var(--lia-text-secondary)', // gray-600
  'var(--lia-text-secondary)', // gray-700
] as const

export const SYSTEM_INITIAL_STAGES: DynamicStage[] = [
  {
    id: 'sourcing',
    name: 'sourcing',
    displayName: 'Funil',
    order: 0,
    color: 'var(--lia-text-secondary)',
    stageType: 'active',
    isInitial: true,
    actionBehavior: 'intake'
  },
  {
    id: 'screening',
    name: 'screening',
    displayName: 'Triagem',
    order: 1,
    color: 'var(--lia-text-secondary)',
    stageType: 'active',
    isInitial: false,
    actionBehavior: 'screening'
  }
]

export const SYSTEM_FINAL_STAGES: DynamicStage[] = [
  {
    id: 'hired',
    name: 'hired',
    displayName: 'Contratado',
    order: 900,
    color: 'var(--lia-text-secondary)',
    stageType: 'final',
    isFinal: true,
    isHired: true,
    actionBehavior: 'conclusion_hired'
  },
  {
    id: 'rejected',
    name: 'rejected',
    displayName: 'Reprovado',
    order: 901,
    color: 'var(--lia-text-tertiary)',
    stageType: 'final',
    isFinal: true,
    isRejection: true,
    actionBehavior: 'conclusion_rejected'
  },
  {
    id: 'offer_declined',
    name: 'offer_declined',
    displayName: 'Proposta Recusada',
    order: 902,
    color: 'var(--lia-text-tertiary)',
    stageType: 'final',
    isFinal: true,
    actionBehavior: 'conclusion_declined'
  }
]

export const STAGES_REQUIRING_CONFIRMATION = ['hired', 'rejected', 'offer_declined'] as const

export const ACTION_BEHAVIOR_MODALS: Record<string, string> = {
  'screening': 'wsi-triagem-invite',
  'scheduling': 'scheduling',
  'evaluation': 'evaluation-send',
  'verification': 'data-request',
  'offer': 'offer-send',
  'conclusion_hired': 'decision-flow',
  'conclusion_rejected': 'decision-flow',
  'conclusion_declined': 'decision-flow',
  'rejection_feedback': 'rejection-feedback',
}

export const LEGACY_STAGE_MAPPING: Record<string, string> = {
  'funil': 'sourcing',
  'triagem': 'screening',
  'entrevista': 'interview_hr',
  'entrevista_rh': 'interview_hr',
  'entrevista_tecnica': 'interview_technical',
  'entrevista_gestor': 'interview_manager',
  'final': 'offer',
  'proposta': 'offer',
  'aprovados': 'hired',
  'contratado': 'hired',
  'reprovados': 'rejected',
  'reprovado': 'rejected',
  'proposta_recusada': 'offer_declined'
}

export const DEFAULT_SUB_STATUS_SUGGESTIONS: Record<string, string> = {
  hired: 'onboarding_scheduled',
  rejected: 'another_candidate_selected',
  offer_declined: 'accepted_other_offer',
  screening: 'cv_received',
  long_list: 'added_to_long_list',
  short_list: 'added_to_short_list',
  interview_hr: 'awaiting_hr_schedule',
  interview_technical: 'awaiting_technical_schedule',
  interview_manager: 'awaiting_manager1_schedule',
  interview_final: 'awaiting_final_schedule',
  offer: 'preparing_offer',
  references: 'references_requested',
}

export const SALARY_RANGES = {
  junior: { min: 3000, max: 6000 },
  pleno: { min: 6000, max: 12000 },
  senior: { min: 12000, max: 25000 },
  specialist: { min: 18000, max: 35000 },
  lead: { min: 20000, max: 40000 },
}
