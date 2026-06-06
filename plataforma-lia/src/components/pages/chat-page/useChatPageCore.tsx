"use client"

import { useState, useCallback, useEffect, useMemo, useRef } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { useLocale } from "next-intl"
import { useChatLayout } from "@/hooks/chat/useChatLayout"
import { useUIActions } from "@/hooks/ui/useUIActions"
import { promoteCandidateToBase } from "@/lib/api/candidate-search"
import { useLiaChatContext } from "@/contexts/lia-float-context"
import { useChatPageHandlers } from "./useChatPageHandlers"
import {
  FileText, Users, Plus, MessageSquare, Search, Calendar,
  UserCheck, RefreshCcw,
} from "lucide-react"
import { type QuickAction, defaultCandidateActions } from "@/components/ui/quick-action-chips"
import { type CommandItem, defaultCommands } from "@/components/ui/command-palette"
import { buildNavigationCommands, buildActionCommands } from "@/lib/navigation/navigation-commands"
import { useCommandCatalog } from "@/hooks/lia/use-command-catalog"
import {
  CandidateSummaryCard, JobSummaryCard, WSIScoreCard,
  CompensationSummaryCard, InterviewConfirmationCard,
  ProgressTrackerCard, CompanyBenefitsSummaryCard,
} from "@/components/ui-actions"
import type { SidePanelType, PanelSubmitData, ChatCardType } from "@/components/ui-actions/types"
import type { ParsedEntities, SearchMode, SearchMetadata } from "@/components/search/smart-search-input"
import type { CandidateResult } from "@/components/search/search-results-card"
import type { Message, ContextPanelData } from "./types"
import { emptyConversation, modernConversation } from "./constants"
import { useChatMessages } from "./chat-core/useChatMessages"
import { useChatSession } from "./chat-core/useChatSession"
import { MAX_FILE_SIZE_MB } from "./chat-core/chat-core.constants"
import { toast } from "sonner"

export function useChatPageCore({ initialConversationId }: { initialConversationId?: string | null } = {}) {
  const searchParams = useSearchParams()
  const router = useRouter()
  const locale = useLocale()
  const { data: commandCatalog } = useCommandCatalog()
  const conversationType = searchParams?.get('conversation') || 'empty'
  const initialConversation = conversationType === 'empty' ? emptyConversation : modernConversation

  // ── Unified LIA Chat Context ────────────────────────────────────────────────
  const { chatConversationId, setChatConversationId, addChatMessage } = useLiaChatContext()

  // ── Lifted state (shared between sub-hooks) ───────────────────────────────
  const [contextData, setContextData] = useState<ContextPanelData | null>(null)
  const [isPanelOpen, setIsPanelOpen] = useState(false)

  // ── Sub-hook: messages, files, voice, scroll, text utils ─────────────────
  const msg = useChatMessages({
    initialMessages: initialConversation,
    setContextData,
    setIsPanelOpen,
  })

  // ── Sub-hook: session, streaming, search, filters, events ────────────────
  const session = useChatSession({
    initialConversation,
    conversationType,
    messages: msg.messages,
    setMessages: msg.setMessages,
    setIsLoading: msg.setIsLoading,
    setContextData,
    setIsPanelOpen,
    initialConversationId,
  })

  // ── UI Actions System ─────────────────────────────────────────────────────
  const handlePanelSubmit = useCallback(async (_data: PanelSubmitData) => {}, [])
  const handlePanelClose = useCallback((_panelType: SidePanelType) => {}, [])

  const handleChatCardAction = useCallback((cardType: ChatCardType, action: string, data: unknown) => {
    if (cardType === "candidate_summary" && action === "schedule") {
      const candidateData = data as { id: string; name: string; email?: string; title?: string }
      session.setSelectedCandidateForScheduling({
        name: candidateData.name,
        email: candidateData.email || "",
        id: candidateData.id,
        job_title: candidateData.title || "Candidato",
      })
      session.setIsSchedulingModalOpen(true)
    }
  }, [session])

  const uiActions = useUIActions({
    onPanelSubmit: handlePanelSubmit,
    onPanelClose: handlePanelClose,
    onChatCardAction: handleChatCardAction,
    enableWebSocket: false,
  })

  // ── Layout ────────────────────────────────────────────────────────────────
  const isEmptyChat = msg.messages.length === 0
  const { chatContainerClass, inputContainerClass, messagesContainerClass } = useChatLayout({
    isEmptyChat,
    isPanelOpen,
  })

  // ── Initial context panel from seeded conversation ────────────────────────
  useEffect(() => {
    if (initialConversation.length > 0) {
      const messageWithContext = initialConversation.slice().reverse().find(m => m.contextData)
      if (messageWithContext?.contextData) {
        setContextData(messageWithContext.contextData as unknown as ContextPanelData)
        setIsPanelOpen(true)
      }
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Keyboard navigation ───────────────────────────────────────────────────
  useEffect(() => {
    const handleKeyboard = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'f') {
        e.preventDefault()
        msg.setShowSearch(true)
      }
      if (e.ctrlKey && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) {
        e.preventDefault()
        const direction = e.key === 'ArrowUp' ? -1 : 1
        const newIndex = Math.max(0, Math.min(msg.messages.length - 1, msg.currentMessageIndex + direction))
        msg.setCurrentMessageIndex(newIndex)
        const messageElements = document.querySelectorAll('[data-message-id]')
        if (messageElements[newIndex]) {
          messageElements[newIndex].scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
      }
      if (e.key === 'Escape') {
        msg.setShowSearch(false)
        msg.setSearchTerm("")
      }
      if (e.ctrlKey && e.key === '/') {
        e.preventDefault()
        msg.inputRef.current?.focus()
      }
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        const activeElement = document.activeElement
        const isInputFocused = activeElement?.tagName === 'INPUT' || activeElement?.tagName === 'TEXTAREA'
        if (!isInputFocused || activeElement === msg.inputRef.current) {
          e.preventDefault()
          session.setIsCommandPaletteOpen(true)
        }
      }
    }
    window.addEventListener('keydown', handleKeyboard)
    return () => window.removeEventListener('keydown', handleKeyboard)
  }, [msg.currentMessageIndex, msg.messages.length, msg, session])

  // ── Smart search activation ───────────────────────────────────────────────
  const activateSmartSearch = useCallback(() => {
    session.setIsSmartSearchMode(true)
    session.setSmartSearchQuery(msg.input)
    msg.setInput("")
    if (session.searchFlow.flowState === "idle") {
      session.searchFlow.startProfileCollection()
    }
  }, [msg, session])

  // ── Extracted handlers (send, pipeline, etc.) ─────────────────────────────
  const { handleSmartSearchSubmit, handleSmartSearchCancel, handleSendMessage, handlePipelineAction } =
    useChatPageHandlers({
      input: msg.input,
      setInput: msg.setInput,
      isLoading: msg.isLoading,
      setIsLoading: msg.setIsLoading,
      messages: msg.messages,
      setMessages: msg.setMessages,
      searchFlow: session.searchFlow as unknown as Record<string, unknown> & {
        flowState: string
        startSearch: (q: string, e: ParsedEntities, m?: SearchMode, meta?: SearchMetadata) => Promise<void>
        reset: () => void
        submitProfile: (profile: string) => void
        submitSearch: (params: Record<string, unknown>) => void
        showResults: () => void
        startProfileCollection: () => void
      },
      activeSearchFilters: session.activeSearchFilters,
      setIsSmartSearchMode: session.setIsSmartSearchMode,
      setSmartSearchQuery: session.setSmartSearchQuery,
      setSearchPreviewData: session.setSearchPreviewData,
      setHasSearchResults: session.setHasSearchResults,
      setContextData: setContextData as unknown as (v: Record<string, unknown> | null) => void,
      setIsPanelOpen,
      contextData: contextData as unknown as Record<string, unknown> | null,
      attachedFiles: msg.attachedFiles,
      setAttachedFiles: msg.setAttachedFiles,
      audioBlob: msg.audioBlob,
      setAudioBlob: msg.setAudioBlob,
      setChatTitle: session.setChatTitle,
      setFileAnalysisContext: msg.setFileAnalysisContext as unknown as (v: Record<string, unknown> | null) => void,
      fileAnalysisContext: msg.fileAnalysisContext as unknown as Record<string, unknown> | null,
      wsIsConnected: session.wsIsConnected,
      wsSendMessage: session.wsSendMessage,
      wsClearTokens: session.wsClearTokens,
      wsStreamingModeRef: session.wsStreamingModeRef,
      selectedCandidateForScheduling: session.selectedCandidateForScheduling as unknown as Record<string, unknown> | null,
      setSelectedCandidateForScheduling: session.setSelectedCandidateForScheduling as unknown as (v: Record<string, unknown> | null) => void,
      setIsSchedulingModalOpen: session.setIsSchedulingModalOpen,
      chatConversationId,
      setChatConversationId,
      addChatMessage,
      scrollToBottom: msg.scrollToBottom,
    })

  // ── AI-First Action Handlers ──────────────────────────────────────────────
  const handleScheduleInterview = useCallback(() => {
    if (
      contextData?.type === 'candidate-suggestions' &&
      contextData.data?.candidates &&
      Array.isArray(contextData.data.candidates) &&
      contextData.data.candidates.length > 0
    ) {
      const candidate = contextData.data.candidates[0]
      if (candidate?.name) {
        session.setSelectedCandidateForScheduling({
          name: candidate.name,
          email: candidate.contact?.email || candidate.email || '',
          id: candidate.id || candidate.candidateId,
          job_title: candidate.current_title || 'Candidato',
          job_vacancy_id: candidate.job_vacancy_id,
        })
        session.setIsSchedulingModalOpen(true)
        return
      }
    }
    handleSendMessage("agendar entrevista")
  }, [contextData, handleSendMessage, session])

  const handleEvaluateFit = useCallback(() => handleSendMessage("avaliar fit técnico do candidato"), [handleSendMessage])
  const handleGenerateEmail = useCallback(() => handleSendMessage("gerar email de follow-up"), [handleSendMessage])
  const handleSendWhatsApp = useCallback(() => handleSendMessage("enviar mensagem whatsapp"), [handleSendMessage])
  const handleCompareProfiles = useCallback(() => handleSendMessage("comparar perfis de candidatos"), [handleSendMessage])
  // Onda 4-P0-Fase7 (2026-05-24): trocado '/indicadores' (rota inexistente,
  // bug padrão Task #712 descoberto via check_no_broken_window_location.py)
  // pra '/teams-tab/dashboard' (rota canonical que existe + é mapeada como
  // DASHBOARD em src/lib/canonical-pages.ts:71).
  const handleViewAnalytics = useCallback(() => { window.location.href = '/teams-tab/dashboard' }, [])

  // ── Candidate search handlers ─────────────────────────────────────────────
  const handleSelectCandidate = useCallback((candidate: CandidateResult) => {
    session.setSelectedCandidateForDetail(candidate)
    session.setIsCandidateDetailOpen(true)
  }, [session])

  const handleAddCandidatesToJob = useCallback((candidateIds: string[]) => {
    handleSendMessage(`Adicionar ${candidateIds.length} candidato(s) selecionado(s) à vaga atual`)
  }, [handleSendMessage])

  const handleCompareCandidates = useCallback((candidateIds: string[]) => {
    if (candidateIds.length >= 2) handleSendMessage(`Comparar os ${candidateIds.length} candidatos selecionados`)
  }, [handleSendMessage])

  const handleLoadMoreCandidates = useCallback((query: string, threadId?: string) => {
    session.setPendingPearchSearch({ query, threadId })
    session.setIsCreditDialogOpen(true)
  }, [session])

  const handleConfirmPearchSearch = useCallback(() => {
    if (session.pendingPearchSearch) {
      handleSendMessage(`Buscar mais candidatos para "${session.pendingPearchSearch.query}" no banco global Pearch`)
      session.setIsCreditDialogOpen(false)
      session.setPendingPearchSearch(null)
    }
  }, [session, handleSendMessage])

  const handleAddCandidateToJob = useCallback((candidateId: string) => {
    handleSendMessage(`Adicionar candidato ${candidateId} à vaga atual`)
    session.setIsCandidateDetailOpen(false)
  }, [handleSendMessage, session])

  const handleSaveToBase = useCallback(async (candidateId: string) => {
    try {
      const result = await promoteCandidateToBase(candidateId)
      if (result.success) {
        if (session.selectedCandidateForDetail) {
          session.setSelectedCandidateForDetail({
            ...session.selectedCandidateForDetail,
            is_discovered: false,
            source: "local",
          })
        }
        if (contextData?.type === 'candidate-suggestions' && contextData.data?.candidates) {
          setContextData(prev => prev ? {
            ...prev,
            data: {
              ...prev.data,
              candidates: (prev.data.candidates as Record<string, unknown>[]).map(c =>
                c.id === candidateId ? { ...c, is_discovered: false, source: "local" } : c
              ),
            },
          } : null)
        }
        msg.setMessages(prev => [...prev, {
          id: Date.now(), sender: "lia",
          content: result.was_merged
            ? `Candidato **${session.selectedCandidateForDetail?.name || 'selecionado'}** foi mesclado com perfil existente na sua base.`
            : `Candidato **${session.selectedCandidateForDetail?.name || 'selecionado'}** foi salvo na sua base local com sucesso!`,
          timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
          type: "text",
        }])
      }
    } catch {
      msg.setMessages(prev => [...prev, {
        id: Date.now(), sender: "lia",
        content: "Desculpe, ocorreu um erro ao salvar o candidato na base. Por favor, tente novamente.",
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        type: "text",
      }])
    }
  }, [session, contextData, msg])

  // ── Keyboard send ─────────────────────────────────────────────────────────
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // ── renderChatCard ────────────────────────────────────────────────────────
  const renderChatCard = useCallback((message: Message) => {
    if (!message.chatCardType || !message.chatCardData) return null
    const { chatCardType, chatCardData } = message
    const handleCardAction = (action: string) => handleChatCardAction(chatCardType, action, chatCardData)

    switch (chatCardType) {
      case "candidate_summary":
        return (
          <CandidateSummaryCard
            data={chatCardData as unknown as Parameters<typeof CandidateSummaryCard>[0]['data']}
            onSchedule={() => handleCardAction("schedule")}
            onViewProfile={() => handleCardAction("view_details")}
            onApprove={() => handleCardAction("add_shortlist")}
          />
        )
      case "wsi_score":
        return (
          <WSIScoreCard
            data={chatCardData as unknown as Parameters<typeof WSIScoreCard>[0]['data']}
            onViewDetails={() => handleCardAction("view_details")}
          />
        )
      case "compensation_summary":
        return (
          <CompensationSummaryCard
            data={chatCardData as unknown as Parameters<typeof CompensationSummaryCard>[0]['data']}
            onEdit={() => handleCardAction("edit")}
          />
        )
      case "interview_confirmation":
        return (
          <InterviewConfirmationCard
            data={chatCardData as unknown as Parameters<typeof InterviewConfirmationCard>[0]['data']}
            onAddToCalendar={() => handleCardAction("reschedule")}
            onCopyLink={() => handleCardAction("cancel")}
            onSendReminder={() => handleCardAction("confirm")}
          />
        )
      case "progress_tracker":
        return (
          <ProgressTrackerCard
            data={chatCardData as unknown as Parameters<typeof ProgressTrackerCard>[0]['data']}
          />
        )
      case "job_summary":
        return (
          <JobSummaryCard
            data={chatCardData as unknown as Parameters<typeof JobSummaryCard>[0]['data']}
            onEdit={() => handleCardAction("edit")}
            onPublish={() => handleCardAction("publish")}
            onView={() => handleCardAction("view_candidates")}
          />
        )
      case "company_benefits":
        return (
          <CompanyBenefitsSummaryCard
            data={chatCardData as unknown as Parameters<typeof CompanyBenefitsSummaryCard>[0]['data']}
            onViewAll={() => handleCardAction("view_all")}
            onAction={handleCardAction}
          />
        )
      default:
        return null
    }
  }, [handleChatCardAction])

  // ── Command Palette items ────────────────────────────────────────────────
  const commandItems: CommandItem[] = [
    // Fase 1: comandos de navegação DERIVADOS de canonical-pages.ts (DRY,
    // zero drift). Categoria 'Navegação' do Ctrl+/ — "/list de navegação".
    ...buildNavigationCommands({ locale, navigate: (url) => router.push(url) }),
    // Fase 2: comandos de AÇÃO derivados do capability_map (backend catalog).
    ...buildActionCommands(commandCatalog ?? [], handleSendMessage),
    ...defaultCommands({
      onSchedule: handleScheduleInterview,
      onEvaluate: handleEvaluateFit,
      onEmail: handleGenerateEmail,
      onWhatsApp: handleSendWhatsApp,
      onCompare: handleCompareProfiles,
      onAnalytics: handleViewAnalytics,
    }),
    { id: 'create-job', label: 'Criar Nova Vaga', description: 'Configure requisitos do sistema com descrição detalhada', category: 'actions', icon: Plus as unknown as React.ReactNode, shortcut: "", onSelect: () => handleSendMessage("Criar uma nova vaga") },
    { id: 'approve-job', label: 'Solicitar Aprovação de Vaga', description: 'Encaminhe documentação para aprovação gerencial', category: 'actions', icon: FileText as unknown as React.ReactNode, shortcut: "", onSelect: () => handleSendMessage("Solicite aprovação de nova vaga") },
    { id: 'share-candidates', label: 'Compartilhar Candidatos com Gestor', description: 'Crie relatório com perfis aprovados e recomendações', category: 'actions', icon: UserCheck as unknown as React.ReactNode, shortcut: "", onSelect: () => handleSendMessage("Compartilhe candidatos com gestor") },
    { id: 'feedback-interview', label: 'Solicitar Feedback de Entrevista', description: 'Colete avaliação detalhada pós-entrevista do gestor', category: 'actions', icon: MessageSquare as unknown as React.ReactNode, shortcut: "", onSelect: () => handleSendMessage("Solicite feedback de entrevista") },
    { id: 'candidate-info', label: 'Consultar Informações de Candidato', description: 'Obtenha histórico específico e histórico completo', category: 'actions', icon: Search as unknown as React.ReactNode, shortcut: "", onSelect: () => handleSendMessage("Consulte informações sobre candidato") },
    { id: 'add-candidate', label: 'Adicionar Novo Candidato', description: 'Cadastre perfil com talentos', category: 'actions', icon: UserCheck as unknown as React.ReactNode, shortcut: "", onSelect: () => handleSendMessage("Adicione novo candidato") },
    { id: 'reschedule-interview', label: 'Reagendar Entrevista', description: 'Cancele horário e notifique automaticamente participantes', category: 'actions', icon: Calendar as unknown as React.ReactNode, shortcut: "", onSelect: () => handleSendMessage("Reagende uma entrevista") },
    { id: 'update-status', label: 'Atualizar Status do Candidato', description: 'Modifique situação no processo e envie notificações', category: 'actions', icon: RefreshCcw as unknown as React.ReactNode, shortcut: "", onSelect: () => handleSendMessage("Atualize status do candidato") },
  ]

  // ── Quick Actions ────────────────────────────────────────────────────────
  const getQuickActions = (): QuickAction[] => {
    const baseActions: QuickAction[] = defaultCandidateActions.map(action => ({
      ...action,
      onClick: () => {
        switch (action.id) {
          case 'schedule': handleScheduleInterview(); break
          case 'evaluate': handleEvaluateFit(); break
          case 'email': handleGenerateEmail(); break
          case 'whatsapp': handleSendWhatsApp(); break
          case 'compare': handleCompareProfiles(); break
          case 'analytics': handleViewAnalytics(); break
        }
      },
    }))
    if (contextData?.type === 'candidate-suggestions')
      return baseActions.filter(a => ['schedule', 'evaluate', 'email', 'whatsapp'].includes(a.id))
    return baseActions.slice(0, 4)
  }

  // ── Dynamic placeholder ──────────────────────────────────────────────────
  const getPlaceholderText = (): string => {
    if (contextData?.type === 'candidate-suggestions')
      return 'Ex: "agendar amanhã às 14h comigo" ou "avaliar fit técnico"'
    if (contextData?.data?.candidates && (contextData.data.candidates as Record<string, unknown>[]).length > 0) {
      const candidate = (contextData.data.candidates as Record<string, unknown>[])[0]
      return `Pergunte sobre ${candidate.name}... Ex: "agendar entrevista com ${String(candidate.name).split(' ')[0]}"`
    }
    return 'Peça a LIA...'
  }

  // ── Return (same signature as original) ─────────────────────────────────
  return {
    // Search params
    conversationType,

    // Core state (from msg)
    messages: msg.messages, setMessages: msg.setMessages,
    input: msg.input, setInput: msg.setInput,
    isLoading: msg.isLoading,
    contextData, setContextData,
    isPanelOpen, setIsPanelOpen,
    searchTerm: msg.searchTerm, setSearchTerm: msg.setSearchTerm,
    showSearch: msg.showSearch, setShowSearch: msg.setShowSearch,
    newMessageIndicator: msg.newMessageIndicator,
    currentMessageIndex: msg.currentMessageIndex,
    availableCredits: session.availableCredits ?? 0,
    creditsError: session.creditsError,

    // Scheduling state (from session)
    isSchedulingModalOpen: session.isSchedulingModalOpen, setIsSchedulingModalOpen: session.setIsSchedulingModalOpen,
    isCommandPaletteOpen: session.isCommandPaletteOpen, setIsCommandPaletteOpen: session.setIsCommandPaletteOpen,
    selectedCandidateForScheduling: session.selectedCandidateForScheduling,

    // Candidate search state
    isCandidateDetailOpen: session.isCandidateDetailOpen, setIsCandidateDetailOpen: session.setIsCandidateDetailOpen,
    selectedCandidateForDetail: session.selectedCandidateForDetail, setSelectedCandidateForDetail: session.setSelectedCandidateForDetail,
    isCreditDialogOpen: session.isCreditDialogOpen, setIsCreditDialogOpen: session.setIsCreditDialogOpen,
    pendingPearchSearch: session.pendingPearchSearch,

    // Smart search state
    isSmartSearchMode: session.isSmartSearchMode,
    smartSearchQuery: session.smartSearchQuery, setSmartSearchQuery: session.setSmartSearchQuery,
    hasSearchResults: session.hasSearchResults,
    searchPreviewData: session.searchPreviewData,
    searchFlow: session.searchFlow,

    // Global settings
    globalSearchSettings: session.globalSearchSettings,
    globalSettingsLoading: session.globalSettingsLoading,

    // File state
    attachedFiles: msg.attachedFiles,
    fileValidationError: msg.fileValidationError, setFileValidationError: msg.setFileValidationError,
    fileInputRef: msg.fileInputRef,
    MAX_FILE_SIZE_MB,

    // Voice state
    isRecording: msg.isRecording,
    recordingTime: msg.recordingTime,
    audioBlob: msg.audioBlob, setAudioBlob: msg.setAudioBlob,

    // File analysis
    fileAnalysisContext: msg.fileAnalysisContext, setFileAnalysisContext: msg.setFileAnalysisContext,

    // Refs
    messagesEndRef: msg.messagesEndRef,
    messagesContainerRef: msg.messagesContainerRef,
    inputRef: msg.inputRef,

    // Layout
    isEmptyChat,
    chatContainerClass, inputContainerClass, messagesContainerClass,

    // Chat metadata
    chatId: session.chatId,
    chatTitle: session.chatTitle,
    activeTab: session.activeTab, setActiveTab: session.setActiveTab,

    // Pending action
    activePendingAction: session.activePendingAction,

    // Empty field notifications
    emptyFieldNotifications: session.emptyFieldNotifications,
    currentSuggestion: session.currentSuggestion,
    isLoadingSuggestion: session.isLoadingSuggestion,

    // Filters
    isFiltersModalOpen: session.isFiltersModalOpen, setIsFiltersModalOpen: session.setIsFiltersModalOpen,
    activeSearchFilters: session.activeSearchFilters,

    // Handlers
    handleSendMessage,
    handleKeyPress,
    handleActionClick: msg.handleActionClick,
    handleSmartSearchSubmit,
    handleSmartSearchCancel,
    handleApplyFilters: session.handleApplyFilters,
    handleFileButtonClick: msg.handleFileButtonClick,
    handleFileChange: msg.handleFileChange,
    handleRemoveFile: msg.handleRemoveFile,
    handleFilesSelected: msg.handleFilesSelected,
    handleFileAnalyzed: msg.handleFileAnalyzed,
    handleAudioTranscription: msg.handleAudioTranscription,
    handleAudioRecordingStart: msg.handleAudioRecordingStart,
    handleAudioRecordingEnd: msg.handleAudioRecordingEnd,
    handleRecordingToggle: msg.handleRecordingToggle,
    startRecording: msg.startRecording,
    stopRecording: msg.stopRecording,
    handleEmptyFieldAction: session.handleEmptyFieldAction,
    handleSuggestionAccepted: session.handleSuggestionAccepted,
    handleSuggestionRejected: session.handleSuggestionRejected,
    handleScheduleInterview,
    handleEvaluateFit,
    handleGenerateEmail,
    handleSendWhatsApp,
    handleCompareProfiles,
    handleViewAnalytics,
    handlePipelineAction,
    handleSelectCandidate,
    handleAddCandidatesToJob,
    handleCompareCandidates,
    handleLoadMoreCandidates,
    handleConfirmPearchSearch,
    handleAddCandidateToJob,
    handleSaveToBase,
    activateSmartSearch,

    // Derived / utility
    scrollToBottom: msg.scrollToBottom,
    checkNewMessageIndicator: msg.checkNewMessageIndicator,
    getRelativeTime: msg.getRelativeTime,
    getQuickSuggestions: msg.getQuickSuggestions,
    getActiveFiltersCount: session.getActiveFiltersCount,
    highlightSearchTerm: msg.highlightSearchTerm,
    formatMessageContent: msg.formatMessageContent,
    renderChatCard,
    commandItems,
    getQuickActions,
    getPlaceholderText,

    // UI Actions
    uiActions,
  }
}
