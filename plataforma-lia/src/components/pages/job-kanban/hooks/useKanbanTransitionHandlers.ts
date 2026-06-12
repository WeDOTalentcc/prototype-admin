"use client"

import { useCallback } from "react"
import { type KanbanCandidate } from "@/components/kanban"

interface UseKanbanTransitionHandlersProps {
  openTransition: (candidates: KanbanCandidate[], from: string, to: string) => void
  closeTransition: () => void
  setTransitionInitialPrompt: (p: string) => void
  setTransitionAllowStageSelection: (v: boolean) => void
  setTransitionInterviewAlert: (a: { name: string; date: string } | null) => void
  // Modal setters used by handleOpenSpecializedModal
  setWsiInviteCandidate: (c: unknown) => void
  setShowWSIInviteModal: (v: boolean) => void
  setUnifiedModalCandidate: (c: unknown) => void
  setUnifiedModalType: (t: string) => void
  setUnifiedModalSituation: (s: string | undefined) => void
  setUnifiedModalOpen: (v: boolean) => void
  setDataRequestModalCandidate: (c: unknown) => void
  setShowDataRequestModal: (v: boolean) => void
  setDecisionFlowCandidate: (c: unknown) => void
  setDecisionFlowType: (t: string) => void
  setShowDecisionFlowModal: (v: boolean) => void
}

export function useKanbanTransitionHandlers({
  openTransition,
  closeTransition,
  setTransitionInitialPrompt,
  setTransitionAllowStageSelection,
  setTransitionInterviewAlert,
  setWsiInviteCandidate,
  setShowWSIInviteModal,
  setUnifiedModalCandidate,
  setUnifiedModalType,
  setUnifiedModalSituation,
  setUnifiedModalOpen,
  setDataRequestModalCandidate,
  setShowDataRequestModal,
  setDecisionFlowCandidate,
  setDecisionFlowType,
  setShowDecisionFlowModal,
}: UseKanbanTransitionHandlersProps) {

  const handleTransitionRequired = useCallback((
    candidates: KanbanCandidate[],
    fromStage: string,
    toStage: string
  ) => {
    const isFromInterview = (fromStage || '').toLowerCase().includes('interview') || (fromStage || '').toLowerCase().includes('entrevista')
    const candidateWithInterview = candidates.find(c => c.agendada)

    if (isFromInterview && candidateWithInterview) {
      const c = candidateWithInterview
      const dateStr = (c.interviewDate as string | undefined) || new Date(c.agendada as string).toLocaleDateString('pt-BR', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })
      setTransitionInitialPrompt(
        `O recrutador está movendo ${c.name as string} da etapa de entrevista. Este candidato tem uma entrevista agendada para ${dateStr}. Isso significa cancelar a entrevista? Ou prefere alterar o horário e mantê-lo na entrevista? Pergunte e aguarde a resposta do recrutador.`
      )
      setTransitionAllowStageSelection(true)
      setTransitionInterviewAlert({ name: c.name as string, date: dateStr })
    }

    openTransition(candidates, fromStage, toStage)
  }, [openTransition, setTransitionInitialPrompt, setTransitionAllowStageSelection, setTransitionInterviewAlert])

  const handleOpenSpecializedModal = useCallback((
    modalType: string,
    context: { candidates?: Record<string, unknown>[]; toStage?: string; [key: string]: unknown }
  ) => {
    switch (modalType) {
      case 'wsi-triagem-invite':
        if ((context.candidates ?? []).length > 0) {
          setWsiInviteCandidate(context.candidates![0])
          setShowWSIInviteModal(true)
        }
        break
      case 'scheduling':
        if ((context.candidates ?? []).length > 0) {
          setUnifiedModalCandidate(context.candidates![0])
          setUnifiedModalType('agendamento')
          setUnifiedModalSituation('agendamento')
          setUnifiedModalOpen(true)
        }
        break
      case 'data-request':
        if ((context.candidates ?? []).length > 0) {
          setDataRequestModalCandidate(context.candidates![0])
          setShowDataRequestModal(true)
        }
        break
      case 'decision-flow':
        if ((context.candidates ?? []).length > 0) {
          const candidate = context.candidates![0]
          setDecisionFlowCandidate(candidate)
          setDecisionFlowType(context.toStage === 'hired' ? 'confirm_hire' : 'reject_pre_triage')
          setShowDecisionFlowModal(true)
        }
        break
      case 'rejection-feedback':
        if ((context.candidates ?? []).length > 0) {
          const _c0 = context.candidates![0] as Record<string, unknown>
          // FE-2b: carrega o contexto para o modal pre-preencher o feedback via IA
          // (preview-feedback). Read-only ate o recrutador enviar; sem mover aqui.
          setUnifiedModalCandidate({
            ..._c0,
            _aiFeedbackContext: {
              vacancyCandidateId: _c0.id,
              toStage: (context.toStage as string) || 'rejected',
              subStatus: (context.subStatus as string | undefined) ?? null,
            },
          })
          setUnifiedModalType('feedback')
          setUnifiedModalSituation('feedback_construtivo')
          setUnifiedModalOpen(true)
        }
        break
      case 'evaluation-send':
        if ((context.candidates ?? []).length > 0) {
          setUnifiedModalCandidate(context.candidates![0])
          setUnifiedModalType('email')
          setUnifiedModalSituation('avaliacao_tecnica')
          setUnifiedModalOpen(true)
        }
        break
      case 'offer-send':
        if ((context.candidates ?? []).length > 0) {
          setUnifiedModalCandidate(context.candidates![0])
          setUnifiedModalType('email')
          setUnifiedModalSituation('proposta')
          setUnifiedModalOpen(true)
        }
        break
      default:
    }
    closeTransition()
  }, [
    closeTransition,
    setWsiInviteCandidate, setShowWSIInviteModal,
    setUnifiedModalCandidate, setUnifiedModalType, setUnifiedModalSituation, setUnifiedModalOpen,
    setDataRequestModalCandidate, setShowDataRequestModal,
    setDecisionFlowCandidate, setDecisionFlowType, setShowDecisionFlowModal,
  ])

  return {
    handleTransitionRequired,
    handleOpenSpecializedModal,
  }
}
