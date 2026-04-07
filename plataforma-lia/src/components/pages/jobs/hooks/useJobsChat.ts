"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import { callOrchestratedJobsManagement } from "@/lib/api/kanban-assistant"
import { useLiaSuggestions, useJobInsights, useLiaExpandedPrompt } from "@/hooks/use-lia-suggestions"
import { useCompanyId } from "@/hooks/useCompanyId"
import type { Job } from "@/components/jobs"

// ---------------------------------------------------------------------------
// useJobsChat
// Responsável por: chat inline lateral (3 níveis: mini, geral, criação de vaga),
// mensagens LIA, processamento de comandos, sugestões contextuais,
// prompt expandido, controle de largura do painel LIA.
// ---------------------------------------------------------------------------

interface LiaInlineMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isTyping?: boolean
}

interface LiaOrchestratorMessage {
  id: string
  type: 'user' | 'response'
  content: string
  timestamp: number
  agentUsed?: string
  suggestedPrompts?: string[]
  action_executed?: boolean
  action_result?: Record<string, unknown>
  action_type?: string
  needs_confirmation?: boolean
  needs_params?: boolean
  pending_action_id?: string
}

interface UseJobsChatOptions {
  filteredJobs: Job[]
  allJobs: Job[]
  selectedJobsForBatch: Set<number>
  onAddRecentItem?: (item: { id: string; type: 'vaga' | 'chat' | 'candidato'; title: string; subtitle?: string; meta?: Record<string, string | undefined> }) => void
  onChatOpened?: () => void
  pendingChatOpen?: { mode: 'general' | 'job-creation' } | null
  setActiveFilter?: (filter: string) => void
  loadBackendJobs: () => Promise<void>
}

interface UseJobsChatReturn {
  state: {
    showInlineChat: boolean
    chatMode: 'general' | 'job-creation' | null
    inlineChatInitialMessage: string | undefined
    isChatFullscreen: boolean
    isTableCollapsed: boolean
    liaInlineMessages: LiaInlineMessage[]
    liaInlineLoading: boolean
    liaInlineMessagesEndRef: React.RefObject<HTMLDivElement | null>
    liaInputRef: React.RefObject<HTMLInputElement | null>
    showExpandedLIA: boolean
    liaPromptValue: string
    userCollapsedLIA: boolean
    liaWidth: number
    isResizingLIA: boolean
    showLiaSuggestions: boolean
    liaHighlight: boolean
    liaMessages: LiaOrchestratorMessage[]
    isLiaProcessing: boolean
    jobsConversationId: string | undefined
    orchestratorSuggestions: string[]
    dynamicSuggestions: ReturnType<typeof useLiaSuggestions>['suggestions']
    suggestionsLoading: boolean
    dynamicInsights: ReturnType<typeof useJobInsights>['insights']
    insightsLoading: boolean
    liaResponse: ReturnType<typeof useLiaExpandedPrompt>['response']
    liaPromptLoading: boolean
    followUpSuggestions: ReturnType<typeof useLiaExpandedPrompt>['followUpSuggestions']
  }
  actions: {
    setShowInlineChat: (v: boolean) => void
    setChatMode: (v: 'general' | 'job-creation' | null) => void
    setInlineChatInitialMessage: (v: string | undefined) => void
    setIsChatFullscreen: (v: boolean) => void
    setIsTableCollapsed: (v: boolean) => void
    setLiaInlineMessages: React.Dispatch<React.SetStateAction<LiaInlineMessage[]>>
    setShowExpandedLIA: (v: boolean) => void
    setLiaPromptValue: (v: string) => void
    setUserCollapsedLIA: (v: boolean) => void
    setLiaWidth: (v: number) => void
    setIsResizingLIA: (v: boolean) => void
    setShowLiaSuggestions: (v: boolean) => void
    setLiaMessages: React.Dispatch<React.SetStateAction<LiaOrchestratorMessage[]>>
    setJobsConversationId: (v: string | undefined) => void
    setOrchestratorSuggestions: (v: string[]) => void
    sendLiaInlineMessage: (content: string) => Promise<void>
    openGeneralChat: (initialMessage?: string) => void
    openJobCreationChat: (initialMessage?: string) => void
    closeChat: () => void
    returnToGeneralChat: () => void
    returnToLateralPrompt: (messages?: Array<{ id: string; role: 'user' | 'assistant'; content: string; timestamp: Date }>) => void
    toggleTableExpansion: () => void
    handleAICommand: (command: string, action?: string) => Promise<void>
    getContextualSuggestions: () => string[]
    refreshSuggestions: ReturnType<typeof useLiaSuggestions>['refresh']
    generateInsights: ReturnType<typeof useJobInsights>['generateInsights']
    sendLiaPrompt: ReturnType<typeof useLiaExpandedPrompt>['sendPrompt']
  }
}

export function useJobsChat({
  filteredJobs,
  allJobs,
  selectedJobsForBatch,
  onAddRecentItem,
  onChatOpened,
  pendingChatOpen,
  setActiveFilter,
  loadBackendJobs,
}: UseJobsChatOptions): UseJobsChatReturn {
  const { companyId: resolvedCompanyId } = useCompanyId()
  const [showInlineChat, setShowInlineChat] = useState(false)
  const [chatMode, setChatMode] = useState<'general' | 'job-creation' | null>(null)
  const [inlineChatInitialMessage, setInlineChatInitialMessage] = useState<string | undefined>()
  const [isChatFullscreen, setIsChatFullscreen] = useState(false)
  const [isTableCollapsed, setIsTableCollapsed] = useState(false)

  const [liaInlineMessages, setLiaInlineMessages] = useState<LiaInlineMessage[]>([])
  const [liaInlineLoading, setLiaInlineLoading] = useState(false)
  const liaInlineMessagesEndRef = useRef<HTMLDivElement>(null)
  const liaInputRef = useRef<HTMLInputElement>(null)
  const liaInlineChatIdRef = useRef<string>(`chat-inline-${Date.now()}`)

  const [showExpandedLIA, setShowExpandedLIA] = useState(false)
  const [liaPromptValue, setLiaPromptValue] = useState("")
  const [userCollapsedLIA, setUserCollapsedLIA] = useState(false)
  const [liaWidth, setLiaWidth] = useState(400)
  const [isResizingLIA, setIsResizingLIA] = useState(false)
  const [showLiaSuggestions, setShowLiaSuggestions] = useState(false)
  const [liaHighlight, setLiaHighlight] = useState(false)

  const [liaMessages, setLiaMessages] = useState<LiaOrchestratorMessage[]>([])
  const [isLiaProcessing, setIsLiaProcessing] = useState(false)
  const [jobsConversationId, setJobsConversationId] = useState<string | undefined>(undefined)
  const [orchestratorSuggestions, setOrchestratorSuggestions] = useState<string[]>([])

  const { suggestions: dynamicSuggestions, loading: suggestionsLoading, refresh: refreshSuggestions } = useLiaSuggestions("default", 6)
  const { insights: dynamicInsights, generateInsights, loading: insightsLoading } = useJobInsights()
  const { sendPrompt: sendLiaPrompt, response: liaResponse, loading: liaPromptLoading, followUpSuggestions } = useLiaExpandedPrompt()

  // Handle pendingChatOpen prop
  useEffect(() => {
    if (pendingChatOpen) {
      if (pendingChatOpen.mode === 'job-creation') {
        setShowInlineChat(true)
        setChatMode('job-creation')
        setIsTableCollapsed(true)
      } else {
        setShowInlineChat(true)
        setChatMode('general')
        setIsTableCollapsed(true)
      }
      onChatOpened?.()
    }
  }, [pendingChatOpen, onChatOpened])

  // Auto-expand LIA sidebar on selection
  useEffect(() => {
    if (selectedJobsForBatch.size > 0 && !userCollapsedLIA) {
      setShowExpandedLIA(true)
    } else if (selectedJobsForBatch.size === 0) {
      setShowExpandedLIA(false)
      setUserCollapsedLIA(false)
    }
  }, [selectedJobsForBatch.size, userCollapsedLIA])

  // Listen for preview tab navigation event
  useEffect(() => {
    const handleSetPreviewTab = (event: CustomEvent) => {
      // Forward to parent via event if needed — the preview hook handles its own tab
    }
    window.addEventListener('setJobPreviewTab', handleSetPreviewTab as EventListener)
    return () => window.removeEventListener('setJobPreviewTab', handleSetPreviewTab as EventListener)
  }, [])

  // Scroll inline messages to bottom
  useEffect(() => {
    liaInlineMessagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [liaInlineMessages])

  // -------------------------------------------------------------------------
  // Chat mode helpers
  // -------------------------------------------------------------------------
  const isJobCreationIntent = (message: string): boolean => {
    const lower = message.toLowerCase()
    return [
      'criar vaga', 'nova vaga', 'abrir vaga', 'cadastrar vaga', 'registrar vaga',
      'quero criar', 'preciso de uma vaga', 'preciso abrir', 'montar vaga',
      'configurar vaga', 'iniciar processo seletivo', 'novo processo seletivo',
    ].some(p => lower.includes(p))
  }

  const openGeneralChat = useCallback((initialMessage?: string) => {
    setShowInlineChat(true)
    setChatMode('general')
    setInlineChatInitialMessage(initialMessage)
    setIsTableCollapsed(true)
    onAddRecentItem?.({
      id: liaInlineChatIdRef.current,
      type: 'chat',
      title: initialMessage
        ? `Chat: ${initialMessage.slice(0, 40)}${initialMessage.length > 40 ? '...' : ''}`
        : 'Chat com LIA',
      meta: { conversationId: liaInlineChatIdRef.current },
    })
  }, [onAddRecentItem])

  const openJobCreationChat = useCallback((initialMessage?: string) => {
    const wizardId = `chat-wizard-${Date.now()}`
    setShowInlineChat(true)
    setChatMode('job-creation')
    setInlineChatInitialMessage(initialMessage)
    setIsTableCollapsed(true)
    onAddRecentItem?.({
      id: wizardId,
      type: 'chat',
      title: initialMessage
        ? `Criação: ${initialMessage.slice(0, 35)}${initialMessage.length > 35 ? '...' : ''}`
        : 'Criação de Vaga',
      meta: { conversationId: wizardId },
    })
  }, [onAddRecentItem])

  const closeChat = useCallback(() => {
    setShowInlineChat(false)
    setChatMode(null)
    setInlineChatInitialMessage(undefined)
    setIsTableCollapsed(false)
    liaInlineChatIdRef.current = `chat-inline-${Date.now()}`
  }, [])

  const returnToGeneralChat = useCallback(() => {
    setChatMode('general')
  }, [])

  const returnToLateralPrompt = useCallback((messages?: Array<{ id: string; role: 'user' | 'assistant'; content: string; timestamp: Date }>) => {
    if (messages && messages.length > 0) {
      setLiaInlineMessages(messages.map(m => ({
        id: m.id, role: m.role, content: m.content, timestamp: m.timestamp,
      })))
    }
    setShowInlineChat(false)
    setChatMode(null)
    setInlineChatInitialMessage(undefined)
    setIsTableCollapsed(false)
    setShowExpandedLIA(true)
  }, [])

  const toggleTableExpansion = useCallback(() => {
    setIsTableCollapsed(prev => !prev)
  }, [])

  // -------------------------------------------------------------------------
  // sendLiaInlineMessage
  // -------------------------------------------------------------------------
  const sendLiaInlineMessage = useCallback(async (content: string) => {
    if (isJobCreationIntent(content)) {
      openJobCreationChat(content)
      return
    }

    const userMessage: LiaInlineMessage = {
      id: `user-${Date.now()}`, role: 'user', content, timestamp: new Date(),
    }
    setLiaInlineMessages(prev => [...prev, userMessage])
    setLiaInlineLoading(true)

    onAddRecentItem?.({
      id: liaInlineChatIdRef.current,
      type: 'chat',
      title: `Chat: ${content.slice(0, 40)}${content.length > 40 ? '...' : ''}`,
      meta: { conversationId: liaInlineChatIdRef.current },
    })

    try {
      const selectedJobIds = Array.from(selectedJobsForBatch).map(String)
      const response = await fetch('/api/backend-proxy/lia/expanded-prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content,
          context_type: 'jobs',
          context_ids: selectedJobIds.length > 0 ? selectedJobIds : undefined,
        }),
      })

      if (!response.ok) throw new Error('Falha na resposta')

      const data = await response.json()
      setLiaInlineMessages(prev => [...prev, {
        id: `lia-${Date.now()}`,
        role: 'assistant',
        content: data.response || 'Desculpe, não consegui processar sua mensagem.',
        timestamp: new Date(),
      }])
    } catch {
      setLiaInlineMessages(prev => [...prev, {
        id: `lia-${Date.now()}`,
        role: 'assistant',
        content: 'Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.',
        timestamp: new Date(),
      }])
    } finally {
      setLiaInlineLoading(false)
    }
  }, [openJobCreationChat, selectedJobsForBatch, onAddRecentItem])

  // -------------------------------------------------------------------------
  // handleAICommand (multi-agent orchestrator)
  // -------------------------------------------------------------------------
  const processLocalJobCommand = (command: string, jobs: Job[]): string => {
    const trimmed = command.trim().toLowerCase()
    const activeJobs = jobs.filter(j => j.status === 'Ativa')

    if (trimmed.includes('quantas vagas') || trimmed.includes('vagas abertas') || trimmed.includes('total de vagas')) {
      return `📊 **Resumo de Vagas**\n\n• **Total:** ${jobs.length}\n• **Ativas:** ${activeJobs.length}\n• **Paralisadas:** ${jobs.filter(j => j.status === 'Paralisada').length}\n• **Concluídas:** ${jobs.filter(j => j.status === 'Concluída').length}`
    }
    if (trimmed.includes('vagas urgentes') || trimmed.includes('urgente') || trimmed.includes('prioridade alta')) {
      const urgentes = jobs.filter(j => j.priority === 'alta' || j.urgencyLevel >= 4)
      if (urgentes.length === 0) return `✅ **Nenhuma vaga urgente no momento**`
      return `🚨 **${urgentes.length} Vaga(s) Urgente(s)**\n\n${urgentes.slice(0, 10).map((j, i) => `${i + 1}. **${j.title}** - ${j.department}`).join('\n')}`
    }
    if (trimmed.includes('sem candidatos') || trimmed.includes('funil vazio')) {
      const empty = jobs.filter(j => j.funnel.total === 0)
      if (empty.length === 0) return `✅ **Todas as vagas têm candidatos!**`
      return `⚠️ **${empty.length} Vaga(s) sem Candidatos**\n\n${empty.slice(0, 10).map((j, i) => `${i + 1}. **${j.title}**`).join('\n')}`
    }
    return `🤔 **Modo offline** — Para análises detalhadas tente novamente em instantes.\n\n💡 Comandos locais: "quantas vagas abertas", "vagas urgentes", "sem candidatos"`
  }

  const handleAICommand = useCallback(async (command: string, action?: string) => {
    setLiaMessages(prev => [...prev, {
      id: `user-${Date.now()}`, type: 'user', content: command, timestamp: Date.now(),
    }])
    setIsLiaProcessing(true)

    const jobs = filteredJobs
    const jobsContext = {
      total: jobs.length,
      active: jobs.filter(j => j.status === 'Ativa').length,
      paused: jobs.filter(j => j.status === 'Paralisada').length,
      completed: jobs.filter(j => j.status === 'Concluída').length,
      urgent: jobs.filter(j => j.priority === 'alta' || j.urgencyLevel >= 4).length,
      withoutCandidates: jobs.filter(j => j.funnel.total === 0).length,
      totalCandidates: jobs.reduce((sum, j) => sum + j.funnel.total, 0),
      selectedJobs: Array.from(selectedJobsForBatch).map(id => {
        const job = jobs.find(j => j.id === id)
        return job ? { id: job.id, title: job.title, department: job.department, status: job.status } : null
      }).filter(Boolean),
      topJobs: jobs.slice(0, 10).map(j => ({
        id: j.id, title: j.title, department: j.department, status: j.status,
        priority: j.priority, candidatesTotal: j.funnel.total,
        candidatesInterview: j.funnel.interview, hired: j.funnel.hired,
        daysOpen: Math.floor((Date.now() - new Date(j.openDate).getTime()) / (1000 * 60 * 60 * 24)),
      })),
    }

    try {
      const selectedJobsArray = Array.from(selectedJobsForBatch).map(id => {
        const job = jobs.find(j => j.id === id)
        return job ? { id: job.id, title: job.title, department: job.department, status: job.status } : null
      }).filter((j) => j !== null) as { id: number; title: string; department: string; status: string }[]

      const response = await callOrchestratedJobsManagement({
        message: command,
        jobs_context: jobsContext,
        selected_jobs: selectedJobsArray.length > 0 ? selectedJobsArray : undefined,
        top_jobs: jobsContext.topJobs,
        conversation_history: liaMessages.slice(-10).map(m => ({
          role: m.type === 'user' ? 'user' : 'assistant',
          content: m.content,
        })),
        action: action || 'general_query',
        conversation_id: jobsConversationId,
        company_id: resolvedCompanyId ?? '',
      })

      if (response.conversation_id) setJobsConversationId(response.conversation_id)

      setLiaMessages(prev => [...prev, {
        id: `response-${Date.now()}`,
        type: 'response',
        content: response.content,
        timestamp: Date.now(),
        agentUsed: response.agent_used,
        suggestedPrompts: response.suggested_prompts,
        action_executed: response.action_executed,
        action_result: response.action_result,
        action_type: response.action_type,
        needs_confirmation: response.needs_confirmation,
        needs_params: response.needs_params,
        pending_action_id: response.pending_action_id,
      }])

      if (response.action_executed && response.action_result) {
        setTimeout(() => loadBackendJobs(), 500)
      }
      if (response.suggested_prompts?.length) setOrchestratorSuggestions(response.suggested_prompts)
      if (response.ui_action === 'start_job_wizard') {
        openJobCreationChat(response.ui_action_params?.initial_message || '')
      } else if (response.ui_action === 'filter_jobs' && response.ui_action_params?.filter) {
        setActiveFilter?.(response.ui_action_params.filter)
      }
    } catch {
      const responseContent = processLocalJobCommand(command, jobs)
      setLiaMessages(prev => [...prev, {
        id: `response-${Date.now()}`, type: 'response', content: responseContent, timestamp: Date.now(),
      }])
    } finally {
      setIsLiaProcessing(false)
    }
  }, [filteredJobs, selectedJobsForBatch, liaMessages, jobsConversationId, loadBackendJobs, openJobCreationChat, setActiveFilter])

  // -------------------------------------------------------------------------
  // getContextualSuggestions
  // -------------------------------------------------------------------------
  const getContextualSuggestions = useCallback((): string[] => {
    const jobs = filteredJobs
    const suggestions: string[] = []
    const urgentCount = jobs.filter(j => j.priority === 'alta' || j.urgencyLevel >= 4).length
    if (urgentCount > 0) suggestions.push(`Analisar ${urgentCount} vaga${urgentCount > 1 ? 's' : ''} urgente${urgentCount > 1 ? 's' : ''}`)
    const emptyPipeline = jobs.filter(j => j.funnel.total === 0).length
    if (emptyPipeline > 0) suggestions.push(`${emptyPipeline} vaga${emptyPipeline > 1 ? 's' : ''} sem candidatos`)
    const now = Date.now()
    const upcomingDeadlines = jobs.filter(j => {
      if (!j.deadline) return false
      const days = Math.floor((new Date(j.deadline).getTime() - now) / (1000 * 60 * 60 * 24))
      return days >= 0 && days <= 7
    }).length
    if (upcomingDeadlines > 0) suggestions.push(`Vagas com deadline em 7 dias`)
    const pausedCount = jobs.filter(j => j.status === 'Paralisada').length
    if (pausedCount > 0) suggestions.push(`Revisar ${pausedCount} vaga${pausedCount > 1 ? 's' : ''} paralisada${pausedCount > 1 ? 's' : ''}`)
    if (suggestions.length === 0) { suggestions.push('Resumo das minhas vagas'); suggestions.push('Performance dos últimos 30 dias') }
    if (suggestions.length < 4 && !suggestions.some(s => s.includes('Performance'))) suggestions.push('Performance das vagas ativas')
    if (suggestions.length < 4) suggestions.push('Top 5 vagas com mais candidatos')
    return suggestions.slice(0, 4)
  }, [filteredJobs])

  return {
    state: {
      showInlineChat, chatMode, inlineChatInitialMessage, isChatFullscreen, isTableCollapsed,
      liaInlineMessages, liaInlineLoading, liaInlineMessagesEndRef, liaInputRef,
      showExpandedLIA, liaPromptValue, userCollapsedLIA, liaWidth, isResizingLIA,
      showLiaSuggestions, liaHighlight, liaMessages, isLiaProcessing, jobsConversationId,
      orchestratorSuggestions, dynamicSuggestions, suggestionsLoading, dynamicInsights,
      insightsLoading, liaResponse, liaPromptLoading, followUpSuggestions,
    },
    actions: {
      setShowInlineChat, setChatMode, setInlineChatInitialMessage, setIsChatFullscreen,
      setIsTableCollapsed, setLiaInlineMessages, setShowExpandedLIA, setLiaPromptValue,
      setUserCollapsedLIA, setLiaWidth, setIsResizingLIA, setShowLiaSuggestions, setLiaMessages,
      setJobsConversationId, setOrchestratorSuggestions, sendLiaInlineMessage,
      openGeneralChat, openJobCreationChat, closeChat, returnToGeneralChat, returnToLateralPrompt,
      toggleTableExpansion, handleAICommand, getContextualSuggestions,
      refreshSuggestions, generateInsights, sendLiaPrompt,
    },
  }
}
