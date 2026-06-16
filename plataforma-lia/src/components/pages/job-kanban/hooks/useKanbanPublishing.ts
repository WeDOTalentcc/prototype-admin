"use client"

import { useState, useEffect, useCallback } from "react"
import { liaApi } from "@/services/lia-api"
import { toast } from "sonner"
import { useJobUIStore } from "@/stores/job-ui-store"

interface UseKanbanPublishingProps {
  job?: Record<string, unknown>
  jobEditForm: Record<string, unknown>
  setJobEditForm: React.Dispatch<React.SetStateAction<Record<string, unknown>>>
  setActiveTab: (tab: "management" | "edit") => void
}

export function useKanbanPublishing({
  job,
  jobEditForm,
  setJobEditForm,
  setActiveTab,
}: UseKanbanPublishingProps) {
  const [isCreationMode, setIsCreationMode] = useState(false)
  const [isPublishing, setIsPublishing] = useState(false)
  const [publicLink, setPublicLink] = useState<string | null>(null)
  const [showPublishSuccess, setShowPublishSuccess] = useState(false)

  const consumeJobCreationMode = useJobUIStore(s => s.consumeJobCreationMode)

  useEffect(() => {
    if (!job?.backendId) return
    if (consumeJobCreationMode(job.backendId as string)) {
      setIsCreationMode(true)
      setActiveTab("edit")
    }
  }, [job?.backendId, setActiveTab, consumeJobCreationMode])

  const handlePublishJob = useCallback(async () => {
    const vacancyId = job?.backendId as string | undefined
    if (!vacancyId) return

    setIsPublishing(true)
    try {
      // Auto-salva o formulário antes de publicar
      const fieldMapping: Record<string, string> = {
        title: 'title', department: 'department', location: 'location',
        workModel: 'work_model', type: 'employment_type', seniority: 'seniority_level',
        urgencyLevel: 'urgency_level', priority: 'priority',
        recruiter: 'recruiter', recruiterEmail: 'recruiter_email',
        manager: 'hiring_manager', managerEmail: 'hiring_manager_email',
        openDate: 'open_date', deadline: 'deadline',
        deadlineScreening: 'deadline_screening', deadlineShortlist: 'deadline_shortlist',
        deadlineClosing: 'deadline_closing',
        benefits: 'benefits', description: 'description',
        targetAudience: 'target_audience', targetSector: 'target_sector',
        visibility: 'visibility', isConfidential: 'is_confidential',
        isAffirmative: 'is_affirmative', languages: 'languages',
      }
      const autoSavePayload: Record<string, unknown> = {}
      Object.entries(fieldMapping).forEach(([formKey, apiKey]) => {
        const val = jobEditForm[formKey]
        if (val !== undefined && val !== '' && val !== null) {
          autoSavePayload[apiKey] = val
        }
      })
      if (jobEditForm.salaryMin || jobEditForm.salaryMax) {
        autoSavePayload['salary_range'] = {
          min: jobEditForm.salaryMin ? Number(jobEditForm.salaryMin) : null,
          max: jobEditForm.salaryMax ? Number(jobEditForm.salaryMax) : null,
          currency: 'BRL',
        }
      }
      if (Object.keys(autoSavePayload).length > 0) {
        await liaApi.updateJobVacancy(vacancyId, autoSavePayload)
      }

      const linkResult = await liaApi.generatePublicLink(vacancyId)

      await liaApi.updateJobVacancy(vacancyId, { status: "Ativa" } as Record<string, unknown>)

      setPublicLink(linkResult.public_url)
      setShowPublishSuccess(true)
      setIsCreationMode(false)

      setJobEditForm((prev: Record<string, unknown>) => ({
        ...prev,
        status: "Ativa",
        public_url: linkResult.public_url,
      }))

      toast.success("Vaga publicada!", { description: "A vaga está ativa e o link de candidatura foi gerado." })
    } catch (error: unknown) {
      const detail = error instanceof Error ? error.message : "Erro desconhecido"
      toast.error("Erro ao publicar", { description: `Não foi possível publicar a vaga: ${detail}` })
    } finally {
      setIsPublishing(false)
    }
  }, [job?.backendId, jobEditForm, setJobEditForm])

  return {
    isCreationMode, setIsCreationMode,
    isPublishing, setIsPublishing,
    publicLink, setPublicLink,
    showPublishSuccess, setShowPublishSuccess,
    handlePublishJob,
  }
}
