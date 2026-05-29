"use client"

import { useState, useCallback, useEffect, useMemo, useRef } from "react"
import { liaApi } from "@/services/lia-api"
import { useLiaFloat, useLiaChatContext } from "@/contexts/lia-float-context"
import type { Message, ContextPanelData, SelectedCandidateForScheduling, PendingPearchSearch } from "./chat-core.types"
import type { SearchFilters } from "@/components/search/advanced-filters-modal"
import type { SearchPreviewData } from "@/components/search/search-preview-card"
import type { CandidateResult } from "@/components/search/search-results-card"
import { useGlobalSearchSettings } from "@/hooks/search/useGlobalSearchSettings"
import { useEmptyFieldNotifications, type FieldValueSuggestion } from "@/hooks/candidates/use-empty-field-notifications"
import { useSearchFlow } from "@/hooks/search/useSearchFlow"
import { useCurrentCompany } from "@/hooks/company/use-current-company"

interface UseChatSessionOptions {
  initialConversation: Message[]
  conversationType: string
  messages: Message[]
  setMessages: (fn: (prev: Message[]) => Message[]) => void
  setIsLoading: (v: boolean) => void
  setContextData: (data: ContextPanelData | null) => void
  setIsPanelOpen: (open: boolean) => void
  initialConversationId?: string | null
}

export function useChatSession({
  initialConversation,
  conversationType,
  messages,
  setMessages,
  setIsLoading,
  setContextData,
  setIsPanelOpen,
  initialConversationId,
}: UseChatSessionOptions) {
  const {
    chatConversationId,
    setChatConversationId,
    switchChatContext,
    sendChatMessage,
    initChatConversation,
    loadChatHistory,
    chatIsConnected,
    chatIsStreaming,
    chatStreamingContent,
    connectChat,
    disconnectChat,
  } = useLiaChatContext()

  // ── Scheduling / Command Palette ───────────────────────────
  const [isSchedulingModalOpen, setIsSchedulingModalOpen] = useState(false)
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false)
  const [selectedCandidateForScheduling, setSelectedCandidateForScheduling] =
    useState<SelectedCandidateForScheduling | null>(null)

  // ── Candidate Search (Pearch) ──────────────────────────────
  const [isCandidateDetailOpen, setIsCandidateDetailOpen] = useState(false)
  const [selectedCandidateForDetail, setSelectedCandidateForDetail] = useState<CandidateResult | null>(null)
  const [isCreditDialogOpen, setIsCreditDialogOpen] = useState(false)
  const [pendingPearchSearch, setPendingPearchSearch] = useState<PendingPearchSearch | null>(null)

  // ── Smart Search ───────────────────────────────────────────
  const [isSmartSearchMode, setIsSmartSearchMode] = useState(false)
  const [smartSearchQuery, setSmartSearchQuery] = useState("")
  const searchFlow = useSearchFlow()
  const [searchPreviewData, setSearchPreviewData] = useState<SearchPreviewData | null>(null)
  const [hasSearchResults, setHasSearchResults] = useState(false)

  // ── Filters ────────────────────────────────────────────────
  const [isFiltersModalOpen, setIsFiltersModalOpen] = useState(false)
  const [activeSearchFilters, setActiveSearchFilters] = useState<SearchFilters>({})

  // ── Global settings ────────────────────────────────────────
  const { settings: globalSearchSettings, loading: globalSettingsLoading } = useGlobalSearchSettings()

  useEffect(() => {
    if (!globalSettingsLoading && globalSearchSettings) {
      setActiveSearchFilters(prev => ({
        ...prev,
        ppiOptions: {
          ...prev.ppiOptions,
          searchType: globalSearchSettings.searchType,
          highFreshness: globalSearchSettings.highFreshness,
          showEmails: globalSearchSettings.showEmails,
          showPhoneNumbers: globalSearchSettings.showPhoneNumbers,
        },
      }))
    }
  }, [globalSettingsLoading, globalSearchSettings])

  // ── Company context ──────────────────────────────────────
  const { companyId } = useCurrentCompany()

  // ── Empty field notifications ──────────────────────────────
  const emptyFieldNotifications = useEmptyFieldNotifications()
  const [currentSuggestion, setCurrentSuggestion] = useState<FieldValueSuggestion | null>(null)
  const [isLoadingSuggestion, setIsLoadingSuggestion] = useState(false)

  // ── Credits ────────────────────────────────────────────────
  const [availableCredits, setAvailableCredits] = useState<number | null>(null)
  const [creditsError, setCreditsError] = useState<string | null>(null)

  useEffect(() => {
    const fetchCredits = async () => {
      try {
        const balance = await liaApi.getCreditBalance("demo-user")
        setAvailableCredits(balance.available_credits)
        setCreditsError(null)
      } catch (err) {
        setCreditsError(err instanceof Error ? err.message : "Erro ao obter saldo de créditos")
        setAvailableCredits(null)
      }
    }
    fetchCredits()
  }, [])

  // ── Mark context type as "general" for Chat Page ──────────
  // On initial mount: handle URL param redirection and set up general context
  useEffect(() => {
    const params = new URLSearchParams(typeof window !== 'undefined' ? window.location.search : '')
    const urlConvId = params.get("conversation_id")

    if (urlConvId) {
      switchChatContext("general", { conversationId: urlConvId, continuePrevious: true })
      loadChatHistory(urlConvId).then(history => {
        if (history.length > 0) {
          setMessages(() => history as unknown as import("./chat-core.types").Message[])
        }
      }).catch((err) => { console.error('[useChatSession] loadChatHistory (url) failed', err) })
      params.delete("conversation_id")
      const qs = params.toString()
      window.history.replaceState({}, "", window.location.pathname + (qs ? `?${qs}` : ""))
    } else if (!initialConversationId) {
      switchChatContext("general", { conversationId: null })
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // ── React to intentional redirect via initialConversationId prop ───────────
  // Handles in-app navigation (e.g., from float to chat page with an existing conversation)
  useEffect(() => {
    if (!initialConversationId) return
    switchChatContext("general", { conversationId: initialConversationId, continuePrevious: true })
    loadChatHistory(initialConversationId).then(history => {
      if (history.length > 0) {
        setMessages(() => history as unknown as import("./chat-core.types").Message[])
      }
    }).catch((err) => { console.error('[useChatSession] loadChatHistory (initialConversationId) failed', err) })
  }, [initialConversationId]) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Chat ID & Title ────────────────────────────────────────
  const [chatId, setChatId] = useState("#0000")

  useEffect(() => {
    const timestamp = Date.now()
    setChatId(`#${String(timestamp).slice(-4)}`)
  }, [])

  const [chatTitle, setChatTitle] = useState(() => {
    if (conversationType === 'empty') return 'Nova Conversa'
    const firstMessages = initialConversation.slice(0, 5).map(m => m.content.toLowerCase()).join(' ')
    if (firstMessages.includes('vaga') || firstMessages.includes('posição') || firstMessages.includes('diretor')) {
      const directorMatch = firstMessages.match(/diretor\s+de\s+(\w+)/i)
      if (directorMatch) {
        return `Vaga ${directorMatch[0].split(' ').map((w: string) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}`
      }
      return 'Nova Vaga'
    }
    if (firstMessages.includes('candidato') || firstMessages.includes('triagem')) return 'Análise de Candidatos'
    if (firstMessages.includes('relatório') || firstMessages.includes('dashboard')) return 'Relatório & Analytics'
    if (firstMessages.includes('onboarding')) return 'Plano de Onboarding'
    return 'Conversa Geral'
  })

  const updateChatTitle = useCallback((newTitle: string) => setChatTitle(newTitle), [])

  const [activeTab, setActiveTab] = useState<"conversa" | "controle">("conversa")

  // ── Dynamic panel (split-screen) ──────────────────────────
  const { closeDynamicPanel } = useLiaFloat()

  // ── Unified Streaming (via LiaChatContext) ──────────────────
  const wsStreamingModeRef = useRef(false)

  useEffect(() => {
    connectChat()
    return () => { disconnectChat() }
  }, [connectChat, disconnectChat])

  const wsIsConnected = chatIsConnected
  const wsIsStreaming = chatIsStreaming

  const wsSendMessage = useCallback((content: string) => {
    sendChatMessage(content)
  }, [sendChatMessage])

  const wsClearTokens = useCallback(() => {
    // Tokens are managed by the unified connection; no-op for compatibility
  }, [])

  useEffect(() => {
    if (!wsStreamingModeRef.current || !chatStreamingContent) return
    const snapshot = chatStreamingContent
    setMessages(prev => {
      const updated = [...prev]
      const last = updated[updated.length - 1]
      if (last?.sender === 'lia') updated[updated.length - 1] = { ...last, content: snapshot }
      return updated
    })
  }, [chatStreamingContent, setMessages])

  useEffect(() => {
    if (wsStreamingModeRef.current && !chatIsStreaming && chatStreamingContent) {
      wsStreamingModeRef.current = false
      setIsLoading(false)
    }
  }, [chatIsStreaming, chatStreamingContent, setIsLoading])

  // ── Derived ────────────────────────────────────────────────
  const activePendingAction = useMemo(() => {
    const lastLia = [...messages].reverse().find(m => m.sender === "lia")
    const pending = lastLia?.data?.pending_action
    if (!pending || (pending as Record<string, unknown>).awaiting_confirmation) return null
    const missing = (pending as Record<string, unknown>).missing_params
    if (!missing || !(missing as unknown[]).length) return null
    return {
      intent: (pending as Record<string, unknown>).intent as string,
      missing_params: missing as string[],
    }
  }, [messages])

  // ── Window event listeners ─────────────────────────────────
  // "Nova Conversa"
  useEffect(() => {
    const handleNewChat = () => {
      setMessages(() => [])
      setContextData(null)
      setIsPanelOpen(false)
      setChatTitle('Nova Conversa')
      closeDynamicPanel()
      switchChatContext("general", { conversationId: null, resetConversation: true })
    }
    window.addEventListener('lia:new-chat', handleNewChat)
    return () => window.removeEventListener('lia:new-chat', handleNewChat)
  }, [setMessages, setContextData, setIsPanelOpen, closeDynamicPanel, switchChatContext])

  // "Funil Aberto"
  useEffect(() => {
    const handleOpenPipeline = async () => {
      setChatTitle('Gerenciamento de Pipeline')
      setIsLoading(true)
      try {
        const report = await liaApi.getStaleCandidates(3, 50)
        if (report && report.groups) {
          setContextData({
            type: "pipeline-report",
            title: "Funil - Candidatos Parados",
            data: report as unknown as Record<string, unknown>,
          })
          setIsPanelOpen(true)
          const totalStale = report.total_stale ||
            (report.groups as unknown as Record<string, unknown>[]).reduce(
              (acc: number, job: Record<string, unknown>) =>
                acc + ((job.stale_candidates as unknown[] | undefined)?.length || 0), 0
            )
          setMessages(prev => [...prev, {
            id: Date.now(), sender: "lia",
            content: Number(totalStale) > 0
              ? `Encontrei **${totalStale} candidatos** que estão parados há mais de 3 dias em **${report.groups.length} vagas**. No painel ao lado você pode ver o detalhamento e tomar ações rápidas para cada candidato.\n\nQuer que eu priorize alguma vaga específica ou sugira as próximas ações?`
              : `Ótimo! Todos os candidatos estão fluindo bem pelo funil. Nenhum candidato está parado há mais de 3 dias.\n\nPosso ajudar com outra coisa?`,
            timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
            type: "text",
          }])
        }
      } catch {
        setMessages(prev => [...prev, {
          id: Date.now(), sender: "lia",
          content: "Desculpe, não consegui carregar os dados do funil. Tente novamente em alguns instantes.",
          timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
          type: "text",
        }])
      } finally {
        setIsLoading(false)
      }
    }
    window.addEventListener('lia-open-pipeline', handleOpenPipeline as unknown as EventListener)
    return () => window.removeEventListener('lia-open-pipeline', handleOpenPipeline as unknown as EventListener)
  }, [setMessages, setContextData, setIsPanelOpen, setIsLoading])

  // "Nova Tarefa"
  useEffect(() => {
    const handleNewTask = async () => {
      setChatTitle('Nova Tarefa')

      try {
        const params = new URLSearchParams({ limit: '6' })
        if (companyId) params.set('company_id', companyId)
        const response = await fetch(`/api/backend-proxy/lia/suggestions?${params.toString()}`)

        if (!response.ok) {
          throw new Error(`Suggestions API returned ${response.status}`)
        }

        const data = await response.json()
        const taskSuggestions: { icon?: string; title: string; description: string }[] = Array.isArray(data.suggestions)
          ? data.suggestions
          : []

        const suggestionsText = taskSuggestions.length > 0
          ? taskSuggestions.map(s => `${s.icon || '💡'} **${s.title}** - ${s.description}`).join('\n')
          : null

        setMessages(prev => [...prev, {
          id: Date.now(), sender: "lia",
          content: suggestionsText
            ? `Olá! Estou pronta para ajudar você a criar uma nova tarefa. O que você gostaria de fazer?\n\n${suggestionsText}\n\nDigite o que você precisa ou escolha uma das opções acima!`
            : `Olá! Estou pronta para ajudar você a criar uma nova tarefa. O que você gostaria de fazer?\n\nDigite o que você precisa e vou ajudá-lo!`,
          timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
          type: "text",
        }])
      } catch (err) {
        setMessages(prev => [...prev, {
          id: Date.now(), sender: "lia",
          content: `Olá! Estou pronta para ajudar você a criar uma nova tarefa.\n\nNo momento não consegui carregar as sugestões personalizadas, mas pode me contar o que precisa e eu ajudo!`,
          timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
          type: "text",
        }])
      }
    }
    window.addEventListener('lia-new-task', handleNewTask)
    return () => window.removeEventListener('lia-new-task', handleNewTask)
  }, [setMessages, companyId])

  // "Nova Vaga"
  useEffect(() => {
    const handleNewJob = async () => {
      setChatTitle('Nova Vaga')
      if (companyId) await emptyFieldNotifications.fetchNotifications(companyId)
      setMessages(prev => [...prev, {
        id: Date.now(), sender: "lia",
        content: `Vou ajudar você a criar uma nova vaga. Me conte sobre a posição que você precisa preencher — cargo, departamento, modalidade (presencial/híbrida/remota) — ou cole uma descrição de vaga existente que eu extraio as informações automaticamente.`,
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        type: "text",
      }])
    }
    window.addEventListener('lia-new-job', handleNewJob)
    return () => window.removeEventListener('lia-new-job', handleNewJob)
  }, [emptyFieldNotifications, setMessages, companyId])

  // Library events
  useEffect(() => {
    const handleExecuteCommand = (event: CustomEvent) => {
      const { command, title } = event.detail
      setChatTitle(title || 'Comando da Biblioteca')
      setMessages(prev => [...prev, {
        id: Date.now(), sender: "user", content: command,
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        type: "text",
      }])
      setTimeout(() => {
        setMessages(prev => [...prev, {
          id: Date.now() + 1, sender: "lia",
          content: `Entendido! Estou processando seu comando: **"${title}"**\n\nAguarde enquanto analiso as informações...`,
          timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
          type: "text",
        }])
      }, 500)
    }

    const handleLibraryPrompt = (event: CustomEvent) => {
      const { prompt } = event.detail
      setChatTitle('Conversa com LIA')
      setMessages(prev => [...prev, {
        id: Date.now(), sender: "user", content: prompt,
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        type: "text",
      }])
    }

    const handleLibraryCategory = (event: CustomEvent) => {
      const { category } = event.detail
      setChatTitle(`Explorar ${category}`)
      setMessages(prev => [...prev, {
        id: Date.now(), sender: "lia",
        content: `Vamos explorar comandos de **${category}**! O que você gostaria de fazer?\n\nPosso ajudar com tarefas como buscar informações, gerar relatórios, automatizar processos ou criar conteúdo relacionado a ${category.toLowerCase()}.\n\nMe conte sua necessidade!`,
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        type: "text",
      }])
    }

    window.addEventListener('lia-execute-command', handleExecuteCommand as EventListener)
    window.addEventListener('lia-library-prompt', handleLibraryPrompt as EventListener)
    window.addEventListener('lia-library-category', handleLibraryCategory as EventListener)
    return () => {
      window.removeEventListener('lia-execute-command', handleExecuteCommand as EventListener)
      window.removeEventListener('lia-library-prompt', handleLibraryPrompt as EventListener)
      window.removeEventListener('lia-library-category', handleLibraryCategory as EventListener)
    }
  }, [setMessages])

  // ── Empty field notification handlers ─────────────────────
  const handleEmptyFieldAction = useCallback(async (action: string) => {
    const notification = emptyFieldNotifications.currentNotification
    if (!notification) return
    if (action === 'fill_now') {
      setIsLoadingSuggestion(true)
      if (!companyId) return
      const suggestion = await emptyFieldNotifications.getSuggestion(companyId, notification.field_key)
      setCurrentSuggestion(suggestion)
      setIsLoadingSuggestion(false)
      await emptyFieldNotifications.handleAction(companyId, notification.field_key, action)
    } else {
      if (!companyId) return
      await emptyFieldNotifications.handleAction(companyId, notification.field_key, action)
      setCurrentSuggestion(null)
      setMessages(prev => [...prev, {
        id: Date.now(), sender: "lia",
        content: action === 'remind_later'
          ? `Certo! Vou lembrar você sobre o campo **${notification.field_label}** em 7 dias. Por enquanto, usarei dados alternativos para as sugestões.`
          : `Entendido! Não vou mais lembrar sobre o campo **${notification.field_label}**. Usarei dados alternativos quando necessário.`,
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        type: "text",
      }])
    }
  }, [emptyFieldNotifications, setMessages, companyId])

  const handleSuggestionAccepted = useCallback((fieldKey: string, value: unknown) => {
    const formattedValue = typeof value === 'object' ? JSON.stringify(value) : String(value)
    setMessages(prev => [...prev, {
      id: Date.now(), sender: "lia",
      content: `Ótimo! O campo **${fieldKey}** foi atualizado com: ${formattedValue}\n\nAgora posso usar esse valor nas minhas sugestões para esta e futuras vagas.`,
      timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
      type: "text",
    }])
    setCurrentSuggestion(null)
  }, [setMessages])

  const handleSuggestionRejected = useCallback(() => {
    setCurrentSuggestion(null)
    setMessages(prev => [...prev, {
      id: Date.now(), sender: "lia",
      content: `Sem problemas! Usarei dados alternativos para as sugestões. Você pode configurar esse campo a qualquer momento nas configurações da empresa.`,
      timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
      type: "text",
    }])
  }, [setMessages])

  // ── Filter handlers ────────────────────────────────────────
  const handleApplyFilters = useCallback((filters: SearchFilters) => {
    setActiveSearchFilters(filters)
    setIsFiltersModalOpen(false)
  }, [])

  const getActiveFiltersCount = useCallback(() => {
    let count = 0
    Object.values(activeSearchFilters).forEach(category => {
      if (category) {
        Object.values(category).forEach(value => {
          if (value !== undefined && value !== null && value !== "" &&
            !(Array.isArray(value) && value.length === 0)) count++
        })
      }
    })
    return count
  }, [activeSearchFilters])

  return {
    isSchedulingModalOpen, setIsSchedulingModalOpen,
    isCommandPaletteOpen, setIsCommandPaletteOpen,
    selectedCandidateForScheduling, setSelectedCandidateForScheduling,
    isCandidateDetailOpen, setIsCandidateDetailOpen,
    selectedCandidateForDetail, setSelectedCandidateForDetail,
    isCreditDialogOpen, setIsCreditDialogOpen,
    pendingPearchSearch, setPendingPearchSearch,
    isSmartSearchMode, setIsSmartSearchMode,
    smartSearchQuery, setSmartSearchQuery,
    searchFlow,
    searchPreviewData, setSearchPreviewData,
    hasSearchResults, setHasSearchResults,
    isFiltersModalOpen, setIsFiltersModalOpen,
    activeSearchFilters,
    globalSearchSettings, globalSettingsLoading,
    emptyFieldNotifications,
    currentSuggestion,
    isLoadingSuggestion,
    availableCredits,
    creditsError,
    chatId,
    chatTitle, setChatTitle,
    activeTab, setActiveTab,
    updateChatTitle,
    wsIsConnected,
    wsSendMessage,
    wsClearTokens,
    wsStreamingModeRef,
    activePendingAction,
    handleEmptyFieldAction,
    handleSuggestionAccepted,
    handleSuggestionRejected,
    handleApplyFilters,
    getActiveFiltersCount,
    chatConversationId,
    setChatConversationId,
    sendChatMessage,
    initChatConversation,
    loadChatHistory,
  }
}
