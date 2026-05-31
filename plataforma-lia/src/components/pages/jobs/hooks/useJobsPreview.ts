"use client"

import { useState, useEffect } from "react"
import { liaApi, type JobVacancyMetrics } from "@/services/lia-api"
import { useScreeningConfig, limitToApprovalPreset } from "@/hooks/recruitment/useScreeningConfig"
import { toast } from "sonner"
import type { Job, PreviewTab } from "@/components/jobs"

// ---------------------------------------------------------------------------
// useJobsPreview
// Responsável por: painel de preview de vagas (JobPreviewPanel), formulário
// de edição inline (jobDataForm), métricas da vaga, configuração de triagem,
// modal de edição de triagem (WSI), modais de configuração de screening.
// ---------------------------------------------------------------------------

interface UseJobsPreviewOptions {
  setBackendJobs: React.Dispatch<React.SetStateAction<Job[]>>
}

interface UseJobsPreviewReturn {
  state: {
    showJobPreview: boolean
    previewJob: Job | null
    activePreviewTab: PreviewTab
    showFullDescription: boolean
    showStageDates: boolean
    showExpandedDetails: boolean
    jobDataForm: Record<string, unknown>
    savingSection: string | null
    newJobDataBenefit: string
    newJobDataLang: string
    newJobDataLangLevel: string
    openJobDataSections: Record<string, boolean>
    jobMetrics: JobVacancyMetrics | null
    isLoadingJobMetrics: boolean
    previewWidth: number
    isResizingPreview: boolean
    screeningConfig: ReturnType<typeof useScreeningConfig>['config']
    isLoadingScreeningConfig: boolean
    screeningConfigExpanded: boolean
    isEditingScreeningConfig: boolean
    editChannels: { whatsapp: boolean; chat_web: boolean; phone: boolean }
    editMinScorePreset: 'rigorous' | 'recommended' | 'flexible'
    editTimeoutHours: number
    editMaxRetries: number
    editAutoApprovalPreset: 'conservative' | 'recommended' | 'autonomous'
    showScreeningChannelsModal: boolean
    showScreeningSettingsModal: boolean
    showScreeningSchedulingModal: boolean
    showQuestionEditModal: boolean
    screeningBlockExpanded: boolean
    isEditingScreening: boolean
    selectedBlock: number
    adjustmentDiffs: Record<string, unknown>[]
    adjustmentIterations: number
    isGeneratingWSI: boolean
    pendingAdjustedQuestions: Record<string, unknown>[]
    acceptedQuestions: Set<string>
    wsiGenerationMode: 'compact' | 'full' | null
    wsiGenerationCompleted: boolean
    wsiProgressCollapsed: boolean
    wsiGeneratedCount: number
    wsiGenerationStep: number
    wsiDynamicMessage: string
    wsiGenerationContext: Record<string, unknown> | null
    activeDashboardModal: 'minhasVagas' | 'performanceLia' | null
    showWSITutorialModal: boolean
    dashboardPeriod: '1m' | '3m' | '6m' | '9m' | '12m'
    showReport: boolean
    reportJob: Job | null
    showCreateJobModal: boolean
    pendingNavigateJobId: string | null
  }
  actions: {
    setShowJobPreview: (v: boolean) => void
    setPreviewJob: (v: Job | null) => void
    setActivePreviewTab: (v: PreviewTab) => void
    setShowFullDescription: (v: boolean) => void
    setShowStageDates: (v: boolean) => void
    setShowExpandedDetails: (v: boolean) => void
    setJobDataForm: React.Dispatch<React.SetStateAction<Record<string, unknown>>>
    setOpenJobDataSections: React.Dispatch<React.SetStateAction<Record<string, boolean>>>
    setNewJobDataBenefit: (v: string) => void
    setNewJobDataLang: (v: string) => void
    setNewJobDataLangLevel: (v: string) => void
    setPreviewWidth: (v: number) => void
    setIsResizingPreview: (v: boolean) => void
    setScreeningConfigExpanded: (v: boolean) => void
    setIsEditingScreeningConfig: (v: boolean) => void
    setEditChannels: React.Dispatch<React.SetStateAction<{ whatsapp: boolean; chat_web: boolean; phone: boolean }>>
    setEditMinScorePreset: (v: 'rigorous' | 'recommended' | 'flexible') => void
    setEditTimeoutHours: (v: number) => void
    setEditMaxRetries: (v: number) => void
    setEditAutoApprovalPreset: (v: 'conservative' | 'recommended' | 'autonomous') => void
    setShowScreeningChannelsModal: (v: boolean) => void
    setShowScreeningSettingsModal: (v: boolean) => void
    setShowScreeningSchedulingModal: (v: boolean) => void
    setShowQuestionEditModal: (v: boolean) => void
    setScreeningBlockExpanded: (v: boolean) => void
    setIsEditingScreening: (v: boolean) => void
    setSelectedBlock: (v: number) => void
    setAdjustmentDiffs: React.Dispatch<React.SetStateAction<Record<string, unknown>[]>>
    setAdjustmentIterations: (v: number) => void
    setIsGeneratingWSI: (v: boolean) => void
    setPendingAdjustedQuestions: React.Dispatch<React.SetStateAction<Record<string, unknown>[]>>
    setAcceptedQuestions: React.Dispatch<React.SetStateAction<Set<string>>>
    setWsiGenerationMode: (v: 'compact' | 'full' | null) => void
    setWsiGenerationCompleted: (v: boolean) => void
    setWsiProgressCollapsed: (v: boolean) => void
    setWsiGeneratedCount: (v: number) => void
    setWsiGenerationStep: (v: number) => void
    setWsiDynamicMessage: (v: string) => void
    setWsiGenerationContext: (v: Record<string, unknown> | null) => void
    setActiveDashboardModal: (v: 'minhasVagas' | 'performanceLia' | null) => void
    setShowWSITutorialModal: (v: boolean) => void
    setDashboardPeriod: (v: '1m' | '3m' | '6m' | '9m' | '12m') => void
    setShowReport: (v: boolean) => void
    setReportJob: (v: Job | null) => void
    setShowCreateJobModal: (v: boolean) => void
    setPendingNavigateJobId: (v: string | null) => void
    handleJobPreview: (job: Job) => void
    handleSaveJobDataSection: (sectionId: string, fields: string[]) => Promise<void>
    handleScreeningStatusChange: (jobId: string, newStatus: string, extraData?: { pause_reason?: string; scheduled_end_date?: string }) => Promise<boolean>
    handleUpdateJobField: (field: 'status' | 'visibility' | 'priority' | 'stage', value: string) => Promise<void>
    handleShowReport: (job: Job) => void
    handleCloseReport: () => void
    updateScreeningConfig: ReturnType<typeof useScreeningConfig>['updateConfig']
  }
}

export function useJobsPreview({ setBackendJobs }: UseJobsPreviewOptions): UseJobsPreviewReturn {
  const [showJobPreview, setShowJobPreview] = useState(false)
  const [previewJob, setPreviewJob] = useState<Job | null>(null)
  const [activePreviewTab, setActivePreviewTab] = useState<PreviewTab>('screening')
  const [showFullDescription, setShowFullDescription] = useState(false)
  const [showStageDates, setShowStageDates] = useState(false)
  const [showExpandedDetails, setShowExpandedDetails] = useState(false)

  const [openJobDataSections, setOpenJobDataSections] = useState<Record<string, boolean>>({ 'info-geral': true })
  const [jobDataForm, setJobDataForm] = useState<Record<string, unknown>>({})
  const [savingSection, setSavingSection] = useState<string | null>(null)
  const [newJobDataBenefit, setNewJobDataBenefit] = useState('')
  const [newJobDataLang, setNewJobDataLang] = useState('')
  const [newJobDataLangLevel, setNewJobDataLangLevel] = useState('Intermediário')

  const [jobMetrics, setJobMetrics] = useState<JobVacancyMetrics | null>(null)
  const [isLoadingJobMetrics, setIsLoadingJobMetrics] = useState(false)

  const [previewWidth, setPreviewWidth] = useState(400)
  const [isResizingPreview, setIsResizingPreview] = useState(false)

  const { config: screeningConfig, isLoading: isLoadingScreeningConfig, updateConfig: updateScreeningConfig } = useScreeningConfig(previewJob?.backendId || null)

  const [screeningConfigExpanded, setScreeningConfigExpanded] = useState(false)
  const [isEditingScreeningConfig, setIsEditingScreeningConfig] = useState(false)
  const [editChannels, setEditChannels] = useState({ whatsapp: true, chat_web: true, phone: false })
  const [editMinScorePreset, setEditMinScorePreset] = useState<'rigorous' | 'recommended' | 'flexible'>('recommended')
  const [editTimeoutHours, setEditTimeoutHours] = useState(48)
  const [editMaxRetries, setEditMaxRetries] = useState(2)
  const [editAutoApprovalPreset, setEditAutoApprovalPreset] = useState<'conservative' | 'recommended' | 'autonomous'>('recommended')

  const [showScreeningChannelsModal, setShowScreeningChannelsModal] = useState(false)
  const [showScreeningSettingsModal, setShowScreeningSettingsModal] = useState(false)
  const [showScreeningSchedulingModal, setShowScreeningSchedulingModal] = useState(false)

  const [showQuestionEditModal, setShowQuestionEditModal] = useState(false)
  const [screeningBlockExpanded, setScreeningBlockExpanded] = useState(true)
  const [isEditingScreening, setIsEditingScreening] = useState(false)
  const [selectedBlock, setSelectedBlock] = useState<number>(2)
  const [adjustmentDiffs, setAdjustmentDiffs] = useState<Record<string, unknown>[]>([])
  const [adjustmentIterations, setAdjustmentIterations] = useState(0)
  const [isGeneratingWSI, setIsGeneratingWSI] = useState(false)
  const [pendingAdjustedQuestions, setPendingAdjustedQuestions] = useState<Record<string, unknown>[]>([])
  const [acceptedQuestions, setAcceptedQuestions] = useState<Set<string>>(new Set())
  const [wsiGenerationMode, setWsiGenerationMode] = useState<'compact' | 'full' | null>(null)
  const [wsiGenerationCompleted, setWsiGenerationCompleted] = useState(false)
  const [wsiProgressCollapsed, setWsiProgressCollapsed] = useState(false)
  const [wsiGeneratedCount, setWsiGeneratedCount] = useState(0)
  const [wsiGenerationStep, setWsiGenerationStep] = useState(0)
  const [wsiDynamicMessage, setWsiDynamicMessage] = useState('')
  const [wsiGenerationContext, setWsiGenerationContext] = useState<Record<string, unknown> | null>(null)

  const [activeDashboardModal, setActiveDashboardModal] = useState<'minhasVagas' | 'performanceLia' | null>(null)
  const [showWSITutorialModal, setShowWSITutorialModal] = useState(false)
  const [dashboardPeriod, setDashboardPeriod] = useState<'1m' | '3m' | '6m' | '9m' | '12m'>('3m')
  const [showReport, setShowReport] = useState(false)
  const [reportJob, setReportJob] = useState<Job | null>(null)
  const [showCreateJobModal, setShowCreateJobModal] = useState(false)
  const [pendingNavigateJobId, setPendingNavigateJobId] = useState<string | null>(null)

  // Sync screening config edit fields when config changes
  useEffect(() => {
    if (!isEditingScreeningConfig && screeningConfig) {
      setEditChannels({
        whatsapp: screeningConfig.channels?.whatsapp?.enabled ?? true,
        chat_web: screeningConfig.channels?.chat_web?.enabled ?? true,
        phone: screeningConfig.channels?.phone?.enabled ?? false,
      })
      setEditMinScorePreset(screeningConfig.settings?.min_score_preset ?? 'recommended')
      setEditTimeoutHours(screeningConfig.settings?.response_timeout_hours ?? 48)
      setEditMaxRetries(screeningConfig.settings?.max_retries ?? 2)
       
      setEditAutoApprovalPreset(screeningConfig.settings?.auto_approval_preset ?? limitToApprovalPreset(screeningConfig.settings?.auto_approval_limit))
    }
  }, [screeningConfig, isEditingScreeningConfig])

  // Fetch job metrics when previewJob changes
  useEffect(() => {
    if (previewJob?.backendId) {
      setIsLoadingJobMetrics(true)
      liaApi.getJobVacancyMetrics(previewJob.backendId)
        .then((metrics) => setJobMetrics(metrics))
        .catch(() => setJobMetrics(null))
        .finally(() => setIsLoadingJobMetrics(false))
    } else {
      setJobMetrics(null)
    }
  }, [previewJob?.backendId])

  // Sync form when previewJob changes
  useEffect(() => {
    if (previewJob) {
      setJobDataForm({
        title: previewJob.title || '',
        department: previewJob.department || '',
        location: previewJob.location || '',
        workModel: previewJob.workModel || 'presencial',
        type: previewJob.type || 'CLT',
        seniority: previewJob.seniority || '',
        status: previewJob.status || 'Ativa',
        urgencyLevel: previewJob.urgencyLevel || 3,
        recruiter: previewJob.recruiter || '',
        recruiterEmail: previewJob.recruiterEmail || '',
        manager: previewJob.manager || '',
        managerEmail: previewJob.managerEmail || '',
        openDate: previewJob.openDate || '',
        deadline: previewJob.deadline || '',
        deadlineScreening: previewJob.deadlineScreening || '',
        deadlineShortlist: previewJob.deadlineShortlist || '',
        deadlineClosing: previewJob.deadlineClosing || '',
        salaryMin: (previewJob.salaryRange as Record<string, unknown> | undefined)?.min || '',
        salaryMax: (previewJob.salaryRange as Record<string, unknown> | undefined)?.max || '',
        bonusMin: '',
        bonusMax: '',
        benefits: previewJob.benefits || [],
        targetAudience: previewJob.targetAudience || '',
        targetSector: previewJob.targetSector || '',
        targetSegment: previewJob.targetSegment || '',
        languages: previewJob.languages || [],
        publishedLinkedIn: previewJob.publishedLinkedIn || false,
        publishedWebsite: previewJob.publishedWebsite || false,
        publishedIndeed: previewJob.publishedIndeed || false,
        visibility: previewJob.visibility || 'public',
        isConfidential: previewJob.isConfidential || false,
        maskedCompanyName: previewJob.maskedCompanyName || '',
        isAffirmative: previewJob.isAffirmative || false,
        affirmativeType: '',
        confidentialityConfig: previewJob.confidentialityConfig || {
          can_reveal_company_name: true,
          can_discuss_salary: true,
          can_discuss_benefits: true,
          can_discuss_location: true,
        },
      })
    }
  }, [previewJob])

  // Listen for preview tab switch event
  useEffect(() => {
    const handleSetPreviewTab = (event: CustomEvent) => {
      const tab = event.detail as PreviewTab
      setActivePreviewTab(tab)
    }
    window.addEventListener('setJobPreviewTab', handleSetPreviewTab as EventListener)
    return () => window.removeEventListener('setJobPreviewTab', handleSetPreviewTab as EventListener)
  }, [])

  // -------------------------------------------------------------------------
  // Actions
  // -------------------------------------------------------------------------
  const handleJobPreview = (job: Job) => {
    setPreviewJob(job)
    setShowJobPreview(true)
  }

  const handleSaveJobDataSection = async (sectionId: string, fields: string[]) => {
    if (!previewJob) return
    setSavingSection(sectionId)
    try {
      const fieldMapping: Record<string, string> = {
        title: 'title', department: 'department', location: 'location',
        workModel: 'work_model', type: 'employment_type', seniority: 'seniority_level',
        status: 'status', urgencyLevel: 'urgency_level', recruiter: 'recruiter',
        recruiterEmail: 'recruiter_email', manager: 'hiring_manager',
        managerEmail: 'hiring_manager_email', openDate: 'open_date', deadline: 'deadline',
        deadlineScreening: 'deadline_screening', deadlineShortlist: 'deadline_shortlist',
        deadlineClosing: 'deadline_closing', screeningStatus: 'screening_status',
        benefits: 'benefits', targetAudience: 'target_audience', targetSector: 'target_sector',
        targetSegment: 'target_segment', languages: 'languages',
        publishedLinkedIn: 'published_linkedin', publishedWebsite: 'published_website',
        publishedIndeed: 'published_indeed', visibility: 'visibility',
        isConfidential: 'is_confidential', maskedCompanyName: 'masked_company_name',
        isAffirmative: 'is_affirmative', affirmativeType: 'affirmative_type',
        confidentialityConfig: 'confidentiality_config', description: 'description',
      }

      const updates: Record<string, unknown> = {}
      fields.forEach(f => {
        const backendKey = fieldMapping[f] || f
        const value = jobDataForm[f]
        if (f === 'salaryMin' || f === 'salaryMax') {
          if (!updates['salary_range']) {
            updates['salary_range'] = {
              min: jobDataForm.salaryMin ? Number(jobDataForm.salaryMin) : null,
              max: jobDataForm.salaryMax ? Number(jobDataForm.salaryMax) : null,
              currency: 'BRL',
            }
          }
          return
        }
        if (f === 'bonusMin' || f === 'bonusMax') {
          if (!updates['bonus_range']) {
            updates['bonus_range'] = {
              min: jobDataForm.bonusMin ? Number(jobDataForm.bonusMin) : null,
              max: jobDataForm.bonusMax ? Number(jobDataForm.bonusMax) : null,
            }
          }
          return
        }
        updates[backendKey] = value
      })

      await liaApi.updateJobVacancy(previewJob.backendId || previewJob.jobId, updates)
      toast.success('Seção salva com sucesso!')

      const updatedJob = { ...previewJob }
      fields.forEach(f => { ;(updatedJob as Record<string, unknown>)[f] = jobDataForm[f] })
      if (fields.includes('salaryMin') || fields.includes('salaryMax')) {
        ;(updatedJob as Record<string, unknown>).salaryRange = {
          min: jobDataForm.salaryMin ? Number(jobDataForm.salaryMin) : null,
          max: jobDataForm.salaryMax ? Number(jobDataForm.salaryMax) : null,
          currency: 'BRL',
        }
        ;(updatedJob as Record<string, unknown>).salaryMin = jobDataForm.salaryMin ? Number(jobDataForm.salaryMin) : null
        ;(updatedJob as Record<string, unknown>).salaryMax = jobDataForm.salaryMax ? Number(jobDataForm.salaryMax) : null
      }
      setPreviewJob(updatedJob)
    } catch {
      toast.error('Erro ao salvar. Tente novamente.')
    } finally {
      setSavingSection(null)
    }
  }

  const handleScreeningStatusChange = async (jobId: string, newStatus: string, extraData?: { pause_reason?: string; scheduled_end_date?: string }) => {
    try {
      await liaApi.updateScreeningStatus(jobId, newStatus, extraData)
      setBackendJobs(prev => prev.map(j => j.backendId === jobId ? { ...j, screeningStatus: newStatus as Job['screeningStatus'] } : j))
      return true
    } catch {
      return false
    }
  }

  const handleUpdateJobField = async (field: 'status' | 'visibility' | 'priority' | 'stage', value: string) => {
    if (!previewJob) return
    try {
      await liaApi.updateJobVacancy(previewJob.backendId, { [field]: value })
      const updatedJob = { ...previewJob, [field]: value }
      setPreviewJob(updatedJob)
      setBackendJobs(prev => prev.map(job => job.backendId === previewJob.backendId ? { ...job, [field]: value } : job))
      const labels: Record<string, string> = { status: 'Status', visibility: 'Visibilidade', priority: 'Prioridade', stage: 'Etapa' }
      toast.success(`${labels[field]} atualizado para "${value}"`)
    } catch {
      toast.error('Erro ao atualizar campo. Tente novamente.')
    }
  }

  const handleShowReport = (job: Job) => { setReportJob(job); setShowReport(true) }
  const handleCloseReport = () => { setShowReport(false); setReportJob(null) }

  return {
    state: {
      showJobPreview, previewJob, activePreviewTab, showFullDescription, showStageDates,
      showExpandedDetails, jobDataForm, savingSection, newJobDataBenefit, newJobDataLang,
      newJobDataLangLevel, openJobDataSections, jobMetrics, isLoadingJobMetrics,
      previewWidth, isResizingPreview, screeningConfig, isLoadingScreeningConfig,
      screeningConfigExpanded, isEditingScreeningConfig, editChannels, editMinScorePreset,
      editTimeoutHours, editMaxRetries, editAutoApprovalPreset, showScreeningChannelsModal,
      showScreeningSettingsModal, showScreeningSchedulingModal, showQuestionEditModal,
      screeningBlockExpanded, isEditingScreening, selectedBlock, adjustmentDiffs,
      adjustmentIterations, isGeneratingWSI, pendingAdjustedQuestions, acceptedQuestions,
      wsiGenerationMode, wsiGenerationCompleted, wsiProgressCollapsed, wsiGeneratedCount,
      wsiGenerationStep, wsiDynamicMessage, wsiGenerationContext, activeDashboardModal,
      showWSITutorialModal, dashboardPeriod, showReport, reportJob, showCreateJobModal, pendingNavigateJobId,
    },
    actions: {
      setShowJobPreview, setPreviewJob, setActivePreviewTab, setShowFullDescription,
      setShowStageDates, setShowExpandedDetails, setJobDataForm, setOpenJobDataSections,
      setNewJobDataBenefit, setNewJobDataLang, setNewJobDataLangLevel, setPreviewWidth,
      setIsResizingPreview, setScreeningConfigExpanded, setIsEditingScreeningConfig,
      setEditChannels, setEditMinScorePreset, setEditTimeoutHours, setEditMaxRetries,
      setEditAutoApprovalPreset, setShowScreeningChannelsModal, setShowScreeningSettingsModal,
      setShowScreeningSchedulingModal, setShowQuestionEditModal, setScreeningBlockExpanded,
      setIsEditingScreening, setSelectedBlock, setAdjustmentDiffs, setAdjustmentIterations,
      setIsGeneratingWSI, setPendingAdjustedQuestions, setAcceptedQuestions, setWsiGenerationMode,
      setWsiGenerationCompleted, setWsiProgressCollapsed, setWsiGeneratedCount, setWsiGenerationStep,
      setWsiDynamicMessage, setWsiGenerationContext, setActiveDashboardModal, setShowWSITutorialModal,
      setDashboardPeriod, setShowReport, setReportJob,
      setShowCreateJobModal, setPendingNavigateJobId, handleJobPreview, handleSaveJobDataSection,
      handleScreeningStatusChange, handleUpdateJobField, handleShowReport, handleCloseReport,
      updateScreeningConfig,
    },
  }
}
