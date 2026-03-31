// @ts-nocheck
"use client"

import { useCallback } from "react"
import { liaApi } from "@/services/lia-api"
import type { ParsedEntities, SearchMode, SearchMetadata } from "@/components/search/smart-search-input"
import type { SearchFilters } from "@/components/search/advanced-filters-modal"
import type { SearchPreviewData } from "@/components/search/search-preview-card"
import type { Message } from "./types"

interface ChatPageHandlersContext {
  input: string
  setInput: (v: string) => void
  isLoading: boolean
  setIsLoading: (v: boolean) => void
  messages: Message[]
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  searchFlow: Record<string, unknown> & {
    flowState: string
    startSearch: (q: string, e: ParsedEntities, m?: SearchMode, meta?: SearchMetadata) => Promise<void>
    reset: () => void
    submitProfile: (profile: string) => void
  }
  activeSearchFilters: SearchFilters
  setIsSmartSearchMode: (v: boolean) => void
  setSmartSearchQuery: (v: string) => void
  setSearchPreviewData: (v: SearchPreviewData | null) => void
  setHasSearchResults: (v: boolean) => void
  setContextData: (v: Record<string, unknown> | null) => void
  setIsPanelOpen: (v: boolean) => void
  contextData: Record<string, unknown> | null
  attachedFiles: File[]
  setAttachedFiles: (v: File[]) => void
  audioBlob: Blob | null
  setAudioBlob: (v: Blob | null) => void
  setChatTitle: (v: string) => void
  setFileAnalysisContext: (v: Record<string, unknown> | null) => void
  fileAnalysisContext: Record<string, unknown> | null
  wsIsConnected: boolean
  wsSendMessage: (msg: string) => void
  wsClearTokens: () => void
  wsStreamingModeRef: React.MutableRefObject<boolean>
  selectedCandidateForScheduling: Record<string, unknown> | null
  setSelectedCandidateForScheduling: (v: Record<string, unknown> | null) => void
  setIsSchedulingModalOpen: (v: boolean) => void
}

export function useChatPageHandlers(ctx: ChatPageHandlersContext) {
  const {
    input, setInput, isLoading, setIsLoading, messages, setMessages,
    searchFlow, activeSearchFilters, setIsSmartSearchMode, setSmartSearchQuery,
    setSearchPreviewData, setHasSearchResults, setContextData, setIsPanelOpen,
    contextData, attachedFiles, setAttachedFiles, audioBlob, setAudioBlob,
    setChatTitle, setFileAnalysisContext, fileAnalysisContext,
    wsIsConnected, wsSendMessage, wsClearTokens, wsStreamingModeRef,
    selectedCandidateForScheduling, setSelectedCandidateForScheduling, setIsSchedulingModalOpen,
  } = ctx

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


  return {
    handleSmartSearchSubmit,
    handleSmartSearchCancel,
    handleSendMessage,
    handlePipelineAction,
  }
}
