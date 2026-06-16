import { useState, useCallback } from 'react'
import type { KanbanCandidate, DynamicStage } from '../types'

interface TransitionModalState {
  isOpen: boolean
  candidates: KanbanCandidate[]
  fromStage: string
  toStage: string
  toStageDisplayName: string
  actionBehavior: string
  subStatusOptions: Array<{ code: string; display_name: string; category?: string }>
}

export function useUniversalTransition(dynamicStages: DynamicStage[]) {
  const [modalState, setModalState] = useState<TransitionModalState>({
    isOpen: false,
    candidates: [],
    fromStage: '',
    toStage: '',
    toStageDisplayName: '',
    actionBehavior: 'passive',
    subStatusOptions: []
  })

  const openTransition = useCallback((
    candidates: KanbanCandidate[],
    fromStage: string,
    toStage: string
  ) => {
    const targetStage = dynamicStages.find(s => s.id === toStage || s.name === toStage)
    const actionBehavior = targetStage?.actionBehavior || 'passive'
    const displayName = targetStage?.displayName || toStage

    // Prefer sub-statuses from company pipeline (DB); fall back to hardcoded list
    const subStatusOptions = targetStage?.subStatuses?.length
      ? targetStage.subStatuses.map(ss => ({ code: ss.name, display_name: ss.display_name, category: ss.category }))
      : getSubStatusOptionsForBehavior(actionBehavior, toStage)

    setModalState({
      isOpen: true,
      candidates,
      fromStage,
      toStage,
      toStageDisplayName: displayName,
      actionBehavior,
      subStatusOptions
    })
  }, [dynamicStages])

  const closeTransition = useCallback(() => {
    setModalState(prev => ({ ...prev, isOpen: false }))
  }, [])

  return { modalState, openTransition, closeTransition }
}

export function getSubStatusOptionsForBehavior(actionBehavior: string, _stageId: string): Array<{ code: string; display_name: string }> {
  const behaviorSubStatuses: Record<string, Array<{ code: string; display_name: string }>> = {
    'intake': [
      { code: 'new', display_name: 'Novo' },
      { code: 'viewed', display_name: 'Visualizado' },
      { code: 'referred', display_name: 'Indicado' }
    ],
    'screening': [
      { code: 'invite_sent', display_name: 'Convite Enviado' },
      { code: 'awaiting_response', display_name: 'Aguardando Resposta' },
      { code: 'in_progress', display_name: 'Em Andamento' },
      { code: 'screening_complete', display_name: 'Triagem Completa' }
    ],
    'scheduling': [
      { code: 'invite_sent', display_name: 'Convite Enviado' },
      { code: 'scheduled', display_name: 'Agendada' },
      { code: 'confirmed', display_name: 'Confirmada' },
      { code: 'completed', display_name: 'Realizada' },
      { code: 'no_show', display_name: 'No-show' }
    ],
    'evaluation': [
      { code: 'test_sent', display_name: 'Teste Enviado' },
      { code: 'in_progress', display_name: 'Em Andamento' },
      { code: 'completed', display_name: 'Concluído' },
      { code: 'expired', display_name: 'Expirado' }
    ],
    'verification': [
      { code: 'request_sent', display_name: 'Solicitação Enviada' },
      { code: 'awaiting', display_name: 'Aguardando' },
      { code: 'documents_received', display_name: 'Documentos Recebidos' },
      { code: 'verified', display_name: 'Verificado' }
    ],
    'offer': [
      { code: 'offer_prepared', display_name: 'Proposta Elaborada' },
      { code: 'offer_sent', display_name: 'Proposta Enviada' },
      { code: 'under_review', display_name: 'Em Análise' },
      { code: 'accepted', display_name: 'Aceita' },
      { code: 'rejected', display_name: 'Recusada' },
      { code: 'counter_offer', display_name: 'Contra-proposta' }
    ],
    'passive': [
      { code: 'approved_hr', display_name: 'Aprovado RH' },
      { code: 'approved_technical', display_name: 'Aprovado Técnico' },
      { code: 'approved_final', display_name: 'Aprovado Final' }
    ],
    'conclusion_hired': [
      { code: 'offer_accepted', display_name: 'Proposta Aceita' },
      { code: 'onboarding', display_name: 'Em Onboarding' },
      { code: 'integrated', display_name: 'Integrado' }
    ],
    'conclusion_rejected': [
      { code: 'profile_inadequate', display_name: 'Perfil Inadequado' },
      { code: 'rejected_screening', display_name: 'Reprovado Triagem' },
      { code: 'rejected_interview', display_name: 'Reprovado Entrevista' },
      { code: 'rejected_test', display_name: 'Reprovado Teste' },
      { code: 'withdrew', display_name: 'Desistência' },
      { code: 'no_response', display_name: 'Sem Resposta' }
    ],
    'conclusion_declined': [
      { code: 'salary', display_name: 'Salário' },
      { code: 'benefits', display_name: 'Benefícios' },
      { code: 'work_model', display_name: 'Modelo de Trabalho' },
      { code: 'other_offer', display_name: 'Outra Proposta' },
      { code: 'personal', display_name: 'Motivo Pessoal' },
      { code: 'location', display_name: 'Localização' }
    ],
    'standby': [
      { code: 'talent_pool', display_name: 'Banco de Talentos' },
      { code: 'future_opportunity', display_name: 'Oportunidade Futura' },
      { code: 'seasonal', display_name: 'Sazonal' }
    ]
  }

  return behaviorSubStatuses[actionBehavior] || []
}
