"use client"

import { useState, useEffect, useCallback, useRef, useMemo } from "react"
import { useSearchParams } from "next/navigation"
import { useChatLayout } from "@/hooks/useChatLayout"
import { useEmptyFieldNotifications, type FieldValueSuggestion } from "@/hooks/use-empty-field-notifications"
import { liaApi } from "@/services/lia-api"
import {
  FileText, Users, Plus, MessageSquare, Search, Calendar, BarChart3, Target,
  UserCheck, RefreshCcw, Database
} from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import type { CandidateResult } from "@/components/search/search-results-card"
import type { ParsedEntities, SearchMode, SearchMetadata } from "@/components/search/smart-search-input"
import type { SearchFilters } from "@/components/search/advanced-filters-modal"
import type { SearchPreviewData } from "@/components/search/search-preview-card"
import type { FileAnalysisResult } from "@/components/ui/file-upload-button"
import { promoteCandidateToBase } from "@/lib/api/candidate-search"
import { useSearchFlow } from "@/hooks/useSearchFlow"
import { useUIActions } from "@/hooks/useUIActions"
import { useAgentStreaming } from "@/hooks/use-agent-streaming"
import { useGlobalSearchSettings } from "@/hooks/useGlobalSearchSettings"
import type { SidePanelType, PanelSubmitData, ChatCardType } from "@/components/ui-actions/types"
import { type QuickAction, defaultCandidateActions } from "@/components/ui/quick-action-chips"
import { type CommandItem, defaultCommands } from "@/components/ui/command-palette"
import {
  CandidateSummaryCard,
  JobSummaryCard,
  WSIScoreCard,
  CompensationSummaryCard,
  InterviewConfirmationCard,
  ProgressTrackerCard,
  CompanyBenefitsSummaryCard
} from "@/components/ui-actions"
import type { Message, ContextPanelData } from "./types"
import { emptyConversation, modernConversation } from "./constants"

export function useChatPageCore() {
  const searchParams = useSearchParams()
  
  // Permite alternar entre conversas via URL (/?conversation=director para histórico)
  // Por padrão, inicia com conversa vazia
  const conversationType = searchParams?.get('conversation') || 'empty'
  const initialConversation = conversationType === 'empty' ? emptyConversation : modernConversation
  
  const [messages, setMessages] = useState<Message[]>(initialConversation)
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [contextData, setContextData] = useState<ContextPanelData | null>(null)
  const [isPanelOpen, setIsPanelOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState("")
  const [showSearch, setShowSearch] = useState(false)
  const [newMessageIndicator, setNewMessageIndicator] = useState(false)
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0)
  const [availableCredits, setAvailableCredits] = useState<number>(50)

  // Interview Scheduling Modal state
  const [isSchedulingModalOpen, setIsSchedulingModalOpen] = useState(false)
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false)
  const [selectedCandidateForScheduling, setSelectedCandidateForScheduling] = useState<{
    name: string
    email: string
    id?: string
    job_title: string
    job_vacancy_id?: string
  } | null>(null)

  // Candidate Search states (Pearch Integration)
  const [isCandidateDetailOpen, setIsCandidateDetailOpen] = useState(false)
  const [selectedCandidateForDetail, setSelectedCandidateForDetail] = useState<CandidateResult | null>(null)
  const [isCreditDialogOpen, setIsCreditDialogOpen] = useState(false)
  const [pendingPearchSearch, setPendingPearchSearch] = useState<{
    query: string
    threadId?: string
  } | null>(null)

  // Smart Search Mode - expands input with dynamic tags
  const [isSmartSearchMode, setIsSmartSearchMode] = useState(false)
  const [smartSearchQuery, setSmartSearchQuery] = useState("")

  // Search Flow State Machine - controls the candidate search experience
  const searchFlow = useSearchFlow()
  const [searchPreviewData, setSearchPreviewData] = useState<SearchPreviewData | null>(null)
  const [hasSearchResults, setHasSearchResults] = useState(false)
  
  // Global Search Settings - provides default values for search filters
  const { settings: globalSearchSettings, loading: globalSettingsLoading } = useGlobalSearchSettings()
  
  // UI Actions System - Side panels and Chat Cards from agents
  const handlePanelSubmit = useCallback(async (data: PanelSubmitData) => {
    // Here you can send the data back to the backend or process it
  }, [])

  const handlePanelClose = useCallback((panelType: SidePanelType) => {
  }, [])

  const handleChatCardAction = useCallback((cardType: ChatCardType, action: string, data: unknown) => {
    // Process chat card actions - e.g., schedule interview, view candidate details
    if (cardType === "candidate_summary" && action === "schedule") {
      const candidateData = data as { id: string; name: string; email?: string; title?: string }
      setSelectedCandidateForScheduling({
        name: candidateData.name,
        email: candidateData.email || "",
        id: candidateData.id,
        job_title: candidateData.title || "Candidato"
      })
      setIsSchedulingModalOpen(true)
    }
  }, [])

  const uiActions = useUIActions({
    onPanelSubmit: handlePanelSubmit,
    onPanelClose: handlePanelClose,
    onChatCardAction: handleChatCardAction,
    enableWebSocket: false // UI-actions WS (panels/cards) — kept disabled; token streaming uses useAgentStreaming below
  })

  // Advanced Filters Modal
  const [isFiltersModalOpen, setIsFiltersModalOpen] = useState(false)
  const [activeSearchFilters, setActiveSearchFilters] = useState<SearchFilters>({})
  
  // Empty Field Notifications - for job creation wizard
  const emptyFieldNotifications = useEmptyFieldNotifications()
  const [currentSuggestion, setCurrentSuggestion] = useState<FieldValueSuggestion | null>(null)
  const [isLoadingSuggestion, setIsLoadingSuggestion] = useState(false)
  const DEFAULT_COMPANY_ID = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
  
  // Initialize search filters with global settings when loaded
  useEffect(() => {
    if (!globalSettingsLoading && globalSearchSettings) {
      setActiveSearchFilters(prev => ({
        ...prev,
        ppiOptions: {
          ...prev.ppiOptions,
          searchType: globalSearchSettings.searchType,
          highFreshness: globalSearchSettings.highFreshness,
          showEmails: globalSearchSettings.showEmails,
          showPhoneNumbers: globalSearchSettings.showPhoneNumbers
        }
      }))
    }
  }, [globalSettingsLoading, globalSearchSettings])
  
  // File Attachment states
  const [attachedFiles, setAttachedFiles] = useState<File[]>([])
  const [fileValidationError, setFileValidationError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  // File validation constants
  const MAX_FILE_SIZE_MB = 10
  const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
  const ALLOWED_FILE_TYPES = {
    'application/pdf': 'PDF',
    'application/msword': 'DOC',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
    'text/plain': 'TXT',
    'text/csv': 'CSV',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'XLSX',
    'application/vnd.ms-excel': 'XLS',
    'image/png': 'PNG',
    'image/jpeg': 'JPG',
    'image/jpg': 'JPG'
  } as const
  
  // Voice Recording states
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null)
  
  // Toast notifications
  const { toast } = useToast()
  
  // File analysis context - stores analyzed file data to include in messages
  const [fileAnalysisContext, setFileAnalysisContext] = useState<FileAnalysisResult | null>(null)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  
  // Detecta se a conversa está vazia para ajustar layout
  const isEmptyChat = messages.length === 0
  
  // Chat layout hook - gerencia estados de layout (empty, chat-only, chat-with-panel)
  const { mode: layoutMode, chatContainerClass, inputContainerClass, messagesContainerClass } = useChatLayout({
    isEmptyChat,
    isPanelOpen
  })
  
  // Ciclo fechado: detectar ação pendente na última mensagem da LIA
  const activePendingAction = useMemo(() => {
    const lastLia = [...messages].reverse().find(m => m.sender === "lia")
    const pending = lastLia?.data?.pending_action
    if (!pending || pending.awaiting_confirmation) return null
    if (!pending.missing_params?.length) return null
    return { intent: pending.intent as string, missing_params: pending.missing_params as string[] }
  }, [messages])

  // Sistema de Títulos Automáticos para Histórico
  // Use fixed initial value to avoid hydration mismatch
  const [chatId, setChatId] = useState("#0000")

  // Generate ID on client-side only
  useEffect(() => {
    const timestamp = Date.now()
    const id = String(timestamp).slice(-4)
    setChatId(`#${id}`)
  }, [])

  // ── Agent Streaming via WebSocket ────────────────────────────────────────
  // Receives LangGraph tokens in real-time from StreamingCallback → ws_manager.
  // Connects to /ws/chat/{wsSessionId}; tokens update the last LIA message live.
  // Falls back to SSE path when WS is not connected.
  const wsSessionId = chatId.replace('#', '')
  const {
    tokens: wsTokens,
    isStreaming: wsIsStreaming,
    isConnected: wsIsConnected,
    connect: wsConnect,
    disconnect: wsDisconnect,
    clearTokens: wsClearTokens,
    sendMessage: wsSendMessage,
  } = useAgentStreaming(wsSessionId)

  // Ref updated synchronously so finally{} can check it without async state lag
  const wsStreamingModeRef = useRef(false)

  // Connect once chatId settles to a real value (not the SSR placeholder '#0000')
  useEffect(() => {
    if (wsSessionId && wsSessionId !== '0000') {
      wsConnect()
    }
    return () => { wsDisconnect() }
  }, [wsSessionId, wsConnect, wsDisconnect])

  // Update last LIA message as WS tokens accumulate
  useEffect(() => {
    if (!wsStreamingModeRef.current || !wsTokens) return
    setMessages(prev => {
      const updated = [...prev]
      const last = updated[updated.length - 1]
      if (last?.sender === 'lia') {
        updated[updated.length - 1] = { ...last, content: wsTokens }
      }
      return updated
    })
  }, [wsTokens])

  // Reset isLoading when WS streaming ends (token_done received)
  useEffect(() => {
    if (wsStreamingModeRef.current && !wsIsStreaming && wsTokens) {
      wsStreamingModeRef.current = false
      setIsLoading(false)
    }
  }, [wsIsStreaming, wsTokens])
  // ─────────────────────────────────────────────────────────────────────────

  const [chatTitle, setChatTitle] = useState(() => {
    if (conversationType === 'empty') {
      return 'Nova Conversa'
    }
    
    // Detecta o tipo de conversa baseado nas primeiras mensagens
    const firstMessages = initialConversation.slice(0, 5).map(m => m.content.toLowerCase()).join(' ')
    
    if (firstMessages.includes('vaga') || firstMessages.includes('posição') || firstMessages.includes('diretor')) {
      // Tenta extrair o cargo específico
      const directorMatch = firstMessages.match(/diretor\s+de\s+(\w+)/i)
      if (directorMatch) {
        return `Vaga ${directorMatch[0].split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}`
      }
      return 'Nova Vaga'
    }
    
    if (firstMessages.includes('candidato') || firstMessages.includes('triagem')) {
      return 'Análise de Candidatos'
    }
    
    if (firstMessages.includes('relatório') || firstMessages.includes('dashboard')) {
      return 'Relatório & Analytics'
    }
    
    if (firstMessages.includes('onboarding')) {
      return 'Plano de Onboarding'
    }
    
    return 'Conversa Geral'
  })

  const [activeTab, setActiveTab] = useState<"conversa" | "controle">("conversa")
  
  // Função helper para atualizar título manualmente (útil para quando criar nova conversa)
  const updateChatTitle = useCallback((newTitle: string) => {
    setChatTitle(newTitle)
  }, [])

  // Process contextData from initial/seeded conversation messages
  useEffect(() => {
    // Only run once on mount to check if any initial message has contextData
    if (initialConversation.length > 0) {
      // Find the last message with contextData (most recent)
      const messageWithContext = initialConversation
        .slice()
        .reverse()
        .find(msg => msg.contextData)
      
      if (messageWithContext && messageWithContext.contextData) {
        setContextData(messageWithContext.contextData)
        setIsPanelOpen(true)
      }
    }
  }, []) // Empty dependency array - run only on mount

  // Fetch credit balance on mount
  useEffect(() => {
    const fetchCredits = async () => {
      try {
        const balance = await liaApi.getCreditBalance("demo-user")
        setAvailableCredits(balance.available_credits)
      } catch (error) {
        // Keep default value (50) on error
      }
    }
    
    fetchCredits()
  }, []) // Empty dependency array - run only on mount

  // Escuta evento de "Novo Chat" do botão do sidebar
  useEffect(() => {
    const handleNewChat = () => {
      setMessages([])
      setInput("")
      setContextData(null)
      setIsPanelOpen(false)
      setChatTitle('Nova Conversa')
    }

    window.addEventListener('lia:new-chat', handleNewChat)
    return () => window.removeEventListener('lia:new-chat', handleNewChat)
  }, [])

  // Escuta evento de "Ver Pipeline" do Daily Briefing Card
  useEffect(() => {
    const handleOpenPipeline = async (event: CustomEvent) => {
      setChatTitle('Gerenciamento de Pipeline')
      setIsLoading(true)
      
      try {
        const report = await liaApi.getStaleCandidates(3, 50)
        
        if (report && report.groups) {
          setContextData({
            type: "pipeline-report",
            title: "Pipeline - Candidatos Parados",
            data: report
          })
          setIsPanelOpen(true)
          
          const totalStale = report.total_stale || report.groups.reduce(
            (acc: number, job: Record<string, unknown>) => acc + ((job.stale_candidates as unknown[] | undefined)?.length || 0), 0
          )
          
          const newMessage: Message = {
            id: Date.now(),
            sender: "lia",
            content: totalStale > 0 
              ? `Encontrei **${totalStale} candidatos** que estão parados há mais de 3 dias em **${report.groups.length} vagas**. No painel ao lado você pode ver o detalhamento e tomar ações rápidas para cada candidato.\n\nQuer que eu priorize alguma vaga específica ou sugira as próximas ações?`
              : `Ótimo! Todos os candidatos estão fluindo bem pelo pipeline. Nenhum candidato está parado há mais de 3 dias.\n\nPosso ajudar com outra coisa?`,
            timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
            type: "text"
          }
          setMessages(prev => [...prev, newMessage])
        }
      } catch (error) {
        const errorMessage: Message = {
          id: Date.now(),
          sender: "lia",
          content: "Desculpe, não consegui carregar os dados do pipeline. Tente novamente em alguns instantes.",
          timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
          type: "text"
        }
        setMessages(prev => [...prev, errorMessage])
      } finally {
        setIsLoading(false)
      }
    }

    window.addEventListener('lia-open-pipeline', handleOpenPipeline as EventListener)
    return () => window.removeEventListener('lia-open-pipeline', handleOpenPipeline as EventListener)
  }, [])

  // Escuta evento de "Nova Tarefa" do botão do Painel de Controle
  useEffect(() => {
    const handleNewTask = () => {
      setChatTitle('Nova Tarefa')
      
      const taskSuggestions = [
        { icon: '🔍', title: 'Buscar candidatos', description: 'Encontrar perfis que atendam aos requisitos de uma vaga' },
        { icon: '📋', title: 'Criar nova vaga', description: 'Definir uma nova posição com requisitos e benefícios' },
        { icon: '📞', title: 'Agendar entrevistas', description: 'Organizar entrevistas com candidatos selecionados' },
        { icon: '✉️', title: 'Enviar comunicações', description: 'Enviar emails ou mensagens para candidatos' },
        { icon: '📊', title: 'Gerar relatório', description: 'Criar análises e relatórios de recrutamento' },
        { icon: '🎯', title: 'Fazer triagem', description: 'Avaliar e qualificar candidatos de uma vaga' },
      ]
      
      const suggestionsText = taskSuggestions.map(s => `${s.icon} **${s.title}** - ${s.description}`).join('\n')
      
      const newMessage: Message = {
        id: Date.now(),
        sender: "lia",
        content: `Olá! Estou pronta para ajudar você a criar uma nova tarefa. O que você gostaria de fazer?\n\n${suggestionsText}\n\nDigite o que você precisa ou escolha uma das opções acima!`,
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        type: "text"
      }
      setMessages(prev => [...prev, newMessage])
    }

    window.addEventListener('lia-new-task', handleNewTask)
    return () => window.removeEventListener('lia-new-task', handleNewTask)
  }, [])

  // Handler para ações de notificação de campos vazios
  const handleEmptyFieldAction = useCallback(async (action: string) => {
    const notification = emptyFieldNotifications.currentNotification
    if (!notification) return
    
    if (action === 'fill_now') {
      setIsLoadingSuggestion(true)
      const suggestion = await emptyFieldNotifications.getSuggestion(DEFAULT_COMPANY_ID, notification.field_key)
      setCurrentSuggestion(suggestion)
      setIsLoadingSuggestion(false)
      await emptyFieldNotifications.handleAction(DEFAULT_COMPANY_ID, notification.field_key, action)
    } else {
      await emptyFieldNotifications.handleAction(DEFAULT_COMPANY_ID, notification.field_key, action)
      setCurrentSuggestion(null)
      
      // Adiciona mensagem de confirmação no chat
      const confirmMessage: Message = {
        id: Date.now(),
        sender: "lia",
        content: action === 'remind_later' 
          ? `Certo! Vou lembrar você sobre o campo **${notification.field_label}** em 7 dias. Por enquanto, usarei dados alternativos para as sugestões.`
          : `Entendido! Não vou mais lembrar sobre o campo **${notification.field_label}**. Usarei dados alternativos quando necessário.`,
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        type: "text"
      }
      setMessages(prev => [...prev, confirmMessage])
    }
  }, [emptyFieldNotifications])

  // Handler para quando o recrutador aceita uma sugestão
  const handleSuggestionAccepted = useCallback((fieldKey: string, value: unknown) => {
    const formattedValue = typeof value === 'object' ? JSON.stringify(value) : String(value)
    
    const confirmMessage: Message = {
      id: Date.now(),
      sender: "lia",
      content: `Ótimo! O campo **${fieldKey}** foi atualizado com: ${formattedValue}\n\nAgora posso usar esse valor nas minhas sugestões para esta e futuras vagas.`,
      timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
      type: "text"
    }
    setMessages(prev => [...prev, confirmMessage])
    setCurrentSuggestion(null)
  }, [])
  
  // Handler para quando o recrutador rejeita a sugestão
  const handleSuggestionRejected = useCallback(() => {
    setCurrentSuggestion(null)
    
    const confirmMessage: Message = {
      id: Date.now(),
      sender: "lia",
      content: `Sem problemas! Usarei dados alternativos para as sugestões. Você pode configurar esse campo a qualquer momento nas configurações da empresa.`,
      timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
      type: "text"
    }
    setMessages(prev => [...prev, confirmMessage])
  }, [])

  // Escuta evento de "Nova Vaga" do botão da página de Vagas
  useEffect(() => {
    const handleNewJob = async () => {
      setChatTitle('Nova Vaga')
      
      // Primeiro, verifica se há campos vazios com toggles ativos
      await emptyFieldNotifications.fetchNotifications(DEFAULT_COMPANY_ID)
      
      const newMessage: Message = {
        id: Date.now(),
        sender: "lia",
        content: `Olá! Sou a **LIA**, sua assistente de recrutamento. Vou ajudar você a criar uma nova vaga de forma conversacional.

Para começar, me conte sobre a posição que você precisa preencher:

**O que preciso saber:**
- Qual é o **cargo/título** da vaga?
- Para qual **departamento** ou **área** é essa posição?
- É uma vaga **presencial**, **híbrida** ou **remota**?

Você pode me contar livremente ou colar uma descrição de vaga existente que eu extraio as informações automaticamente!`,
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        type: "text"
      }
      setMessages(prev => [...prev, newMessage])
    }

    window.addEventListener('lia-new-job', handleNewJob)
    return () => window.removeEventListener('lia-new-job', handleNewJob)
  }, [emptyFieldNotifications])

  // Escuta eventos da Biblioteca LIA
  useEffect(() => {
    const handleExecuteCommand = (event: CustomEvent) => {
      const { command, title } = event.detail
      setChatTitle(title || 'Comando da Biblioteca')
      
      const userMessage: Message = {
        id: Date.now(),
        sender: "user",
        content: command,
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        type: "text"
      }
      setMessages(prev => [...prev, userMessage])
      
      setTimeout(() => {
        const liaResponse: Message = {
          id: Date.now() + 1,
          sender: "lia",
          content: `Entendido! Estou processando seu comando: **"${title}"**\n\nAguarde enquanto analiso as informações...`,
          timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
          type: "text"
        }
        setMessages(prev => [...prev, liaResponse])
      }, 500)
    }

    const handleLibraryPrompt = (event: CustomEvent) => {
      const { prompt } = event.detail
      setChatTitle('Conversa com LIA')
      
      const userMessage: Message = {
        id: Date.now(),
        sender: "user",
        content: prompt,
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        type: "text"
      }
      setMessages(prev => [...prev, userMessage])
    }

    const handleLibraryCategory = (event: CustomEvent) => {
      const { category } = event.detail
      setChatTitle(`Explorar ${category}`)
      
      const newMessage: Message = {
        id: Date.now(),
        sender: "lia",
        content: `Vamos explorar comandos de **${category}**! O que você gostaria de fazer?\n\nPosso ajudar com tarefas como buscar informações, gerar relatórios, automatizar processos ou criar conteúdo relacionado a ${category.toLowerCase()}.\n\nMe conte sua necessidade!`,
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        type: "text"
      }
      setMessages(prev => [...prev, newMessage])
    }

    window.addEventListener('lia-execute-command', handleExecuteCommand as EventListener)
    window.addEventListener('lia-library-prompt', handleLibraryPrompt as EventListener)
    window.addEventListener('lia-library-category', handleLibraryCategory as EventListener)
    
    return () => {
      window.removeEventListener('lia-execute-command', handleExecuteCommand as EventListener)
      window.removeEventListener('lia-library-prompt', handleLibraryPrompt as EventListener)
      window.removeEventListener('lia-library-category', handleLibraryCategory as EventListener)
    }
  }, [])

  // Função para converter timestamp para relativo
  const getRelativeTime = useCallback((timestamp: string) => {
    const now = new Date()
    const messageTime = new Date(`2024-02-22T${timestamp}:00`)
    const diffInMinutes = Math.floor((now.getTime() - messageTime.getTime()) / (1000 * 60))

    if (diffInMinutes < 1) return "agora"
    if (diffInMinutes < 60) return `há ${diffInMinutes} min`
    if (diffInMinutes < 1440) return `há ${Math.floor(diffInMinutes / 60)}h`
    return "ontem"
  }, [])

  // Sugestões de resposta rápida baseadas no contexto
  const getQuickSuggestions = useCallback(() => {
    const lastLiaMessage = messages.filter(m => m.sender === "lia").pop()
    if (!lastLiaMessage) return []

    const content = lastLiaMessage.content.toLowerCase()

    if (content.includes("competências") || content.includes("liderança")) {
      return ["Concordo", "Preciso de mais detalhes", "Vamos prosseguir"]
    }
    if (content.includes("remuneração") || content.includes("salário")) {
      return ["Está dentro do orçamento", "Precisamos ajustar", "Perfeito"]
    }
    if (content.includes("candidato") || content.includes("perfil")) {
      return ["Interessante", "Vamos agendar", "Preciso avaliar"]
    }
    return ["Entendi", "Continue", "Preciso de mais informações"]
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  // Calculate active filters count
  const getActiveFiltersCount = useCallback(() => {
    let count = 0
    Object.values(activeSearchFilters).forEach(category => {
      if (category) {
        Object.values(category).forEach(value => {
          if (value !== undefined && value !== null && value !== "" && 
              !(Array.isArray(value) && value.length === 0)) {
            count++
          }
        })
      }
    })
    return count
  }, [activeSearchFilters])

  // Handle filters apply
  const handleApplyFilters = useCallback((filters: SearchFilters) => {
    setActiveSearchFilters(filters)
    setIsFiltersModalOpen(false)
  }, [])

  // Smart Search Handlers
  const handleSmartSearchSubmit = useCallback(async (query: string, entities: ParsedEntities, mode?: SearchMode, metadata?: SearchMetadata) => {
    setIsSmartSearchMode(false)
    setSmartSearchQuery("")
    
    // Construct search metadata with mode and filters
    const finalMode = mode || "natural"
    const finalMetadata: SearchMetadata = metadata || { mode: finalMode }
    
    // Submit search with all context (mode, metadata, filters)
    searchFlow.submitSearch({
      query,
      entities,
      mode: finalMode,
      metadata: finalMetadata,
      filters: activeSearchFilters
    })
    
    // Add user message showing what they searched for (use unique timestamp-based IDs)
    const timestamp = Date.now()
    const userMessage: Message = {
      id: timestamp,
      sender: "user",
      content: query,
      timestamp: new Date().toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit"
      }),
      type: "text"
    }
    setMessages(prev => [...prev, userMessage])
    
    // Set preview data with loading state
    setSearchPreviewData({
      query,
      localCount: 0,
      pearchEstimate: 0,
      pearchCredits: 0,
      isSearchingLocal: true,
      isEstimatingPearch: true
    })
    
    // Create enriched search query with detected entities
    let enrichedQuery = query
    if (entities.job_title || entities.skills?.length || entities.location) {
      const parts: string[] = []
      if (entities.job_title) parts.push(`cargo: ${entities.job_title}`)
      if (entities.location) parts.push(`local: ${entities.location}`)
      if (entities.skills?.length) parts.push(`skills: ${entities.skills.join(", ")}`)
      if (entities.years_experience) parts.push(`experiência: ${entities.years_experience}`)
      if (entities.seniority) parts.push(`senioridade: ${entities.seniority}`)
      enrichedQuery = `Buscar candidatos: ${query} [${parts.join(" | ")}]`
    }
    
    setIsLoading(true)
    
    try {
      // Execute real search via backend
      const response = await liaApi.sendMessage({
        content: enrichedQuery,
        user_id: "demo-user"
      })
      
      const workflowData = response.conversation?.workflow_data || response.message.message_metadata?.workflow_data
      const searchResults = workflowData?.search_results
      
      const localCount = searchResults?.local_count || searchResults?.local_candidates?.length || 0
      const globalCandidates = searchResults?.global_candidates || []
      
      // Update preview with real counts
      setSearchPreviewData({
        query,
        localCount,
        pearchEstimate: globalCandidates.length > 0 ? globalCandidates.length : Math.floor(Math.random() * 50) + 10,
        pearchCredits: Math.max(5, Math.ceil(localCount / 2) + 5),
        isSearchingLocal: false,
        isEstimatingPearch: false
      })
      
      // Store the response for later use (use unique ID to avoid duplicates)
      const liaResponse: Message = {
        id: timestamp + 1,
        sender: "lia",
        content: localCount > 0 
          ? `Encontrei **${localCount} candidato(s)** no banco proprietário que correspondem ao perfil.\n\nVocê pode ver os resultados abaixo ou expandir a busca para o banco global com 800M+ perfis.`
          : `Não encontrei candidatos correspondentes no banco proprietário, mas posso buscar no banco global com 800M+ perfis.`,
        timestamp: new Date().toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit"
        }),
        type: "text",
        data: {
          workflow_data: workflowData
        }
      }
      
      setMessages(prev => [...prev.filter(m => m.type !== "thinking"), liaResponse])
      
      if (searchResults) {
        setHasSearchResults(true)
        searchFlow.showResults()
        
        const totalCount = localCount + globalCandidates.length
        if (totalCount > 0) {
          setContextData({
            type: "candidate-suggestions",
            title: `Candidatos Encontrados (${totalCount})`,
            data: {
              query: searchResults.query,
              source: searchResults.source,
              localCount,
              totalCount,
              candidates: [...(searchResults.local_candidates || []), ...globalCandidates]
            }
          })
          setIsPanelOpen(true)
        }
      }
      
    } catch (error) {
      setSearchPreviewData(null)
      
      const errorMessage: Message = {
        id: timestamp + 2,
        sender: "lia",
        content: "Desculpe, ocorreu um erro ao buscar candidatos. Por favor, tente novamente.",
        timestamp: new Date().toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit"
        }),
        type: "text"
      }
      setMessages(prev => [...prev.filter(m => m.type !== "thinking"), errorMessage])
    } finally {
      setIsLoading(false)
    }
  }, [searchFlow, activeSearchFilters])

  const handleSmartSearchCancel = useCallback(() => {
    setIsSmartSearchMode(false)
    setSmartSearchQuery("")
    searchFlow.reset()
    setSearchPreviewData(null)
  }, [searchFlow])

  // ============================================
  // FILE ATTACHMENT HANDLERS
  // ============================================
  const handleFileButtonClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      const newFiles = Array.from(files)
      const validFiles: File[] = []
      const errors: string[] = []
      
      newFiles.forEach(file => {
        if (file.size > MAX_FILE_SIZE_BYTES) {
          const sizeMB = (file.size / (1024 * 1024)).toFixed(1)
          errors.push(`"${file.name}" excede ${MAX_FILE_SIZE_MB}MB (${sizeMB}MB)`)
          return
        }
        
        if (!(file.type in ALLOWED_FILE_TYPES)) {
          const ext = file.name.split('.').pop()?.toUpperCase() || 'desconhecido'
          errors.push(`"${file.name}" tem tipo não suportado (.${ext})`)
          return
        }
        
        validFiles.push(file)
      })
      
      if (errors.length > 0) {
        const errorMessage = errors.length === 1 
          ? errors[0] 
          : `${errors.length} arquivos rejeitados:\n• ${errors.join('\n• ')}`
        setFileValidationError(errorMessage)
        
        setTimeout(() => setFileValidationError(null), 5000)
      }
      
      if (validFiles.length > 0) {
        setAttachedFiles(prev => [...prev, ...validFiles])
        
        const fileNames = validFiles.map(f => f.name).join(", ")
        const message = validFiles.length === 1
          ? `Arquivo "${fileNames}" anexado. O que gostaria que eu fizesse com ele?`
          : `${validFiles.length} arquivos anexados (${fileNames}). O que gostaria que eu fizesse com eles?`
        
        const liaResponse: Message = {
          id: Date.now(),
          sender: "lia",
          content: message,
          timestamp: new Date().toLocaleTimeString("pt-BR", {
            hour: "2-digit",
            minute: "2-digit"
          }),
          type: "text",
          actions: [
            { label: "Analisar CV", icon: FileText, variant: "default" },
            { label: "Extrair dados", icon: Database, variant: "outline" },
            { label: "Comparar perfis", icon: Users, variant: "outline" }
          ]
        }
        setMessages(prev => [...prev, liaResponse])
      }
    }
    if (e.target) {
      e.target.value = ""
    }
  }, [MAX_FILE_SIZE_BYTES, ALLOWED_FILE_TYPES])

  const handleRemoveFile = useCallback((index: number) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index))
  }, [])

  // File Upload Button handlers
  const handleFilesSelected = useCallback((files: File[]) => {
    setAttachedFiles(prev => [...prev, ...files])
  }, [])

  const handleFileAnalyzed = useCallback((file: File, analysis: FileAnalysisResult) => {
    if (analysis.success) {
      setFileAnalysisContext(analysis)
      toast({
        title: "Arquivo analisado",
        description: `${file.name} foi processado. A análise será enviada junto com sua próxima mensagem.`,
      })
    } else {
      toast({
        title: "Erro na análise",
        description: analysis.error || `Não foi possível analisar ${file.name}`,
        variant: "destructive",
      })
    }
  }, [toast])

  // Audio Record Button handlers
  const handleAudioTranscription = useCallback((text: string) => {
    setInput(prev => prev ? `${prev} ${text}` : text)
    toast({
      title: "Áudio transcrito",
      description: "O texto foi adicionado ao campo de mensagem.",
    })
    inputRef.current?.focus()
  }, [toast])

  const handleAudioRecordingStart = useCallback(() => {
    toast({
      title: "Gravando...",
      description: "Fale sua mensagem. Clique novamente para parar.",
    })
  }, [toast])

  const handleAudioRecordingEnd = useCallback(() => {
    toast({
      title: "Processando áudio",
      description: "Aguarde enquanto transcrevemos sua mensagem.",
    })
  }, [toast])

  // ============================================
  // VOICE RECORDING HANDLERS
  // ============================================
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }
      
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" })
        setAudioBlob(audioBlob)
        
        stream.getTracks().forEach(track => track.stop())
      }
      
      mediaRecorder.start()
      setIsRecording(true)
      setRecordingTime(0)
      
      recordingTimerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)
      
    } catch (error) {
      const errorMessage: Message = {
        id: Date.now(),
        sender: "lia",
        content: "Não consegui acessar o microfone. Por favor, verifique as permissões do navegador e tente novamente.",
        timestamp: new Date().toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit"
        }),
        type: "text"
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }, [recordingTime])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current)
        recordingTimerRef.current = null
      }
    }
  }, [isRecording])

  const handleRecordingToggle = useCallback(() => {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }, [isRecording, startRecording, stopRecording])

  // Cleanup recording timer on unmount
  useEffect(() => {
    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current)
      }
    }
  }, [])

  // Activate Smart Search Mode when LIA suggests insufficient data
  const activateSmartSearch = useCallback(() => {
    setIsSmartSearchMode(true)
    setSmartSearchQuery(input)
    setInput("")
    if (searchFlow.flowState === "idle") {
      searchFlow.startProfileCollection()
    }
  }, [input, searchFlow])

  // Detectar se há novas mensagens fora da área visível
  const checkNewMessageIndicator = useCallback(() => {
    if (!messagesContainerRef.current) return

    const container = messagesContainerRef.current
    const isAtBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 100

    setNewMessageIndicator(!isAtBottom && messages.length > 0)
  }, [messages.length])

  // Navegação por teclado
  useEffect(() => {
    const handleKeyboard = (e: KeyboardEvent) => {
      // Busca com Ctrl+F
      if (e.ctrlKey && e.key === 'f') {
        e.preventDefault()
        setShowSearch(true)
      }

      // Navegação com Ctrl+↑/↓
      if (e.ctrlKey && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) {
        e.preventDefault()
        const direction = e.key === 'ArrowUp' ? -1 : 1
        const newIndex = Math.max(0, Math.min(messages.length - 1, currentMessageIndex + direction))
        setCurrentMessageIndex(newIndex)

        // Scroll para a mensagem
        const messageElements = document.querySelectorAll('[data-message-id]')
        if (messageElements[newIndex]) {
          messageElements[newIndex].scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
      }

      // Fechar busca com Escape
      if (e.key === 'Escape') {
        setShowSearch(false)
        setSearchTerm("")
      }

      // Focar input com Ctrl+/
      if (e.ctrlKey && e.key === '/') {
        e.preventDefault()
        inputRef.current?.focus()
      }

      // Abrir Command Palette com Cmd+K ou Ctrl+K
      // Only if no input/textarea is focused (respect active element)
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        const activeElement = document.activeElement
        const isInputFocused = activeElement?.tagName === 'INPUT' || activeElement?.tagName === 'TEXTAREA'
        
        // Only open palette if not in input/textarea or if in our chat input
        if (!isInputFocused || activeElement === inputRef.current) {
          e.preventDefault()
          setIsCommandPaletteOpen(true)
        }
      }
    }

    window.addEventListener('keydown', handleKeyboard)
    return () => window.removeEventListener('keydown', handleKeyboard)
  }, [currentMessageIndex, messages.length])

  useEffect(() => {
    scrollToBottom()
    checkNewMessageIndicator()
  }, [messages, checkNewMessageIndicator])

  // Highlight de texto na busca
  const formatMessageContent = useCallback((text: string) => {
    // 1. Converter **texto** para <strong>texto</strong>
    let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    
    // 2. Converter quebras de linha duplas para parágrafos
    formatted = formatted.replace(/\n\n/g, '<br/><br/>')
    
    // 3. Converter quebras de linha simples para <br/>
    formatted = formatted.replace(/\n/g, '<br/>')
    
    // 4. Adicionar espaçamento extra após bullet points
    formatted = formatted.replace(/•\s/g, '• ')
    
    return formatted
  }, [])

  const highlightSearchTerm = useCallback((text: string, term: string) => {
    // Primeiro formata o conteúdo
    let formatted = formatMessageContent(text)
    
    // Depois aplica o highlight se houver termo de busca
    if (!term) return formatted
    const regex = new RegExp(`(${term})`, 'gi')
    return formatted.replace(regex, '<mark class="bg-status-warning/10 dark:bg-status-warning/10">$1</mark>')
  }, [formatMessageContent])

  const renderChatCard = useCallback((message: Message) => {
    if (!message.chatCardType || !message.chatCardData) return null
    
    const { chatCardType, chatCardData } = message
    
    const handleCardAction = (action: string) => {
      handleChatCardAction(chatCardType, action, chatCardData)
    }

    switch (chatCardType) {
      case "candidate_summary":
        return (
          <CandidateSummaryCard
            data={chatCardData as {
              id: string
              name: string
              title: string
              location: string
              experience_years: number
              skills: string[]
              match_score: number
              email?: string
              phone?: string
              linkedin_url?: string
              salary_expectation?: string
            }}
            onScheduleInterview={() => handleCardAction("schedule")}
            onViewDetails={() => handleCardAction("view_details")}
            onAddToShortlist={() => handleCardAction("add_shortlist")}
          />
        )
      case "wsi_score":
        return (
          <WSIScoreCard
            data={chatCardData as {
              candidate_name: string
              overall_score: number
              work_style: { score: number; details: string }
              independence: { score: number; details: string }
              consistency: { score: number; details: string }
            }}
            onViewDetails={() => handleCardAction("view_details")}
          />
        )
      case "compensation_summary":
        return (
          <CompensationSummaryCard
            data={chatCardData as {
              salary_range: { min: number; max: number; target: number }
              currency: string
              benefits: string[]
              equity?: string
              bonus?: string
            }}
            onEdit={() => handleCardAction("edit")}
            onApprove={() => handleCardAction("approve")}
          />
        )
      case "interview_confirmation":
        return (
          <InterviewConfirmationCard
            data={chatCardData as {
              candidate_name: string
              interview_date: string
              interview_time: string
              interview_type: "presencial" | "remoto" | "hibrido"
              interviewers: string[]
              location?: string
              meeting_link?: string
            }}
            onReschedule={() => handleCardAction("reschedule")}
            onCancel={() => handleCardAction("cancel")}
            onConfirm={() => handleCardAction("confirm")}
          />
        )
      case "progress_tracker":
        return (
          <ProgressTrackerCard
            data={chatCardData as {
              process_name: string
              current_stage: string
              stages: Array<{
                name: string
                status: "completed" | "current" | "pending"
                date?: string
              }>
              candidates_count?: number
            }}
            onViewDetails={() => handleCardAction("view_details")}
          />
        )
      case "job_summary":
        return (
          <JobSummaryCard
            data={chatCardData as {
              title: string
              department: string
              location: string
              salary_range: { min: number; max: number }
              requirements: string[]
              status: "draft" | "active" | "paused" | "closed"
            }}
            onEdit={() => handleCardAction("edit")}
            onPublish={() => handleCardAction("publish")}
            onViewCandidates={() => handleCardAction("view_candidates")}
          />
        )
      case "company_benefits":
        return (
          <CompanyBenefitsSummaryCard
            data={chatCardData as {
              benefits: Array<{
                id?: string
                name: string
                description?: string
                category: string
                value_type?: "monetary" | "percentage" | "informative"
                value?: number
                percentage_value?: number
                is_highlighted?: boolean
              }>
              total_count?: number
              highlighted_count?: number
            }}
            onViewAll={() => handleCardAction("view_all")}
            onAction={handleCardAction}
          />
        )
      default:
        return null
    }
  }, [handleChatCardAction])

  const handleSendMessage = useCallback(async (customContent?: string) => {
    const userMessageContent = customContent || input
    if (!userMessageContent.trim() || isLoading) return
    
    const normalizedContent = userMessageContent.toLowerCase().trim()
    
    // Intercept "Buscar candidatos" to activate profile collection flow
    const isSearchCandidatesRequest = 
      normalizedContent.includes('buscar candidatos') ||
      normalizedContent.includes('buscar candidato') ||
      normalizedContent.includes('encontrar candidatos') ||
      normalizedContent.includes('procurar candidatos') ||
      normalizedContent === 'buscar candidatos'
    
    if (isSearchCandidatesRequest && searchFlow.flowState === "idle") {
      const newMessage: Message = {
        id: messages.length + 1,
        sender: "user",
        content: userMessageContent,
        timestamp: new Date().toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit"
        }),
        type: "text"
      }
      setMessages(prev => [...prev, newMessage])
      setInput("")
      
      // LIA asks for profile details instead of searching immediately
      const liaResponse: Message = {
        id: messages.length + 2,
        sender: "lia",
        content: `Vou te ajudar a encontrar os melhores candidatos! Para uma busca mais precisa, me conte sobre o perfil que você procura.

**O que você pode descrever:**
- **Cargo**: Ex: "Desenvolvedor Python Sênior", "Analista de Marketing"
- **Skills principais**: Ex: "Python, AWS, Docker" ou "SEO, Google Ads"
- **Localização**: Ex: "São Paulo", "remoto", "híbrido RJ"
- **Senioridade**: Ex: "júnior", "pleno", "sênior"

Digite abaixo o perfil ideal e vou buscar simultaneamente no nosso banco proprietário e no banco global com 800M+ perfis.`,
        timestamp: new Date().toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit"
        }),
        type: "text"
      }
      setMessages(prev => [...prev, liaResponse])
      
      // Activate Smart Search mode for profile collection
      searchFlow.startProfileCollection()
      setIsSmartSearchMode(true)
      setSmartSearchQuery("")
      setChatTitle('Busca de Candidatos')
      return
    }
    
    const newMessage: Message = {
      id: messages.length + 1,
      sender: "user",
      content: userMessageContent,
      timestamp: new Date().toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit"
      }),
      type: "text"
    }

    setMessages(prev => [...prev, newMessage])
    setInput("")
    setIsLoading(true)
    
    const currentAttachments = [...attachedFiles]
    const currentAudio = audioBlob
    const currentFileAnalysis = fileAnalysisContext
    
    setAttachedFiles([])
    setAudioBlob(null)
    setFileAnalysisContext(null)

    const thinkingMessage: Message = {
      id: messages.length + 2,
      sender: "lia",
      content: "",
      timestamp: new Date().toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit"
      }),
      type: "thinking",
      thinkingMessage: currentAttachments.length > 0 
        ? "Processando arquivos e sua solicitação..." 
        : currentAudio 
          ? "Transcrevendo áudio e processando..." 
          : "Processando sua solicitação com IA..."
    }

    setMessages(prev => [...prev, thinkingMessage])

    try {
      const messageContent = currentFileAnalysis
        ? `${userMessageContent}\n\n[Contexto do arquivo analisado: ${currentFileAnalysis.filename}]\n${currentFileAnalysis.summary || ''}\n${currentFileAnalysis.extractedText ? `Texto extraído: ${currentFileAnalysis.extractedText.substring(0, 500)}...` : ''}`
        : userMessageContent

      // Use streaming for text-only messages (no attachments / audio)
      const useStreaming = currentAttachments.length === 0 && !currentAudio

      if (useStreaming && wsIsConnected) {
        // WS path — tokens arrive via LangGraph StreamingCallback (USE_LANGGRAPH_NATIVE=True)
        const streamingMessage: Message = {
          id: messages.length + 3,
          sender: "lia",
          content: "",
          timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
          type: "text",
        }
        setMessages(prev => {
          const newMsgs = [...prev]
          newMsgs[newMsgs.length - 1] = streamingMessage
          return newMsgs
        })
        wsClearTokens()
        wsStreamingModeRef.current = true
        wsSendMessage(messageContent)
        // isLoading reset by useEffect watching wsIsStreaming; finally block checks wsStreamingModeRef

      } else if (useStreaming) {
        // SSE path — fallback when WS is not connected (direct Anthropic streaming)
        const streamingMessage: Message = {
          id: messages.length + 3,
          sender: "lia",
          content: "",
          timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
          type: "text",
        }
        setMessages(prev => {
          const newMsgs = [...prev]
          newMsgs[newMsgs.length - 1] = streamingMessage
          return newMsgs
        })

        const streamResp = await fetch('/api/lia/chat/stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content: messageContent }),
        })

        if (!streamResp.ok || !streamResp.body) {
          throw new Error(`Stream request failed: ${streamResp.status}`)
        }

        const reader = streamResp.body.getReader()
        const decoder = new TextDecoder()
        let accumulated = ""

        outer: while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const rawChunk = decoder.decode(value, { stream: true })
          for (const line of rawChunk.split('\n')) {
            if (!line.startsWith('data: ')) continue
            const payload = line.slice(6).trim()
            if (payload === '[DONE]') break outer

            try {
              const parsed = JSON.parse(payload)
              if (parsed.token) {
                accumulated += parsed.token
                const snapshot = accumulated
                setMessages(prev => {
                  const updated = [...prev]
                  const last = updated[updated.length - 1]
                  if (last?.sender === "lia") {
                    updated[updated.length - 1] = { ...last, content: snapshot }
                  }
                  return updated
                })
              } else if (parsed.error) {
                throw new Error(parsed.error)
              }
            } catch (_) {
              // ignore partial JSON chunks
            }
          }
        }

      } else {
        // Fallback: regular (blocking) request for attachments / audio
        const response = await liaApi.sendMessage({
          content: messageContent,
          user_id: "demo-user",
          attachments: currentAttachments.length > 0 ? currentAttachments : undefined,
          audio: currentAudio || undefined
        })

        const liaResponse: Message = {
          id: messages.length + 3,
          sender: "lia",
          content: response.message.content,
          timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
          type: "text",
          data: {
            ...response.message.message_metadata,
            workflow_data: response.conversation?.workflow_data || response.message.message_metadata?.workflow_data
          }
        }

        const workflowData = response.conversation?.workflow_data || response.message.message_metadata?.workflow_data

        if (workflowData?.search_results) {
          const searchResults = workflowData.search_results
          const totalCount = (searchResults.local_candidates?.length || 0) + (searchResults.global_candidates?.length || 0)
          const panelData = {
            type: "candidate-suggestions" as const,
            title: `Candidatos Encontrados (${totalCount})`,
            data: {
              query: searchResults.query,
              source: searchResults.source,
              localCount: searchResults.local_count,
              totalCount,
              candidates: [...(searchResults.local_candidates || []), ...(searchResults.global_candidates || [])]
            }
          }
          liaResponse.contextData = panelData
          setContextData(panelData)
          setIsPanelOpen(true)
        } else if (response.conversation?.workflow_type === 'job_creation' && workflowData) {
          if (workflowData.completion_percentage !== undefined) {
            const jobState = workflowData
            const collectedFields = Object.keys(jobState.field_status || {}).filter(k => jobState.field_status[k] === 'collected')
            const pendingFields = Object.keys(jobState.field_status || {}).filter(k => jobState.field_status[k] === 'pending')
            const panelData = {
              type: "job-creation-progress" as const,
              title: "Progresso: Criação de Vaga",
              data: {
                completion_percentage: Math.round(jobState.completion_percentage || 0),
                collected_fields: collectedFields,
                pending_fields: pendingFields,
                next_panel: jobState.current_panel || 'Aguardando próxima etapa'
              }
            }
            liaResponse.contextData = panelData
            setContextData(panelData)
            setIsPanelOpen(true)
          } else if (workflowData.frames) {
            const frames = workflowData.frames
            let panelData: ContextPanelData | null = null
            if (frames.org_chart) panelData = { type: "org-chart", title: "Organograma da Posição", data: frames.org_chart }
            else if (frames.interview_flow) panelData = { type: "interview-flow", title: "Fluxo de Entrevistas", data: frames.interview_flow }
            else if (frames.timeline) panelData = { type: "timeline", title: "Cronograma de Recrutamento", data: frames.timeline }
            else if (frames.technical_matrix) panelData = { type: "technical-matrix", title: "Matriz Técnica - Requisitos da Vaga", data: frames.technical_matrix }
            if (panelData) {
              liaResponse.contextData = panelData
              setContextData(panelData)
              setIsPanelOpen(true)
            }
          }
        }

        setMessages(prev => {
          const newMessages = [...prev]
          newMessages[newMessages.length - 1] = liaResponse
          return newMessages
        })

        // Ciclo fechado: notificar outros componentes (ex: kanban) quando uma ação foi executada
        const actionResult = response.message.message_metadata?.action_result
        if (actionResult?.success) {
          window.dispatchEvent(
            new CustomEvent("lia:action-executed", {
              detail: { action_id: actionResult.action_id, data: actionResult.data }
            })
          )
        }
      }

    } catch (error) {

      const errorMessage: Message = {
        id: messages.length + 3,
        sender: "lia",
        content: "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.",
        timestamp: new Date().toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit"
        }),
        type: "text"
      }

      setMessages(prev => {
        const newMessages = [...prev]
        newMessages[newMessages.length - 1] = errorMessage
        return newMessages
      })
    } finally {
      // Skip resetting isLoading when WS streaming mode is active —
      // the useEffect watching wsIsStreaming will reset it when streaming ends.
      if (!wsStreamingModeRef.current) {
        setIsLoading(false)
      }
    }
  }, [input, isLoading, messages.length, wsIsConnected, wsSendMessage, wsClearTokens])

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleActionClick = (message: Message, action: Record<string, unknown>) => {
    if (message.contextData) {
      setContextData({
        type: message.contextData.type,
        title: message.contextData.title,
        data: message.contextData.data
      })
      setIsPanelOpen(true)
    }
  }

  // AI-First Action Handlers
  const handleScheduleInterview = useCallback(() => {
    // Safe validation before dereferencing candidate data
    if (
      contextData?.type === 'candidate-suggestions' &&
      contextData.data?.candidates &&
      Array.isArray(contextData.data.candidates) &&
      contextData.data.candidates.length > 0
    ) {
      const candidate = contextData.data.candidates[0]
      
      // Ensure candidate has required fields
      if (candidate?.name) {
        setSelectedCandidateForScheduling({
          name: candidate.name,
          email: candidate.contact?.email || candidate.email || '',
          id: candidate.id || candidate.candidateId,
          job_title: candidate.current_title || 'Candidato',
          job_vacancy_id: candidate.job_vacancy_id // Preserve job vacancy ID from context
        })
        setIsSchedulingModalOpen(true)
        return
      }
    }
    
    // Fallback: send prompt to LIA if no valid candidate data
    handleSendMessage("agendar entrevista")
  }, [contextData, handleSendMessage])

  const handleEvaluateFit = useCallback(() => {
    handleSendMessage("avaliar fit técnico do candidato")
  }, [handleSendMessage])

  const handleGenerateEmail = useCallback(() => {
    handleSendMessage("gerar email de follow-up")
  }, [handleSendMessage])

  const handleSendWhatsApp = useCallback(() => {
    handleSendMessage("enviar mensagem whatsapp")
  }, [handleSendMessage])

  const handleCompareProfiles = useCallback(() => {
    handleSendMessage("comparar perfis de candidatos")
  }, [handleSendMessage])

  const handleViewAnalytics = useCallback(() => {
    // router.push('/indicadores')
    window.location.href = '/indicadores'
  }, [])

  const handlePipelineAction = useCallback(async (candidateId: string, actionId: string, candidateName: string) => {
    try {
      const result = await liaApi.executePipelineAction(candidateId, actionId)
      
      if (result.success) {
        const liaMessage: Message = {
          id: messages.length + 1,
          sender: "lia",
          content: result.message,
          timestamp: new Date().toLocaleTimeString("pt-BR", {
            hour: "2-digit",
            minute: "2-digit"
          }),
          type: "text"
        }
        setMessages(prev => [...prev, liaMessage])
        
        if (result.open_modal === "interview_scheduling") {
          setSelectedCandidateForScheduling({
            name: candidateName,
            id: candidateId,
            email: "",
            job_title: ""
          })
          setIsSchedulingModalOpen(true)
        }
        
        if (result.navigate) {
          window.location.href = result.navigate
        }
        
        if (contextData?.type === "pipeline-report") {
          const updatedData = await liaApi.getStaleCandidates()
          setContextData({
            type: "pipeline-report",
            title: "Pipeline de Candidatos",
            data: updatedData
          })
        }
      }
    } catch (error) {
      const errorMessage: Message = {
        id: messages.length + 1,
        sender: "lia",
        content: "Desculpe, ocorreu um erro ao executar a ação. Tente novamente.",
        timestamp: new Date().toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit"
        }),
        type: "text"
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }, [messages.length, contextData])

  // Candidate Search Handlers (Pearch Integration)
  const handleSelectCandidate = useCallback((candidate: CandidateResult) => {
    setSelectedCandidateForDetail(candidate)
    setIsCandidateDetailOpen(true)
  }, [])

  const handleAddCandidatesToJob = useCallback((candidateIds: string[]) => {
    const count = candidateIds.length
    handleSendMessage(`Adicionar ${count} candidato(s) selecionado(s) à vaga atual`)
  }, [handleSendMessage])

  const handleCompareCandidates = useCallback((candidateIds: string[]) => {
    if (candidateIds.length >= 2) {
      handleSendMessage(`Comparar os ${candidateIds.length} candidatos selecionados`)
    }
  }, [handleSendMessage])

  const handleLoadMoreCandidates = useCallback((query: string, threadId?: string) => {
    setPendingPearchSearch({ query, threadId })
    setIsCreditDialogOpen(true)
  }, [])

  const handleConfirmPearchSearch = useCallback(() => {
    if (pendingPearchSearch) {
      handleSendMessage(`Buscar mais candidatos para "${pendingPearchSearch.query}" no banco global Pearch`)
      setIsCreditDialogOpen(false)
      setPendingPearchSearch(null)
    }
  }, [pendingPearchSearch, handleSendMessage])

  const handleAddCandidateToJob = useCallback((candidateId: string) => {
    handleSendMessage(`Adicionar candidato ${candidateId} à vaga atual`)
    setIsCandidateDetailOpen(false)
  }, [handleSendMessage])

  const handleSaveToBase = useCallback(async (candidateId: string) => {
    try {
      const result = await promoteCandidateToBase(candidateId)
      if (result.success) {
        if (selectedCandidateForDetail) {
          setSelectedCandidateForDetail({
            ...selectedCandidateForDetail,
            is_discovered: false,
            source: "local"
          })
        }
        if (contextData?.type === 'candidate-suggestions' && contextData.data?.candidates) {
          setContextData(prev => prev ? {
            ...prev,
            data: {
              ...prev.data,
              candidates: prev.data.candidates.map((c: Record<string, unknown>) => 
                c.id === candidateId 
                  ? { ...c, is_discovered: false, source: "local" }
                  : c
              )
            }
          } : null)
        }
        const liaMessage: Message = {
          id: Date.now(),
          sender: "lia",
          content: result.was_merged 
            ? `Candidato **${selectedCandidateForDetail?.name || 'selecionado'}** foi mesclado com perfil existente na sua base.`
            : `Candidato **${selectedCandidateForDetail?.name || 'selecionado'}** foi salvo na sua base local com sucesso!`,
          timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
          type: "text"
        }
        setMessages(prev => [...prev, liaMessage])
      }
    } catch (error) {
      const errorMessage: Message = {
        id: Date.now(),
        sender: "lia",
        content: "Desculpe, ocorreu um erro ao salvar o candidato na base. Por favor, tente novamente.",
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        type: "text"
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }, [selectedCandidateForDetail, contextData])

  // Command Palette Items
  const commandItems: CommandItem[] = [
    ...defaultCommands({
      onSchedule: handleScheduleInterview,
      onEvaluate: handleEvaluateFit,
      onEmail: handleGenerateEmail,
      onWhatsApp: handleSendWhatsApp,
      onCompare: handleCompareProfiles,
      onAnalytics: handleViewAnalytics
    }),
    // Prompt Suggestions integradas no Cmd+K
    {
      id: 'create-job',
      label: 'Criar Nova Vaga',
      description: 'Configure requisitos do sistema com descrição detalhada',
      category: 'Tarefas LIA',
      icon: Plus,
      shortcut: [],
      onExecute: () => handleSendMessage("Criar uma nova vaga")
    },
    {
      id: 'approve-job',
      label: 'Solicitar Aprovação de Vaga',
      description: 'Encaminhe documentação para aprovação gerencial',
      category: 'Tarefas LIA',
      icon: FileText,
      shortcut: [],
      onExecute: () => handleSendMessage("Solicite aprovação de nova vaga")
    },
    {
      id: 'share-candidates',
      label: 'Compartilhar Candidatos com Gestor',
      description: 'Crie relatório com perfis aprovados e recomendações',
      category: 'Tarefas LIA',
      icon: UserCheck,
      shortcut: [],
      onExecute: () => handleSendMessage("Compartilhe candidatos com gestor")
    },
    {
      id: 'feedback-interview',
      label: 'Solicitar Feedback de Entrevista',
      description: 'Colete avaliação detalhada pós-entrevista do gestor',
      category: 'Tarefas LIA',
      icon: MessageSquare,
      shortcut: [],
      onExecute: () => handleSendMessage("Solicite feedback de entrevista")
    },
    {
      id: 'candidate-info',
      label: 'Consultar Informações de Candidato',
      description: 'Obtenha histórico específico e histórico completo',
      category: 'Tarefas LIA',
      icon: Search,
      shortcut: [],
      onExecute: () => handleSendMessage("Consulte informações sobre candidato")
    },
    {
      id: 'add-candidate',
      label: 'Adicionar Novo Candidato',
      description: 'Cadastre perfil com talentos',
      category: 'Tarefas LIA',
      icon: UserCheck,
      shortcut: [],
      onExecute: () => handleSendMessage("Adicione novo candidato")
    },
    {
      id: 'reschedule-interview',
      label: 'Reagendar Entrevista',
      description: 'Cancele horário e notifique automaticamente participantes',
      category: 'Tarefas LIA',
      icon: Calendar,
      shortcut: [],
      onExecute: () => handleSendMessage("Reagende uma entrevista")
    },
    {
      id: 'update-status',
      label: 'Atualizar Status do Candidato',
      description: 'Modifique situação no processo e envie notificações',
      category: 'Tarefas LIA',
      icon: RefreshCcw,
      shortcut: [],
      onExecute: () => handleSendMessage("Atualize status do candidato")
    }
  ]

  // Quick Actions (contextual based on current context)
  const getQuickActions = (): QuickAction[] => {
    const baseActions: QuickAction[] = defaultCandidateActions.map(action => ({
      ...action,
      onClick: () => {
        switch (action.id) {
          case 'schedule':
            handleScheduleInterview()
            break
          case 'evaluate':
            handleEvaluateFit()
            break
          case 'email':
            handleGenerateEmail()
            break
          case 'whatsapp':
            handleSendWhatsApp()
            break
          case 'compare':
            handleCompareProfiles()
            break
          case 'analytics':
            handleViewAnalytics()
            break
        }
      }
    }))

    // Show only first 4 most relevant actions based on context
    if (contextData?.type === 'candidate-suggestions') {
      return baseActions.filter(a => ['schedule', 'evaluate', 'email', 'whatsapp'].includes(a.id))
    }
    
    return baseActions.slice(0, 4)
  }

  // Dynamic placeholder based on context
  const getPlaceholderText = (): string => {
    if (contextData?.type === 'candidate-suggestions') {
      return 'Ex: "agendar amanhã às 14h comigo" ou "avaliar fit técnico"'
    }
    if (contextData && contextData.data?.candidates?.length > 0) {
      const candidate = contextData.data.candidates[0]
      return `Pergunte sobre ${candidate.name}... Ex: "agendar entrevista com ${candidate.name.split(' ')[0]}"`
    }
    return 'Peça a LIA...'
  }


  return {
    // Search params
    conversationType,

    // Core state
    messages, setMessages,
    input, setInput,
    isLoading,
    contextData, setContextData,
    isPanelOpen, setIsPanelOpen,
    searchTerm, setSearchTerm,
    showSearch, setShowSearch,
    newMessageIndicator,
    currentMessageIndex,
    availableCredits,

    // Scheduling state
    isSchedulingModalOpen, setIsSchedulingModalOpen,
    isCommandPaletteOpen, setIsCommandPaletteOpen,
    selectedCandidateForScheduling,

    // Candidate search state
    isCandidateDetailOpen, setIsCandidateDetailOpen,
    selectedCandidateForDetail, setSelectedCandidateForDetail,
    isCreditDialogOpen, setIsCreditDialogOpen,
    pendingPearchSearch,

    // Smart search state
    isSmartSearchMode,
    smartSearchQuery, setSmartSearchQuery,
    hasSearchResults,
    searchPreviewData,
    searchFlow,

    // Global settings
    globalSearchSettings, globalSettingsLoading,

    // File state
    attachedFiles,
    fileValidationError, setFileValidationError,
    fileInputRef,
    MAX_FILE_SIZE_MB,

    // Voice state
    isRecording,
    recordingTime,
    audioBlob, setAudioBlob,

    // File analysis
    fileAnalysisContext, setFileAnalysisContext,

    // Refs
    messagesEndRef,
    messagesContainerRef,
    inputRef,

    // Layout
    isEmptyChat,
    chatContainerClass, inputContainerClass, messagesContainerClass,

    // Chat metadata
    chatId,
    chatTitle,
    activeTab, setActiveTab,

    // Pending action
    activePendingAction,

    // Empty field notifications
    emptyFieldNotifications,
    currentSuggestion,
    isLoadingSuggestion,

    // Filters
    isFiltersModalOpen, setIsFiltersModalOpen,
    activeSearchFilters,

    // Handlers
    handleSendMessage,
    handleKeyPress,
    handleActionClick,
    handleSmartSearchSubmit,
    handleSmartSearchCancel,
    handleApplyFilters,
    handleFileButtonClick,
    handleFileChange,
    handleRemoveFile,
    handleFilesSelected,
    handleFileAnalyzed,
    handleAudioTranscription,
    handleAudioRecordingStart,
    handleAudioRecordingEnd,
    handleRecordingToggle,
    startRecording,
    stopRecording,
    handleEmptyFieldAction,
    handleSuggestionAccepted,
    handleSuggestionRejected,
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
    scrollToBottom,
    checkNewMessageIndicator,
    getRelativeTime,
    getQuickSuggestions,
    getActiveFiltersCount,
    highlightSearchTerm,
    formatMessageContent,
    renderChatCard,
    commandItems,
    getQuickActions,
    getPlaceholderText,

    // UI Actions
    uiActions,
  }
}
