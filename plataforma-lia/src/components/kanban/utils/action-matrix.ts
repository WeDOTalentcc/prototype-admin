export interface ActionBehaviorConfig {
  label: string
  description: string
  modalType: 'screening' | 'scheduling' | 'evaluation' | 'verification' | 'offer' | 'passive' | 'conclusion'
  defaultChannel: 'email' | 'whatsapp' | 'email_whatsapp'
  allowLiaAuto: boolean
  iconName: string
  specializedModal?: string
  defaultSubStatuses: string[]
}

export const AUTHORITATIVE_ACTION_MATRIX: Record<string, ActionBehaviorConfig> = {
  intake: {
    label: 'Receber Candidato',
    description: 'IA orienta o recrutador sobre o candidato recebido',
    modalType: 'passive',
    defaultChannel: 'email',
    allowLiaAuto: true,
    iconName: 'UserPlus',
    defaultSubStatuses: ['new', 'sourced', 'applied'],
  },
  screening: {
    label: 'Convidar para Triagem WSI',
    description: 'IA conduz triagem automatizada com o candidato',
    modalType: 'screening',
    defaultChannel: 'email',
    allowLiaAuto: true,
    iconName: 'ClipboardList',
    defaultSubStatuses: ['invite_sent', 'in_progress', 'completed', 'expired'],
  },
  scheduling: {
    label: 'Abrir Agendamento',
    description: 'IA envia convite de agendamento ao candidato',
    modalType: 'scheduling',
    defaultChannel: 'email_whatsapp',
    allowLiaAuto: true,
    iconName: 'Calendar',
    specializedModal: 'SchedulingModal',
    defaultSubStatuses: ['invite_sent', 'confirmed', 'rescheduled', 'no_show', 'completed'],
  },
  evaluation: {
    label: 'Enviar Teste',
    description: 'IA envia teste técnico ou avaliação',
    modalType: 'evaluation',
    defaultChannel: 'email',
    allowLiaAuto: true,
    iconName: 'FileText',
    defaultSubStatuses: ['test_sent', 'in_progress', 'completed', 'expired'],
  },
  verification: {
    label: 'Solicitar Documentos',
    description: 'IA solicita documentos necessários',
    modalType: 'verification',
    defaultChannel: 'email',
    allowLiaAuto: true,
    iconName: 'FileText',
    defaultSubStatuses: ['request_sent', 'partial', 'completed', 'pending_review'],
  },
  offer: {
    label: 'Enviar Proposta',
    description: 'Preparar e enviar proposta salarial',
    modalType: 'offer',
    defaultChannel: 'email',
    allowLiaAuto: true,
    iconName: 'Gift',
    specializedModal: 'ProposalModal',
    defaultSubStatuses: ['offer_sent', 'under_review', 'negotiating', 'accepted', 'declined'],
  },
  passive: {
    label: 'Mover Candidato',
    description: 'IA orienta sobre a movimentação do candidato',
    modalType: 'passive',
    defaultChannel: 'email',
    allowLiaAuto: true,
    iconName: 'ArrowRight',
    defaultSubStatuses: ['moved', 'awaiting'],
  },
  standby: {
    label: 'Mover para Stand By',
    description: 'IA registra candidato no banco de talentos',
    modalType: 'passive',
    defaultChannel: 'email',
    allowLiaAuto: true,
    iconName: 'ArrowRight',
    defaultSubStatuses: ['talent_pool', 'future_opportunity', 'seasonal'],
  },
  conclusion_hired: {
    label: 'Confirmar Contratação',
    description: 'IA envia boas-vindas e próximos passos ao candidato',
    modalType: 'conclusion',
    defaultChannel: 'email',
    allowLiaAuto: true,
    iconName: 'CheckCircle',
    defaultSubStatuses: ['hired', 'onboarding'],
  },
  conclusion_rejected: {
    label: 'Reprovar Candidato',
    description: 'Candidato não aprovado no processo',
    modalType: 'conclusion',
    defaultChannel: 'email',
    allowLiaAuto: true,
    iconName: 'XCircle',
    defaultSubStatuses: ['profile_not_aligned', 'insufficient_technical_skills', 'another_candidate_selected', 'cultural_fit', 'overqualified', 'underqualified', 'candidate_withdrew'],
  },
  conclusion_declined: {
    label: 'Proposta Recusada',
    description: 'IA envia agradecimento e mantém porta aberta',
    modalType: 'conclusion',
    defaultChannel: 'email',
    allowLiaAuto: true,
    iconName: 'XCircle',
    defaultSubStatuses: ['salary', 'benefits', 'counter_offer', 'personal_reasons', 'other_opportunity'],
  },
}

export function getActionConfig(actionBehavior: string): ActionBehaviorConfig {
  return AUTHORITATIVE_ACTION_MATRIX[actionBehavior] || AUTHORITATIVE_ACTION_MATRIX['passive']
}

export function getDefaultChannel(actionBehavior: string): string {
  return getActionConfig(actionBehavior).defaultChannel
}

export function isLiaAutoAllowed(actionBehavior: string): boolean {
  return getActionConfig(actionBehavior).allowLiaAuto
}

export function getModalType(actionBehavior: string): string {
  return getActionConfig(actionBehavior).modalType
}
