"use client"

import { useState, useEffect } from "react"
import { liaApi } from "@/services/lia-api"
import { archiveJobs, unarchiveJobs } from "@/services/lia-api/jobs-api"
import { toast } from "sonner"
import type { Job } from "@/components/jobs"

// ---------------------------------------------------------------------------
// useJobsBulkActions
// Responsável por: seleção em massa de vagas, ações de linha (pin/urgente/fav),
// modais de ação em massa (comparar, publicar, despublicar, insights, duplicar,
// pausar/ativar status, atribuir recrutador), lista de recrutadores da empresa.
// ---------------------------------------------------------------------------

interface UseJobsBulkActionsOptions {
  allJobs: Job[]
  filteredJobs: Job[]
  setBackendJobs: React.Dispatch<React.SetStateAction<Job[]>>
}

interface UseJobsBulkActionsReturn {
  state: {
    selectedJobsForBatch: Set<number>
    pinnedJobs: Set<number>
    urgentJobs: Set<number>
    favoriteJobs: Set<number>
    showCompareModal: boolean
    showPublishModal: boolean
    showUnpublishModal: boolean
    showInsightsModal: boolean
    showDuplicateModal: boolean
    showStatusModal: boolean
    showAssignRecruiterModal: boolean
    statusModalMode: 'pause' | 'activate'
    companyRecruiters: Array<{
      id: string; name: string; email?: string; avatar?: string
      active_jobs_count?: number; performance_score?: number
    }>
    isLoadingRecruiters: boolean
    showReactivateScreeningDialog: boolean
    reactivateScreeningJobs: Record<string, unknown>[]
    reactivateEndDate: string
    isArchivingJobs: boolean
  }
  actions: {
    setSelectedJobsForBatch: React.Dispatch<React.SetStateAction<Set<number>>>
    setShowCompareModal: (v: boolean) => void
    setShowPublishModal: (v: boolean) => void
    setShowUnpublishModal: (v: boolean) => void
    setShowInsightsModal: (v: boolean) => void
    setShowDuplicateModal: (v: boolean) => void
    setShowStatusModal: (v: boolean) => void
    setShowAssignRecruiterModal: (v: boolean) => void
    setShowReactivateScreeningDialog: (v: boolean) => void
    setReactivateScreeningJobs: React.Dispatch<React.SetStateAction<Record<string, unknown>[]>>
    setReactivateEndDate: (v: string) => void
    selectAllJobs: () => void
    deselectAllJobs: () => void
    toggleJobSelection: (jobId: number) => void
    togglePinJob: (jobId: number) => void
    toggleUrgentJob: (jobId: number) => Promise<void>
    toggleFavoriteJob: (jobId: number) => void
    handleJobCompare: () => void
    requestJobCompare: (jobIds?: number[]) => void
    handleJobPublish: () => void
    handleJobInsights: () => void
    handleJobDuplicate: () => void
    handleJobToggleStatus: () => void
    handleJobAssignRecruiter: () => void
    getSelectedJobsHaveActiveStatus: () => boolean
    handleJobArchive: (archive: boolean) => Promise<boolean>
  }
}

export function useJobsBulkActions({
  allJobs,
  filteredJobs,
  setBackendJobs,
}: UseJobsBulkActionsOptions): UseJobsBulkActionsReturn {
  const [selectedJobsForBatch, setSelectedJobsForBatch] = useState<Set<number>>(new Set())
  const [pinnedJobs, setPinnedJobs] = useState<Set<number>>(new Set())
  const [urgentJobs, setUrgentJobs] = useState<Set<number>>(new Set())
  const [favoriteJobs, setFavoriteJobs] = useState<Set<number>>(new Set())

  const [showCompareModal, setShowCompareModal] = useState(false)
  const [showPublishModal, setShowPublishModal] = useState(false)
  const [showUnpublishModal, setShowUnpublishModal] = useState(false)
  const [showInsightsModal, setShowInsightsModal] = useState(false)
  const [showDuplicateModal, setShowDuplicateModal] = useState(false)
  const [showStatusModal, setShowStatusModal] = useState(false)
  const [showAssignRecruiterModal, setShowAssignRecruiterModal] = useState(false)
  const [statusModalMode, setStatusModalMode] = useState<'pause' | 'activate'>('pause')
  const [companyRecruiters, setCompanyRecruiters] = useState<Array<{
    id: string; name: string; email?: string; avatar?: string
    active_jobs_count?: number; performance_score?: number
  }>>([])
  const [isLoadingRecruiters, setIsLoadingRecruiters] = useState(false)
  const [showReactivateScreeningDialog, setShowReactivateScreeningDialog] = useState(false)
  const [reactivateScreeningJobs, setReactivateScreeningJobs] = useState<Record<string, unknown>[]>([])
  const [reactivateEndDate, setReactivateEndDate] = useState('')
  const [isArchivingJobs, setIsArchivingJobs] = useState(false)

  // Load company recruiters when assign or duplicate modal opens
  useEffect(() => {
    if ((showAssignRecruiterModal || showDuplicateModal) && companyRecruiters.length === 0 && !isLoadingRecruiters) {
      setIsLoadingRecruiters(true)
      liaApi.getCompanyUsers({ role: 'recruiter', isActive: true })
        .then((response) => {
          setCompanyRecruiters(response.users.map(user => ({
            id: user.id,
            name: user.name,
            email: user.email,
            active_jobs_count: user.active_jobs_count,
            performance_score: user.performance_score,
          })))
        })
        .catch((err) => { console.error('[useJobsBulkActions] getCompanyUsers fetch failed', err) })
        .finally(() => setIsLoadingRecruiters(false))
    }
  }, [showAssignRecruiterModal, showDuplicateModal, companyRecruiters.length, isLoadingRecruiters])

  // -------------------------------------------------------------------------
  // Selection helpers
  // -------------------------------------------------------------------------
  const selectAllJobs = () => {
    const allJobIds = new Set(filteredJobs.map(job => job.id))
    setSelectedJobsForBatch(allJobIds)
  }

  const deselectAllJobs = () => {
    setSelectedJobsForBatch(new Set())
  }

  const toggleJobSelection = (jobId: number) => {
    setSelectedJobsForBatch(prev => {
      const next = new Set(prev)
      if (next.has(jobId)) {
        next.delete(jobId)
      } else {
        next.add(jobId)
      }
      return next
    })
  }

  // -------------------------------------------------------------------------
  // Row-level actions
  // -------------------------------------------------------------------------
  const togglePinJob = (jobId: number) => {
    setPinnedJobs(prev => {
      const next = new Set(prev)
      if (next.has(jobId)) next.delete(jobId)
      else next.add(jobId)
      return next
    })
  }

  const toggleUrgentJob = async (jobId: number) => {
    const job = allJobs.find(j => j.id === jobId)
    if (!job?.backendId) { toast.error('Vaga não encontrada'); return }

    const isCurrentlyUrgent = urgentJobs.has(jobId)
    const newUrgencyLevel = isCurrentlyUrgent ? 3 : 5

    try {
      await liaApi.updateJobVacancy(job.backendId, { urgency_level: newUrgencyLevel })
      setUrgentJobs(prev => {
        const next = new Set(prev)
        if (isCurrentlyUrgent) next.delete(jobId)
        else next.add(jobId)
        return next
      })
      toast.success(isCurrentlyUrgent ? 'Vaga marcada como normal' : 'Vaga marcada como urgente')
    } catch {
      toast.error('Erro ao atualizar urgência da vaga')
    }
  }

  const toggleFavoriteJob = (jobId: number) => {
    setFavoriteJobs(prev => {
      const next = new Set(prev)
      if (next.has(jobId)) next.delete(jobId)
      else next.add(jobId)
      return next
    })
  }

  // -------------------------------------------------------------------------
  // Modal triggers for bulk actions
  // -------------------------------------------------------------------------
  const requestJobCompare = (jobIds?: number[]) => {
    // ui_action `compare_jobs` (produtor: jobs_management_assistant_service) pode
    // trazer job_ids explicitos; senao usa a selecao atual. Sempre exige >= 2 vagas.
    if (jobIds && jobIds.length >= 2) {
      setSelectedJobsForBatch(new Set(jobIds))
      setShowCompareModal(true)
      return
    }
    if (selectedJobsForBatch.size < 2) { toast.error("Selecione pelo menos 2 vagas para comparar"); return }
    setShowCompareModal(true)
  }

  const handleJobCompare = () => requestJobCompare()

  const handleJobPublish = () => setShowPublishModal(true)
  const handleJobInsights = () => setShowInsightsModal(true)

  const handleJobDuplicate = () => {
    if (selectedJobsForBatch.size !== 1) { toast.error("Selecione apenas 1 vaga para duplicar"); return }
    setShowDuplicateModal(true)
  }

  const handleJobToggleStatus = () => {
    const selected = allJobs.filter(job => selectedJobsForBatch.has(job.id))
    const hasActive = selected.some(job => job.status === 'Ativa')
    setStatusModalMode(hasActive ? 'pause' : 'activate')
    setShowStatusModal(true)
  }

  const handleJobAssignRecruiter = () => setShowAssignRecruiterModal(true)

  const handleJobArchive = async (archive: boolean): Promise<boolean> => {
    const selected = allJobs.filter(job => selectedJobsForBatch.has(job.id))
    if (selected.length === 0) return false

    const backendIds = selected
      .map((job) => job.backendId)
      .filter((id): id is string => Boolean(id))

    if (backendIds.length === 0) {
      toast.error('Nenhuma vaga válida selecionada')
      return false
    }

    setIsArchivingJobs(true)
    try {
      if (archive) {
        await archiveJobs(backendIds)
        setBackendJobs(prev => prev.filter(j => !selectedJobsForBatch.has(j.id)))
        toast.success(`${backendIds.length} vaga${backendIds.length > 1 ? 's' : ''} arquivada${backendIds.length > 1 ? 's' : ''}`)
      } else {
        await unarchiveJobs(backendIds)
        setBackendJobs(prev => prev.map(j =>
          selectedJobsForBatch.has(j.id) ? { ...j, status: 'Rascunho' as const } : j
        ))
        toast.success(`${backendIds.length} vaga${backendIds.length > 1 ? 's' : ''} desarquivada${backendIds.length > 1 ? 's' : ''}`)
      }
      setSelectedJobsForBatch(new Set())
      return true
    } catch (err) {
      const action = archive ? 'arquivar' : 'desarquivar'
      toast.error(`Falha ao ${action} vagas`)
      return false
    } finally {
      setIsArchivingJobs(false)
    }
  }

  const getSelectedJobsHaveActiveStatus = () => {
    return allJobs.filter(job => selectedJobsForBatch.has(job.id)).some(job => job.status === 'Ativa')
  }

  return {
    state: {
      selectedJobsForBatch, pinnedJobs, urgentJobs, favoriteJobs,
      showCompareModal, showPublishModal, showUnpublishModal, showInsightsModal,
      showDuplicateModal, showStatusModal, showAssignRecruiterModal, statusModalMode,
      companyRecruiters, isLoadingRecruiters, showReactivateScreeningDialog,
      reactivateScreeningJobs, reactivateEndDate,
      isArchivingJobs,
    },
    actions: {
      setSelectedJobsForBatch, setShowCompareModal, setShowPublishModal, setShowUnpublishModal,
      setShowInsightsModal, setShowDuplicateModal, setShowStatusModal, setShowAssignRecruiterModal,
      setShowReactivateScreeningDialog, setReactivateScreeningJobs, setReactivateEndDate,
      selectAllJobs, deselectAllJobs, toggleJobSelection, togglePinJob, toggleUrgentJob,
      toggleFavoriteJob, handleJobCompare, requestJobCompare, handleJobPublish, handleJobInsights, handleJobDuplicate,
      handleJobToggleStatus, handleJobAssignRecruiter, getSelectedJobsHaveActiveStatus, handleJobArchive,
    },
  }
}
