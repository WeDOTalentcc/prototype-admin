"use client"


import { formatBRL } from "@/lib/pricing"
import React, { useEffect, useRef, useCallback } from "react"
import { useRouter } from "next/navigation"
import { liaApi } from "@/services/lia-api"

// Sub-hooks
import { useJobsData } from "./useJobsData"
import { useJobsFilters } from "./useJobsFilters"
import { useJobsTableConfig } from "./useJobsTableConfig"
import { useJobsChat } from "./useJobsChat"
import { useJobsBulkActions } from "./useJobsBulkActions"
import { useJobsPreview } from "./useJobsPreview"

// Stores
import { useNavigationStore } from "@/stores/navigation-store"

// Navigation helpers (canonical, post-mortem 2026-04-29)
import { navigateToJobDetail } from "@/lib/navigation/job-navigation"

// Types
import type { Job } from "@/components/jobs"

// -------------------------------------------------------------------------
// Interface pública do hook — NÃO ALTERAR (compatibilidade com consumidores)
// -------------------------------------------------------------------------
interface JobsPageProps {
  onNavigate?: (page: string) => void
  onAddRecentItem?: (item: { id: string; type: 'vaga' | 'chat' | 'candidato'; title: string; subtitle?: string; meta?: Record<string, string | undefined> }) => void
  pendingChatOpen?: { mode: 'general' | 'job-creation' } | null
  onChatOpened?: () => void
  pendingJobOpen?: { jobId: string; jobTitle: string } | null
  onJobOpened?: () => void
}

// -------------------------------------------------------------------------
// useJobsPageCore — orquestrador dos sub-hooks
// -------------------------------------------------------------------------
export function useJobsPageCore(props: JobsPageProps) {
  const { onNavigate, onAddRecentItem, pendingChatOpen, onChatOpened, pendingJobOpen, onJobOpened } = props
  const router = useRouter()

  // -----------------------------------------------------------------------
  // Camada 1: Dados (backend jobs + dashboard stats)
  // -----------------------------------------------------------------------
  const {
    state: dataState,
    actions: dataActions,
  } = useJobsData()

  const { backendJobs, hasMounted, jobsRefreshKey, dashboardStats, isLoadingStats, isExternalSourceFallback } = dataState
  const { setBackendJobs, setJobsRefreshKey, loadBackendJobs } = dataActions

  const allJobs = backendJobs

  // -----------------------------------------------------------------------
  // Camada 2: Filtros + filteredJobs
  // -----------------------------------------------------------------------
  const {
    state: filtersState,
    actions: filtersActions,
  } = useJobsFilters({ backendJobs })

  const { filteredJobs } = filtersState

  // -----------------------------------------------------------------------
  // Camada 3: Configuração de tabela (colunas, resize, drag, sort)
  // -----------------------------------------------------------------------
  const {
    state: tableState,
    actions: tableActions,
  } = useJobsTableConfig()

  // -----------------------------------------------------------------------
  // Camada 4: Preview de vagas
  // -----------------------------------------------------------------------
  const {
    state: previewState,
    actions: previewActions,
  } = useJobsPreview({ setBackendJobs })

  // -----------------------------------------------------------------------
  // Camada 5: Ações em massa (seleção, modais, pin, urgente, favorito)
  // -----------------------------------------------------------------------
  const {
    state: bulkState,
    actions: bulkActions,
  } = useJobsBulkActions({
    allJobs,
    filteredJobs,
    setBackendJobs,
  })

  // -----------------------------------------------------------------------
  // Camada 6: Chat LIA inline + orquestrador
  // -----------------------------------------------------------------------
  const {
    state: chatState,
    actions: chatActions,
  } = useJobsChat({
    filteredJobs,
    allJobs,
    selectedJobsForBatch: bulkState.selectedJobsForBatch,
    onAddRecentItem,
    onChatOpened,
    pendingChatOpen,
    setActiveFilter: filtersActions.setActiveFilter,
    openCompareModal: bulkActions.requestJobCompare,
    loadBackendJobs,
  })

  // -----------------------------------------------------------------------
  // Navigation: navigate to candidate (store) + pendingJobOpen
  // -----------------------------------------------------------------------
  const hasProcessedNavigateToCandidate = useRef(false)
  const navigationStoreNavigateToCandidate = useNavigationStore(s => s.navigateToCandidate)
  const consumeNavigateToCandidate = useNavigationStore(s => s.consumeNavigateToCandidate)

  useEffect(() => {
    if (hasProcessedNavigateToCandidate.current) return
    if (!allJobs.length) return
    if (!navigationStoreNavigateToCandidate) return

    hasProcessedNavigateToCandidate.current = true
    const result = consumeNavigateToCandidate()
    if (!result) return
    const nav = result.nav

    try {
      let matchedJob = allJobs.find(j => j.jobId === nav.jobId || j.title === nav.jobTitle)
      if (!matchedJob && nav.jobTitle) {
        const norm = nav.jobTitle.toLowerCase()
        matchedJob = allJobs.find(j => j.title.toLowerCase().includes(norm) || norm.includes(j.title.toLowerCase()))
      }
      if (!matchedJob && nav.jobId) {
        matchedJob = allJobs.find(j => j.backendId === nav.jobId || j.jobId?.includes(nav.jobId!) || nav.jobId!.includes(j.jobId || ''))
      }
      if (!matchedJob) {
        const activeJobs = allJobs.filter(j => j.status === 'Ativa')
        if (activeJobs.length > 0) matchedJob = activeJobs[0]
      }

      if (matchedJob) {
        setSelectedJobAndOpenKanban(matchedJob)
        onAddRecentItem?.({
          id: matchedJob.backendId || matchedJob.jobId || String(matchedJob.id),
          type: 'vaga',
          title: matchedJob.title,
          subtitle: (matchedJob as unknown as Record<string, unknown>).company as string | undefined,
          meta: { jobId: matchedJob.backendId || matchedJob.jobId || String(matchedJob.id) },
        })
      }
    } catch {
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allJobs, onAddRecentItem, navigationStoreNavigateToCandidate, consumeNavigateToCandidate])

  // Navigate to newly created job when it appears in allJobs (fallback)
  useEffect(() => {
    if (!previewState.pendingNavigateJobId || !allJobs.length) return
    const matched = allJobs.find(j => j.backendId === previewState.pendingNavigateJobId)
    if (!matched) return
    previewActions.setPendingNavigateJobId(null)
    setSelectedJobAndOpenKanban(matched)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allJobs, previewState.pendingNavigateJobId])

  // Open pending job from external navigation
  useEffect(() => {
    if (!pendingJobOpen) return
    let cancelled = false

    const tryOpenJob = async () => {
      let jobs = allJobs
      if (jobs.length === 0) {
        for (let attempt = 0; attempt < 5; attempt++) {
          if (cancelled) return
          try {
            const response = await liaApi.listJobVacancies()
            if (response?.items?.length) {
              // Minimal conversion — same structure as useJobsData
              const stageMapping: Record<string, Job['stage']> = {
                'Planejamento': 'Planejamento', 'Aprovação': 'Aprovação', 'Publicada': 'Publicada',
                'Triagem': 'Triagem', 'Entrevistas': 'Entrevistas', 'Finalização': 'Finalização', 'Encerrada': 'Encerrada',
              }
              const convertedJobs: Job[] = response.items.map((jv_raw, index: number) => { const jv = jv_raw as unknown as Record<string, unknown>
                const funnelData = (jv.funnel_data as Record<string, number>) || { total: 0, screening: 0, interview: 0, final: 0, hired: 0 }
                return {
                  id: index + 1,
                  backendId: jv.id as string,
                  jobId: `WDT-${(jv.id as string).slice(0, 8).toUpperCase()}`,
                  title: jv.title as string,
                  department: (jv.department as string) || 'Geral',
                  location: (jv.location as string) || 'Não especificado',
                  workModel: ((jv.work_model as Job['workModel']) || 'híbrido'),
                  type: (jv.employment_type as string) || 'CLT',
                  seniority: (jv.seniority_level as string) || (jv.seniority as string) || undefined,
                  salary: jv.salary_range ? `${formatBRL(Number((jv.salary_range as Record<string, number>).min ?? 0))} - ${formatBRL(Number((jv.salary_range as Record<string, number>).max ?? 0))}` : 'A combinar',
                  status: ((jv.status as Job['status']) || 'Rascunho'),
                  stage: stageMapping[(jv.stage as string) || ''] || 'Triagem',
                  openDate: (jv.open_date as string)?.split('T')[0] || (jv.created_at as string)?.split('T')[0] || new Date().toISOString().split('T')[0],
                  deadline: (jv.deadline as string)?.split('T')[0] || undefined,
                  description: (jv.description as string) || '',
                  requirements: (jv.requirements as string[]) || [],
                  manager: (jv.manager as string) || 'Não definido',
                  recruiter: (jv.recruiter as string) || 'Não definido',
                  priority: ((jv.priority as Job['priority']) || 'média'),
                  funnel: { total: funnelData.total || 0, screening: funnelData.screening || 0, interview: funnelData.interview || 0, final: funnelData.final || 0, hired: funnelData.hired || 0 },
                  tags: (jv.tags as string[]) || [],
                  conversationId: (jv.conversation_id as string) || undefined,
                  createdAt: (jv.created_at as string) || undefined,
                  benefits: [], managerEmail: '', recruiterEmail: '', nps: 0, urgencyLevel: 3 as 1 | 2 | 3 | 4 | 5,
                  approvalStatus: 'pendente' as const, publishedLinkedIn: false, publishedWebsite: false,
                  isConfidential: false, visibility: 'public' as const, technicalRequirements: [], languages: [],
                  behavioralCompetencies: [], screeningQuestions: [], interviewStages: [], hiringProcess: [],
                  isAffirmative: false,
                } as unknown as Job
              })
              if (!cancelled) { setBackendJobs(convertedJobs); jobs = convertedJobs }
              break
            }
          } catch {
            await new Promise(r => setTimeout(r, 2000))
          }
        }
      }
      if (cancelled || jobs.length === 0) return
      const matched = jobs.find(j => j.backendId === pendingJobOpen.jobId || j.jobId === pendingJobOpen.jobId || j.title === pendingJobOpen.jobTitle)
      if (matched && !cancelled) setSelectedJobAndOpenKanban(matched)
      onJobOpened?.()
    }

    tryOpenJob()
    return () => { cancelled = true }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingJobOpen])

  // -----------------------------------------------------------------------
  // Kanban navigation state
  // -----------------------------------------------------------------------
  // Must start false — store-driven navigation runs via useEffect after mount.
  const [showKanban, setShowKanban] = React.useState(false)
  const [selectedJob, setSelectedJob] = React.useState<Job | null>(null)

  const setSelectedJobAndOpenKanban = (job: Job) => {
    setSelectedJob(job)
    setShowKanban(true)
    previewActions.setShowJobPreview(false)
    previewActions.setPreviewJob(null)
  }

  const handleJobClick = (job: Job) => {
    setSelectedJobAndOpenKanban(job)
    onAddRecentItem?.({
      id: job.backendId || job.jobId || String(job.id),
      type: 'vaga',
      title: job.title,
      subtitle: (job as unknown as Record<string, unknown>).company as string | undefined,
      meta: { jobId: job.backendId || job.jobId || String(job.id) },
    })
  }

  const handleBackToJobs = () => {
    setShowKanban(false)
    setSelectedJob(null)
  }

  // Navigate to the newly created job — routed through canonical helper
  // (post-mortem 2026-04-29: the /jobs/<id> page was deleted from the
  // app; until product decides the replacement, the helper centralizes
  // the no-op + toast UX).
  const navigateToCreatedJob = React.useCallback((jobId: string, jobTitle: string) => {
    navigateToJobDetail(router, jobId, jobTitle)
  }, [router])

  // -----------------------------------------------------------------------
  // Return: flat object preserving EXACT public interface
  // -----------------------------------------------------------------------
  return {
    // --- router ---
    router,

    // --- data ---
    hasMounted,
    allJobs,
    backendJobs,
    isLoadingJobs: dataState.isLoadingJobs,
    jobsError: dataState.jobsError,
    jobsRefreshKey,
    dashboardStats,
    isLoadingStats,
    isExternalSourceFallback,
    setBackendJobs,
    setJobsRefreshKey,
    loadBackendJobs,

    // --- kanban nav ---
    selectedJob,
    setSelectedJob,
    showKanban,
    setShowKanban,
    handleJobClick,
    handleBackToJobs,
    navigateToCreatedJob,

    // --- filters ---
    searchTerm: filtersState.searchTerm,
    setSearchTerm: filtersActions.setSearchTerm,
    selectedStatusFilter: filtersState.selectedStatusFilter,
    setSelectedStatusFilter: filtersActions.setSelectedStatusFilter,
    selectedDaysFilter: filtersState.selectedDaysFilter,
    setSelectedDaysFilter: filtersActions.setSelectedDaysFilter,
    activeFilter: filtersState.activeFilter,
    setActiveFilter: filtersActions.setActiveFilter,
    booleanSearch: filtersState.booleanSearch,
    setBooleanSearch: filtersActions.setBooleanSearch,
    advancedFilters: filtersState.advancedFilters,
    setAdvancedFilters: filtersActions.setAdvancedFilters,
    savedSearches: filtersState.savedSearches,
    setSavedSearches: filtersActions.setSavedSearches,
    searchHistory: filtersState.searchHistory,
    showAdvancedSearch: filtersState.showAdvancedSearch,
    setShowAdvancedSearch: filtersActions.setShowAdvancedSearch,
    expandedSections: filtersState.expandedSections,
    setExpandedSections: filtersActions.setExpandedSections,
    showSearchHistory: filtersState.showSearchHistory,
    setShowSearchHistory: filtersActions.setShowSearchHistory,
    showSavedSearches: filtersState.showSavedSearches,
    setShowSavedSearches: filtersActions.setShowSavedSearches,
    showSuggestions: filtersState.showSuggestions,
    setShowSuggestions: filtersActions.setShowSuggestions,
    selectedTemplate: filtersState.selectedTemplate,
    setSelectedTemplate: filtersActions.setSelectedTemplate,
    jobFilters: filtersState.jobFilters,
    setJobFilters: filtersActions.setJobFilters,
    showTableFiltersPanel: filtersState.showTableFiltersPanel,
    setShowTableFiltersPanel: filtersActions.setShowTableFiltersPanel,
    navigationFilters: filtersState.navigationFilters,
    stageFilters: filtersState.stageFilters,
    filteredJobs,
    statusFilters: filtersState.statusFilters,
    handleSearch: filtersActions.handleSearch,
    handleAISearch: filtersActions.handleAISearch,
    clearAllFilters: filtersActions.clearAllFilters,
    clearAllJobFilters: filtersActions.clearAllJobFilters,
    toggleAdvancedFilter: filtersActions.toggleAdvancedFilter,
    removeAdvancedFilter: filtersActions.removeAdvancedFilter,
    toggleSection: filtersActions.toggleSection,
    toggleJobFilter: filtersActions.toggleJobFilter,
    getActiveAdvancedFiltersCount: filtersActions.getActiveAdvancedFiltersCount,
    getActiveJobFiltersCount: filtersActions.getActiveJobFiltersCount,
    getActiveFiltersCount: filtersActions.getActiveAdvancedFiltersCount,
    hasActiveFilters: () => filtersActions.getActiveAdvancedFiltersCount() > 0,
    saveSearch: filtersActions.saveSearch,
    saveSearchAsTemplate: filtersActions.saveSearchAsTemplate,
    handleApplySavedSearch: filtersActions.handleApplySavedSearch,
    handleDeleteSavedSearch: filtersActions.handleDeleteSavedSearch,
    handleRenameSavedSearch: filtersActions.handleRenameSavedSearch,
    handleStatusFilterChange: filtersActions.handleStatusFilterChange,
    handleTemplateSelection: filtersActions.handleTemplateSelection,
    getJobCountByStatus: filtersActions.getJobCountByStatus,
    getJobCountByStage: filtersActions.getJobCountByStage,
    searchTemplates: filtersActions.searchTemplates,

    // --- table config ---
    columnConfig: tableState.columnConfig,
    visibleColumnIds: tableState.visibleColumnIds,
    savedColumnViews: tableState.savedColumnViews,
    showColumnConfig: tableState.showColumnConfig,
    setShowColumnConfig: tableActions.setShowColumnConfig,
    jobsColumnWidths: tableState.jobsColumnWidths,
    jobsColumnOrder: tableState.jobsColumnOrder,
    jobsSortColumn: tableState.jobsSortColumn,
    jobsSortDirection: tableState.jobsSortDirection,
    draggedJobColumnId: tableState.draggedJobColumnId,
    dragOverJobColumnId: tableState.dragOverJobColumnId,
    resizingJobColumn: tableState.resizingJobColumn,
    hookToTableColumnMap: tableState.hookToTableColumnMap,
    toggleColumn: tableActions.toggleColumn,
    resetColumnsToDefault: tableActions.resetColumnsToDefault,
    saveColumnView: tableActions.saveColumnView,
    applyColumnView: tableActions.applyColumnView,
    deleteColumnView: tableActions.deleteColumnView,
    getColumnsByCategory: tableActions.getColumnsByCategory,
    handleToggleColumnConfig: tableActions.handleToggleColumnConfig,
    handleJobsSort: tableActions.handleJobsSort,
    startJobsColumnResize: tableActions.startJobsColumnResize,
    handleJobsColumnDragStart: tableActions.handleJobsColumnDragStart,
    handleJobsColumnDragOver: tableActions.handleJobsColumnDragOver,
    handleJobsColumnDragLeave: tableActions.handleJobsColumnDragLeave,
    handleJobsColumnDrop: tableActions.handleJobsColumnDrop,
    handleJobsColumnDragEnd: tableActions.handleJobsColumnDragEnd,

    // --- preview ---
    showJobPreview: previewState.showJobPreview,
    setShowJobPreview: previewActions.setShowJobPreview,
    previewJob: previewState.previewJob,
    setPreviewJob: previewActions.setPreviewJob,
    activePreviewTab: previewState.activePreviewTab,
    setActivePreviewTab: previewActions.setActivePreviewTab,
    showFullDescription: previewState.showFullDescription,
    setShowFullDescription: previewActions.setShowFullDescription,
    showStageDates: previewState.showStageDates,
    showExpandedDetails: previewState.showExpandedDetails,
    jobDataForm: previewState.jobDataForm,
    setJobDataForm: previewActions.setJobDataForm,
    openJobDataSections: previewState.openJobDataSections,
    setOpenJobDataSections: previewActions.setOpenJobDataSections,
    savingSection: previewState.savingSection,
    newJobDataBenefit: previewState.newJobDataBenefit,
    setNewJobDataBenefit: previewActions.setNewJobDataBenefit,
    newJobDataLang: previewState.newJobDataLang,
    setNewJobDataLang: previewActions.setNewJobDataLang,
    newJobDataLangLevel: previewState.newJobDataLangLevel,
    setNewJobDataLangLevel: previewActions.setNewJobDataLangLevel,
    jobMetrics: previewState.jobMetrics,
    isLoadingJobMetrics: previewState.isLoadingJobMetrics,
    previewWidth: previewState.previewWidth,
    setPreviewWidth: previewActions.setPreviewWidth,
    isResizingPreview: previewState.isResizingPreview,
    setIsResizingPreview: previewActions.setIsResizingPreview,
    screeningConfig: previewState.screeningConfig,
    isLoadingScreeningConfig: previewState.isLoadingScreeningConfig,
    updateScreeningConfig: previewActions.updateScreeningConfig,
    screeningConfigExpanded: previewState.screeningConfigExpanded,
    setScreeningConfigExpanded: previewActions.setScreeningConfigExpanded,
    isEditingScreeningConfig: previewState.isEditingScreeningConfig,
    setIsEditingScreeningConfig: previewActions.setIsEditingScreeningConfig,
    editChannels: previewState.editChannels,
    setEditChannels: previewActions.setEditChannels,
    editMinScorePreset: previewState.editMinScorePreset,
    setEditMinScorePreset: previewActions.setEditMinScorePreset,
    editTimeoutHours: previewState.editTimeoutHours,
    setEditTimeoutHours: previewActions.setEditTimeoutHours,
    editMaxRetries: previewState.editMaxRetries,
    setEditMaxRetries: previewActions.setEditMaxRetries,
    editAutoApprovalPreset: previewState.editAutoApprovalPreset,
    setEditAutoApprovalPreset: previewActions.setEditAutoApprovalPreset,
    showScreeningChannelsModal: previewState.showScreeningChannelsModal,
    setShowScreeningChannelsModal: previewActions.setShowScreeningChannelsModal,
    showScreeningSettingsModal: previewState.showScreeningSettingsModal,
    setShowScreeningSettingsModal: previewActions.setShowScreeningSettingsModal,
    showScreeningSchedulingModal: previewState.showScreeningSchedulingModal,
    setShowScreeningSchedulingModal: previewActions.setShowScreeningSchedulingModal,
    showQuestionEditModal: previewState.showQuestionEditModal,
    setShowQuestionEditModal: previewActions.setShowQuestionEditModal,
    screeningBlockExpanded: previewState.screeningBlockExpanded,
    setScreeningBlockExpanded: previewActions.setScreeningBlockExpanded,
    isEditingScreening: previewState.isEditingScreening,
    setIsEditingScreening: previewActions.setIsEditingScreening,
    selectedBlock: previewState.selectedBlock,
    setSelectedBlock: previewActions.setSelectedBlock,
    adjustmentDiffs: previewState.adjustmentDiffs,
    setAdjustmentDiffs: previewActions.setAdjustmentDiffs,
    adjustmentIterations: previewState.adjustmentIterations,
    setAdjustmentIterations: previewActions.setAdjustmentIterations,
    isGeneratingWSI: previewState.isGeneratingWSI,
    setIsGeneratingWSI: previewActions.setIsGeneratingWSI,
    pendingAdjustedQuestions: previewState.pendingAdjustedQuestions,
    setPendingAdjustedQuestions: previewActions.setPendingAdjustedQuestions,
    acceptedQuestions: previewState.acceptedQuestions,
    setAcceptedQuestions: previewActions.setAcceptedQuestions,
    wsiGenerationMode: previewState.wsiGenerationMode,
    setWsiGenerationMode: previewActions.setWsiGenerationMode,
    wsiGenerationCompleted: previewState.wsiGenerationCompleted,
    setWsiGenerationCompleted: previewActions.setWsiGenerationCompleted,
    wsiProgressCollapsed: previewState.wsiProgressCollapsed,
    setWsiProgressCollapsed: previewActions.setWsiProgressCollapsed,
    wsiGeneratedCount: previewState.wsiGeneratedCount,
    setWsiGeneratedCount: previewActions.setWsiGeneratedCount,
    wsiGenerationStep: previewState.wsiGenerationStep,
    setWsiGenerationStep: previewActions.setWsiGenerationStep,
    wsiDynamicMessage: previewState.wsiDynamicMessage,
    setWsiDynamicMessage: previewActions.setWsiDynamicMessage,
    wsiGenerationContext: previewState.wsiGenerationContext,
    setWsiGenerationContext: previewActions.setWsiGenerationContext,
    activeDashboardModal: previewState.activeDashboardModal,
    setActiveDashboardModal: previewActions.setActiveDashboardModal,
    showWSITutorialModal: previewState.showWSITutorialModal,
    setShowWSITutorialModal: previewActions.setShowWSITutorialModal,
    dashboardPeriod: previewState.dashboardPeriod,
    setDashboardPeriod: previewActions.setDashboardPeriod,
    showReport: previewState.showReport,
    reportJob: previewState.reportJob,
    showCreateJobModal: previewState.showCreateJobModal,
    setShowCreateJobModal: previewActions.setShowCreateJobModal,
    setPendingNavigateJobId: previewActions.setPendingNavigateJobId,
    handleJobPreview: previewActions.handleJobPreview,
    handleSaveJobDataSection: previewActions.handleSaveJobDataSection,
    handleScreeningStatusChange: previewActions.handleScreeningStatusChange,
    handleUpdateJobField: previewActions.handleUpdateJobField,
    handleShowReport: previewActions.handleShowReport,
    handleCloseReport: previewActions.handleCloseReport,

    // --- bulk actions ---
    selectedJobsForBatch: bulkState.selectedJobsForBatch,
    setSelectedJobsForBatch: bulkActions.setSelectedJobsForBatch,
    pinnedJobs: bulkState.pinnedJobs,
    urgentJobs: bulkState.urgentJobs,
    favoriteJobs: bulkState.favoriteJobs,
    showCompareModal: bulkState.showCompareModal,
    setShowCompareModal: bulkActions.setShowCompareModal,
    showPublishModal: bulkState.showPublishModal,
    setShowPublishModal: bulkActions.setShowPublishModal,
    showUnpublishModal: bulkState.showUnpublishModal,
    setShowUnpublishModal: bulkActions.setShowUnpublishModal,
    showInsightsModal: bulkState.showInsightsModal,
    setShowInsightsModal: bulkActions.setShowInsightsModal,
    showDuplicateModal: bulkState.showDuplicateModal,
    setShowDuplicateModal: bulkActions.setShowDuplicateModal,
    showStatusModal: bulkState.showStatusModal,
    setShowStatusModal: bulkActions.setShowStatusModal,
    showAssignRecruiterModal: bulkState.showAssignRecruiterModal,
    setShowAssignRecruiterModal: bulkActions.setShowAssignRecruiterModal,
    statusModalMode: bulkState.statusModalMode,
    companyRecruiters: bulkState.companyRecruiters,
    isLoadingRecruiters: bulkState.isLoadingRecruiters,
    showReactivateScreeningDialog: bulkState.showReactivateScreeningDialog,
    setShowReactivateScreeningDialog: bulkActions.setShowReactivateScreeningDialog,
    reactivateScreeningJobs: bulkState.reactivateScreeningJobs,
    setReactivateScreeningJobs: bulkActions.setReactivateScreeningJobs,
    reactivateEndDate: bulkState.reactivateEndDate,
    setReactivateEndDate: bulkActions.setReactivateEndDate,
    selectAllJobs: bulkActions.selectAllJobs,
    deselectAllJobs: bulkActions.deselectAllJobs,
    toggleJobSelection: bulkActions.toggleJobSelection,
    togglePinJob: bulkActions.togglePinJob,
    toggleUrgentJob: bulkActions.toggleUrgentJob,
    toggleFavoriteJob: bulkActions.toggleFavoriteJob,
    handleJobCompare: bulkActions.handleJobCompare,
    handleJobPublish: bulkActions.handleJobPublish,
    handleJobInsights: bulkActions.handleJobInsights,
    handleJobDuplicate: bulkActions.handleJobDuplicate,
    handleJobToggleStatus: bulkActions.handleJobToggleStatus,
    handleJobAssignRecruiter: bulkActions.handleJobAssignRecruiter,
    getSelectedJobsHaveActiveStatus: bulkActions.getSelectedJobsHaveActiveStatus,
    handleJobArchive: bulkActions.handleJobArchive,
    isArchivingJobs: bulkState.isArchivingJobs,

    // --- chat (orquestrador LIA + abertura do chat flutuante unificado) ---
    liaMessages: chatState.liaMessages,
    isLiaProcessing: chatState.isLiaProcessing,
    jobsConversationId: chatState.jobsConversationId,
    orchestratorSuggestions: chatState.orchestratorSuggestions,
    dynamicSuggestions: chatState.dynamicSuggestions,
    suggestionsLoading: chatState.suggestionsLoading,
    dynamicInsights: chatState.dynamicInsights,
    insightsLoading: chatState.insightsLoading,
    liaResponse: chatState.liaResponse,
    liaPromptLoading: chatState.liaPromptLoading,
    followUpSuggestions: chatState.followUpSuggestions,
    openGeneralChat: chatActions.openGeneralChat,
    openJobCreationChat: chatActions.openJobCreationChat,
    handleAICommand: chatActions.handleAICommand,
    getContextualSuggestions: chatActions.getContextualSuggestions,
  }
}
