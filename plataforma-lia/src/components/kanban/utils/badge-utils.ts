export type BadgeType = 'sub_status' | 'pending_candidate' | 'pending_recruiter' | 'time_alert' | 'conclusion'

export interface CandidateBadge {
  type: BadgeType
  label: string
  icon: string
  color: 'gray' | 'cyan' | 'amber' | 'red' | 'green'
  priority: number
}

interface SubStatusDisplay {
  label: string
  icon: string
  color: 'gray' | 'cyan' | 'amber' | 'red' | 'green'
}

export const SUB_STATUS_DISPLAY_MAP: Record<string, SubStatusDisplay> = {
  // intake
  new: { label: 'Novo', icon: 'brain', color: 'cyan' },
  viewed: { label: 'Visualizado', icon: 'eye', color: 'gray' },
  referred: { label: 'Indicado', icon: 'user-plus', color: 'cyan' },

  // screening
  invite_sent: { label: 'Convite Enviado', icon: 'send', color: 'cyan' },
  awaiting_response: { label: 'Aguardando Resposta', icon: 'clock', color: 'amber' },
  screening_complete: { label: 'Triagem Completa', icon: 'check-circle', color: 'green' },

  // scheduling
  scheduled: { label: 'Agendada', icon: 'calendar', color: 'cyan' },
  confirmed: { label: 'Confirmada', icon: 'check-circle', color: 'green' },
  no_show: { label: 'No-show', icon: 'alert-circle', color: 'red' },

  // evaluation
  test_sent: { label: 'Teste Enviado', icon: 'file-text', color: 'cyan' },
  expired: { label: 'Expirado', icon: 'clock', color: 'red' },

  // verification
  request_sent: { label: 'Solicitação Enviada', icon: 'send', color: 'cyan' },
  awaiting: { label: 'Aguardando', icon: 'clock', color: 'amber' },
  documents_received: { label: 'Documentos Recebidos', icon: 'file-text', color: 'green' },
  verified: { label: 'Verificado', icon: 'check-circle', color: 'green' },

  // offer
  offer_prepared: { label: 'Proposta Elaborada', icon: 'file-text', color: 'gray' },
  offer_sent: { label: 'Proposta Enviada', icon: 'send', color: 'cyan' },
  under_review: { label: 'Em Análise', icon: 'loader', color: 'amber' },
  accepted: { label: 'Aceita', icon: 'check-circle', color: 'green' },
  rejected: { label: 'Recusada', icon: 'alert-circle', color: 'red' },
  counter_offer: { label: 'Contra-proposta', icon: 'alert-triangle', color: 'amber' },

  // passive
  approved_hr: { label: 'Aprovado RH', icon: 'check', color: 'green' },
  approved_technical: { label: 'Aprovado Técnico', icon: 'check', color: 'green' },
  approved_final: { label: 'Aprovado Final', icon: 'check-circle', color: 'green' },

  // conclusion_hired
  hired: { label: 'Contratado', icon: 'check-circle', color: 'green' },
  offer_accepted: { label: 'Proposta Aceita', icon: 'check-circle', color: 'green' },
  onboarding: { label: 'Em Onboarding', icon: 'loader', color: 'amber' },
  integrated: { label: 'Integrado', icon: 'check-circle', color: 'green' },

  // conclusion_rejected
  profile_inadequate: { label: 'Perfil Inadequado', icon: 'alert-circle', color: 'red' },
  rejected_screening: { label: 'Reprovado Triagem', icon: 'alert-circle', color: 'red' },
  rejected_interview: { label: 'Reprovado Entrevista', icon: 'alert-circle', color: 'red' },
  rejected_test: { label: 'Reprovado Teste', icon: 'alert-circle', color: 'red' },
  withdrew: { label: 'Desistência', icon: 'alert-triangle', color: 'amber' },
  no_response: { label: 'Sem Resposta', icon: 'clock', color: 'red' },

  // conclusion_declined
  salary: { label: 'Salário', icon: 'alert-triangle', color: 'amber' },
  benefits: { label: 'Benefícios', icon: 'alert-triangle', color: 'amber' },
  work_model: { label: 'Modelo de Trabalho', icon: 'alert-triangle', color: 'amber' },
  other_offer: { label: 'Outra Proposta', icon: 'alert-triangle', color: 'amber' },
  personal: { label: 'Motivo Pessoal', icon: 'alert-triangle', color: 'amber' },
  location: { label: 'Localização', icon: 'alert-triangle', color: 'amber' },

  // generic shared codes
  in_progress: { label: 'Em Andamento', icon: 'loader', color: 'amber' },
  completed: { label: 'Realizada', icon: 'check', color: 'green' },
}

function getPendingActionBadge(actionBehavior: string, subStatus: string): CandidateBadge | null {
  if (actionBehavior === 'screening' && subStatus === 'invite_sent') {
    return { type: 'pending_candidate', label: 'Aguardando Triagem', icon: 'clock', color: 'amber', priority: 20 }
  }
  if (actionBehavior === 'scheduling' && subStatus === 'invite_sent') {
    return { type: 'pending_candidate', label: 'Aguardando Agendamento', icon: 'clock', color: 'amber', priority: 20 }
  }
  if (actionBehavior === 'evaluation' && subStatus === 'test_sent') {
    return { type: 'pending_candidate', label: 'Aguardando Teste', icon: 'clock', color: 'amber', priority: 20 }
  }
  if (actionBehavior === 'offer' && subStatus === 'offer_sent') {
    return { type: 'pending_candidate', label: 'Aguardando Resposta', icon: 'clock', color: 'amber', priority: 20 }
  }
  return null
}

function getTimeAlertBadge(lastActionDate: string, slaHours: number): CandidateBadge | null {
  const now = new Date()
  const actionDate = new Date(lastActionDate)
  const hoursSince = (now.getTime() - actionDate.getTime()) / (1000 * 60 * 60)

  if (hoursSince > slaHours) {
    return { type: 'time_alert', label: 'Prazo excedido', icon: 'alert-circle', color: 'red', priority: 5 }
  }
  if (hoursSince > slaHours * 0.8) {
    return { type: 'time_alert', label: 'Prazo próximo', icon: 'alert-triangle', color: 'amber', priority: 8 }
  }
  return null
}

export function getCandidateBadges(params: {
  subStatus?: string
  actionBehavior?: string
  stageId?: string
  needsAction?: boolean
  lastActionDate?: string
  slaHours?: number
}): CandidateBadge[] {
  const badges: CandidateBadge[] = []

  if (params.subStatus) {
    const subStatusDisplay = SUB_STATUS_DISPLAY_MAP[params.subStatus]
    if (subStatusDisplay) {
      badges.push({
        type: 'sub_status',
        label: subStatusDisplay.label,
        icon: subStatusDisplay.icon,
        color: subStatusDisplay.color,
        priority: 10
      })
    }
  }

  if (params.actionBehavior && params.subStatus) {
    const pendingBadge = getPendingActionBadge(params.actionBehavior, params.subStatus)
    if (pendingBadge) badges.push(pendingBadge)
  }

  if (params.lastActionDate && params.slaHours) {
    const timeBadge = getTimeAlertBadge(params.lastActionDate, params.slaHours)
    if (timeBadge) badges.push(timeBadge)
  }

  return badges.sort((a, b) => a.priority - b.priority)
}
