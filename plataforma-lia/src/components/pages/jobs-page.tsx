"use client"

import React, { useState, useRef, useEffect, useMemo } from"react"
import { useRouter } from"next/navigation"
import dynamic from"next/dynamic"
import { Button } from"@/components/ui/button"
import { EmptyState } from"@/components/ui/empty-state"
import { LiaPromptHeader } from"@/components/ui/lia-prompt-header"
import { Card, CardContent } from"@/components/ui/card"
import { Badge } from"@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import { Input } from"@/components/ui/input"
import { AISearchToggle } from"@/components/ai-search-toggle"
import { tabStyles } from"@/lib/design-tokens"
import { IntelligenceNotifications } from"@/components/intelligence-notifications"
import { Search, Plus, MapPin, Calendar, Users, DollarSign, Eye, Edit, Edit2, Share2, Clock, Layout, Layers3, Layers, ChevronDown, ChevronUp, ChevronLeft, BarChart3, TrendingUp, TrendingDown, FileText, ExternalLink, Briefcase, Building, Building2, Target, CheckCircle, CheckCircle2, XCircle, Linkedin, Globe, Shield, Hash, UserCheck, Heart, MoreHorizontal, Grid3X3, List, Maximize2, Minimize2, Star, Brain, Expand, Copy, MessageSquare, MoreVertical, Settings, Settings2, X, ChevronsLeftRight, Bell, Pin, Github, Mail, Lock, LockOpen, MessageCircle, AlertCircle, AlertTriangle, ShieldAlert, Lightbulb, ChevronRight, Home, Zap, ClipboardList, ListChecks, CalendarCheck, ThumbsUp, Phone, Send, Bookmark, Paperclip, Mic, GripVertical, ArrowUp, ArrowDown, ArrowUpDown, Filter, Award, Trash2, RefreshCw, ArrowRight, ArrowLeft, HelpCircle, Timer, GraduationCap, BookOpen, Scale, Loader2, History, Languages, UserCircle, CalendarDays, Link, Save, Check, RotateCcw, CalendarClock, Info, Archive, Gauge } from"lucide-react"
import { JobKanbanPage } from"./job-kanban-page"
import { BulkActionsBar } from"@/components/ui/bulk-actions-bar"
import { JobCompareModal } from"@/components/modals/job-compare-modal"
import { JobPublishModal } from"@/components/modals/job-publish-modal"
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
  // @ts-ignore TODO: fix type
  const state = useJobsPageCore(props)

  // eslint-disable-next-line react-hooks/rules-of-hooks
  const { statusOrder, groupedJobs } = useMemo(() => {
    const order = [
      'Ativa', 'Aprovada', 'Aguardando aprovação', 'Reaberta', 'Paralisada', 'Interna',
      'Rascunho', 'Fechada (preenchida)', 'Fechada (expirada)', 'Cancelada', 'Concluída', 'Arquivada'
    ] as const
    const grouped: Record<string, Job[]> = {}
    order.forEach(s => { grouped[s] = [] })
    ;(state.filteredJobs || []).forEach((job: Job) => { if (grouped[job.status]) grouped[job.status].push(job) })
    return { statusOrder: order, groupedJobs: grouped }
  }, [state.filteredJobs])

  // Kanban navigation (moved from hook — hooks must not return JSX)
  if (state.showKanban && state.selectedJob) {
    // @ts-ignore TODO: fix type
    return <JobKanbanPage key={`kanban-${state.selectedJob.id}`} job={state.selectedJob} onBack={state.handleBackToJobs} />
  }
  if (state.showKanban && !state.selectedJob) {
    return (
      <div className="h-full flex items-center justify-center bg-white dark:bg-lia-bg-primary">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-lia-border-default border-t-gray-600 rounded-full animate-spin motion-reduce:animate-none mx-auto mb-3" />
          <p className="text-base-ui text-lia-text-tertiary">Carregando vaga...</p>
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



  if (!hasMounted) {
    return (
      <div className="h-full flex flex-col bg-white dark:bg-lia-bg-primary overflow-hidden">
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
    <div className="h-full flex flex-col bg-white dark:bg-lia-bg-primary overflow-hidden relative">
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
      <div className={`flex-shrink-0 px-4 pt-3 pb-0 bg-white dark:bg-lia-bg-primary ${chatMode ==='job-creation' && isChatFullscreen ?'hidden' :''}`}>
        {/* Header Principal - Padrão Funil de Talentos */}
        <div className="flex items-center justify-between mb-0.5">
            <div className="flex items-center gap-3">
              <div>
                <h1 className="text-xl font-['Open_Sans',sans-serif] font-semibold wedo-text-black flex items-center gap-2">
                  <Briefcase className="w-5 h-5 text-lia-text-secondary" />
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

        {/* Sistema de Abas - Pill style (padrão ElevenLabs) */}
        <div className="mb-0">
          <nav className="flex items-center gap-1 nav-tabs" aria-label="Tabs" role="tablist">
            {navigationFilters.map((filter) => (
              <button
                key={filter.id}
                onClick={() => {
                  setActiveFilter(filter.id)
                }}
                role="tab"
                aria-selected={activeFilter === filter.id}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer font-['Open_Sans',sans-serif] ${
                  activeFilter === filter.id
                    ? 'bg-gray-100 text-gray-900 dark:bg-gray-800'
                    : 'text-lia-text-secondary hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                <span>{filter.label}</span>
                {!filter.isDashboard && (
                  <span className={`text-[10px] font-semibold ${
                    activeFilter === filter.id
                      ? 'text-gray-500'
                      : 'text-lia-text-tertiary'
                  }`}>
                    {isLoadingJobs ? (
                      <span className="inline-block w-4 h-3 bg-gray-200 dark:bg-lia-bg-elevated rounded animate-pulse motion-reduce:animate-none" />
                    ) : (
                      filter.count
                    )}
                  </span>
                )}
              </button>
            ))}
          </nav>
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
                     
                      className="flex-1 bg-transparent placeholder-gray-400 text-sm focus:outline-none text-lia-text-primary"
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
                        // @ts-ignore TODO: fix type
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
                <Badge className="bg-gray-100 text-lia-text-primary border-lia-border-default dark:bg-lia-bg-secondary dark:border-lia-border-default text-xs font-bold">
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
                // @ts-ignore TODO: fix type
                variant={showTableFiltersPanel ?"default" :"outline"}
                size="sm"
                className={`gap-2 text-xs h-8 px-3 ${showTableFiltersPanel ?'bg-gray-900 hover:bg-gray-800 dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover text-white' :''}`}
                onClick={() => setShowTableFiltersPanel(!showTableFiltersPanel)}
                title="Filtrar resultados da tabela"
              >
                <Target className="w-3 h-3" />
                Filtros
                {getActiveJobFiltersCount() > 0 && (
                  <Badge variant="secondary" className="bg-gray-900 text-white dark:bg-lia-btn-primary-bg ml-1 text-xs font-bold">
                    {getActiveJobFiltersCount()}
                  </Badge>
                )}
              </Button>

              <Button
                // @ts-ignore TODO: fix type
                variant={showColumnConfig ?"default" :"outline"}
                size="sm"
                className={`gap-2 text-xs h-8 px-3 ${showColumnConfig ?'bg-gray-900 hover:bg-black dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover text-white' :''}`}
                onClick={handleToggleColumnConfig}
                title="Configurar colunas da tabela"
              >
                <ChevronsLeftRight className="w-3 h-3" />
                Colunas
                <Badge
                  variant="secondary"
                  className={`ml-1 text-xs ${
                    showColumnConfig
                      ?'bg-gray-800 text-white dark:bg-lia-bg-tertiary font-bold'
                      :'bg-gray-100 text-lia-text-primary dark:bg-lia-bg-elevated'
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
            <div className="text-xs text-lia-text-primary flex items-center gap-3">
              {(searchTerm || selectedDaysFilter !=='todas') && (
                <Badge variant="outline" className="text-xs bg-gray-100 text-lia-text-primary border-lia-border-default dark:bg-lia-bg-secondary dark:border-lia-border-default font-medium">
                  filtros ativos
                </Badge>
              )}

            </div>

            <div className="flex items-center gap-2">
              {/* Removido botão Selecionar Todas */}
            </div>
          </div>

          {/* Barra de Ações em Massa para Vagas - No topo do layout */}
          <BulkActionsBar
            selectedCount={selectedJobsForBatch.size}
            entityLabel="vaga"
            entityIcon={<Briefcase className="w-3.5 h-3.5 text-lia-text-secondary" />}
            onDeselectAll={deselectAllJobs}
            className="flex-shrink-0 mb-3"
            actions={[
              {
                id: 'publish',
                label: 'Publicar',
                icon: <Share2 className="w-3.5 h-3.5 text-lia-text-secondary" />,
                onClick: handleJobPublish,
              },
              {
                id: 'insights',
                label: 'Insights',
                icon: <Brain className="w-3.5 h-3.5 text-wedo-cyan" />,
                onClick: handleJobInsights,
              },
              {
                id: 'duplicate',
                label: 'Duplicar',
                icon: <Copy className="w-3.5 h-3.5 text-lia-text-secondary" />,
                onClick: handleJobDuplicate,
              },
              {
                id: 'toggle_status',
                label: getSelectedJobsHaveActiveStatus() ? 'Pausar' : 'Ativar',
                icon: getSelectedJobsHaveActiveStatus()
                  ? <X className="w-3.5 h-3.5 text-lia-text-secondary" />
                  : <CheckCircle2 className="w-3.5 h-3.5 text-lia-text-secondary" />,
                onClick: handleJobToggleStatus,
              },
              {
                id: 'assign_recruiter',
                label: 'Recrutador',
                icon: <UserCheck className="w-3.5 h-3.5 text-lia-text-secondary" />,
                onClick: handleJobAssignRecruiter,
              },
            ]}
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
              // @ts-ignore TODO: fix type
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
              // @ts-ignore TODO: fix type
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
                    <ChevronRight className="w-5 h-5 text-lia-text-primary" />
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
                        <span className="text-xs font-medium text-lia-text-primary" aria-live="polite" aria-atomic="true">
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
          showUnpublishModal={showUnpublishModal}
          onCloseUnpublishModal={() => setShowUnpublishModal(false)}
          showInsightsModal={showInsightsModal}
          onCloseInsightsModal={() => setShowInsightsModal(false)}
          showDuplicateModal={showDuplicateModal}
          onCloseDuplicateModal={() => setShowDuplicateModal(false)}
          showStatusModal={showStatusModal}
          onCloseStatusModal={() => setShowStatusModal(false)}
          statusModalMode={statusModalMode}
          showAssignRecruiterModal={showAssignRecruiterModal}
          onCloseAssignRecruiterModal={() => setShowAssignRecruiterModal(false)}
          showCreateJobModal={showCreateJobModal}
          onCloseCreateJobModal={() => setShowCreateJobModal(false)}
          showEditJobModal={showEditJobModal}
          onCloseEditJobModal={() => setShowEditJobModal(false)}
          editingJob={editingJob}
          showScreeningChannelsModal={showScreeningChannelsModal}
          onCloseScreeningChannelsModal={() => setShowScreeningChannelsModal(false)}
          showScreeningSettingsModal={showScreeningSettingsModal}
          onCloseScreeningSettingsModal={() => setShowScreeningSettingsModal(false)}
          showScreeningSchedulingModal={showScreeningSchedulingModal}
          onCloseScreeningSchedulingModal={() => setShowScreeningSchedulingModal(false)}
          screeningConfig={screeningConfig}
          updateScreeningConfig={updateScreeningConfig}
          showReactivateScreeningDialog={showReactivateScreeningDialog}
          // @ts-ignore TODO: fix type
          reactivateScreeningJobs={reactivateScreeningJobs}
          reactivateEndDate={reactivateEndDate}
          showWSITutorialModal={showWSITutorialModal}
          onCloseWSITutorialModal={() => setShowWSITutorialModal(false)}
          companyRecruiters={companyRecruiters}
          activeFilter={activeFilter}
          onDeselectAll={deselectAllJobs}
          onRefreshJobs={loadBackendJobs}
          onSetBackendJobs={setBackendJobs}
          onSetSelectedJob={setSelectedJob}
          onSetPreviewJob={setPreviewJob}
          onSetEditingJob={setEditingJob}
          onSetActiveFilter={setActiveFilter}
          onOpenJobCreationChat={openJobCreationChat}
          onSetPendingNavigateJobId={setPendingNavigateJobId}
          onSetReactivateScreeningDialog={setShowReactivateScreeningDialog}
          // @ts-ignore TODO: fix type
          onSetReactivateScreeningJobs={setReactivateScreeningJobs}
          onSetReactivateEndDate={setReactivateEndDate}
          jobs={allJobs.filter(job => selectedJobsForBatch.has(job.id)).map(job => ({
            id: String(job.id),
            code: job.jobId,
            title: job.title,
            status: job.status,
            is_published: job.status === "Ativa",
            published_channels: []
          }))}
          onPublish={async (jobIds, channels, options) => {
            try {
              const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
              for (const job of selectedJobs) {
                if (!job.backendId) continue
                await liaApi.updateJobVacancy(job.backendId, { status: "Ativa", published_website: channels.includes("portal") })
                if (channels.includes("linkedin")) {
                  try { const r = await liaApi.publishToLinkedIn(job.backendId); if ((r as any).mock) toast.info("Publicação simulada no LinkedIn") } catch {}
                }
                if (channels.includes("indeed")) {
                  try { const r = await liaApi.publishToIndeed(job.backendId); if ((r as any).note) toast.info("Publicação simulada no Indeed") } catch {}
                }
              }
              toast.success("Vagas publicadas com sucesso")
              setShowPublishModal(false)
              deselectAllJobs()
              loadBackendJobs()
            } catch { toast.error("Erro ao publicar vagas. Tente novamente.") }
          }}
          onUnpublish={async (jobIds, options) => {
            try {
              const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
              for (const job of selectedJobs) {
                if (!job.backendId) continue
                if (job.publishedLinkedIn) { try { await liaApi.unpublishFromPlatform(job.backendId, "linkedin") } catch {} }
                if (job.publishedIndeed) { try { await liaApi.unpublishFromPlatform(job.backendId, "indeed") } catch {} }
                if (options?.freezeJob) { try { await liaApi.updateJobVacancy(job.backendId, { status: "Paralisada" }) } catch {} }
              }
              toast.success("Vagas despublicadas com sucesso")
              setShowPublishModal(false)
              deselectAllJobs()
              loadBackendJobs()
            } catch { toast.error("Erro ao despublicar vagas. Tente novamente.") }
          }}
          onOpenCommunicationModal={(jobIds, templateCategory) => {
            const titles = allJobs.filter(job => jobIds.includes(String(job.id))).map(j => j.title).join(", ")
            toast.info(`Comunicação para: ${titles}`, { duration: 8000 })
          }}
        />
        {/* Job Creation Wizard Modal - DEPRECATED: Now using inline chat */}
        {/* Modal removido - usando super chat inline para criação de vaga */}

      </div>
    </div>
  )
}
