"use client"

import React from "react"
import dynamic from "next/dynamic"

const BigFiveModal = dynamic(() => import("@/components/big-five-modal").then(m => m.BigFiveModal), { ssr: false })
import { SCREENING_STATUS_LABELS, type ScreeningStatus } from "@/types/screening"
import { liaApi } from "@/services/lia-api"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import {
  RECRUITMENT_STAGES,
  getStageByName,
  getSubStatusDisplayName,
  getCompanyPipelineStages,
} from "@/lib/recruitment-stages"
import {
  ArrowLeft, ArrowRight, Layers3, FileText, TrendingUp, Briefcase, MapPin, ListChecks, ChevronRight, ChevronUp, ChevronDown, ChevronLeft,
  ClipboardList, MessageCircle, Clock, Brain, Send, Code, Globe, BrainCircuit, Flag, Linkedin, Languages,
  CheckCircle, AlertCircle, AlertTriangle, X, Download, Share2, Settings, User, Mic, Search, Filter,
  Plus, Users, Star, Heart, MoreVertical, MoreHorizontal, Eye, Calendar, CalendarCheck, Archive, Mail, Phone, Video,
  Trophy, XCircle, ThumbsUp, Target, MessageSquareText, MessageSquare, Building, BarChart3, DollarSign, Activity,
  ArrowUp, ArrowDown, TrendingDown, Award, Pin, Edit, Pencil, Trash2, RefreshCw, Wand2, Library, BookOpen, Folder,
  History, Gauge, UserCheck, Timer, RotateCcw, SortAsc, SortDesc, Columns, Table as TableIcon, Bell, Maximize2, ThumbsDown, ArrowUpDown, EyeOff, GripVertical, Lightbulb, Bookmark, Paperclip, ChevronsLeftRight, Copy, Fingerprint, Loader2, Save, Link2, PauseCircle, PlayCircle
} from "lucide-react"
import { type BulkActionType } from "@/components/ui/bulk-selection-bar"
import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/ui/empty-state"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
const TriagemDetailsModal = dynamic(() => import("@/components/triagem-details-modal").then(m => ({ default: m.TriagemDetailsModal })), {
  ssr: false,
  loading: () => null,
})
const JobReportModal = dynamic(() => import("@/components/job-report-modal").then(m => ({ default: m.JobReportModal })), {
  ssr: false,
  loading: () => null,
})
const SendEmailModal = dynamic(() => import("@/components/email-templates/send-email-modal").then(m => ({ default: m.SendEmailModal })), { ssr: false, loading: () => null })
const UnifiedCommunicationModal = dynamic(() => import("@/components/modals/unified-communication-modal").then(m => ({ default: m.UnifiedCommunicationModal })), { ssr: false, loading: () => null })
const AddToListModal = dynamic(() => import("@/components/modals/add-to-list-modal").then(m => ({ default: m.AddToListModal })), { ssr: false, loading: () => null })
const WSITextScreeningModal = dynamic(() => import("@/components/wsi/wsi-text-screening-modal").then(m => ({ default: m.WSITextScreeningModal })), { ssr: false, loading: () => null })
const WSITriagemInviteModal = dynamic(() => import("@/components/wsi/wsi-triagem-invite-modal").then(m => ({ default: m.WSITriagemInviteModal })), { ssr: false, loading: () => null })
const AddCandidatesToVacancyModal = dynamic(() => import("@/components/modals/add-candidates-to-vacancy-modal").then(m => ({ default: m.AddCandidatesToVacancyModal })), { ssr: false, loading: () => null })
const RubricEvaluationModal = dynamic(() => import("@/components/rubric-evaluation-modal").then(m => ({ default: m.RubricEvaluationModal })), { ssr: false, loading: () => null })
import { ScoreIconButton } from "@/components/ui/score-icon-button"
import { ScoreBreakdownBadgeLazy } from "@/components/score/ScoreBreakdownBadge"
const GeneralScoreModal = dynamic(() => import("@/components/modals/general-score-modal").then(m => ({ default: m.GeneralScoreModal })), { ssr: false, loading: () => null })
const TechnicalTestModal = dynamic(() => import("@/components/modals/technical-test-modal").then(m => ({ default: m.TechnicalTestModal })), { ssr: false, loading: () => null })
const EnglishTestModal = dynamic(() => import("@/components/modals/english-test-modal").then(m => ({ default: m.EnglishTestModal })), { ssr: false, loading: () => null })
const CandidateDecisionFlowModal = dynamic(() => import("@/components/candidate-decision-flow-modal").then(m => ({ default: m.CandidateDecisionFlowModal })), { ssr: false, loading: () => null })
const TestPreviewModal = dynamic(() => import("@/components/pages/job-kanban/TestPreviewModal").then(m => ({ default: m.TestPreviewModal })), { ssr: false, loading: () => null })
const LIASuggestionsPanel = dynamic(() => import("@/components/pages/job-kanban/LIASuggestionsPanel").then(m => ({ default: m.LIASuggestionsPanel })), { ssr: false, loading: () => null })
const TestLibraryModal = dynamic(() => import("@/components/pages/job-kanban/TestLibraryModal").then(m => ({ default: m.TestLibraryModal })), { ssr: false, loading: () => null })
const TestHistoryModal = dynamic(() => import("@/components/pages/job-kanban/TestHistoryModal").then(m => ({ default: m.TestHistoryModal })), { ssr: false, loading: () => null })
const LIAQuestionsPanel = dynamic(() => import("@/components/pages/job-kanban/LIAQuestionsPanel").then(m => ({ default: m.LIAQuestionsPanel })), { ssr: false, loading: () => null })
const CandidateCompareModal = dynamic(() => import("@/components/modals/candidate-compare-modal").then(m => ({ default: m.CandidateCompareModal })), { ssr: false, loading: () => null })

import { AISuggestionBadge } from "@/components/ai"
import { 
  UnifiedCandidateTable, 
  type TableColumn, 
  type TableSortConfig,
  getColumnDefinition,
  getDefaultTableColumns,
  COLUMN_PRESETS,
  InteractiveSubStatusCell,
  InteractiveStageCell
} from "@/components/tables"
import { 
  DataRequestIndicator, 
  type DataRequestStatus, 
  type RequestedField,
  getDataRequestStatusFromFields
} from "@/components/ui/data-request-indicator"
import { 
  StatusBadge, 
  ChannelBadge, 
  SourceBadge, 
  WarningBadge,
  DateTimeBadge,
  OriginBadge,
  AwaitingBadge,
  STAGE_PASTEL_COLORS as STATUS_BADGE_PASTEL_COLORS
} from "@/components/ui/status-badge"
import { OverrideApproveButton } from "@/components/kanban/components/OverrideApproveButton"
import type { DataRequestSubmitData } from "@/components/modals/data-request-modal"
const DataRequestModal = dynamic(() => import("@/components/modals/data-request-modal").then(m => ({ default: m.DataRequestModal })), { ssr: false, loading: () => null })
const CloseVacancyModal = dynamic(() => import("@/components/modals/close-vacancy-modal").then(m => ({ default: m.CloseVacancyModal })), { ssr: false, loading: () => null })
const JobStatusModal = dynamic(() => import("@/components/modals/job-status-modal").then(m => ({ default: m.JobStatusModal })), {
  ssr: false,
  loading: () => null,
})
const ShareSearchModal = dynamic(() => import("@/components/modals/share-search-modal").then(m => ({ default: m.ShareSearchModal })), { ssr: false, loading: () => null })
import { Checkbox } from "@/components/ui/checkbox"
import { BulkActionModal } from "@/components/modals/bulk-action-modal"
import { UnifiedBulkActionsBar, type BulkActionId } from "@/components/ui/unified-bulk-actions-bar"
import { PipelineStagesCarousel } from "@/components/ui/pipeline-stages-carousel"
import { 
  generateWorkHistory, 
  generateEducation, 
  seededRandom, 
  getSalaryByExperience,
  type CandidateForDataGeneration 
} from "@/components/kanban/mock/data-generators"
import { 
  getUrgencyLevel,
  getScoreColor,
  getScoreBgColor,
  getStageColor,
  calculateGeneralScore,
  type UrgencyLevel 
} from "@/components/kanban/utils/status-utils"
import { CandidateTableRow } from "@/components/kanban/components/CandidateTableRow"
import { ScreeningQuestionsPanel } from "@/components/job-creation"
import { JobEditTab } from "@/components/jobs/JobEditTab"
import { ColumnContextMenu } from "@/components/kanban/components/ColumnContextMenu"
import { SaturationBadge } from "@/components/kanban/components/SaturationBadge"
import { KanbanFiltersPanel } from "@/components/pages/job-kanban/KanbanFiltersPanel"
import { KanbanColumnConfigPanel } from "@/components/pages/job-kanban/KanbanColumnConfigPanel"
import { KanbanTableView } from "@/components/pages/job-kanban/KanbanTableView"
import { KanbanLIASidebar } from "@/components/pages/job-kanban/KanbanLIASidebar"
import { KanbanColumnRenderer } from "@/components/pages/job-kanban/KanbanColumnRenderer"
import { KanbanJobHeader } from "@/components/pages/job-kanban/KanbanJobHeader"
import { KanbanToolbar } from "@/components/pages/job-kanban/KanbanToolbar"

import { AddColumnPopover } from "@/components/pages/job-kanban/AddColumnPopover"
import { calculateNotaLiaGeral, getLiaAlerts, getFilteredAndSortedCandidates as getFilteredAndSortedCandidatesUtil } from "@/components/pages/job-kanban/utils/kanbanHelpers"
const CandidatePreview = dynamic(() => import("@/components/candidate-preview").then(m => ({ default: m.CandidatePreview })), { ssr: false })
const CandidatePage = dynamic(() => import("@/components/candidate-page").then(m => ({ default: m.CandidatePage })), { ssr: false })
const ExpandedChatModal = dynamic(() => import("@/components/expanded-chat-modal").then(m => ({ default: m.ExpandedChatModal })), { ssr: false })
import { useKanbanPageCore } from "@/components/pages/job-kanban/hooks/useKanbanPageCore"
import { KanbanPageModals } from "@/components/pages/job-kanban/KanbanPageModals"

export function JobKanbanPage({ job, onBack }: { job?: Record<string, unknown>, onBack?: () => void }) {
  const state = useKanbanPageCore({ job, onBack })
  const {
    viewMode, setViewMode, currentJob, jobEditForm, setJobEditForm,
    activeTab, setActiveTab, showJobEditor, setShowJobEditor,
    isCreationMode, isPublishing, publicLink, showPublishSuccess, setShowPublishSuccess,
    handlePublishJob, companyDefaults, savingJobSection,
    handleSaveJobSection, isClient, dynamicStages, setDynamicStages,
    candidatesData, setCandidatesData, isLoadingCandidates, hasMounted,
    showSuperChat, setShowSuperChat, showExpandedLIA, setShowExpandedLIA,
    userCollapsedLIA, setUserCollapsedLIA,
    showKanbanFiltersPanel, setShowKanbanFiltersPanel,
    showTableFiltersPanel, setShowTableFiltersPanel,
    showColumnConfig, setShowColumnConfig,
    kanbanScoreMin, setKanbanScoreMin, kanbanStatusFilter, setKanbanStatusFilter,
    kanbanWorkModelFilter, setKanbanWorkModelFilter, kanbanOriginFilter, setKanbanOriginFilter,
    searchQuery, setSearchQuery, selectedCandidates, setSelectedCandidates,
    allTableCandidates, proactiveInsights, dismissInsight,
    pipelineInheritance, computedSuggestions,
    liaMessages, setLiaMessages, liaPromptValue, setLiaPromptValue,
    isLiaLoading, liaExpandedWidth, setLiaExpandedWidth,
    showLiaSuggestionsPanel, setShowLiaSuggestionsPanel,
    isResizingLIA, setIsResizingLIA, chatScrollRef,
    handleAICommand, handleLiaUiAction, openSuperChat, returnToExpandedPrompt,
    selectedCandidate, setSelectedCandidate, showCandidatePage, setShowCandidatePage,
    handleOrchestratedMessage, tableStageFilter, setTableStageFilter,
    tableSortColumn, setTableSortColumn, tableSortDirection, setTableSortDirection,
    currentPage, setCurrentPage, tableColumns, setTableColumns,
    handleTableColumnResize, getPaginatedCandidates,
    saturationData, isPreviewOpen, setIsPreviewOpen,
    previewCandidate, setPreviewCandidate, isPreviewMaximized,
    handleOpenPreview, handleClosePreview, handleTogglePreviewMaximize,
    handleNavigateCandidate, handleCandidatePageOpen, handleCloseCandidatePage,
    favoriteCandidates, handleToggleFavorite, handleToggleShortList,
    handleSendEmail, handleSendWhatsApp, handleSendTriagem,
    handleSendAgendamento, handleSendFeedback,
    handleScheduleInterview, handleAddToVacancy, handleSendWSIInvite,
    handleOpenTriagem, isTriagemOpen,
    handleOpenAnalysis, handleOpenScoreModal, openDecisionFlowModal,
    handleApproveFromScreening, handleRejectFromScreening,
    handleApproveCandidate, handleRejectCandidate,
    handleBulkAction, draggedCandidate, dragOverColumn,
    handleDragStart, handleDragEnd, handleDragOver, handleDragLeave, handleDrop,
    selectedForCompare, setSelectedForCompare, viewedCandidateIds,
    aiSuggestions, approveSuggestion, rejectSuggestion,
    kanbanColumns, getColumnStyle, getStageCategory, getStageAccentStyle,
    STAGE_PASTEL_COLORS, showAddColumnPopover, setShowAddColumnPopover,
    isAddingColumn, setIsAddingColumn, newColumnName, setNewColumnName,
    showAddToVacancyModal, setShowAddToVacancyModal,
    candidateForVacancy, setCandidateForVacancy,
    pipelineStages, clearStageFilters, toggleStageFilter, getStageCount,
    jobData, _jobIdForSL, allCandidateIds, shortListedCandidateIds,
    handleInteractiveStatusChange,
    handleTableTransitionRequest, handleTransitionRequired,
    setSelectedCandidateForModal, setActiveModal,
    setShowBigFiveModal, scoreModalCandidate,
    // @ts-ignore TODO: fix type
    getDataRequestForCandidate, handleDataRequestResend, handleDataRequestViewDetails,
    setTransitionInitialPrompt, setTransitionAllowStageSelection, setTransitionInterviewAlert,
    openTransition, router, user, toast,
    handleInlineRename, handleInlineToggleActive, handleInlineRemove,
    handleInlineMoveLeft, handleInlineMoveRight, handleInlineUpdateSLA,
    handleSaveJobSection: handleSaveJobSectionFromHook,
    showReport, setShowReport, handleCloseReport, handleShowReport,
    showExpandedMetrics, setShowExpandedMetrics,
    showTestLibrary, setShowTestLibrary,
    showTestPreview, setShowTestPreview,
    showTestHistory, setShowTestHistory,
    showLiaSuggestions, setShowLiaSuggestions,
    showTriagemSuggestions, setShowTriagemSuggestions,
    isEditMode, setIsEditMode,
    isEditModeTriagem, setIsEditModeTriagem,
    columnSearchTerm, setColumnSearchTerm,
    showApresentacaoPrompt, setShowApresentacaoPrompt,
    showConceptualPrompt, setShowConceptualPrompt,
    showConceptualPromptTriagem, setShowConceptualPromptTriagem,
    showFechamentoPrompt, setShowFechamentoPrompt,
    expandedCronograma, setExpandedCronograma,
    expandedRoteiro, setExpandedRoteiro,
    expandedTesteTecnico, setExpandedTesteTecnico,
    expandedTesteIngles, setExpandedTesteIngles,
    editingQuestion, setEditingQuestion,
    editingSection, setEditingSection,
    habilidadesTecnicas, setHabilidadesTecnicas,
    isSkillWeightsModified, setIsSkillWeightsModified,
    inferredBehavior, setInferredBehavior,
    perguntasEliminatorias, setPerguntasEliminatorias,
    perguntasInformativas, setPerguntasInformativas,
    perguntasSituacionais, setPerguntasSituacionais,
    perguntasTecnicasAvaliacao, setPerguntasTecnicasAvaliacao,
    jobLocalOverrides, setJobLocalOverrides,
    handleTableSort, startTableColumnResize,
    handleTableColumnDragStart, handleTableColumnDragOver,
    handleTableColumnDragLeave, handleTableColumnDrop, handleTableColumnDragEnd,
    draggedTableColumnId, dragOverTableColumnId,
    setJobStatusModalMode,
    getConversionRate,
    getAllCandidates,
    getFilteredAndSortedCandidates,
    filterCandidates,
    handleBulkActionExecute,
    handleStartWSITextScreening,
    statusModalOpen, pendingMove, confirmMove, cancelMove,
    getSuggestedSubStatus, getAvailableSubStatuses, getSubStatusColor,
    getStageDisplayName, selectedSubStatus, setSelectedSubStatus,
    markCandidateAsViewed, findCandidateById,
    liaConversationId, liaSearchQuery, setLiaSearchQuery,
    showDecisionFlowModal, setShowDecisionFlowModal,
    decisionFlowCandidate, setDecisionFlowCandidate,
    decisionFlowType, handleDecisionFlowConfirm,
    showEmailModal, setShowEmailModal, emailCandidate, setEmailCandidate,
    unifiedModalOpen, unifiedModalCandidate, unifiedModalType, unifiedModalSituation,
    handleUnifiedModalClose, openUnifiedModal,
    showRubricModal, rubricCandidate, rubricEvaluationData, handleRubricModalClose,
    showWSIModal, setShowWSIModal, wsiCandidate, setWsiCandidate,
    showWSIInviteModal, setShowWSIInviteModal,
    wsiInviteCandidate, setWsiInviteCandidate,
    showAddToListModal, setShowAddToListModal,
    showBigFiveModal, selectedCandidateForModal,
    showGeneralScoreModal, setShowGeneralScoreModal,
    showTechnicalTestModal, setShowTechnicalTestModal,
    showEnglishTestModal, setShowEnglishTestModal,
    showCompareModal, setShowCompareModal, compareCandidates, setCompareCandidates,
    activeModal, setActiveModal: _setActiveModalAlias,
    universalModalState, closeTransition,
    handleUniversalTransitionConfirm, handleOpenSpecializedModal,
    transitionInitialPrompt, transitionAllowStageSelection, transitionInterviewAlert,
    showDataRequestModal, setShowDataRequestModal,
    dataRequestModalCandidate, setDataRequestModalCandidate,
    handleDataRequestSubmit,
    showBulkActionModal, setShowBulkActionModal, bulkActionType,
    showJobStatusModal, setShowJobStatusModal, jobStatusModalMode,
    showCloseVacancyModal, setShowCloseVacancyModal,
    showShareGestorModal, setShowShareGestorModal,
    _companyIdForSL,
    activeShortListId, stagesRequiringConfirmation,
    returnEvents, getAlertForCandidate, computeAlerts, hasAlerts,
    saveJobsState, talentFunnel,
    handleCloseCandidatePage: _handleCloseCP,
    triagemCandidate,
    handleCloseTriagem, handleTriagemApprove, handleTriagemReject,
    liaSuggestionsData,
    selectedTriagemQuestion,
    selectedTestForHistory,
    isAddingToList,
    calculateNotaLiaGeral,
    setDecisionFlowType,
    setScoreModalCandidate,
  } = state

  const renderKanbanColumn = (stageId: string, candidates: Record<string, unknown>[], colorClass: string, bgClass: string) => (
    <KanbanColumnRenderer
      stageId={stageId}
      candidates={candidates as unknown as Parameters<typeof KanbanColumnRenderer>[0]["candidates"]}
      colorClass={colorClass}
      bgClass={bgClass}
      dynamicStages={dynamicStages}
      searchQuery={searchQuery}
      draggedCandidate={draggedCandidate as unknown as Parameters<typeof KanbanColumnRenderer>[0]["draggedCandidate"]}
      dragOverColumn={dragOverColumn}
      selectedCandidates={selectedCandidates}
      selectedForCompare={selectedForCompare}
      viewedCandidateIds={viewedCandidateIds}
      favoriteCandidates={favoriteCandidates}
      shortListedCandidateIds={shortListedCandidateIds}
      aiSuggestions={aiSuggestions as unknown as Parameters<typeof KanbanColumnRenderer>[0]["aiSuggestions"]}
      kanbanScoreMin={kanbanScoreMin}
      kanbanStatusFilter={kanbanStatusFilter}
      kanbanWorkModelFilter={kanbanWorkModelFilter}
      kanbanOriginFilter={kanbanOriginFilter}
      currentJob={currentJob}
      _jobIdForSL={_jobIdForSL}
      getColumnStyle={getColumnStyle}
      getStageCategory={getStageCategory}
      calculateNotaLiaGeral={calculateNotaLiaGeral}
      getDataRequestForCandidate={getDataRequestForCandidate as unknown as Parameters<typeof KanbanColumnRenderer>[0]["getDataRequestForCandidate"]}
      setSelectedCandidates={setSelectedCandidates}
      setSelectedForCompare={setSelectedForCompare}
      setCandidatesData={setCandidatesData as unknown as Parameters<typeof KanbanColumnRenderer>[0]["setCandidatesData"]}
      setTransitionInitialPrompt={setTransitionInitialPrompt}
      setTransitionInterviewAlert={setTransitionInterviewAlert}
      setTransitionAllowStageSelection={setTransitionAllowStageSelection}
      setDecisionFlowCandidate={setDecisionFlowCandidate}
      setDecisionFlowType={setDecisionFlowType}
      setShowDecisionFlowModal={setShowDecisionFlowModal}
      onDragStart={handleDragStart as unknown as Parameters<typeof KanbanColumnRenderer>[0]["onDragStart"]}
      onDragEnd={handleDragEnd}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onDragLeave={handleDragLeave}
      onOpenPreview={handleOpenPreview}
      onSendEmail={handleSendEmail}
      onSendWhatsApp={handleSendWhatsApp}
      onScheduleInterview={handleScheduleInterview}
      onToggleFavorite={handleToggleFavorite}
      onToggleShortList={handleToggleShortList}
      onOpenAnalysis={handleOpenAnalysis as unknown as Parameters<typeof KanbanColumnRenderer>[0]["onOpenAnalysis"]}
      onOpenScoreModal={handleOpenScoreModal}
      onOpenDecisionFlowModal={openDecisionFlowModal as unknown as Parameters<typeof KanbanColumnRenderer>[0]["onOpenDecisionFlowModal"]}
      onSendWSIInvite={handleSendWSIInvite}
      onSendFeedback={handleSendFeedback}
      onApproveFromScreening={handleApproveFromScreening as unknown as Parameters<typeof KanbanColumnRenderer>[0]["onApproveFromScreening"]}
      onRejectFromScreening={handleRejectFromScreening as unknown as Parameters<typeof KanbanColumnRenderer>[0]["onRejectFromScreening"]}
      onInlineRename={handleInlineRename}
      onInlineToggleActive={handleInlineToggleActive}
      onInlineRemove={handleInlineRemove}
      onInlineMoveLeft={handleInlineMoveLeft}
      onInlineMoveRight={handleInlineMoveRight}
      onInlineUpdateSLA={handleInlineUpdateSLA}
      onOpenSettings={() => router.push('/configuracoes')}
      onDataRequestResend={handleDataRequestResend}
      onDataRequestViewDetails={handleDataRequestViewDetails}
      approveSuggestion={approveSuggestion}
      rejectSuggestion={rejectSuggestion}
      openTransition={openTransition as unknown as Parameters<typeof KanbanColumnRenderer>[0]["openTransition"]}
    />
  )
  // Renderização apenas no cliente para evitar erros de hidratação SSR
  if (!isClient) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50" role="status" aria-live="polite" aria-label="Carregando...">
        <div className="flex flex-col items-center gap-4" role="status" aria-live="polite" aria-label="Carregando...">
          <div className="animate-spin motion-reduce:animate-none rounded-full h-8 w-8 border-b-2 border-gray-600" role="status" aria-live="polite" aria-label="Carregando..."></div>
          <span className="text-sm text-lia-text-tertiary font-['Open_Sans']">Carregando...</span>
        </div>
      </div>
    )
  }

  return (
    <>
      <style jsx>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.7;
          }
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: scale(0.95);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        .dragging {
          opacity: 0.5;
          cursor: grabbing !important;
        }

        .drop-zone-active {
          background-color: var(--wedo-cyan-bg-05);
          border-color: 'var(--wedo-cyan)';
        }
      `}</style>

    <div className="h-screen bg-gray-50 dark:bg-lia-bg-primary flex flex-col overflow-hidden">
      {/* Header Principal */}
      <KanbanJobHeader
        onBack={onBack}
        router={router}
        currentJob={currentJob}
        jobEditForm={jobEditForm}
        setJobEditForm={setJobEditForm}
        // @ts-ignore TODO: fix type
        setJobStatusModalMode={setJobStatusModalMode}
        setShowJobStatusModal={setShowJobStatusModal}
        setShowCloseVacancyModal={setShowCloseVacancyModal}
        // @ts-ignore TODO: fix type
        setActiveTab={setActiveTab}
        computedSuggestions={computedSuggestions}
        setShowExpandedLIA={setShowExpandedLIA}
        setShowLiaSuggestionsPanel={setShowLiaSuggestionsPanel}
        allTableCandidates={allTableCandidates}
        selectedCandidates={selectedCandidates}
        setSelectedCandidates={setSelectedCandidates}
        setShowShareGestorModal={setShowShareGestorModal}
        handleShowReport={handleShowReport}
        activeTab={activeTab}
        setShowJobEditor={setShowJobEditor}
        pipelineInheritance={pipelineInheritance}
        setJobLocalOverrides={setJobLocalOverrides}
        toast={toast}
      />

      {/* D8 — Insights Proativos (dismiss por sessão via localStorage) */}
      {proactiveInsights.length > 0 && activeTab === 'management' && (
        <div className="px-4 py-2 space-y-1.5">
          {proactiveInsights.slice(0, 3).map(insight => (
            <div
              key={insight.id}
              className={`flex items-start gap-2 px-3 py-2 rounded-md border text-xs ${
                insight.urgency === 'urgent' ? 'bg-status-error/10 border-status-error/30 text-status-error' :
                insight.urgency === 'high' ? 'bg-status-warning/10 border-status-warning/30 text-status-warning' :
                'bg-gray-50 border-lia-border-subtle text-lia-text-secondary'
              }`}
            >
              <span className="font-medium flex-shrink-0">{insight.title}</span>
              <span className="flex-1">{insight.message}</span>
              <button
                onClick={() => dismissInsight(insight.id)}
                className="flex-shrink-0 opacity-50 hover:opacity-100"
                aria-label="Dispensar"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'edit' ? (
        <div className="flex-1 overflow-y-auto bg-white dark:bg-lia-bg-primary">
          <div className="px-4 py-4 pb-12">
            <JobEditTab
              jobEditForm={jobEditForm}
              setJobEditForm={setJobEditForm}
              onSaveSection={handleSaveJobSection}
              savingSection={savingJobSection}
              companyDefaults={companyDefaults}
              job={currentJob}
              onJobUpdate={(updatedJob) => {
                setJobEditForm((prev: Record<string, unknown>) => ({ ...prev, ...updatedJob }))
                setJobLocalOverrides((prev) => ({ ...prev, ...updatedJob }))
              }}
              onFormUpdate={(updates) => {
                setJobEditForm((prev: Record<string, unknown>) => ({ ...prev, ...updates }))
              }}
              isCreationMode={isCreationMode}
              onPublish={handlePublishJob}
              isPublishing={isPublishing}
              publicLink={publicLink}
            />
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-hidden bg-gray-100 dark:bg-lia-bg-primary flex flex-col min-w-0">
          {/* Pipeline Flow - Cards do Funil (apenas no modo Tabela) */}
          {viewMode === "table" && (
            <div className="flex-shrink-0 bg-white dark:bg-lia-bg-primary px-4 py-2 border-b border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="w-full">
                <div className="flex items-center gap-2">
                  {tableStageFilter.length > 0 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={clearStageFilters}
                      className="h-6 text-micro gap-1 flex-shrink-0 px-2"
                    >
                      <X className="w-3 h-3" />
                      Limpar
                    </Button>
                  )}
                  <PipelineStagesCarousel
                    stages={pipelineStages.map(stage => ({
                      id: stage.id,
                      name: stage.id,
                      displayName: stage.name,
                      count: getStageCount(stage.name),
                    }))}
                    selectedStages={tableStageFilter}
                    onStageClick={(stageId) => {
                      const stage = pipelineStages.find(s => s.id === stageId)
                      if (stage) toggleStageFilter(stage.name)
                    }}
                    className="flex-1"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Bulk Actions Banner - Componente Unificado */}
          {selectedCandidates.size > 0 && (
            <div className="flex-shrink-0 px-4 py-2">
              <UnifiedBulkActionsBar
                context="vacancy"
                selectedCount={selectedCandidates.size}
                totalCount={allTableCandidates.length}
                showSelectAll={true}
                isAllSelected={selectedCandidates.size === allTableCandidates.length && allTableCandidates.length > 0}
                onSelectAll={() => {
                  if (selectedCandidates.size === allTableCandidates.length) {
                    setSelectedCandidates(new Set())
                  } else {
                    setSelectedCandidates(new Set(allTableCandidates.map(c => c.id as string)))
                  }
                }}
                onDeselectAll={() => setSelectedCandidates(new Set())}
                onAction={(actionId) => handleBulkAction(actionId as BulkActionType | string)}
              />
            </div>
          )}

          {/* Controles de Visualização e Filtros */}
          <KanbanToolbar
            showExpandedLIA={showExpandedLIA}
            setShowExpandedLIA={setShowExpandedLIA}
            liaPromptValue={liaPromptValue}
            setLiaPromptValue={setLiaPromptValue}
            handleAICommand={handleAICommand}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            viewMode={viewMode}
            // @ts-ignore TODO: fix type
            setViewMode={setViewMode}
            showKanbanFiltersPanel={showKanbanFiltersPanel}
            setShowKanbanFiltersPanel={setShowKanbanFiltersPanel}
            showTableFiltersPanel={showTableFiltersPanel}
            setShowTableFiltersPanel={setShowTableFiltersPanel}
            showColumnConfig={showColumnConfig}
            setShowColumnConfig={setShowColumnConfig}
            // @ts-ignore TODO: fix type
            tableColumns={tableColumns}
            selectedCandidates={selectedCandidates}
            setSelectedCandidates={setSelectedCandidates}
            allTableCandidates={allTableCandidates}
            candidatesData={candidatesData as Record<string, Array<Record<string, unknown>>>}
            tableStageFilter={tableStageFilter}
            kanbanScoreMin={kanbanScoreMin}
            kanbanStatusFilter={kanbanStatusFilter}
            kanbanWorkModelFilter={kanbanWorkModelFilter}
            kanbanOriginFilter={kanbanOriginFilter}
          />

          {/* Container Principal com LIA Sidebar Unificada */}
          <div className="flex-1 flex gap-2 overflow-hidden bg-gray-50 dark:bg-lia-bg-primary min-w-0">
            {/* Super Chat Expandido - Ocupa a maior parte da tela, deixando apenas uma coluna visível */}
            {showSuperChat && (
              <>
              <div 
                className="flex-1 transition-colors motion-reduce:transition-none duration-300 pl-4 py-4 pr-0 min-w-0"
                style={{maxWidth: 'calc(100% - 48px)'}}
              >
                <div className="h-full flex flex-col">
                  <ExpandedChatModal
                    isOpen={true}
                    onClose={() => {
                      setShowSuperChat(false)
                      setUserCollapsedLIA(true)
                    }}
                    initialMessage={liaPromptValue}
                    initialMessages={liaMessages.map(msg => ({
                      id: msg.id,
                      role: msg.type === 'user' ? 'user' : 'assistant',
                      content: msg.content,
                      timestamp: new Date(msg.timestamp)
                    }))}
                    contextTitle="Análise de Candidatos"
                    inline={true}
                    mode="general"
                    onReturnToLateral={returnToExpandedPrompt}
                    hideModeButtons={true}
                    onOrchestratedMessage={handleOrchestratedMessage}
                  />
                </div>
              </div>

              {/* Barra Vertical de Navegação - Estilo colapsado com ícones */}
              <div className="flex-shrink-0 w-12 transition-colors motion-reduce:transition-none duration-300 py-4 pr-2">
                <div className="h-[calc(100vh-12rem)] flex flex-col items-center bg-lia-bg-primary border border-lia-border-subtle rounded-md py-3 gap-2">
                  {/* Botão Expandir */}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowSuperChat(false)}
                    className="h-8 w-8 p-0 rounded-md hover:bg-gray-100"
                    title="Expandir visualização"
                  >
                    <ChevronRight className="w-4 h-4 text-lia-text-tertiary" />
                  </Button>
                  
                  <div className="w-6 h-px bg-gray-200 my-1" />
                  
                  {/* Ícone HubSpot/Integração */}
                  <div className="flex flex-col items-center gap-1 py-2 cursor-pointer hover:bg-gray-50 rounded-md px-2 transition-colors motion-reduce:transition-none">
                    <div className="w-6 h-6 rounded-full bg-wedo-orange flex items-center justify-center">
                      <span className="text-white text-micro font-bold">H</span>
                    </div>
                  </div>
                  
                  {/* Ícone Ações/Automação */}
                  <div className="flex flex-col items-center gap-1 py-2 cursor-pointer hover:bg-gray-50 rounded-md px-2 transition-colors motion-reduce:transition-none">
                    <div className="w-6 h-6 rounded-full bg-status-warning flex items-center justify-center">
                      <Brain className="w-3.5 h-3.5 text-white" />
                    </div>
                  </div>
                  
                  <div className="flex-1" />
                  
                  {/* Candidatos - Texto Vertical */}
                  <div 
                    className="flex flex-col items-center gap-1 py-3 cursor-pointer hover:bg-gray-50 rounded-md px-1 transition-colors motion-reduce:transition-none border-r-2 border-gray-900 dark:border-lia-border-medium"
                    onClick={() => setShowSuperChat(false)}
                  >
                    <Users className="w-4 h-4 text-lia-text-secondary" />
                    <span 
                      className="text-micro font-medium text-lia-text-secondary tracking-wide"
                      style={{writingMode: 'vertical-rl', textOrientation: 'mixed'}}
                     aria-live="polite" aria-atomic="true">
                      Candidatos ({Object.values(candidatesData).flat().length})
                    </span>
                  </div>
                </div>
              </div>
            </>
            )}

            {/* LIA Sidebar Unificada - Visível em ambos os modos (Kanban e Tabela) */}
            {showExpandedLIA && !showSuperChat && (
              <KanbanLIASidebar
                liaMessages={liaMessages as unknown as Parameters<typeof KanbanLIASidebar>[0]["liaMessages"]}
                liaPromptValue={liaPromptValue}
                isLiaLoading={isLiaLoading}
                liaExpandedWidth={liaExpandedWidth}
                computedSuggestions={computedSuggestions}
                showLiaSuggestionsPanel={showLiaSuggestionsPanel}
                selectedCandidates={selectedCandidates}
                isResizingLIA={isResizingLIA}
                candidatesData={candidatesData as unknown as Parameters<typeof KanbanLIASidebar>[0]["candidatesData"]}
                chatScrollRef={chatScrollRef as unknown as Parameters<typeof KanbanLIASidebar>[0]["chatScrollRef"]}
                setLiaMessages={setLiaMessages as unknown as Parameters<typeof KanbanLIASidebar>[0]["setLiaMessages"]}
                setLiaPromptValue={setLiaPromptValue}
                setLiaExpandedWidth={setLiaExpandedWidth}
                setShowExpandedLIA={setShowExpandedLIA}
                setUserCollapsedLIA={setUserCollapsedLIA}
                setShowLiaSuggestionsPanel={setShowLiaSuggestionsPanel}
                setSelectedCandidates={setSelectedCandidates}
                setIsResizingLIA={setIsResizingLIA}
                setSelectedCandidate={setSelectedCandidate}
                setShowCandidatePage={setShowCandidatePage}
                openSuperChat={openSuperChat}
                handleAICommand={handleAICommand}
                handleLiaUiAction={handleLiaUiAction}
              />
            )}

            {/* Visualização Kanban */}
            {viewMode === "kanban" && !showSuperChat && (
              <>
              {/* Painel de Filtros - KANBAN */}
              <KanbanFiltersPanel
                open={showKanbanFiltersPanel}
                onClose={() => setShowKanbanFiltersPanel(false)}
                scoreMin={kanbanScoreMin}
                onScoreMinChange={setKanbanScoreMin}
                statusFilter={kanbanStatusFilter}
                onStatusFilterChange={setKanbanStatusFilter}
                originFilter={kanbanOriginFilter}
                onOriginFilterChange={setKanbanOriginFilter}
                workModelFilter={kanbanWorkModelFilter}
                onWorkModelFilterChange={setKanbanWorkModelFilter}
              />

              <div className="flex-1 overflow-x-auto overflow-y-hidden" suppressHydrationWarning>
                <div className="p-4 h-full" suppressHydrationWarning>
                  {(!hasMounted || isLoadingCandidates) ? (
                    <div className="flex gap-3 h-full min-w-max" suppressHydrationWarning>
                      {dynamicStages.map((stage) => (
                        <div key={stage.id} className="flex flex-col flex-1 bg-lia-bg-primary rounded-md min-w-[250px] max-w-[320px] border border-lia-border-subtle h-[calc(100vh-16rem)]" suppressHydrationWarning>
                          <div className="flex-shrink-0 p-2.5 pb-1.5">
                            <div className="flex items-center gap-1.5">
                              <div className="w-2 h-2 rounded-full animate-pulse motion-reduce:animate-none" style={{backgroundColor: stage.color}}></div>
                              <h3 className="font-medium text-xs text-lia-text-disabled">{stage.displayName}</h3>
                              <span className="text-micro text-lia-text-disabled bg-gray-100 px-1.5 py-0.5 rounded-full animate-pulse motion-reduce:animate-none">...</span>
                            </div>
                          </div>
                          <div className="flex-1 flex items-center justify-center">
                            <div className="animate-pulse motion-reduce:animate-none text-lia-text-disabled text-xs" suppressHydrationWarning>Carregando...</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (() => {
                    const totalCandidates = Object.values(candidatesData).reduce(
                      (sum, arr) => sum + (arr?.length || 0), 0
                    )
                    if (totalCandidates === 0) {
                      return (
                        <EmptyState
                          icon={<Users />}
                          title="Nenhum candidato neste pipeline ainda"
                          description="Adicione candidatos ou busque no banco de talentos para iniciar o processo."
                          action={{
                            label: "Buscar candidatos",
                            onClick: () => setShowAddToVacancyModal(true),
                          }}
                          className="h-64"
                        />
                      )
                    }
                    return (
                    <div
                      className="flex gap-3 h-full min-w-max"
                      key={`kanban-${dynamicStages.map(s => candidatesData[s.id]?.length || 0).join('-')}`}
                      suppressHydrationWarning
                    >
                      {dynamicStages.map(stage => (
                        <React.Fragment key={stage.id}>
                          {renderKanbanColumn(stage.id, candidatesData[stage.id] || [], '', '')}
                        </React.Fragment>
                      ))}
                      <div className="flex-shrink-0 w-[280px]">
                        <div 
                          className="h-full min-h-chart-sm rounded-md border-2 border-dashed border-lia-border-default hover:border-gray-400 flex flex-col items-center justify-center gap-3 cursor-pointer transition-colors motion-reduce:transition-none hover:bg-gray-50/50 group"
                          onClick={() => setShowAddColumnPopover(true)}
                        >
                          <div className="w-10 h-10 rounded-full bg-gray-100 group-hover:bg-gray-200 flex items-center justify-center transition-colors motion-reduce:transition-none">
                            <Plus className="w-5 h-5 text-lia-text-disabled group-hover:text-lia-text-secondary" />
                          </div>
                          <span className="text-xs text-lia-text-disabled group-hover:text-lia-text-secondary font-medium transition-colors motion-reduce:transition-none">
                            Adicionar Coluna
                          </span>
                        </div>
                      </div>
                      <AddColumnPopover
                        isOpen={showAddColumnPopover}
                        onClose={() => setShowAddColumnPopover(false)}
                        dynamicStages={dynamicStages as unknown as Parameters<typeof AddColumnPopover>[0]["dynamicStages"]}
                        isAddingColumn={isAddingColumn}
                        onSetIsAddingColumn={setIsAddingColumn}
                        onAddStage={(stage) => {
                          // eslint-disable-next-line @typescript-eslint/no-explicit-any
                          setDynamicStages(prev => {
                            const finalStages = prev.filter(s => s.isFinal || s.isHired || s.isRejection)
                            const activeStages = prev.filter(s => !s.isFinal && !s.isHired && !s.isRejection)
                            return [...activeStages, stage as unknown as typeof prev[0], ...finalStages]
                          })
                          setCandidatesData(prev => ({ ...prev, [stage.id]: [] }))
                        }}
                      />
                    </div>
                  )
                  })()}
                </div>
              </div>

              {/* Preview do Candidato - Painel Lateral Direito (KANBAN) */}
              {isPreviewOpen && previewCandidate && (
                <div className={`flex-shrink-0 transition-colors motion-reduce:transition-none duration-300 ${isPreviewMaximized ? 'w-[600px]' : 'w-panel-lg'}`}>
                  <div className="bg-white dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle h-[calc(100vh-6rem)] overflow-hidden">
                  <CandidatePreview
                    candidate={previewCandidate}
                    isOpen={isPreviewOpen}
                    onClose={handleClosePreview}
                    isMaximized={isPreviewMaximized}
                    onToggleMaximize={handleTogglePreviewMaximize}
                    candidates={(() => {
                      const data = candidatesData as Record<string, Record<string, unknown>[]>
                      const currentColumn = Object.keys(data).find(col => 
                        data[col].some((c: Record<string, unknown>) => c.id === previewCandidate?.id)
                      )
                      return currentColumn ? data[currentColumn] : []
                    })()}
                    currentIndex={(() => {
                      const data = candidatesData as Record<string, Record<string, unknown>[]>
                      const currentColumn = Object.keys(data).find(col => 
                        data[col].some((c: Record<string, unknown>) => c.id === previewCandidate?.id)
                      )
                      return currentColumn ? data[currentColumn].findIndex((c: Record<string, unknown>) => c.id === previewCandidate?.id) : 0
                    })()}
                    onNavigateCandidate={handleNavigateCandidate}
                    onOpenFullPage={handleCandidatePageOpen}
                    onScheduleInterview={handleScheduleInterview}
                    onAddToVacancy={handleAddToVacancy}
                    onToggleFavorite={handleToggleFavorite}
                    onWSIScreening={handleSendWSIInvite}
                    onOpenTriagemDetails={handleOpenTriagem}
                    isFavorite={previewCandidate ? favoriteCandidates.has(previewCandidate.id as string) : false}
                    onSendEmail={(candidate) => handleSendEmail(candidate)}
                    onSendWhatsApp={(candidate) => handleSendWhatsApp(candidate)}
                    onSendTriagem={(candidate) => handleSendTriagem(candidate)}
                    onSendAgendamento={(candidate) => handleSendAgendamento(candidate)}
                    onSendFeedback={(candidate) => handleSendFeedback(candidate)}
                    jobId={jobData.id?.toString()}
                  />
                  </div>
                </div>
              )}
              </>
            )}

            {/* Visualização em Tabela */}
            {viewMode === "table" && !showSuperChat && (
              <KanbanTableView
                showSuperChat={showSuperChat}
                showTableFiltersPanel={showTableFiltersPanel}
                onShowTableFiltersPanelChange={setShowTableFiltersPanel}
                dynamicStages={dynamicStages}
                tableStageFilter={tableStageFilter}
                onTableStageFilterChange={setTableStageFilter}
                tableSortColumn={tableSortColumn}
                tableSortDirection={tableSortDirection}
                onSortChange={(config) => {
                  setTableSortColumn(config.field)
                  setTableSortDirection(config.direction)
                }}
                currentPage={currentPage}
                onCurrentPageChange={setCurrentPage}
                getPaginatedCandidates={getPaginatedCandidates as unknown as Parameters<typeof KanbanTableView>[0]["getPaginatedCandidates"]}
                showColumnConfig={showColumnConfig}
                onShowColumnConfigChange={setShowColumnConfig}
                tableColumns={tableColumns}
                onTableColumnsChange={setTableColumns}
                selectedCandidates={selectedCandidates}
                onSelectionChange={setSelectedCandidates}
                jobVacancyId={jobData?.id?.toString()}
                saturationData={saturationData}
                onColumnResize={handleTableColumnResize}
                onCandidateClick={handleOpenPreview as unknown as Parameters<typeof KanbanTableView>[0]["onCandidateClick"]}
                onStatusChange={handleInteractiveStatusChange as unknown as Parameters<typeof KanbanTableView>[0]["onStatusChange"]}
                onTransitionRequest={handleTableTransitionRequest as unknown as Parameters<typeof KanbanTableView>[0]["onTransitionRequest"]}
                onTransitionRequired={handleTransitionRequired as unknown as Parameters<typeof KanbanTableView>[0]["onTransitionRequired"]}
                calculateNotaLiaGeral={calculateNotaLiaGeral}
                getLiaAlerts={getLiaAlerts}
                viewedCandidateIds={viewedCandidateIds}
                onOpenTriagem={handleOpenTriagem}
                onOpenAnalysis={handleOpenAnalysis as unknown as Parameters<typeof KanbanTableView>[0]["onOpenAnalysis"]}
                onSetSelectedCandidateForModal={setSelectedCandidateForModal}
                onSetActiveModal={setActiveModal as unknown as Parameters<typeof KanbanTableView>[0]["onSetActiveModal"]}
                onSetShowBigFiveModal={setShowBigFiveModal}
                onSetScoreModalCandidate={setScoreModalCandidate}
                getDataRequestForCandidate={getDataRequestForCandidate as unknown as Parameters<typeof KanbanTableView>[0]["getDataRequestForCandidate"]}
                onDataRequestResend={handleDataRequestResend}
                onDataRequestViewDetails={handleDataRequestViewDetails}
                onApproveFromScreening={handleApproveFromScreening as unknown as Parameters<typeof KanbanTableView>[0]["onApproveFromScreening"]}
                onRejectFromScreening={handleRejectFromScreening as unknown as Parameters<typeof KanbanTableView>[0]["onRejectFromScreening"]}
                onApproveCandidate={handleApproveCandidate as unknown as Parameters<typeof KanbanTableView>[0]["onApproveCandidate"]}
                onRejectCandidate={handleRejectCandidate as unknown as Parameters<typeof KanbanTableView>[0]["onRejectCandidate"]}
                openDecisionFlowModal={openDecisionFlowModal as unknown as Parameters<typeof KanbanTableView>[0]["openDecisionFlowModal"]}
                onSetTransitionInitialPrompt={setTransitionInitialPrompt}
                onSetTransitionAllowStageSelection={setTransitionAllowStageSelection}
                onSetTransitionInterviewAlert={setTransitionInterviewAlert}
                openTransition={openTransition as unknown as Parameters<typeof KanbanTableView>[0]["openTransition"]}
                isPreviewOpen={isPreviewOpen}
                previewCandidate={previewCandidate as unknown as Parameters<typeof KanbanTableView>[0]["previewCandidate"]}
                isPreviewMaximized={isPreviewMaximized}
                onClosePreview={handleClosePreview}
                onTogglePreviewMaximize={handleTogglePreviewMaximize}
                onNavigateCandidate={handleNavigateCandidate}
                onCandidatePageOpen={handleCandidatePageOpen}
                onScheduleInterview={handleScheduleInterview}
                onAddToVacancy={handleAddToVacancy}
                onToggleFavorite={handleToggleFavorite as unknown as Parameters<typeof KanbanTableView>[0]["onToggleFavorite"]}
                favoriteCandidates={favoriteCandidates}
                onSendWSIInvite={handleSendWSIInvite}
                onSendEmail={handleSendEmail}
                onSendWhatsApp={handleSendWhatsApp}
                onSendTriagem={handleSendTriagem as unknown as Parameters<typeof KanbanTableView>[0]["onSendTriagem"]}
                onSendAgendamento={handleSendAgendamento as unknown as Parameters<typeof KanbanTableView>[0]["onSendAgendamento"]}
                onSendFeedback={handleSendFeedback as unknown as Parameters<typeof KanbanTableView>[0]["onSendFeedback"]}
                candidatesData={candidatesData as unknown as Parameters<typeof KanbanTableView>[0]["candidatesData"]}
              />
            )}
          </div>
        </div>
      )}


      <KanbanPageModals {...state} />

    </div>
    </>
  )
}
