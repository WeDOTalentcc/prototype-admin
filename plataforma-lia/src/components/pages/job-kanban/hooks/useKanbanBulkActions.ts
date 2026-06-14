"use client"

import { useCallback } from "react"
import { liaApi } from "@/services/lia-api"
import { type BulkActionType } from "@/components/ui/bulk-actions-bar"
import { type BulkActionResult, type BulkActionExecuteData } from "@/components/modals/bulk-action-modal"
import { type CommunicationType } from "@/components/modals/unified-communication-modal"
import { type KanbanCandidate } from "@/components/kanban"
import { toast } from "sonner"

export interface KanbanBulkActionsContext {
  selectedCandidates: Set<string>
  setSelectedCandidates: (value: Set<string>) => void
  allTableCandidates: KanbanCandidate[]
  setBulkActionType: (type: BulkActionType) => void
  setShowBulkActionModal: (open: boolean) => void
  setDataRequestModalCandidate: (candidate: KanbanCandidate) => void
  setShowDataRequestModal: (open: boolean) => void
  setUnifiedModalType: (type: CommunicationType) => void
  setUnifiedModalCandidate: (candidate: KanbanCandidate | null) => void
  setUnifiedModalOpen: (open: boolean) => void
  setWsiInviteCandidate: (candidate: KanbanCandidate) => void
  setShowWSIInviteModal: (open: boolean) => void
  setShowShareGestorModal: (open: boolean) => void
  setCandidatesData: (updater: (prev: Record<string, KanbanCandidate[]>) => Record<string, KanbanCandidate[]>) => void
}

export function useKanbanBulkActions(ctx: KanbanBulkActionsContext) {
  const {
    selectedCandidates,
    setSelectedCandidates,
    allTableCandidates,
    setBulkActionType,
    setShowBulkActionModal,
    setDataRequestModalCandidate,
    setShowDataRequestModal,
    setUnifiedModalType,
    setUnifiedModalCandidate,
    setUnifiedModalOpen,
    setWsiInviteCandidate,
    setShowWSIInviteModal,
    setShowShareGestorModal,
    setCandidatesData,
  } = ctx

  const handleBulkAction = useCallback((actionId: BulkActionType | string) => {
    if (selectedCandidates.size === 0) return

    switch (actionId) {
      case 'move_stage':
      case 'reject':
        setBulkActionType(actionId as BulkActionType)
        setShowBulkActionModal(true)
        break
      case 'request_data': {
        const selectedForDataRequest = allTableCandidates.filter(c => selectedCandidates.has(c.id))
        if (selectedForDataRequest.length > 0) {
          setDataRequestModalCandidate(selectedForDataRequest[0])
          setShowDataRequestModal(true)
        }
        break
      }
      case 'send_message':
        setUnifiedModalType('email')
        setUnifiedModalCandidate(null)
        setUnifiedModalOpen(true)
        break
      case 'wsi_screening': {
        const selectedForWSI = allTableCandidates.filter(c => selectedCandidates.has(c.id))
        if (selectedForWSI.length > 0) {
          setWsiInviteCandidate(selectedForWSI[0])
          setShowWSIInviteModal(true)
        }
        break
      }
      case 'share_search':
        setShowShareGestorModal(true)
        break
      default:
        toast.success("Ação em Lote", { description: `Ação "${actionId}" para ${selectedCandidates.size} candidato(s)` })
    }
  }, [
    selectedCandidates,
    allTableCandidates,
    setBulkActionType,
    setShowBulkActionModal,
    setDataRequestModalCandidate,
    setShowDataRequestModal,
    setUnifiedModalType,
    setUnifiedModalCandidate,
    setUnifiedModalOpen,
    setWsiInviteCandidate,
    setShowWSIInviteModal,
    setShowShareGestorModal,
  ])

  const handleBulkActionExecute = useCallback(async (data: BulkActionExecuteData): Promise<BulkActionResult[]> => {
    const results: BulkActionResult[] = []

    try {
      if (data.actionType === 'move_stage' && data.targetStage) {
        const apiResult = await liaApi.bulkUpdateStatus({
          candidate_ids: data.candidateIds,
          new_status: data.targetStage
        })

        const failedMap = new Map(apiResult.errors?.map((e) => [e.id, e.error_message]) || [])
        const successfulIds = data.candidateIds.filter(id => !failedMap.has(id))

        if (successfulIds.length > 0) {
          setCandidatesData(prev => {
            const newData = { ...prev }
            const movedCandidates: KanbanCandidate[] = []

            for (const candidateId of successfulIds) {
              for (const [stageId, candidates] of Object.entries(newData)) {
                const candidateIndex = candidates.findIndex((c: KanbanCandidate) => c.id === candidateId)
                if (candidateIndex !== -1) {
                  const candidate: KanbanCandidate = { ...candidates[candidateIndex], stage: data.targetStage }
                  movedCandidates.push(candidate)
                  newData[stageId] = candidates.filter((_: KanbanCandidate, i: number) => i !== candidateIndex)
                  break
                }
              }
            }

            if (movedCandidates.length > 0 && data.targetStage) {
              if (!newData[data.targetStage]) {
                newData[data.targetStage] = []
              }
              newData[data.targetStage] = [...newData[data.targetStage], ...movedCandidates]
            }

            return newData
          })
        }

        for (const candidateId of data.candidateIds) {
          if (failedMap.has(candidateId)) {
            results.push({ candidateId, success: false, error: failedMap.get(candidateId) })
          } else {
            results.push({ candidateId, success: true })
          }
        }

      } else if (data.actionType === 'reject') {
        const apiResult = await liaApi.bulkUpdateStatus({
          candidate_ids: data.candidateIds,
          new_status: 'rejected'
        })

        const failedMap = new Map(apiResult.errors?.map((e) => [e.id, e.error_message]) || [])
        const successfulIds = data.candidateIds.filter(id => !failedMap.has(id))

        if (successfulIds.length > 0) {
          setCandidatesData(prev => {
            const newData = { ...prev }
            const movedCandidates: KanbanCandidate[] = []

            for (const candidateId of successfulIds) {
              for (const [stageId, candidates] of Object.entries(newData)) {
                const candidateIndex = candidates.findIndex((c: KanbanCandidate) => c.id === candidateId)
                if (candidateIndex !== -1) {
                  const candidate: KanbanCandidate = { ...candidates[candidateIndex], stage: 'rejected' }
                  movedCandidates.push(candidate)
                  newData[stageId] = candidates.filter((_: KanbanCandidate, i: number) => i !== candidateIndex)
                  break
                }
              }
            }

            if (movedCandidates.length > 0) {
              if (!newData['rejected']) {
                newData['rejected'] = []
              }
              newData['rejected'] = [...newData['rejected'], ...movedCandidates]
            }

            return newData
          })
        }

        for (const candidateId of data.candidateIds) {
          if (failedMap.has(candidateId)) {
            results.push({ candidateId, success: false, error: failedMap.get(candidateId) })
          } else {
            results.push({ candidateId, success: true })
          }
        }

      } else if (data.actionType === 'send_message') {
        const templateId = data.message || 'default-template'
        const apiResult = await liaApi.bulkSendEmail({
          candidate_ids: data.candidateIds,
          template_id: templateId
        })

        const failedMap = new Map(apiResult.errors?.map((e) => [e.id, e.error_message]) || [])

        for (const candidateId of data.candidateIds) {
          if (failedMap.has(candidateId)) {
            results.push({ candidateId, success: false, error: failedMap.get(candidateId) })
          } else {
            results.push({ candidateId, success: true })
          }
        }

      } else if (data.actionType === 'request_data') {
        for (const candidateId of data.candidateIds) {
          try {
            results.push({ candidateId, success: true })
          } catch (error) {
            results.push({ candidateId, success: false, error: 'Erro ao solicitar dados' })
          }
        }

      } else {
        for (const candidateId of data.candidateIds) {
          results.push({ candidateId, success: true })
        }
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Erro ao processar ação em lote'
      toast.error("Erro", { description: errorMessage })

      for (const candidateId of data.candidateIds) {
        results.push({ candidateId, success: false, error: errorMessage })
      }
    }

    setSelectedCandidates(new Set())

    const successCount = results.filter(r => r.success).length
    const failCount = results.filter(r => !r.success).length

    if (successCount > 0) {
      toast.success("Ação Concluída", { description: failCount > 0
          ? `${successCount} sucesso, ${failCount} falha(s)`
          : `${successCount} candidato(s) processado(s)` })
    }

    return results
  }, [setSelectedCandidates, setCandidatesData])

  return { handleBulkAction, handleBulkActionExecute }
}
