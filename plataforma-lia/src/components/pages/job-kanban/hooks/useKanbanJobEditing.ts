"use client"

import { useCallback } from "react"
import type React from "react"
import { useToast } from "@/hooks/use-toast"
import { liaApi } from "@/services/lia-api"

export interface KanbanJobEditingContext {
  toast: ReturnType<typeof useToast>["toast"]
  currentJob: any
  jobEditForm: Record<string, any>
  setSavingJobSection: (section: string | null) => void
  setEditingSection: (section: string | null) => void
  setDynamicStages: React.Dispatch<React.SetStateAction<any[]>>
  setCandidatesData: (updater: (prev: Record<string, any[]>) => Record<string, any[]>) => void
  mapInterviewStagesToKanban: (interviewStages?: any[]) => any[]
  createInitialCandidatesData: (stages: any[]) => Record<string, any[]>
}

export function useKanbanJobEditing(ctx: KanbanJobEditingContext) {
  const {
    toast,
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
        workModel: 'work_model', type: 'employment_type', level: 'seniority_level',
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
      const updates: Record<string, any> = {}
      fields.forEach(f => {
        if (f === 'salaryMin' || f === 'salaryMax') {
          if (!updates['salary_range']) {
            updates['salary_range'] = {
              min: jobEditForm.salaryMin ? Number(jobEditForm.salaryMin) : null,
              max: jobEditForm.salaryMax ? Number(jobEditForm.salaryMax) : null,
              currency: 'BRL'
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
      await liaApi.updateJobVacancy(jobId, updates)
      if (fields.includes('interviewStages') && jobEditForm.interviewStages) {
        const newStages = mapInterviewStagesToKanban(jobEditForm.interviewStages)
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
      toast({ title: 'Seção salva com sucesso!' })
      setEditingSection(null)
    } catch (error) {
      toast({ title: 'Erro ao salvar. Tente novamente.', variant: 'destructive' })
    } finally {
      setSavingJobSection(null)
    }
  }

  const handleInlineRename = useCallback(async (stageId: string, newName: string) => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || ''
      await fetch(`${baseUrl}/api/v1/recruitment-stages/stages/${stageId}/inline-edit`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ display_name: newName }),
      })
      setDynamicStages(prev => prev.map(s => s.id === stageId ? { ...s, displayName: newName } : s))
      toast({ title: 'Etapa renomeada', description: `Nome atualizado para "${newName}".` })
    } catch {
      toast({ title: 'Erro ao renomear', description: 'Nao foi possivel renomear a etapa.', variant: 'destructive' })
    }
  }, [toast, setDynamicStages])

  const handleInlineToggleActive = useCallback(async (stageId: string, isActive: boolean) => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || ''
      await fetch(`${baseUrl}/api/v1/recruitment-stages/stages/${stageId}/inline-edit`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: isActive }),
      })
      if (!isActive) {
        setDynamicStages(prev => prev.filter(s => s.id !== stageId))
      } else {
        setDynamicStages(prev => prev.map(s => s.id === stageId ? { ...s, isActive } : s))
      }
      toast({ title: isActive ? 'Etapa ativada' : 'Etapa desativada' })
    } catch {
      toast({ title: 'Erro', description: 'Nao foi possivel alterar o status da etapa.', variant: 'destructive' })
    }
  }, [toast, setDynamicStages])

  const handleInlineRemove = useCallback(async (stageId: string) => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || ''
      await fetch(`${baseUrl}/api/v1/recruitment-stages/stages/${stageId}/remove`, {
        method: 'DELETE',
      })
      setDynamicStages(prev => prev.filter(s => s.id !== stageId))
      toast({ title: 'Coluna removida' })
    } catch {
      toast({ title: 'Erro ao remover', description: 'Nao foi possivel remover a coluna.', variant: 'destructive' })
    }
  }, [toast, setDynamicStages])

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
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || ''
      fetch(`${baseUrl}/api/v1/recruitment-stages/stages/reorder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stages: reordered.map(s => ({ stage_id: s.id, new_order: s.order })) }),
      }).catch(() => {})
      return reordered
    })
  }, [setDynamicStages])

  const handleInlineMoveLeft = useCallback((stageId: string) => handleInlineMove(stageId, -1), [handleInlineMove])
  const handleInlineMoveRight = useCallback((stageId: string) => handleInlineMove(stageId, 1), [handleInlineMove])

  const handleInlineUpdateSLA = useCallback(async (stageId: string, slaHours: number) => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || ''
      await fetch(`${baseUrl}/api/v1/recruitment-stages/stages/${stageId}/inline-edit`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sla_hours: slaHours }),
      })
      toast({ title: 'SLA atualizado', description: `SLA definido para ${slaHours} horas.` })
    } catch {
      toast({ title: 'Erro ao atualizar SLA', variant: 'destructive' })
    }
  }, [toast])

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
