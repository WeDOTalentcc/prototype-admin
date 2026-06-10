"use client"

import { useCallback } from "react"
import { type UniversalTransitionConfirmData } from "@/components/kanban"
import { toast } from "sonner"

interface UseKanbanTransitionsParams {
  candidatesData: Record<string, Record<string, unknown>[]>
  setCandidatesData: (fn: (prev: Record<string, Record<string, unknown>[]>) => Record<string, Record<string, unknown>[]>) => void
  universalModalState: { candidates: Array<Record<string, unknown>>; actionBehavior?: string }
  closeTransition: () => void
}

export function useKanbanTransitions({
  candidatesData,
  setCandidatesData,
  universalModalState,
  closeTransition,
}: UseKanbanTransitionsParams) {
  const handleUniversalTransitionConfirm = useCallback(async (data: UniversalTransitionConfirmData) => {
    try {
      const dispatchSummary: { sent: number; failed: number; channel?: string; mock?: boolean; aiPersonalized?: boolean } = { sent: 0, failed: 0 }

      for (const candidateId of data.candidateIds) {
        const candidateSubStatus = data.perCandidateSubStatus?.[candidateId] || data.subStatus
        const response = await fetch('/api/backend-proxy/transition/execute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            vacancy_candidate_id: candidateId,
            to_stage: data.toStage,
            sub_status: candidateSubStatus,
            action: data.action,
            prompt: data.prompt,
            channel: data.channel || 'email',
            action_behavior: data.actionBehavior || universalModalState.actionBehavior,
            extracted_preferences: data.extracted_preferences || undefined,
            // AUD-4: o clique "Confirmar" do modal de transicao E a aprovacao humana (HITL).
            // Com LIA_HITL_GATE on, libera o dispatch; chamadas nao-confirmadas ao endpoint ficam bloqueadas.
            hitl_approved: true,
          })
        })
        const result = await response.json()
        if (result.dispatch_results?.length) {
          for (const dr of result.dispatch_results) {
            if (dr.success) {
              dispatchSummary.sent++
              dispatchSummary.channel = dr.channel
              dispatchSummary.mock = dr.mock
              if (dr.ai_personalized) dispatchSummary.aiPersonalized = true
            } else {
              dispatchSummary.failed++
            }
          }
        }
        setCandidatesData(prev => {
          const newData = { ...prev }
          for (const key of Object.keys(newData)) {
            newData[key] = (newData[key] as Record<string, unknown>[]).filter((c: Record<string, unknown>) => c.id !== candidateId)
          }
          if (!newData[data.toStage]) newData[data.toStage] = []
          const existingCandidate = Object.values(prev).flat().find((c: Record<string, unknown>) => c.id === candidateId)
          newData[data.toStage] = [...newData[data.toStage], {
            ...existingCandidate,
            id: candidateId,
            name: existingCandidate?.name || (data.candidateIds.length === 1 ? (universalModalState.candidates[0]?.name || '') : ''),
            stage: data.toStage,
            sub_status: data.perCandidateSubStatus?.[candidateId] || data.subStatus,
            stageId: data.toStage,
            actionBehavior: data.actionBehavior || universalModalState.actionBehavior,
            needsAction: data.action !== 'just_move',
          }]
          return newData
        })
      }

      closeTransition()

      if (dispatchSummary.sent > 0) {
        const channelLabel = dispatchSummary.channel === 'whatsapp' ? 'WhatsApp' : 'e-mail'
        const mockNote = dispatchSummary.mock ? ' (modo simulação)' : ''
        const aiNote = dispatchSummary.aiPersonalized ? ' (personalizada por IA)' : ''
        toast.success('Transição realizada com envio automático', { description: `${data.candidateIds.length} candidato(s) movido(s). ${dispatchSummary.sent} ${channelLabel}(s) enviado(s)${aiNote}${mockNote}.${dispatchSummary.failed > 0 ? ` ${dispatchSummary.failed} falha(s).` : ''}` })
      } else {
        toast.success('Transição realizada', { description: `${data.candidateIds.length} candidato(s) movido(s) com sucesso.` })
      }
    } catch {
      toast.error('Erro na transição', { description: 'Não foi possível completar a transição.' })
    }
  }, [closeTransition, universalModalState.candidates, setCandidatesData, universalModalState.actionBehavior])

  return { handleUniversalTransitionConfirm }
}
