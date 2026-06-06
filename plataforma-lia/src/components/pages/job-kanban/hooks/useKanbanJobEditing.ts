"use client"

import { useCallback } from "react"
import type React from "react"
import { liaApi } from "@/services/lia-api"
import type { DynamicStage } from "../utils/kanbanStageUtils"
import type { InterviewStageFromJob } from "../utils/kanbanStageUtils"
import { toast } from "sonner"

interface KanbanJobRef {
  id?: string | number
  jobId?: string
  backendId?: string
  interviewStages?: InterviewStageFromJob[]
  [key: string]: unknown
}

export interface KanbanJobEditingContext {
  currentJob: KanbanJobRef
  jobEditForm: Record<string, unknown>
  setSavingJobSection: (section: string | null) => void
  setEditingSection: (section: string | null) => void
  setDynamicStages: React.Dispatch<React.SetStateAction<DynamicStage[]>>
  setCandidatesData: (updater: (prev: Record<string, Record<string, unknown>[]>) => Record<string, Record<string, unknown>[]>) => void
  mapInterviewStagesToKanban: (interviewStages?: InterviewStageFromJob[]) => DynamicStage[]
  createInitialCandidatesData: (stages: DynamicStage[]) => Record<string, Record<string, unknown>[]>
}

export function useKanbanJobEditing(ctx: KanbanJobEditingContext) {
  const {
    currentJob,
    jobEditForm,
    setSavingJobSection,
    setEditingSection,
    setDynamicStages,
    setCandidatesData,
    mapInterviewStagesToKanban,
    createInitialCandidatesData,
  } = ctx

  const handleSaveJobSection = async (sectionId: string, fields: string[]) => {
    if (!currentJob) return
    setSavingJobSection(sectionId)
    try {
      const fieldMapping: Record<string, string> = {
        title: 'title', department: 'department', location: 'location',
        workModel: 'work_model', type: 'employment_type', seniority: 'seniority_level',
        status: 'status', urgencyLevel: 'urgency_level',
        recruiter: 'recruiter', recruiterEmail: 'recruiter_email',
        manager: 'hiring_manager', managerEmail: 'hiring_manager_email',
        openDate: 'open_date', deadline: 'deadline',
        deadlineScreening: 'deadline_screening', deadlineShortlist: 'deadline_shortlist',
        deadlineClosing: 'deadline_closing',
        benefits: 'benefits', targetAudience: 'target_audience',
        targetSector: 'target_sector', targetSegment: 'target_segment',
        languages: 'languages', visibility: 'visibility',
        publishedLinkedIn: 'published_linkedin', publishedWebsite: 'published_website',
        publishedIndeed: 'published_indeed',
        isConfidential: 'is_confidential', maskedCompanyName: 'masked_company_name',
        isAffirmative: 'is_affirmative',
        affirmativeCriteriaPrimary: 'affirmative_criteria_primary',
        affirmativeCriteriaSecondary: 'affirmative_criteria_secondary',
        affirmativeDescription: 'affirmative_description',
        affirmativeDocumentRequired: 'affirmative_document_required',
        affirmativeDocumentTypes: 'affirmative_document_types',
        priority: 'priority',
        description: 'description',
        interviewStages: 'interview_stages',
      }
      const updates: Record<string, unknown> = {}
      fields.forEach(f => {
        if (f === 'salaryMin' || f === 'salaryMax') {
          if (!updates['salary_range']) {
            updates['salary_range'] = {
              min: jobEditForm.salaryMin ? Number(jobEditForm.salaryMin) : null,
              max: jobEditForm.salaryMax ? Number(jobEditForm.salaryMax) : null,
              currency: 'BRL',
              undisclosed: !!jobEditForm.salaryUndisclosed
            }
          }
          return
        }
        if (f === 'bonusMin' || f === 'bonusMax') {
          if (!updates['bonus_range']) {
            updates['bonus_range'] = {
              min: jobEditForm.bonusMin ? Number(jobEditForm.bonusMin) : null,
              max: jobEditForm.bonusMax ? Number(jobEditForm.bonusMax) : null,
              currency: 'BRL'
            }
          }
          return
        }
        updates[fieldMapping[f] || f] = jobEditForm[f]
      })
      const jobId = currentJob.backendId || currentJob.jobId || currentJob.id
      await liaApi.updateJobVacancy(String(jobId), updates)
      if (fields.includes('interviewStages') && (jobEditForm as Record<string, unknown>).interviewStages) {
        const newStages = mapInterviewStagesToKanban((jobEditForm as Record<string, unknown>).interviewStages as unknown as InterviewStageFromJob[])
        setDynamicStages(newStages)
        setCandidatesData(prev => {
          const newData = createInitialCandidatesData(newStages)
          Object.keys(prev).forEach(stageId => {
            const candidates = prev[stageId] || []
            if (newData[stageId]) {
              newData[stageId] = [...candidates]
            } else {
              newData['sourcing'] = [...(newData['sourcing'] || []), ...candidates]
            }
          })
          return newData
        })
      }
      toast.success('Seção salva com sucesso!')
      setEditingSection(null)
    } catch (error) {
      toast.error('Erro ao salvar. Tente novamente.')
    } finally {
      setSavingJobSection(null)
    }
  }

  const handleInlineRename = useCallback(async (stageId: string, newName: string) => {
    try {
      await fetch(`/api/backend-proxy/recruitment-stages/stages/${stageId}/inline-edit`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ display_name: newName }),
      })
      setDynamicStages(prev => prev.map(s => s.id === stageId ? { ...s, displayName: newName } : s))
      toast.success('Etapa renomeada', { description: `Nome atualizado para "${newName}".` })
    } catch {
      toast.error('Erro ao renomear', { description: 'Nao foi possivel renomear a etapa.' })
    }
  }, [setDynamicStages])

  const handleInlineToggleActive = useCallback(async (stageId: string, isActive: boolean) => {
    try {
      await fetch(`/api/backend-proxy/recruitment-stages/stages/${stageId}/inline-edit`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: isActive }),
      })
      if (!isActive) {
        setDynamicStages(prev => prev.filter(s => s.id !== stageId))
      } else {
        setDynamicStages(prev => prev.map(s => s.id === stageId ? { ...s, isActive } : s))
      }
      toast.success(isActive ? 'Etapa ativada' : 'Etapa desativada')
    } catch {
      toast.error('Erro', { description: 'Nao foi possivel alterar o status da etapa.' })
    }
  }, [setDynamicStages])

  const handleInlineRemove = useCallback(async (stageId: string) => {
    try {
      await fetch(`/api/backend-proxy/recruitment-stages/stages/${stageId}/remove`, {
        method: 'DELETE',
      })
      setDynamicStages(prev => prev.filter(s => s.id !== stageId))
      toast.success('Coluna removida')
    } catch {
      toast.error('Erro ao remover', { description: 'Nao foi possivel remover a coluna.' })
    }
  }, [setDynamicStages])

  const handleInlineMove = useCallback(async (stageId: string, direction: -1 | 1) => {
    setDynamicStages(prev => {
      const idx = prev.findIndex(s => s.id === stageId)
      const targetIdx = idx + direction
      if (idx < 0 || targetIdx < 0 || targetIdx >= prev.length) return prev
      const newStages = [...prev]
      const temp = newStages[idx]
      newStages[idx] = newStages[targetIdx]
      newStages[targetIdx] = temp
      const reordered = newStages.map((s, i) => ({ ...s, order: i }))
      fetch(`/api/backend-proxy/recruitment-stages/stages/reorder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stages: reordered.map(s => ({ stage_id: s.id, new_order: s.order })) }),
      }).catch((err) => { console.warn('[useKanbanJobEditing] stages reorder fire-and-forget failed', err) })
      return reordered
    })
  }, [setDynamicStages])

  const handleInlineMoveLeft = useCallback((stageId: string) => handleInlineMove(stageId, -1), [handleInlineMove])
  const handleInlineMoveRight = useCallback((stageId: string) => handleInlineMove(stageId, 1), [handleInlineMove])

  const handleInlineUpdateSLA = useCallback(async (stageId: string, slaHours: number) => {
    try {
      await fetch(`/api/backend-proxy/recruitment-stages/stages/${stageId}/inline-edit`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sla_hours: slaHours }),
      })
      toast.success('SLA atualizado', { description: `SLA definido para ${slaHours} horas.` })
    } catch {
      toast.error('Erro ao atualizar SLA')
    }
  }, [])

  return {
    handleSaveJobSection,
    handleInlineRename,
    handleInlineToggleActive,
    handleInlineRemove,
    handleInlineMoveLeft,
    handleInlineMoveRight,
    handleInlineUpdateSLA,
  }
}
