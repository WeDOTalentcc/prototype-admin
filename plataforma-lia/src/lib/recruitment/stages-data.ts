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
