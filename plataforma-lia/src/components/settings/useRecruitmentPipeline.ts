"use client"

import { useState } from "react"
import { RecruitmentStage } from "@/components/settings/RecruitmentJourneyConfig"
import { mapRawPipelineStage, RawPipelineStage } from "./recruitment-types"
import type { RecruitmentPersistenceState } from "./useRecruitmentPersistence"
import { apiFetch } from "@/lib/api/api-fetch"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"

export interface RecruitmentPipelineState {
  recruitmentStages: RecruitmentStage[]
  hasStageChanges: boolean
  savingStages: boolean
  isEditingPipeline: boolean
  handleStagesChange: (newStages: RecruitmentStage[]) => void
  handleStartEdit: () => void
  handleCancelEdit: () => void
  saveRecruitmentStages: () => Promise<void>
  handleToggleSubStatus: (
    subStatusId: string,
    updates: { is_active?: boolean; is_default?: boolean }
  ) => Promise<void>
}

interface PipelineHookOptions {
  persistence: RecruitmentPersistenceState
  onSuccess: (msg: string) => void
  onError: (msg: string) => void
}

export function useRecruitmentPipeline({
  persistence,
  onSuccess,
  onError,
}: PipelineHookOptions): RecruitmentPipelineState {
  const {
    recruitmentStages,
    setRecruitmentStages,
    originalStages,
    setOriginalStages,
  } = persistence

  const [hasStageChanges, setHasStageChanges] = useState(false)
  const [savingStages, setSavingStages] = useState(false)
  const [isEditingPipeline, setIsEditingPipeline] = useState(false)
  const [stagesBeforeEdit, setStagesBeforeEdit] = useState<RecruitmentStage[]>([])

  const handleStagesChange = (newStages: RecruitmentStage[]) => {
    setRecruitmentStages(newStages)
    setHasStageChanges(JSON.stringify(newStages) !== JSON.stringify(originalStages))
  }

  const handleStartEdit = () => {
    setStagesBeforeEdit([...recruitmentStages])
    setIsEditingPipeline(true)
  }

  const handleCancelEdit = () => {
    setRecruitmentStages(stagesBeforeEdit)
    setHasStageChanges(false)
    setIsEditingPipeline(false)
  }

  const saveRecruitmentStages = async () => {
    setSavingStages(true)
    try {
      const stagesPayload = recruitmentStages.map((s, idx) => ({
        id: s.id.startsWith('stage-') || s.id.startsWith('catalog-') ? undefined : s.id,
        catalog_id: s.catalog_id || undefined,
        name: s.name,
        display_name: s.display_name || s.name,
        stage_order: idx + 1,
        color: s.color,
        icon: s.icon,
        sla_hours: s.sla ? s.sla * 24 : null,
        is_active: s.isActive,
        // P1-W1-06: notes eh mapeado de/para description no backend (mapRawPipelineStage usa s.description)
        description: s.notes || '',
        action_behavior: s.action_behavior || 'passive',
        default_channel: s.default_channel || 'email',
      }))

      const response = await apiFetch('/api/backend-proxy/company-pipeline', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stages: stagesPayload }),
      })

      if (response.ok) {
        notifyChatOfSettingsUpdate({ actionId: "configure_pipeline", section: "pipeline_rules" })
        const data = await response.json()
        if (data.pipeline) {
          const updatedStages = (data.pipeline as RawPipelineStage[]).map(
            mapRawPipelineStage
          )
          setRecruitmentStages(updatedStages)
          setOriginalStages(updatedStages)
        }
        setHasStageChanges(false)
        setIsEditingPipeline(false)
        onSuccess('Pipeline salvo com sucesso!')
      } else {
        onError('Erro ao salvar pipeline. Tente novamente.')
      }
    } catch {
      onError('Erro ao salvar pipeline. Tente novamente.')
    } finally {
      setSavingStages(false)
    }
  }

  const handleToggleSubStatus = async (
    subStatusId: string,
    updates: { is_active?: boolean; is_default?: boolean }
  ): Promise<void> => {
    try {
      const response = await apiFetch(`/api/backend-proxy/recruitment-stages/sub-statuses/${subStatusId}`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updates),
        }
      )
      if (response.ok && updates.is_active !== undefined) {
        setRecruitmentStages(prev =>
          prev.map(s => {
            const sub = (s.sub_statuses || []).find(ss => ss.id === subStatusId)
            if (!sub) return s
            return {
              ...s,
              sub_statuses: updates.is_active
                ? s.sub_statuses
                : (s.sub_statuses || []).filter(ss => ss.id !== subStatusId),
            }
          })
        )
      }
    } catch {
      // Swallow — UI stays in sync with last known good state
    }
  }

  return {
    recruitmentStages,
    hasStageChanges,
    savingStages,
    isEditingPipeline,
    handleStagesChange,
    handleStartEdit,
    handleCancelEdit,
    saveRecruitmentStages,
    handleToggleSubStatus,
  }
}
