"use client"

import { useState, useCallback } from "react"
import { Message, ContextPanelData } from "@/types/chat"
import { SearchFilters } from "@/components/search/advanced-filters-modal"
import { SearchPreviewData } from "@/components/search/search-preview-card"
import { ParsedEntities, SearchMode, SearchMetadata } from "@/components/search/smart-search-input"
import { liaApi } from "@/services/lia-api"
import { useSearchFlow } from "@/hooks/search/useSearchFlow"

// ──────────────────────────────────────────────────────────────────────────────
// Types
// ──────────────────────────────────────────────────────────────────────────────

export interface ChatSearchState {
  searchTerm: string
  showSearch: boolean
  isSmartSearchMode: boolean
  smartSearchQuery: string
  searchPreviewData: SearchPreviewData | null
  hasSearchResults: boolean
  isFiltersModalOpen: boolean
  activeSearchFilters: SearchFilters
  availableCredits: number
}

export interface ChatSearchActions {
  setSearchTerm: React.Dispatch<React.SetStateAction<string>>
  setShowSearch: React.Dispatch<React.SetStateAction<boolean>>
  setIsSmartSearchMode: React.Dispatch<React.SetStateAction<boolean>>
  setSmartSearchQuery: React.Dispatch<React.SetStateAction<string>>
  setSearchPreviewData: React.Dispatch<React.SetStateAction<SearchPreviewData | null>>
  setHasSearchResults: React.Dispatch<React.SetStateAction<boolean>>
  setIsFiltersModalOpen: React.Dispatch<React.SetStateAction<boolean>>
  setActiveSearchFilters: React.Dispatch<React.SetStateAction<SearchFilters>>
  setAvailableCredits: React.Dispatch<React.SetStateAction<number>>
  handleSmartSearchSubmit: (
    query: string,
    entities: ParsedEntities,
    mode?: SearchMode,
    metadata?: SearchMetadata
  ) => Promise<void>
  handleSmartSearchCancel: () => void
  handleApplyFilters: (filters: SearchFilters) => void
  getActiveFiltersCount: () => number
  getQuickSuggestions: () => string[]
  activateSmartSearch: (currentInput: string) => void
  searchFlow: ReturnType<typeof useSearchFlow>
}

export interface UseChatSearchReturn {
  state: ChatSearchState
  actions: ChatSearchActions
}

// ──────────────────────────────────────────────────────────────────────────────
// Hook
// ──────────────────────────────────────────────────────────────────────────────

interface UseChatSearchParams {
  messages: Message[]
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  setIsLoading: React.Dispatch<React.SetStateAction<boolean>>
  setContextData: React.Dispatch<React.SetStateAction<ContextPanelData | null>>
  setIsPanelOpen: React.Dispatch<React.SetStateAction<boolean>>
  input: string
  setInput: React.Dispatch<React.SetStateAction<string>>
}

export function useChatSearch({
  messages,
  setMessages,
  setIsLoading,
  setContextData,
  setIsPanelOpen,
  input,
  setInput,
}: UseChatSearchParams): UseChatSearchReturn {
  const searchFlow = useSearchFlow()

  const [searchTerm, setSearchTerm] = useState("")
  const [showSearch, setShowSearch] = useState(false)
  const [isSmartSearchMode, setIsSmartSearchMode] = useState(false)
  const [smartSearchQuery, setSmartSearchQuery] = useState("")
  const [searchPreviewData, setSearchPreviewData] = useState<SearchPreviewData | null>(null)
  const [hasSearchResults, setHasSearchResults] = useState(false)
  const [isFiltersModalOpen, setIsFiltersModalOpen] = useState(false)
  const [activeSearchFilters, setActiveSearchFilters] = useState<SearchFilters>({})
  const [availableCredits, setAvailableCredits] = useState<number>(50)

  // ── computed helpers ─────────────────────────────────────────────────────────

  const getActiveFiltersCount = useCallback((): number => {
    let count = 0
    Object.values(activeSearchFilters).forEach((category) => {
      if (category) {
        Object.values(category as Record<string, unknown>).forEach((value) => {
          if (
            value !== undefined &&
            value !== null &&
            value !== "" &&
            !(Array.isArray(value) && value.length === 0)
          ) {
            count++
          }
        })
      }
    })
    return count
  }, [activeSearchFilters])

  const getQuickSuggestions = useCallback((): string[] => {
    const lastLiaMessage = messages.filter((m) => m.sender === "lia").pop()
    if (!lastLiaMessage) return []

    const content = lastLiaMessage.content.toLowerCase()

    if (
      content.includes("competências") ||
      content.includes("liderança")
    ) {
      return ["Concordo", "Preciso de mais detalhes", "Vamos prosseguir"]
    }
    if (
      content.includes("remuneração") ||
      content.includes("salário")
    ) {
      return ["Está dentro do orçamento", "Precisamos ajustar", "Perfeito"]
    }
    if (
      content.includes("candidato") ||
      content.includes("perfil")
    ) {
      return ["Interessante", "Vamos agendar", "Preciso avaliar"]
    }
    return ["Entendi", "Continue", "Preciso de mais informações"]
  }, [messages])

  // ── handlers ─────────────────────────────────────────────────────────────────

  const handleApplyFilters = useCallback((filters: SearchFilters) => {
    setActiveSearchFilters(filters)
    setIsFiltersModalOpen(false)
  }, [])

  const handleSmartSearchSubmit = useCallback(
    async (
      query: string,
      entities: ParsedEntities,
      mode?: SearchMode,
      metadata?: SearchMetadata
    ): Promise<void> => {
      setIsSmartSearchMode(false)
      setSmartSearchQuery("")

      const finalMode = mode || "natural"
      const finalMetadata: SearchMetadata = metadata || { mode: finalMode }

      searchFlow.submitSearch({
        query,
        entities,
        mode: finalMode,
        metadata: finalMetadata,
        filters: activeSearchFilters,
      })

      const timestamp = Date.now()
      const userMessage: Message = {
        id: timestamp,
        sender: "user",
        content: query,
        timestamp: new Date().toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit",
        }),
        type: "text",
      }
      setMessages((prev) => [...prev, userMessage])

      setSearchPreviewData({
        query,
        localCount: 0,
        pearchEstimate: 0,
        pearchCredits: 0,
        isSearchingLocal: true,
        isEstimatingPearch: true,
      })

      let enrichedQuery = query
      if (
        entities.job_title ||
        entities.skills?.length ||
        entities.location
      ) {
        const parts: string[] = []
        if (entities.job_title) parts.push(`cargo: ${entities.job_title}`)
        if (entities.location) parts.push(`local: ${entities.location}`)
        if (entities.skills?.length)
          parts.push(`skills: ${entities.skills.join(", ")}`)
        if (entities.years_experience)
          parts.push(`experiência: ${entities.years_experience}`)
        if (entities.seniority)
          parts.push(`senioridade: ${entities.seniority}`)
        enrichedQuery = `Buscar candidatos: ${query} [${parts.join(" | ")}]`
      }

      setIsLoading(true)

      try {
        const response = await liaApi.sendMessage({
          content: enrichedQuery,
          user_id: "demo-user",
        })

        const workflowData =
          (response.conversation as Record<string, unknown>)?.workflow_data ||
          (response.message.message_metadata as Record<string, unknown>)?.workflow_data
        const searchResults = (workflowData as Record<string, unknown>)?.search_results as Record<string, unknown> | undefined

        const localCount =
          (searchResults?.local_count as number) ||
          ((searchResults?.local_candidates as unknown[])?.length ?? 0)
        const globalCandidates =
          (searchResults?.global_candidates as unknown[]) || []

        setSearchPreviewData({
          query,
          localCount,
          pearchEstimate:
            globalCandidates.length > 0
              ? globalCandidates.length
              : Math.floor(Math.random() * 50) + 10,
          pearchCredits: Math.max(5, Math.ceil(localCount / 2) + 5),
          isSearchingLocal: false,
          isEstimatingPearch: false,
        })

        const liaResponse: Message = {
          id: timestamp + 1,
          sender: "lia",
          content:
            localCount > 0
              ? `Encontrei **${localCount} candidato(s)** no banco proprietário que correspondem ao perfil.\n\nVocê pode ver os resultados abaixo ou expandir a busca para o banco global com 800M+ perfis.`
              : `Não encontrei candidatos correspondentes no banco proprietário, mas posso buscar no banco global com 800M+ perfis.`,
          timestamp: new Date().toLocaleTimeString("pt-BR", {
            hour: "2-digit",
            minute: "2-digit",
          }),
          type: "text",
          data: {
            workflow_data: workflowData as Record<string, unknown>,
          },
        }

        setMessages((prev) => [
          ...prev.filter((m) => m.type !== "thinking"),
          liaResponse,
        ])

        if (searchResults) {
          setHasSearchResults(true)
          searchFlow.showResults()

          const totalCount = localCount + globalCandidates.length
          if (totalCount > 0) {
            setContextData({
              type: "candidate-suggestions",
              title: `Candidatos Encontrados (${totalCount})`,
              data: {
                query: searchResults.query as string,
                source: searchResults.source as string,
                localCount,
                totalCount,
                candidates: [
                  ...((searchResults.local_candidates as unknown[]) || []),
                  ...globalCandidates,
                ],
              },
            })
            setIsPanelOpen(true)
          }
        }
      } catch {
        setSearchPreviewData(null)

        const errorMessage: Message = {
          id: timestamp + 2,
          sender: "lia",
          content:
            "Desculpe, ocorreu um erro ao buscar candidatos. Por favor, tente novamente.",
          timestamp: new Date().toLocaleTimeString("pt-BR", {
            hour: "2-digit",
            minute: "2-digit",
          }),
          type: "text",
        }
        setMessages((prev) => [
          ...prev.filter((m) => m.type !== "thinking"),
          errorMessage,
        ])
      } finally {
        setIsLoading(false)
      }
    },
    [
      searchFlow,
      activeSearchFilters,
      setMessages,
      setIsLoading,
      setContextData,
      setIsPanelOpen,
    ]
  )

  const handleSmartSearchCancel = useCallback(() => {
    setIsSmartSearchMode(false)
    setSmartSearchQuery("")
    searchFlow.reset()
    setSearchPreviewData(null)
  }, [searchFlow])

  const activateSmartSearch = useCallback(
    (currentInput: string) => {
      setIsSmartSearchMode(true)
      setSmartSearchQuery(currentInput)
      setInput("")
      if (searchFlow.flowState === "idle") {
        searchFlow.startProfileCollection()
      }
    },
    [searchFlow, setInput]
  )

  return {
    state: {
      searchTerm,
      showSearch,
      isSmartSearchMode,
      smartSearchQuery,
      searchPreviewData,
      hasSearchResults,
      isFiltersModalOpen,
      activeSearchFilters,
      availableCredits,
    },
    actions: {
      setSearchTerm,
      setShowSearch,
      setIsSmartSearchMode,
      setSmartSearchQuery,
      setSearchPreviewData,
      setHasSearchResults,
      setIsFiltersModalOpen,
      setActiveSearchFilters,
      setAvailableCredits,
      handleSmartSearchSubmit,
      handleSmartSearchCancel,
      handleApplyFilters,
      getActiveFiltersCount,
      getQuickSuggestions,
      activateSmartSearch,
      searchFlow,
    },
  }
}
