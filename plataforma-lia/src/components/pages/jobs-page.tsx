"use client"

import React, { useState, useRef, useEffect, useMemo } from"react"
import { useRouter } from"next/navigation"
import dynamic from"next/dynamic"
import { Button } from"@/components/ui/button"
import { WSITutorialModal } from"@/components/pages/jobs/WSITutorialModal"
import { EmptyState } from"@/components/ui/empty-state"
import { LiaPromptHeader } from"@/components/ui/lia-prompt-header"
import { Card, CardContent } from"@/components/ui/card"
import { Badge } from"@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import { Input } from"@/components/ui/input"
import { AISearchToggle } from"@/components/ai-search-toggle"
import { IntelligenceNotifications } from"@/components/intelligence-notifications"
import { Search, Plus, MapPin, Calendar, Users, DollarSign, Eye, Edit, Edit2, Share2, Clock, Layout, Layers3, Layers, ChevronDown, ChevronUp, ChevronLeft, BarChart3, TrendingUp, TrendingDown, FileText, ExternalLink, Briefcase, Building, Building2, Target, CheckCircle, CheckCircle2, XCircle, Linkedin, Globe, Shield, Hash, UserCheck, Heart, MoreHorizontal, Grid3X3, List, Maximize2, Minimize2, Star, Brain, Expand, Copy, MessageSquare, MoreVertical, Settings, Settings2, X, ChevronsLeftRight, Bell, Pin, Github, Mail, Lock, LockOpen, MessageCircle, AlertCircle, AlertTriangle, ShieldAlert, Lightbulb, ChevronRight, Home, Zap, ClipboardList, ListChecks, CalendarCheck, ThumbsUp, Phone, Send, Bookmark, Paperclip, Mic, GripVertical, ArrowUp, ArrowDown, ArrowUpDown, Filter, Award, Trash2, RefreshCw, ArrowRight, ArrowLeft, HelpCircle, Timer, GraduationCap, BookOpen, Scale, Loader2, History, Languages, UserCircle, CalendarDays, Link, Save, Check, RotateCcw, CalendarClock, Info, Archive, Gauge } from"lucide-react"
import { JobKanbanPage } from"./job-kanban-page"
const JobReportModal = dynamic(() => import("@/components/job-report-modal").then(m => ({ default: m.JobReportModal })), {
  ssr: false,
  loading: () => null,
})
import { JobActionsBar } from"@/components/job-actions-bar"
import { JobCompareModal } from"@/components/modals/job-compare-modal"
import { JobPublishModal } from"@/components/modals/job-publish-modal"
const JobUnpublishModal = dynamic(() => import("@/components/modals/job-unpublish-modal").then(m => ({ default: m.JobUnpublishModal })), {
  ssr: false,
  loading: () => null,
})
import type { UnpublishData } from"@/components/modals/job-unpublish-modal"
import { JobInsightsModal } from"@/components/modals/job-insights-modal"
import { JobDuplicateModal } from"@/components/modals/job-duplicate-modal"
const JobStatusModal = dynamic(() => import("@/components/modals/job-status-modal").then(m => ({ default: m.JobStatusModal })), {
  ssr: false,
  loading: () => null,
})
import { JobAssignRecruiterModal } from"@/components/modals/job-assign-recruiter-modal"
const EditJobModal = dynamic(() => import("@/components/modals/edit-job-modal").then(m => ({ default: m.EditJobModal })), {
  ssr: false,
  loading: () => null,
})
import { CreateJobModal } from"@/components/modals/create-job-modal"
import { ActionResultCard } from"@/components/chat/action-result-card"
import { ContextPill } from"@/components/ui/context-pill"
import { QuickActionChips, type QuickAction } from"@/components/ui/quick-action-chips"
import { PromptSuggestionsPopover } from"@/components/ui/prompt-suggestions-popover"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from"@/components/ui/popover"
import { LiaQueriesGuide } from"@/components/ui/lia-queries-guide"
import { LiaVacancyQueriesGuide } from"@/components/ui/lia-vacancy-queries-guide"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from"@/components/ui/select"
import { Label } from"@/components/ui/label"
import { Textarea } from"@/components/ui/textarea"
import { Switch } from"@/components/ui/switch"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from"@/components/ui/dialog"
import { toast } from"sonner"
import { AudioRecordButton } from"@/components/ui/audio-record-button"
import { ScreeningChannelsModal, ScreeningSettingsModal, ScreeningSchedulingModal } from"@/components/screening-config"
import type { ScreeningStatus } from"@/components/screening-config"
import { QuestionAdjustmentChat, QuestionDiffView, AdjustmentCounter, JDEvaluationPanel } from"@/components/wsi"
import { 
  type Job, 
  type JobFilters, 
  type JobFunnel,
  type TechnicalRequirement,
  type Language,
  type BehavioralCompetency,
  type InterviewStage,
  type ScreeningQuestion,
  type SalaryRange,
  type OrganizationalStructure,
  type Timeline,
  type GovernanceRules,
  type ViewMode,
  type PreviewTab
} from"@/components/jobs"
import { 
  getStatusColor, 
  priorityColors, 
  WSI_BLOCKS, 
  WSI_AUTOMATIC_MESSAGES, 
  formatMessageWithVariables,
  getBloomComplexity,
  getEstimatedTime
} from"@/components/jobs/jobsPageConstants"
import { JobFiltersPanel } from"@/components/jobs/JobFilters"
import { ColumnConfigPanel } from"@/components/pages/jobs/ColumnConfigPanel"
import { TableFiltersPanel } from"@/components/pages/jobs/TableFiltersPanel"
import { InlineChatPanel } from"@/components/pages/jobs/InlineChatPanel"
import { JobPreviewPanel } from"@/components/pages/jobs/JobPreviewPanel"
import { JobsCompactTableView } from"@/components/pages/jobs/JobsCompactTableView"
import { JobsModalsSection } from"@/components/pages/jobs/JobsModalsSection"
import { JobsDashboardView } from"@/components/pages/jobs/JobsDashboardView"
const ExpandedChatModal = dynamic(() => import("@/components/expanded-chat-modal").then(m => ({ default: m.ExpandedChatModal })), { ssr: false })
import { liaApi } from"@/services/lia-api"
import { useJobsPageCore } from"./jobs/hooks/useJobsPageCore"

interface JobsPageProps {
  onNavigate?: (page: string) => void
  onAddRecentItem?: (item: { id: string; type:'vaga' |'chat' |'candidato'; title: string; subtitle?: string; meta?: Record<string, string | undefined> }) => void
  pendingChatOpen?: { chatId: string; chatTitle: string } | null
  onChatOpened?: () => void
  pendingJobOpen?: { jobId: string; jobTitle: string } | null
  onJobOpened?: () => void
}

export function JobsPage(props: JobsPageProps) {
  const { onAddRecentItem } = props
  const state = useJobsPageCore(props)

  // Kanban navigation (moved from hook — hooks must not return JSX)
  if (state.showKanban && state.selectedJob) {
    return <JobKanbanPage key={`kanban-${state.selectedJob.id}`} job={state.selectedJob} onBack={state.handleBackToJobs} />
  }
  if (state.showKanban && !state.selectedJob) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-lia-bg-primary">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-lia-border-default border-t-gray-600 rounded-full animate-spin motion-reduce:animate-none mx-auto mb-3" />
          <p className="text-base-ui text-lia-text-tertiary dark:text-lia-text-tertiary">Carregando vaga...</p>
        </div>
      </div>
    )
  }

  const {
    hasMounted,
    activeFilter, activePreviewTab, allJobs, applyColumnView, chatMode, clearAllJobFilters,
    closeChat, columnConfig, companyRecruiters, deleteColumnView, deselectAllJobs, editingJob,
    filteredJobs, getActiveFiltersCount, getActiveJobFiltersCount, getContextualSuggestions, getSelectedJobsHaveActiveStatus, handleApplySavedSearch,
    handleCloseReport, handleDeleteSavedSearch, handleJobAssignRecruiter, handleJobClick, handleJobDuplicate, handleJobInsights,
    handleJobPublish, handleJobToggleStatus, handleRenameSavedSearch, handleToggleColumnConfig, hasActiveFilters, inlineChatInitialMessage,
    isChatFullscreen, isLoadingJobMetrics, isLoadingJobs, isLoadingScreeningConfig, isResizingLIA, isTableCollapsed,
    jobFilters, jobMetrics, liaInlineLoading, liaInlineMessages, liaInlineMessagesEndRef, liaInputRef,
    liaPromptValue, liaWidth, navigationFilters, openGeneralChat, openJobCreationChat, orchestratorSuggestions,
    previewJob, previewWidth, reactivateEndDate, reactivateScreeningJobs,
    reportJob, resetColumnsToDefault, returnToGeneralChat, returnToLateralPrompt, saveColumnView, saveSearchAsTemplate,
    savedColumnViews, savedSearches, screeningConfig, searchTerm, selectAllJobs, selectedDaysFilter,
    selectedJob, selectedJobsForBatch, sendLiaInlineMessage, setActiveFilter, setActivePreviewTab, setBackendJobs,
    setChatMode, setEditingJob, setIsChatFullscreen, setIsResizingLIA, setIsResizingPreview, setJobsRefreshKey,
    setLiaInlineMessages, setLiaPromptValue, setLiaWidth, setPendingNavigateJobId, setPreviewJob, setPreviewWidth,
    setReactivateEndDate, setReactivateScreeningJobs, setSearchTerm, setSelectedJob, setShowAssignRecruiterModal, setShowColumnConfig,
    setShowCompareModal, setShowCreateJobModal, setShowDuplicateModal, setShowEditJobModal, setShowExpandedLIA, setShowInsightsModal,
    setShowJobPreview, setShowPublishModal, setShowReactivateScreeningDialog, setShowScreeningChannelsModal, setShowScreeningSchedulingModal, setShowScreeningSettingsModal,
    setShowStatusModal, setShowTableFiltersPanel, setShowUnpublishModal, setShowWSITutorialModal, setUserCollapsedLIA, showAssignRecruiterModal,
    showColumnConfig, showCompareModal, showCreateJobModal, showDuplicateModal, showEditJobModal, showExpandedLIA,
    showInlineChat, showInsightsModal, showJobPreview, showPublishModal, showReactivateScreeningDialog, showReport,
    showScreeningChannelsModal, showScreeningSchedulingModal, showScreeningSettingsModal, showStatusModal, showTableFiltersPanel, showUnpublishModal,
    showWSITutorialModal, statusModalMode, toggleColumn, toggleJobFilter, toggleTableExpansion, updateScreeningConfig,
    urgentJobs, favoriteJobs, pinnedJobs,
    toggleJobSelection, toggleUrgentJob, toggleFavoriteJob, togglePinJob,
    handleJobPreview, handleJobsSort,
    hookToTableColumnMap, jobsColumnOrder, jobsColumnWidths,
    jobsSortColumn, jobsSortDirection,
    draggedJobColumnId, dragOverJobColumnId,
    handleJobsColumnDragStart, handleJobsColumnDragOver, handleJobsColumnDragLeave, handleJobsColumnDrop, handleJobsColumnDragEnd,
    startJobsColumnResize,
    userCollapsedLIA, visibleColumnIds,
    loadBackendJobs, router,
  } = state

  const { statusOrder, groupedJobs } = useMemo(() => {
    const order = [
      'Ativa', 'Aprovada', 'Aguardando aprovação', 'Reaberta', 'Paralisada', 'Interna',
      'Rascunho', 'Fechada (preenchida)', 'Fechada (expirada)', 'Cancelada', 'Concluída', 'Arquivada'
    ] as const
    const grouped: Record<string, Job[]> = {}
    order.forEach(s => { grouped[s] = [] })
    filteredJobs.forEach(job => { if (grouped[job.status]) grouped[job.status].push(job) })
    return { statusOrder: order, groupedJobs: grouped }
  }, [filteredJobs])

  if (!hasMounted) {
    return (
      <div className="h-full flex flex-col bg-gray-50 dark:bg-lia-bg-primary overflow-hidden">
        <div className="flex-1 overflow-hidden">
          <div className="p-2.5 max-w-full overflow-x-auto">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="h-6 w-48 bg-gray-200 dark:bg-lia-bg-secondary rounded-md animate-pulse motion-reduce:animate-none" />
                <div className="h-4 w-64 bg-gray-200 dark:bg-lia-bg-secondary rounded-md animate-pulse motion-reduce:animate-none mt-2" />
              </div>
              <div className="h-8 w-24 bg-gray-200 dark:bg-lia-bg-secondary rounded-md animate-pulse motion-reduce:animate-none" />
            </div>
            <div className="space-y-2 mt-6">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="h-12 bg-gray-200 dark:bg-lia-bg-secondary rounded-md animate-pulse motion-reduce:animate-none" />
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-lia-bg-primary overflow-hidden relative">
      {/* Super Chat Fullscreen Mode - Cobre toda a área de conteúdo */}
      {chatMode ==='job-creation' && isChatFullscreen && showInlineChat && (
        <div className="absolute inset-0 z-50 bg-white dark:bg-lia-bg-primary flex flex-col">
          <ExpandedChatModal
            isOpen={true}
            onClose={closeChat}
            initialMessage={inlineChatInitialMessage}
            initialMessages={liaInlineMessages}
            contextTitle="Criação de Vaga"
            inline={true}
            mode="job-creation"
            onJobCreated={() => {
              returnToGeneralChat()
            }}
            onReturnToLateral={returnToLateralPrompt}
            onFullscreenChange={setIsChatFullscreen}
            onMessagesUpdate={(msgs) => setLiaInlineMessages(msgs)}
          />
        </div>
      )}
      
      {/* Header Fixo - Título e Tabs (oculto em fullscreen) */}
      <div className={`flex-shrink-0 px-4 pt-3 pb-0 bg-gray-50 dark:bg-lia-bg-primary ${chatMode ==='job-creation' && isChatFullscreen ?'hidden' :''}`}>
        {/* Header Principal - Padrão Funil de Talentos */}
        <div className="flex items-center justify-between mb-0.5">
            <div className="flex items-center gap-3">
              <div>
                <h1 className="text-xl font-['Open_Sans',sans-serif] font-semibold wedo-text-black flex items-center gap-2">
                  <Briefcase className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                  Gestão de Vagas
                </h1>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button 
                className="gap-2 h-8 px-3 bg-gray-800"
                onClick={() => setShowCreateJobModal(true)}
              >
                <Plus className="w-4 h-4" />
                Nova Vaga
              </Button>
            </div>
          </div>

        {/* Sistema de Abas - Padrão Funil de Talentos */}
        <div className="mb-0">
          <div className="border-b border-lia-border-subtle dark:border-lia-border-subtle">
            <nav className="-mb-px flex items-center space-x-6 nav-tabs" aria-label="Tabs" role="tablist">
              {/* TODO Sprint 3: migrar para <Tabs> shadcn */}
              {navigationFilters.map((filter) => (
                <button
                  key={filter.id}
                  onClick={() => {
                    setActiveFilter(filter.id)
                  }}
                  role="tab"
                  className={`group inline-flex items-center py-2 px-1 border-b-2 tab-button ${
                    activeFilter === filter.id
                      ?'border-gray-900 text-lia-text-primary dark:border-lia-border-subtle dark:text-lia-text-primary font-semibold'
                      :'border-transparent text-lia-text-primary hover:text-lia-text-primary hover:border-lia-border-default dark:text-lia-text-primary dark:hover:text-lia-text-secondary'
                  }`}
                >
                  <span>{filter.label}</span>
                  {!filter.isDashboard && (
                    <Badge
                      variant="secondary"
                      className={`ml-2 text-xs ${
                        activeFilter === filter.id
                          ?'bg-gray-100 text-lia-text-primary dark:bg-lia-bg-elevated dark:text-lia-text-primary font-semibold'
                          :'bg-gray-100 text-lia-text-primary dark:bg-lia-bg-secondary dark:text-lia-text-primary'
                      }`}
                    >
                      {isLoadingJobs ? (
                        <span className="inline-block w-4 h-3 bg-gray-300 dark:bg-lia-bg-elevated rounded-md animate-pulse motion-reduce:animate-none" />
                      ) : (
                        filter.count
                      )}
                    </Badge>
                  )}

                </button>
              ))}
            </nav>
          </div>

        </div>
      </div>

      {/* Área de Conteúdo Scrollável (oculto em fullscreen) */}
      <div className={`flex-1 flex flex-col overflow-hidden px-4 pt-2 pb-2 ${chatMode ==='job-creation' && isChatFullscreen ?'hidden' :''}`}>
        {/* Dashboard Visão Geral - Prompt Centralizado */}
        {activeFilter ==='visao-geral' && (
          <div className="min-h-[60vh] flex flex-col items-center justify-center py-8">
            {/* Container centralizado com título */}
            <div className="w-full max-w-[780px] mx-auto px-4 flex flex-col">
              <LiaPromptHeader title="Posso te ajudar com análises de vagas?" />
              {/* Container externo - Background branco como funil de talentos */}
              <div className="rounded-xl overflow-hidden bg-lia-bg-primary border border-lia-border-subtle">
                {/* Área de Tags - Linha superior */}
                <div className="px-4 pt-4 pb-4 border-b border-b-gray-200">
                  <div className="flex flex-wrap items-center gap-2">
                    {/* Tag 1: Criar nova vaga */}
                    <button
                      onClick={() => {
                        setActiveFilter('todas')
                        setTimeout(() => openJobCreationChat('Criar nova vaga'), 100)
                      }}
                      className="group inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full transition-[width,height] bg-gray-100 text-lia-text-primary hover:bg-gray-900 hover:text-white font-open-sans"
                    >
                      <Plus className="w-3.5 h-3.5 text-lia-text-primary group-hover:text-white transition-colors motion-reduce:transition-none" />
                      Criar nova vaga
                    </button>
                    {/* Tag 2: Ver minhas vagas */}
                    <button
                      onClick={() => setActiveFilter('ativas')}
                      className="group inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full transition-[width,height] bg-gray-100 text-lia-text-primary hover:bg-gray-900 hover:text-white font-open-sans"
                    >
                      <Briefcase className="w-3.5 h-3.5 text-lia-text-primary group-hover:text-white transition-colors motion-reduce:transition-none" />
                      Ver minhas vagas
                    </button>
                    {/* Tag 3: Ver todas as vagas */}
                    <button
                      onClick={() => setActiveFilter('todas')}
                      className="group inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full transition-[width,height] bg-gray-100 text-lia-text-primary hover:bg-gray-900 hover:text-white font-open-sans"
                    >
                      <Building2 className="w-3.5 h-3.5 text-lia-text-primary group-hover:text-white transition-colors motion-reduce:transition-none" />
                      Ver todas as vagas
                    </button>
                    {/* Tag 4: Resumo das vagas */}
                    <button
                      onClick={() => {
                        setActiveFilter('todas')
                        setTimeout(() => openGeneralChat('Resumo das minhas vagas ativas'), 100)
                      }}
                      className="group inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full transition-[width,height] bg-gray-100 text-lia-text-primary hover:bg-gray-900 hover:text-white font-open-sans"
                    >
                      <BarChart3 className="w-3.5 h-3.5 text-lia-text-primary group-hover:text-white transition-colors motion-reduce:transition-none" />
                      Resumo das vagas
                    </button>
                    {/* Botão Mais ideias - Modal com tabs igual ao prompt expandido */}
                    <LiaVacancyQueriesGuide
                      onSelectQuery={(query) => {
                        setActiveFilter('todas')
                        setTimeout(() => openGeneralChat(query), 100)
                      }}
                    />
                  </div>
                </div>

                {/* Input - Estilo Funil de Talentos */}
                <div className="px-4 pt-4 pb-4">
                  <div className="flex items-center gap-3 px-4 py-3 bg-lia-bg-primary rounded-md border border-lia-border-subtle transition-colors motion-reduce:transition-none focus-within:border-gray-400 focus-within:ring-1 focus-within:ring-gray-900/20">
                    {/* Input */}
                    <input
                      type="text"
                      placeholder="Como posso te ajudar com suas vagas hoje?"
                      value={liaPromptValue}
                      onChange={(e) => setLiaPromptValue(e.target.value)}
                     
                      className="flex-1 bg-transparent placeholder-gray-400 text-sm focus:outline-none text-lia-text-primary dark:text-lia-text-primary"
                      onKeyDown={(e) => {
                        if (e.key ==='Enter' && liaPromptValue.trim()) {
                          setActiveFilter('todas')
                          setTimeout(() => {
                            openGeneralChat(liaPromptValue.trim())
                            setLiaPromptValue('')
                          }, 100)
                        }
                      }}
                    />
                    
                    {/* Ícones à direita - Estilo Funil de Talentos */}
                    <div className="flex items-center gap-1">
                      {/* Botão Microfone */}
                      <AudioRecordButton
                        onTranscription={(text) => setLiaPromptValue(prev => prev ? `${prev} ${text}` : text)}
                        className="w-7 h-7 rounded-md flex items-center justify-center hover:bg-gray-100 transition-colors motion-reduce:transition-none"
                      />
                    </div>
                    
                    {/* Botão Busca/Enviar */}
                    <button
                      className="flex items-center justify-center hover:opacity-70 transition-opacity motion-reduce:transition-none"
                      onClick={() => {
                        if (liaPromptValue.trim()) {
                          setActiveFilter('todas')
                          setTimeout(() => {
                            openGeneralChat(liaPromptValue.trim())
                            setLiaPromptValue('')
                          }, 100)
                        } else {
                          setActiveFilter('todas')
                          setTimeout(() => openGeneralChat(), 100)
                        }
                      }}
                      title="Buscar"
                    >
                      <Search className="w-4 h-4 text-lia-text-secondary" />
                    </button>
                  </div>
                </div>

                {/* Segunda linha de tags - Sugestões Dinâmicas (estilo Funil) */}
                <div className="px-4 pb-4">
                  <div className="flex flex-wrap items-start gap-2 pt-3">
                    <span className="text-xs text-lia-text-primary font-medium mt-0.5">Sugestões:</span>
                    {/* Renderiza sugestões do orquestrador quando disponíveis, senão usa contextuais baseadas no estado */}
                    {(orchestratorSuggestions.length > 0 ? orchestratorSuggestions : getContextualSuggestions()).slice(0, 4).map((suggestion, index) => (
                      <button
                        key={`suggestion-${index}`}
                        onClick={() => {
                          setActiveFilter('todas')
                          setTimeout(() => openGeneralChat(suggestion), 100)
                        }}
                        className="inline-flex items-center px-2.5 py-0.5 text-xs rounded-full transition-[width,height] bg-gray-50 text-lia-text-primary border border-lia-border-subtle hover:text-lia-text-primary hover:bg-gray-100"
                       
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Conteúdo Principal - Lista de Vagas (quando não é visão geral) */}
        {activeFilter !=='visao-geral' && (
        <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
          {/* Toolbar Compacto - Prompt LIA + Controles - Padrão Funil de Talentos */}
          {/* Esconde o prompt compacto e botões quando qualquer chat expandido está ativo */}
          {!showExpandedLIA && !showInlineChat && (
            <div className="flex-shrink-0 flex items-center justify-between gap-4 mt-3 mb-2">
              {/* Prompt LIA - Compacto (max 300px) - Estilo Funil de Talentos */}
              <div className="flex-1 max-w-panel-sm">
              <div className="relative">
                <input
                  ref={liaInputRef}
                  type="text"
                  placeholder="Ex: Desenvolvedores Python com 5+ anos em São Paulo..."
                  value={liaPromptValue}
                  onChange={(e) => setLiaPromptValue(e.target.value)}
                  className="w-full h-10 pl-4 pr-20 text-base-ui rounded-md focus:outline-none placeholder:text-lia-text-secondary transition-colors motion-reduce:transition-none border bg-lia-bg-primary"
                  style={{color:"var(--gray-950)"}}
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor ="var(--gray-800)"
                    e.currentTarget.style.boxShadow ="0 0 0 2px var(--gray-600-bg-12)"
                    setShowExpandedLIA(true)
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor ="var(--gray-200)"
                    e.currentTarget.style.boxShadow ="none"
                  }}
                  onKeyDown={(e) => {
                    if (e.key ==='Enter' && liaPromptValue.trim()) {
                      openGeneralChat(liaPromptValue.trim())
                      setLiaPromptValue('')
                    }
                  }}
                />
                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                  <button
                    className="p-1.5 rounded-md transition-colors motion-reduce:transition-none hover:bg-gray-100"
                    onClick={() => openGeneralChat()}
                    title="Expandir chat"
                  >
                    <Maximize2 className="w-4 h-4 text-lia-text-secondary" />
                  </button>
                  <button
                    className="p-1.5 rounded-md transition-colors motion-reduce:transition-none hover:bg-gray-100"
                    onClick={() => {
                      if (liaPromptValue.trim()) {
                        openGeneralChat(liaPromptValue.trim())
                        setLiaPromptValue('')
                      }
                    }}
                  >
                    <Send className="w-4 h-4 text-lia-text-secondary" />
                  </button>
                </div>
              </div>

            </div>

            {/* Controles e Info - Sempre visíveis à direita */}
            <div className="flex items-center gap-3">
              {/* Badge de seleção */}
              {selectedJobsForBatch.size > 0 && (
                <Badge className="bg-gray-100 text-lia-text-primary border-lia-border-default dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:border-lia-border-default text-xs font-bold">
                  🎯 {selectedJobsForBatch.size}
                </Badge>
              )}

              {/* Botão Selecionar Todos */}
              {selectedJobsForBatch.size === 0 && filteredJobs.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={selectAllJobs}
                  className="gap-2 text-xs h-8 px-3"
                >
                  <CheckCircle className="w-3 h-3" />
                  Selecionar Todos
                </Button>
              )}

              {/* Botões de controle */}
              <Button
                variant={showTableFiltersPanel ?"default" :"outline"}
                size="sm"
                className={`gap-2 text-xs h-8 px-3 ${showTableFiltersPanel ?'bg-gray-900 hover:bg-gray-800 dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover dark:text-lia-text-disabled text-white' :''}`}
                onClick={() => setShowTableFiltersPanel(!showTableFiltersPanel)}
                title="Filtrar resultados da tabela"
              >
                <Target className="w-3 h-3" />
                Filtros
                {getActiveJobFiltersCount() > 0 && (
                  <Badge variant="secondary" className="bg-gray-900 text-white dark:bg-lia-btn-primary-bg dark:text-lia-text-disabled ml-1 text-xs font-bold">
                    {getActiveJobFiltersCount()}
                  </Badge>
                )}
              </Button>

              <Button
                variant={showColumnConfig ?"default" :"outline"}
                size="sm"
                className={`gap-2 text-xs h-8 px-3 ${showColumnConfig ?'bg-gray-900 hover:bg-black dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover dark:text-lia-text-disabled text-white' :''}`}
                onClick={handleToggleColumnConfig}
                title="Configurar colunas da tabela"
              >
                <ChevronsLeftRight className="w-3 h-3" />
                Colunas
                <Badge
                  variant="secondary"
                  className={`ml-1 text-xs ${
                    showColumnConfig
                      ?'bg-gray-800 text-white dark:bg-lia-bg-tertiary dark:text-lia-text-primary font-bold'
                      :'bg-gray-100 text-lia-text-primary dark:bg-lia-bg-elevated dark:text-lia-text-primary'
                  }`}
                >
                  6
                </Badge>
              </Button>
            </div>
            </div>
          )}

          {/* Results Summary */}
          <div className="flex-shrink-0 flex items-center justify-between mb-2">
            <div className="text-xs text-lia-text-primary dark:text-lia-text-primary flex items-center gap-3">
              {(searchTerm || selectedDaysFilter !=='todas') && (
                <Badge variant="outline" className="text-xs bg-gray-100 text-lia-text-primary border-lia-border-default dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:border-lia-border-default font-medium">
                  filtros ativos
                </Badge>
              )}

            </div>

            <div className="flex items-center gap-2">
              {/* Removido botão Selecionar Todas */}
            </div>
          </div>

          {/* Barra de Ações em Massa para Vagas - No topo do layout */}
          <JobActionsBar
            selectedCount={selectedJobsForBatch.size}
            onDeselectAll={deselectAllJobs}
            onPublish={handleJobPublish}
            onInsights={handleJobInsights}
            onDuplicate={handleJobDuplicate}
            onToggleStatus={handleJobToggleStatus}
            onAssignRecruiter={handleJobAssignRecruiter}
            hasActiveJobs={getSelectedJobsHaveActiveStatus()}
          />

          {/* Results Layout with Sidebars - Layout flex responsivo */}
          <div className="flex gap-2 transition-colors motion-reduce:transition-none duration-300 flex-1 min-h-0 overflow-hidden">
            {/* LIA Sidebar Expandida - InlineChatPanel */}
            <InlineChatPanel
              showExpandedLIA={showExpandedLIA}
              showInlineChat={showInlineChat}
              chatMode={chatMode}
              inlineChatInitialMessage={inlineChatInitialMessage}
              liaInlineMessages={liaInlineMessages}
              liaInlineLoading={liaInlineLoading}
              isChatFullscreen={isChatFullscreen}
              liaWidth={liaWidth}
              isTableCollapsed={isTableCollapsed}
              isResizingLIA={isResizingLIA}
              userCollapsedLIA={userCollapsedLIA}
              selectedJobsForBatch={selectedJobsForBatch}
              liaPromptValue={liaPromptValue}
              onSetLiaPromptValue={setLiaPromptValue}
              onCloseChat={closeChat}
              onOpenGeneralChat={openGeneralChat}
              onOpenJobCreationChat={openJobCreationChat}
              onReturnToGeneralChat={returnToGeneralChat}
              onReturnToLateralPrompt={returnToLateralPrompt}
              onSendMessage={sendLiaInlineMessage}
              onSetShowExpandedLIA={setShowExpandedLIA}
              onSetUserCollapsedLIA={setUserCollapsedLIA}
              onSetIsChatFullscreen={setIsChatFullscreen}
              onSetIsResizingLIA={setIsResizingLIA}
              onSetLiaWidth={setLiaWidth}
              onSetLiaInlineMessages={setLiaInlineMessages}
              liaInlineMessagesEndRef={liaInlineMessagesEndRef}
              onAddRecentItem={onAddRecentItem}
            />

            {/* 🎯 Inline Table Filters Panel - Filtros Avançados */}
            <TableFiltersPanel
              isOpen={showTableFiltersPanel}
              onClose={() => setShowTableFiltersPanel(false)}
              searchTerm={searchTerm}
              onSearchTermChange={setSearchTerm}
              jobFilters={jobFilters}
              onToggleFilter={toggleJobFilter}
              onClearAllFilters={clearAllJobFilters}
              getActiveFiltersCount={getActiveJobFiltersCount}
              hasActiveFilters={hasActiveFilters}
              savedSearches={savedSearches}
              onSaveSearch={saveSearchAsTemplate}
              onApplySavedSearch={handleApplySavedSearch}
              onRenameSavedSearch={handleRenameSavedSearch}
              onDeleteSavedSearch={handleDeleteSavedSearch}
            />

            {/* Tabela de Vagas - Com suporte a contração e ocultação em fullscreen */}
            {!(chatMode ==='job-creation' && isChatFullscreen) && (
            <div className={`h-full bg-white dark:bg-lia-bg-secondary rounded-md transition-[width,height] duration-300 min-w-0 overflow-hidden ${
              isTableCollapsed 
                ?'w-14 flex-shrink-0' 
                : showJobPreview ?'flex-1' :'flex-1'
            }`}>
              {isTableCollapsed ? (
                /* Versão Contraída - Apenas ícone para expandir */
                <div className="h-full flex flex-col items-center py-4 gap-3">
                  {/* Botão para expandir tabela */}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={toggleTableExpansion}
                    className="h-10 w-10 p-0 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
                    title="Expandir tabela de vagas"
                  >
                    <ChevronRight className="w-5 h-5 text-lia-text-primary dark:text-lia-text-primary" />
                  </Button>
                  
                  {/* Ícone da tabela */}
                  <div className="flex flex-col items-center gap-2 text-lia-text-primary">
                    <Briefcase className="w-5 h-5" />
                    <span className="text-xs font-medium writing-mode-vertical" style={{writingMode:'vertical-rl', textOrientation:'mixed'}} aria-live="polite" aria-atomic="true">
                      Vagas ({filteredJobs.length})
                    </span>
                  </div>
                  
                  {/* Indicador de vagas selecionadas */}
                  {selectedJobsForBatch.size > 0 && (
                    <Badge className="bg-gray-900 text-white text-xs px-1.5 py-0.5">
                      {selectedJobsForBatch.size}
                    </Badge>
                  )}
                </div>
              ) : (
                /* Versão Expandida - Tabela completa com botão de contrair */
                <div className="h-full flex flex-col">
                  {/* Header da tabela com botão de contrair */}
                  {showInlineChat && (
                    <div className="flex-shrink-0 px-3 py-2 bg-gray-50 dark:bg-lia-bg-secondary flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Briefcase className="w-4 h-4 text-lia-text-primary" />
                        <span className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary" aria-live="polite" aria-atomic="true">
                          Vagas ({filteredJobs.length})
                        </span>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={toggleTableExpansion}
                        className="h-7 w-7 p-0 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700"
                        title="Contrair tabela"
                      >
                        <ChevronLeft className="w-4 h-4 text-lia-text-primary" />
                      </Button>
                    </div>
                  )}
                  
                  <div className="flex-1 overflow-y-auto" role="status" aria-live="polite" aria-label="Carregando...">
                    {isLoadingJobs ? (
                      <div className="flex items-center justify-center py-12" role="status" aria-live="polite" aria-label="Carregando...">
                        <div className="flex items-center gap-2 text-sm text-lia-text-tertiary" role="status" aria-live="polite" aria-label="Carregando...">
                          <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none" />
                          <span aria-live="polite" aria-atomic="true">Carregando vagas...</span>
                        </div>
                      </div>
                    ) : filteredJobs.length === 0 ? (
                      <EmptyState
                        icon={<Briefcase />}
                        title="Nenhuma vaga cadastrada"
                        description="Crie sua primeira vaga para começar a atrair candidatos."
                        action={{ label:"Criar primeira vaga", onClick: () => setChatMode('job-creation') }}
                        className="h-64"
                      />
                    ) : (
                      <JobsCompactTableView
                        isLoading={isLoadingJobs}
                        filteredJobs={filteredJobs}
                        statusOrder={statusOrder}
                        groupedJobs={groupedJobs}
                        jobsColumnOrder={jobsColumnOrder}
                        visibleColumnIds={visibleColumnIds}
                        hookToTableColumnMap={hookToTableColumnMap}
                        jobsColumnWidths={jobsColumnWidths}
                        selectedJobsForBatch={selectedJobsForBatch}
                        pinnedJobs={pinnedJobs}
                        urgentJobs={urgentJobs}
                        favoriteJobs={favoriteJobs}
                        draggedJobColumnId={draggedJobColumnId}
                        dragOverJobColumnId={dragOverJobColumnId}
                        jobsSortColumn={jobsSortColumn}
                        jobsSortDirection={jobsSortDirection}
                        onSelectAll={selectAllJobs}
                        onDeselectAll={deselectAllJobs}
                        onToggleJobSelection={toggleJobSelection}
                        onJobPreview={handleJobPreview}
                        onJobClick={handleJobClick}
                        onToggleUrgent={toggleUrgentJob}
                        onTogglePin={togglePinJob}
                        onToggleFavorite={toggleFavoriteJob}
                        onSort={handleJobsSort}
                        onColumnDragStart={handleJobsColumnDragStart}
                        onColumnDragOver={handleJobsColumnDragOver}
                        onColumnDragLeave={handleJobsColumnDragLeave}
                        onColumnDrop={handleJobsColumnDrop}
                        onColumnDragEnd={handleJobsColumnDragEnd}
                        onColumnResize={startJobsColumnResize}
                      />
                    )}
                  </div>
                </div>
              )}
            </div>
            )}

            {/* Job Preview Card */}
            <JobPreviewPanel
              showJobPreview={showJobPreview}
              previewJob={previewJob}
              activePreviewTab={activePreviewTab}
              onTabChange={setActivePreviewTab}
              previewWidth={previewWidth}
              onResize={setPreviewWidth}
              onResizeStart={() => setIsResizingPreview(true)}
              onResizeEnd={() => setIsResizingPreview(false)}
              onClose={() => { setShowJobPreview(false); setPreviewJob(null); setActivePreviewTab('screening') }}
              onJobClick={handleJobClick}
              screeningConfig={screeningConfig}
              isLoadingScreeningConfig={isLoadingScreeningConfig}
              jobMetrics={jobMetrics}
              isLoadingJobMetrics={isLoadingJobMetrics}
            />

            {/* Column Configuration Sidebar - Right */}
            <ColumnConfigPanel
              open={showColumnConfig}
              onClose={() => setShowColumnConfig(false)}
              columnConfig={columnConfig}
              visibleColumnIds={visibleColumnIds}
              savedColumnViews={savedColumnViews}
              toggleColumn={toggleColumn}
              applyColumnView={applyColumnView}
              deleteColumnView={deleteColumnView}
              saveColumnView={saveColumnView}
              resetColumnsToDefault={resetColumnsToDefault}
              onToast={(msg) => toast.success(msg)}
            />
          </div>
        </div>
        )}

        <JobsModalsSection
          allJobs={allJobs}
          selectedJobsForBatch={selectedJobsForBatch}
          showReport={showReport}
          reportJob={reportJob}
          onCloseReport={handleCloseReport}
          showCompareModal={showCompareModal}
          onCloseCompareModal={() => setShowCompareModal(false)}
          showPublishModal={showPublishModal}
          onClosePublishModal={() => setShowPublishModal(false)}
          jobs={allJobs.filter(job => selectedJobsForBatch.has(job.id)).map(job => ({
            id: String(job.id),
            code: job.jobId,
            title: job.title,
            status: job.status,
            is_published: job.status ==='Ativa',
            published_channels: []
          }))}
          onPublish={async (jobIds, channels, options) => {
            try {
              const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
              
              for (const job of selectedJobs) {
                if (!job.backendId) continue
                
                await liaApi.updateJobVacancy(job.backendId, {
                  status:'Ativa',
                  published_website: channels.includes('portal')
                })
                
                if (channels.includes('linkedin')) {
                  try {
                    const linkedInResult = await liaApi.publishToLinkedIn(job.backendId)
                    if (linkedInResult.mock) {
                      toast.info(`LinkedIn: ${linkedInResult.message}`)
                    }
                  } catch (err) {
                  }
                }
                
                if (channels.includes('indeed')) {
                  try {
                    const indeedResult = await liaApi.publishToIndeed(job.backendId)
                    if (indeedResult.note) {
                      toast.info(`Indeed: ${indeedResult.note}`)
                    }
                  } catch (err) {
                  }
                }
              }
              
              toast.success(`${jobIds.length} vaga(s) publicada(s) em ${channels.length} canal(is)`)
              setShowPublishModal(false)
              deselectAllJobs()
              loadBackendJobs()
            } catch (error) {
              toast.error('Erro ao publicar vagas. Tente novamente.')
            }
          }}
          onUnpublish={async (jobIds, options) => {
            try {
              const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
              
              for (const job of selectedJobs) {
                if (!job.backendId) continue
                
                // Despublicar das plataformas
                if (job.publishedLinkedIn) {
                  try {
                    await liaApi.unpublishFromPlatform(job.backendId,'linkedin')
                  } catch (err) {
                  }
                }
                
                if (job.publishedIndeed) {
                  try {
                    await liaApi.unpublishFromPlatform(job.backendId,'indeed')
                  } catch (err) {
                  }
                }
                
                // Se congelar vaga está marcado, altera o status
                if (options?.freezeJob) {
                  try {
                    // Atualiza o status para Paralisada
                    await liaApi.updateJobVacancy(job.backendId, {
                      status:'Paralisada'
                    } as Record<string, unknown>)
                  } catch (err) {
                  }
                }
              }
              
              toast.success(`${jobIds.length} vaga(s) despublicada(s)`)
              setShowPublishModal(false)
              deselectAllJobs()
              loadBackendJobs()
            } catch (error) {
              toast.error('Erro ao despublicar vagas. Tente novamente.')
            }
          }}
          onOpenCommunicationModal={(jobIds, templateCategory) => {
            const selectedJobsList = allJobs.filter(job => jobIds.includes(String(job.id)))
            const jobTitles = selectedJobsList.map(j => j.title).join(',')
            toast.info(
              `Para notificar candidatos das vagas"${jobTitles}", acesse a página do Kanban de cada vaga e use o menu de comunicação.`,
              { duration: 8000 }
            )
          }}
        />

        <JobUnpublishModal
          isOpen={showUnpublishModal}
          onClose={() => setShowUnpublishModal(false)}
          jobs={allJobs.filter(job => selectedJobsForBatch.has(job.id) && job.is_published).map(job => ({
            id: String(job.id),
            code: job.jobId,
            title: job.title,
            status: job.status,
            is_published: job.is_published,
            published_channels: job.published_channels
          }))}
          candidates={[]}
          onUnpublish={async (data: UnpublishData) => {
            try {
              const response = await fetch('/api/backend-proxy/job-boards/unpublish-complete', {
                method:'POST',
                headers: {'Content-Type':'application/json' },
                body: JSON.stringify({
                  job_ids: data.jobIds,
                  freeze_job: data.freezeJob,
                  freeze_reason: data.freezeReason,
                  freeze_start_date: data.freezeStartDate,
                  unfreeze_date: data.unfreezeDate,
                  notify_applicants: data.notifyApplicants,
                  notification_channel: data.notificationChannel,
                  notification_message: data.notificationMessage,
                  notification_subject: data.notificationSubject,
                  candidate_ids: data.candidateIds,
                  cancel_scheduled_interviews: data.cancelScheduledInterviews,
                  cancel_scheduled_screenings: data.cancelScheduledScreenings,
                  send_recruiter_summary: data.sendRecruiterSummary
                })
              })
              
              if (!response.ok) {
                throw new Error('Failed to unpublish')
              }
              
              const result = await response.json()
              
              if (result.frozen_jobs?.length > 0) {
                toast.success(`${result.frozen_jobs.length} vaga(s) congelada(s) com sucesso`)
              } else if (result.unpublished_jobs?.length > 0) {
                toast.success(`${result.unpublished_jobs.length} vaga(s) despublicada(s)`)
              }
              
              deselectAllJobs()
              loadBackendJobs()
            } catch (error) {
              throw error
            }
          }}
          onComplete={() => {
            loadBackendJobs()
          }}
          onNavigateToJobWithCommunication={(jobId, params) => {
            const job = allJobs.find(j => String(j.id) === jobId)
            if (job) {
              const queryParams = new URLSearchParams({
                action:'notify',
                template: params.template,
                channel: params.channel,
                candidates: params.candidateIds.join(',')
              }).toString()
              
              setSelectedJob(job)
              setShowUnpublishModal(false)
              
              localStorage.setItem('pendingCommunicationAction', JSON.stringify({
                template: params.template,
                candidateIds: params.candidateIds,
                channel: params.channel,
                jobId: jobId
              }))
            }
          }}
        />

        <JobInsightsModal
          isOpen={showInsightsModal}
          onClose={() => setShowInsightsModal(false)}
          onSendEmail={(reportData) => {
            const jobTitles = allJobs
              .filter(job => reportData.jobIds.includes(String(job.id)))
              .map(j => j.title)
              .join(',')
            const subject = encodeURIComponent(`Relatório de Insights - ${jobTitles}`)
            const body = encodeURIComponent(`Segue relatório de insights das vagas selecionadas.\n\n${reportData.reportHtml.replace(/<[^>]*>/g,'')}`)
            window.open(`mailto:?subject=${subject}&body=${body}`,'_blank')
            toast.success('Abrindo cliente de email...')
          }}
          jobs={allJobs.filter(job => selectedJobsForBatch.has(job.id)).map(job => ({
            id: String(job.id),
            code: job.jobId,
            title: job.title,
            status: job.status,
            priority: job.priority,
            deadline: job.deadline,
            candidates_count: job.funnel?.total || 0,
            approved_count: job.funnel?.hired || 0,
            screening_count: job.funnel?.screening || 0,
            rejected_count: 0,
            performance_score: job.funnel?.hired ? Math.round((job.funnel.hired / Math.max(job.funnel.total, 1)) * 100) : 0
          }))}
        />

        <JobDuplicateModal
          isOpen={showDuplicateModal}
          onClose={() => setShowDuplicateModal(false)}
          job={(() => {
            const selectedJob = allJobs.find(job => selectedJobsForBatch.has(job.id))
            return selectedJob ? {
              id: String(selectedJob.id),
              code: selectedJob.jobId,
              title: selectedJob.title,
              department: selectedJob.department,
              location: selectedJob.location,
              recruiter: selectedJob.recruiter,
              recruiter_email: selectedJob.recruiterEmail,
              candidates_count: selectedJob.funnel?.total || 0,
              approved_count: selectedJob.funnel?.hired || 0
            } : null
          })()}
          recruiters={companyRecruiters}
          onDuplicate={async (options) => {
            try {
              const selectedJob = allJobs.find(job => selectedJobsForBatch.has(job.id))
              if (!selectedJob?.backendId) {
                toast.error('Vaga não encontrada')
                return
              }
              
              const includesCandidates = options.candidateOption !=='none'
              const candidateFilter = options.candidateOption ==='approved' ?'approved' : (options.candidateOption ==='all' ?'all' : null)
              const selectedRecruiter = companyRecruiters.find(r => r.id === options.recruiterId)
              
              const result = await liaApi.duplicateJobVacancy(selectedJob.backendId, {
                copies: 1,
                includeCandiates: includesCandidates,
                candidateFilter: candidateFilter,
                overrides: {
                  title: options.newTitle,
                  recruiter: selectedRecruiter?.name || selectedJob.recruiter,
                  recruiter_email: selectedRecruiter?.email || selectedJob.recruiterEmail,
                  status:'Rascunho',
                  deadline_shortlist: options.deadlineShortlist,
                  deadline_screening: options.deadlineScreening,
                  deadline_closing: options.deadlineClosing
                }
              })
              
              const newJobId = result?.jobs?.[0]?.id
              const candidatesIncluded = result?.total_candidates_cloned || 0
              
              if (includesCandidates && candidatesIncluded > 0) {
                toast.success(`Vaga"${options.newTitle}" criada com ${candidatesIncluded} candidato(s)!`)
              } else if (options.candidateOption ==='none') {
                toast.success(`Vaga"${options.newTitle}" criada! Inicie a busca de candidatos.`)
              } else {
                toast.success(`Vaga"${options.newTitle}" criada com sucesso!`)
              }
              
              setShowDuplicateModal(false)
              deselectAllJobs()
              await loadBackendJobs()
              
              if (options.candidateOption ==='none' && newJobId) {
                router.push(`/jobs/${newJobId}?action=sourcing`)
              }
            } catch (error) {
              toast.error('Erro ao duplicar vaga. Tente novamente.')
            }
          }}
        />

        <JobStatusModal
          isOpen={showStatusModal}
          onClose={() => setShowStatusModal(false)}
          jobs={allJobs.filter(job => selectedJobsForBatch.has(job.id)).map(job => ({
            id: String(job.id),
            code: job.jobId,
            title: job.title,
            status: job.status,
            candidates_count: job.funnel?.total || 0,
            screening_count: job.funnel?.screening || 0,
            interviews_scheduled: job.funnel?.interview || 0,
            tests_scheduled: 0,
            approved_count: job.funnel?.hired || 0,
            paused_since: job.status ==='Paralisada' ? job.createdAt : undefined
          }))}
          mode={statusModalMode}
          onPause={async (data) => {
            try {
              const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
              const updatePromises = selectedJobs.map(job => {
                if (job.backendId) {
                  return liaApi.updateJobVacancyStatus(job.backendId,'Paralisada')
                }
                return Promise.resolve(null)
              })
              await Promise.all(updatePromises)
              
              if (data.sendRecruiterSummary && data.recruiterNotificationChannel) {
                const channelMap: Record<string, string[]> = {'email': ['email'],'teams': ['teams'],'bell': ['bell'],'email_teams': ['email','teams'],'all': ['email','teams','bell']
                }
                const channels = channelMap[data.recruiterNotificationChannel] || ['bell']
                
                const recruiterIds = [...new Set(selectedJobs
                  .map(j => j.recruiter?.id || j.recruiterId)
                  .filter(Boolean) as string[])]
                
                if (recruiterIds.length === 0) {
                  recruiterIds.push('default_user')
                }
                
                try {
                  await liaApi.sendRecruiterActionNotification({
                    recruiter_ids: recruiterIds,
                    action:'pause',
                    job_titles: selectedJobs.map(j => j.title),
                    job_ids: selectedJobs.map(j => j.backendId || String(j.id)),
                    channels,
                    reason: data.pauseReason,
                    cancelled_screenings: data.cancelScheduledScreenings,
                    cancelled_interviews: data.cancelScheduledInterviews,
                    cancelled_tests: data.cancelScheduledTests,
                    notified_candidates_count: data.notifyApplicants ? data.candidateIds?.length || 0 : 0,
                  })
                } catch (notifError) {
                }
              }
              
              // Update local state to reflect status change + auto-pause screening
              setBackendJobs(prev => prev.map(job => 
                selectedJobsForBatch.has(job.id) 
                  ? { ...job, status:'Paralisada' as string, screeningStatus: job.screeningStatus ==='active' ?'paused' : job.screeningStatus } 
                  : job
              ))
              
              // Auto-pause active screenings
              for (const job of selectedJobs) {
                if (job.backendId && (job.screeningStatus ==='active')) {
                  try {
                    await liaApi.updateScreeningStatus(job.backendId,'paused', { pause_reason:'Vaga pausada automaticamente' })
                  } catch (err) {
                  }
                }
              }
              deselectAllJobs()
            } catch (error) {
              throw error
            }
          }}
          onActivate={async (data) => {
            try {
              const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
              const updatePromises = selectedJobs.map(job => {
                if (job.backendId) {
                  return liaApi.updateJobVacancyStatus(job.backendId,'Ativa')
                }
                return Promise.resolve(null)
              })
              await Promise.all(updatePromises)
              
              if (data.sendRecruiterSummary && data.recruiterNotificationChannel) {
                const channelMap: Record<string, string[]> = {'email': ['email'],'teams': ['teams'],'bell': ['bell'],'email_teams': ['email','teams'],'all': ['email','teams','bell']
                }
                const channels = channelMap[data.recruiterNotificationChannel] || ['bell']
                
                const recruiterIds = [...new Set(selectedJobs
                  .map(j => j.recruiter?.id || j.recruiterId)
                  .filter(Boolean) as string[])]
                
                if (recruiterIds.length === 0) {
                  recruiterIds.push('default_user')
                }
                
                try {
                  await liaApi.sendRecruiterActionNotification({
                    recruiter_ids: recruiterIds,
                    action:'activate',
                    job_titles: selectedJobs.map(j => j.title),
                    job_ids: selectedJobs.map(j => j.backendId || String(j.id)),
                    channels,
                  })
                } catch (notifError) {
                }
              }
              
              // Update local state to reflect status change
              setBackendJobs(prev => prev.map(job => 
                selectedJobsForBatch.has(job.id) 
                  ? { ...job, status:'Ativa' as string } 
                  : job
              ))
              
              // Check if any reactivated jobs had paused screenings - ask to reactivate
              const jobsWithPausedScreening = selectedJobs.filter(j => j.screeningStatus ==='paused' && j.screeningConfig)
              if (jobsWithPausedScreening.length > 0) {
                setReactivateScreeningJobs(jobsWithPausedScreening)
                setShowReactivateScreeningDialog(true)
              }
              deselectAllJobs()
            } catch (error) {
              throw error
            }
          }}
          onNavigateToJobWithCommunication={(jobId, params) => {
            setShowStatusModal(false)
            const job = allJobs.find(j => String(j.id) === jobId)
            if (job) {
              setSelectedJob(job)
              setPreviewJob(job)
              
              localStorage.setItem('pendingCommunicationAction', JSON.stringify({
                template: params.template,
                candidateIds: params.candidateIds,
                channel: params.channel,
                jobId: jobId,
                action:'pause_notification'
              }))
              
              toast.success('Vaga pausada. O modal de comunicação será aberto para notificar candidatos.')
            }
          }}
        />

        <JobAssignRecruiterModal
          isOpen={showAssignRecruiterModal}
          onClose={() => setShowAssignRecruiterModal(false)}
          jobs={allJobs.filter(job => selectedJobsForBatch.has(job.id)).map(job => ({
            id: String(job.id),
            code: job.jobId,
            title: job.title,
            recruiter: job.recruiter
          }))}
          recruiters={companyRecruiters}
          onAssign={async (jobIds, recruiterId, options) => {
            try {
              const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
              const recruiter = companyRecruiters.find(r => r.id === recruiterId)
              
              if (!recruiter) {
                toast.error('Recrutador não encontrado')
                return
              }
              
              const previousRecruiters = [...new Set(selectedJobs
                .map(j => j.recruiter?.id || j.recruiterId)
                .filter(Boolean) as string[])]
              
              const updatePromises = selectedJobs.map(job => {
                if (job.backendId) {
                  return liaApi.updateJobVacancy(job.backendId, {
                    recruiter: recruiter.name,
                    recruiter_email: recruiter.email
                  })
                }
                return Promise.resolve(null)
              })
              await Promise.all(updatePromises)
              
              if (options.notifyRecruiter) {
                try {
                  await liaApi.sendRecruiterActionNotification({
                    recruiter_ids: [recruiterId],
                    action:'assign',
                    job_titles: selectedJobs.map(j => j.title),
                    job_ids: selectedJobs.map(j => j.backendId || String(j.id)),
                    channels: ['bell','email','teams'],
                  })
                } catch (notifError) {
                }
              }
              
              if (options.transferCommunications && previousRecruiters.length > 0) {
                try {
                  await liaApi.transferCommunications({
                    job_ids: selectedJobs.map(j => j.backendId || String(j.id)),
                    from_recruiter_ids: previousRecruiters,
                    to_recruiter_id: recruiterId
                  })
                } catch (transferError) {
                  toast.warning('Comunicações não foram transferidas')
                }
              }
              
              setBackendJobs(prev => prev.map(job => 
                selectedJobsForBatch.has(job.id) 
                  ? { ...job, recruiter: recruiter.name, recruiterEmail: recruiter.email } 
                  : job
              ))
              
              toast.success(`Recrutador atribuído a ${jobIds.length} vaga(s)`)
              setShowAssignRecruiterModal(false)
              deselectAllJobs()
            } catch (error) {
              toast.error('Erro ao atribuir recrutador. Tente novamente.')
            }
          }}
        />

        {/* Modal de Criação de Vaga */}
        <CreateJobModal
          isOpen={showCreateJobModal}
          onClose={() => setShowCreateJobModal(false)}
          onCreateWithWizard={() => {
            setShowCreateJobModal(false)
            if (activeFilter ==='visao-geral') {
              setActiveFilter('todas')
              setTimeout(() => openJobCreationChat(), 100)
            } else {
              openJobCreationChat()
            }
          }}
          onJobCreated={(jobId) => {
            setShowCreateJobModal(false)
            localStorage.setItem("jobCreationMode", jobId)
            setPendingNavigateJobId(jobId)
            setJobsRefreshKey(k => k + 1)
          }}
        />

        {/* Modal de Edição de Vaga */}
        <EditJobModal
          isOpen={showEditJobModal}
          onClose={() => {
            setShowEditJobModal(false)
            setEditingJob(null)
          }}
          job={editingJob}
          onSave={async (jobId, updates) => {
            try {
              await liaApi.updateJobVacancy(jobId, updates)
              toast.success('Vaga atualizada com sucesso!')
              setShowEditJobModal(false)
              setEditingJob(null)
              // Recarregar para aplicar alterações (reload simples e confiável)
              window.location.reload()
            } catch (error) {
              toast.error('Erro ao atualizar vaga. Tente novamente.')
              throw error
            }
          }}
        />

        {/* Modais de Configuração de Triagem */}
        <ScreeningChannelsModal
          isOpen={showScreeningChannelsModal}
          onClose={() => setShowScreeningChannelsModal(false)}
          config={screeningConfig}
          updateConfig={updateScreeningConfig}
        />

        <ScreeningSettingsModal
          isOpen={showScreeningSettingsModal}
          onClose={() => setShowScreeningSettingsModal(false)}
          config={screeningConfig}
          updateConfig={updateScreeningConfig}
        />

        <ScreeningSchedulingModal
          isOpen={showScreeningSchedulingModal}
          onClose={() => setShowScreeningSchedulingModal(false)}
          config={screeningConfig}
          updateConfig={updateScreeningConfig}
        />


        {showReactivateScreeningDialog && reactivateScreeningJobs.length > 0 && (
          <Dialog open={showReactivateScreeningDialog} onOpenChange={(open) => !open && setShowReactivateScreeningDialog(false)}>
            <DialogContent className="max-w-sm rounded-md bg-white border border-lia-border-subtle dark:bg-lia-bg-primary dark:border-lia-border-subtle">
              <DialogHeader className="pb-3 border-b border-lia-border-subtle dark:border-lia-border-subtle">
                <DialogTitle className="text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif]">
                  Reativar Triagem?
                </DialogTitle>
              </DialogHeader>
              <div className="py-4 space-y-3">
                <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
                  {reactivateScreeningJobs.length === 1 
                    ? `A vaga"${reactivateScreeningJobs[0]?.title}" tinha a triagem ativa antes de ser pausada. Deseja reativar a triagem?`
                    : `${reactivateScreeningJobs.length} vagas tinham triagem ativa antes de serem pausadas. Deseja reativá-las?`
                  }
                </p>
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-lia-text-secondary dark:text-lia-text-tertiary">
                    Nova data de término (opcional)
                  </Label>
                  <Input
                    type="date"
                    value={reactivateEndDate}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setReactivateEndDate(e.target.value)}
                    className="h-8 text-xs border-lia-border-subtle dark:border-lia-border-default dark:bg-lia-bg-elevated"
                  />
                </div>
              </div>
              <DialogFooter className="gap-2 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                <Button
                  variant="outline"
                  onClick={() => { setShowReactivateScreeningDialog(false); setReactivateScreeningJobs([]); setReactivateEndDate('') }}
                  className="h-8 px-4 text-xs border-lia-border-default dark:border-lia-border-default"
                >
                  Não, manter pausada
                </Button>
                <Button
                  onClick={async () => {
                    for (const job of reactivateScreeningJobs) {
                      if (job.backendId) {
                        try {
                          await liaApi.updateScreeningStatus(job.backendId,'active', { 
                            scheduled_end_date: reactivateEndDate || undefined 
                          })
                        } catch (err) {
                        }
                      }
                    }
                    setBackendJobs(prev => prev.map(j => 
                      reactivateScreeningJobs.some((rj: Record<string, unknown>) => rj.id === j.id) 
                        ? { ...j, screeningStatus:'active' as string } 
                        : j
                    ))
                    toast.success(`Triagem reativada para ${reactivateScreeningJobs.length} vaga(s)!`)
                    setShowReactivateScreeningDialog(false)
                    setReactivateScreeningJobs([])
                    setReactivateEndDate('')
                  }}
                  className="h-8 px-4 text-xs bg-gray-900 hover:bg-gray-800 text-white dark:bg-lia-btn-primary-bg dark:text-lia-text-disabled dark:hover:bg-lia-btn-primary-hover"
                >
                  Sim, reativar triagem
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}

        {/* Modal de Tutorial WSI - Metodologia WeDoTalent Skill Index */}
        <WSITutorialModal open={showWSITutorialModal} onClose={() => setShowWSITutorialModal(false)} />


        {/* Job Creation Wizard Modal - DEPRECATED: Now using inline chat */}
        {/* Modal removido - usando super chat inline para criação de vaga */}

      </div>
    </div>
  )
}
