"use client"

import { useState, useCallback, useEffect } from "react"
import { Message, ContextPanelData } from "@/types/chat"
import { CandidateResult } from "@/components/search/search-results-card"

// ──────────────────────────────────────────────────────────────────────────────
// Types
// ──────────────────────────────────────────────────────────────────────────────

interface SelectedCandidateForScheduling {
  name: string
  email: string
  id?: string
  job_title: string
  job_vacancy_id?: string
}

interface PendingPearchSearch {
  query: string
  threadId?: string
}

export interface ChatPageState {
  // messages / chat
  messages: Message[]
  input: string
  isLoading: boolean
  chatId: string
  chatTitle: string
  activeTab: "conversa" | "controle"
  newMessageIndicator: boolean
  currentMessageIndex: number
  // modals / overlays
  isSchedulingModalOpen: boolean
  isCommandPaletteOpen: boolean
  selectedCandidateForScheduling: SelectedCandidateForScheduling | null
  isCandidateDetailOpen: boolean
  selectedCandidateForDetail: CandidateResult | null
  isCreditDialogOpen: boolean
  pendingPearchSearch: PendingPearchSearch | null
  // context panel
  contextData: ContextPanelData | null
  isPanelOpen: boolean
}

export interface ChatPageActions {
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  setInput: React.Dispatch<React.SetStateAction<string>>
  setIsLoading: React.Dispatch<React.SetStateAction<boolean>>
  setChatId: React.Dispatch<React.SetStateAction<string>>
  setChatTitle: React.Dispatch<React.SetStateAction<string>>
  setActiveTab: React.Dispatch<React.SetStateAction<"conversa" | "controle">>
  setNewMessageIndicator: React.Dispatch<React.SetStateAction<boolean>>
  setCurrentMessageIndex: React.Dispatch<React.SetStateAction<number>>
  setIsSchedulingModalOpen: React.Dispatch<React.SetStateAction<boolean>>
  setIsCommandPaletteOpen: React.Dispatch<React.SetStateAction<boolean>>
  setSelectedCandidateForScheduling: React.Dispatch<React.SetStateAction<SelectedCandidateForScheduling | null>>
  setIsCandidateDetailOpen: React.Dispatch<React.SetStateAction<boolean>>
  setSelectedCandidateForDetail: React.Dispatch<React.SetStateAction<CandidateResult | null>>
  setIsCreditDialogOpen: React.Dispatch<React.SetStateAction<boolean>>
  setPendingPearchSearch: React.Dispatch<React.SetStateAction<PendingPearchSearch | null>>
  setContextData: React.Dispatch<React.SetStateAction<ContextPanelData | null>>
  setIsPanelOpen: React.Dispatch<React.SetStateAction<boolean>>
  updateChatTitle: (newTitle: string) => void
  getRelativeTime: (timestamp: string) => string
}

export interface UseChatPageStateReturn {
  state: ChatPageState
  actions: ChatPageActions
}

// ──────────────────────────────────────────────────────────────────────────────
// Hook
// ──────────────────────────────────────────────────────────────────────────────

interface UseChatPageStateParams {
  initialConversation: Message[]
  conversationType: string
}

export function useChatPageState({
  initialConversation,
  conversationType,
}: UseChatPageStateParams): UseChatPageStateReturn {
  // ── messages / chat ─────────────────────────────────────────────────────────
  const [messages, setMessages] = useState<Message[]>(initialConversation)
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [newMessageIndicator, setNewMessageIndicator] = useState(false)
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0)

  // ── chat ID / title ──────────────────────────────────────────────────────────
  const [chatId, setChatId] = useState("#0000")

  // Generate ID on client-side only to avoid hydration mismatch
  useEffect(() => {
    const timestamp = Date.now()
    const id = String(timestamp).slice(-4)
    setChatId(`#${id}`)
  }, [])

  const [chatTitle, setChatTitle] = useState<string>(() => {
    if (conversationType === "empty") return "Nova Conversa"

    const firstMessages = initialConversation
      .slice(0, 5)
      .map((m) => m.content.toLowerCase())
      .join(" ")

    if (
      firstMessages.includes("vaga") ||
      firstMessages.includes("posição") ||
      firstMessages.includes("diretor")
    ) {
      const directorMatch = firstMessages.match(/diretor\s+de\s+(\w+)/i)
      if (directorMatch) {
        return `Vaga ${directorMatch[0]
          .split(" ")
          .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
          .join(" ")}`
      }
      return "Nova Vaga"
    }

    if (
      firstMessages.includes("candidato") ||
      firstMessages.includes("triagem")
    ) {
      return "Análise de Candidatos"
    }

    if (
      firstMessages.includes("relatório") ||
      firstMessages.includes("dashboard")
    ) {
      return "Relatório & Analytics"
    }

    if (firstMessages.includes("onboarding")) return "Plano de Integração"

    return "Conversa Geral"
  })

  const [activeTab, setActiveTab] = useState<"conversa" | "controle">(
    "conversa"
  )

  // ── modals / overlays ────────────────────────────────────────────────────────
  const [isSchedulingModalOpen, setIsSchedulingModalOpen] = useState(false)
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false)
  const [selectedCandidateForScheduling, setSelectedCandidateForScheduling] =
    useState<SelectedCandidateForScheduling | null>(null)
  const [isCandidateDetailOpen, setIsCandidateDetailOpen] = useState(false)
  const [selectedCandidateForDetail, setSelectedCandidateForDetail] =
    useState<CandidateResult | null>(null)
  const [isCreditDialogOpen, setIsCreditDialogOpen] = useState(false)
  const [pendingPearchSearch, setPendingPearchSearch] =
    useState<PendingPearchSearch | null>(null)

  // ── context panel ────────────────────────────────────────────────────────────
  const [contextData, setContextData] = useState<ContextPanelData | null>(null)
  const [isPanelOpen, setIsPanelOpen] = useState(false)

  // Process contextData from initial conversation messages (run once on mount)
  useEffect(() => {
    if (initialConversation.length > 0) {
      const messageWithContext = initialConversation
        .slice()
        .reverse()
        .find((msg) => msg.contextData)

      if (messageWithContext?.contextData) {
        setContextData(messageWithContext.contextData as any)
        setIsPanelOpen(true)
      }
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // ── helpers ──────────────────────────────────────────────────────────────────
  const updateChatTitle = useCallback((newTitle: string) => {
    setChatTitle(newTitle)
  }, [])

  const getRelativeTime = useCallback((timestamp: string): string => {
    const now = new Date()
    const messageTime = new Date(`2024-02-22T${timestamp}:00`)
    const diffInMinutes = Math.floor(
      (now.getTime() - messageTime.getTime()) / (1000 * 60)
    )

    if (diffInMinutes < 1) return "agora"
    if (diffInMinutes < 60) return `há ${diffInMinutes} min`
    if (diffInMinutes < 1440) return `há ${Math.floor(diffInMinutes / 60)}h`
    return "ontem"
  }, [])

  // ── return ───────────────────────────────────────────────────────────────────
  return {
    state: {
      messages,
      input,
      isLoading,
      chatId,
      chatTitle,
      activeTab,
      newMessageIndicator,
      currentMessageIndex,
      isSchedulingModalOpen,
      isCommandPaletteOpen,
      selectedCandidateForScheduling,
      isCandidateDetailOpen,
      selectedCandidateForDetail,
      isCreditDialogOpen,
      pendingPearchSearch,
      contextData,
      isPanelOpen,
    },
    actions: {
      setMessages,
      setInput,
      setIsLoading,
      setChatId,
      setChatTitle,
      setActiveTab,
      setNewMessageIndicator,
      setCurrentMessageIndex,
      setIsSchedulingModalOpen,
      setIsCommandPaletteOpen,
      setSelectedCandidateForScheduling,
      setIsCandidateDetailOpen,
      setSelectedCandidateForDetail,
      setIsCreditDialogOpen,
      setPendingPearchSearch,
      setContextData,
      setIsPanelOpen,
      updateChatTitle,
      getRelativeTime,
    },
  }
}
