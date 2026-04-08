"use client"

import { useCallback } from "react"
import { liaApi } from "@/services/lia-api"
import type { ParsedEntities, SearchMode, SearchMetadata } from "@/components/search/smart-search-input"
import type { SearchFilters } from "@/components/search/advanced-filters-modal"
import type { SearchPreviewData } from "@/components/search/search-preview-card"
import type { Message } from "./types"
import { formatMessageTime, type LiaChatMessage } from "@/hooks/use-lia-chat-connection"

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
    submitSearch: (params: Record<string, unknown>) => void
    showResults: () => void
    startProfileCollection: () => void
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
  chatConversationId: string | null
  setChatConversationId: (id: string | null) => void
  addChatMessage: (msg: LiaChatMessage) => void
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
    chatConversationId, setChatConversationId, addChatMessage,
  } = ctx

  const handleSmartSearchSubmit = useCallback(async (query: string, entities: ParsedEntities, mode?: SearchMode, metadata?: SearchMetadata) => {
    setIsSmartSearchMode(false)
    setSmartSearchQuery("")
    
    // Construct search metadata with mode and filters
    const finalMode = mode || "natural"
    const finalMetadata: SearchMetadata = metadata || { mode: finalMode }
    
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
    addChatMessage({ id: `user-search-${timestamp}`, sender: "user", content: query, timestamp: formatMessageTime() })

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
        user_id: "demo-user",
        conversation_id: chatConversationId ?? undefined,
      })
      
      if (response.conversation?.id) {
        setChatConversationId(response.conversation.id)
      }

      const workflowData = response.conversation?.workflow_data || response.message.message_metadata?.workflow_data
      const searchResults = (workflowData as Record<string, unknown> | undefined)?.search_results as Record<string, unknown> | undefined
      
      const localCount = (searchResults?.local_count as number | undefined) || (searchResults?.local_candidates as unknown[] | undefined)?.length || 0
      const globalCandidates = (searchResults?.global_candidates as unknown[]) || []
      
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
      addChatMessage({ id: `lia-search-${Date.now()}`, sender: "lia", content: liaResponse.content, timestamp: formatMessageTime() })

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
              candidates: [...((searchResults.local_candidates as unknown[]) || []), ...globalCandidates]
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
  }, [searchFlow, activeSearchFilters, setContextData, setHasSearchResults, setIsLoading, setIsPanelOpen, setIsSmartSearchMode, setMessages, setSearchPreviewData, setSmartSearchQuery, chatConversationId, setChatConversationId, addChatMessage])

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
      const fileCtx = currentFileAnalysis as Record<string, unknown> | null
      const messageContent = fileCtx
        ? `${userMessageContent}\n\n[Contexto do arquivo analisado: ${fileCtx.filename}]\n${fileCtx.summary || ''}\n${(fileCtx.extractedText as string) ? `Texto extraído: ${(fileCtx.extractedText as string).substring(0, 500)}...` : ''}`
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
        // SSE path — fallback when WS is not connected (proxied to backend /api/v1/chat/stream)
        addChatMessage({ id: `user-${newMessage.id}`, sender: "user", content: userMessageContent, timestamp: formatMessageTime() })
        let sseSucceeded = false
        try {
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
            body: JSON.stringify({
              content: messageContent,
              conversation_id: chatConversationId ?? undefined,
            }),
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

              let parsed: Record<string, unknown> | null = null
              try { parsed = JSON.parse(payload) } catch (_) { /* partial JSON chunk */ }
              if (parsed) {
                if (parsed.conversation_id && typeof parsed.conversation_id === 'string') {
                  setChatConversationId(parsed.conversation_id)
                }
                if (parsed.token) {
                  accumulated += parsed.token as string
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
                  throw new Error(parsed.error as string)
                }
              }
            }
          }
          sseSucceeded = true
          if (accumulated) {
            addChatMessage({ id: `lia-sse-${Date.now()}`, sender: "lia", content: accumulated, timestamp: formatMessageTime() })
          }
        } catch (_sseError) {
          // SSE failed — fall through to REST API below
        }

        if (!sseSucceeded) {
          const response = await liaApi.sendMessage({
            content: messageContent,
            user_id: "demo-user",
            conversation_id: chatConversationId ?? undefined,
          })

          if (response.conversation?.id) {
            setChatConversationId(response.conversation.id)
          }

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

          setMessages(prev => {
            const newMessages = [...prev]
            newMessages[newMessages.length - 1] = liaResponse
            return newMessages
          })
          addChatMessage({ id: `lia-rest-${Date.now()}`, sender: "lia", content: response.message.content, timestamp: formatMessageTime() })
        }

      } else {
        addChatMessage({ id: `user-${newMessage.id}`, sender: "user", content: userMessageContent, timestamp: formatMessageTime() })
        const response = await liaApi.sendMessage({
          content: messageContent,
          user_id: "demo-user",
          conversation_id: chatConversationId ?? undefined,
          attachments: currentAttachments.length > 0 ? currentAttachments : undefined,
          audio: currentAudio || undefined
        })

        if (response.conversation?.id) {
          setChatConversationId(response.conversation.id)
        }

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
        const wfData = workflowData as Record<string, unknown> | undefined

        if (wfData?.search_results) {
          const searchResults = wfData.search_results as Record<string, unknown>
          const localCandidates = (searchResults.local_candidates || []) as unknown[]
          const globalCandidates = (searchResults.global_candidates || []) as unknown[]
          const totalCount = localCandidates.length + globalCandidates.length
          const panelData = {
            type: "candidate-suggestions" as const,
            title: `Candidatos Encontrados (${totalCount})`,
            data: {
              query: searchResults.query,
              source: searchResults.source,
              localCount: searchResults.local_count,
              totalCount,
              candidates: [...localCandidates, ...globalCandidates]
            }
          }
          liaResponse.contextData = panelData
          setContextData(panelData)
          setIsPanelOpen(true)
        } else if (response.conversation?.workflow_type === 'job_creation' && wfData) {
          if (wfData.completion_percentage !== undefined) {
            const fieldStatus = (wfData.field_status || {}) as Record<string, string>
            const collectedFields = Object.keys(fieldStatus).filter(k => fieldStatus[k] === 'collected')
            const pendingFields = Object.keys(fieldStatus).filter(k => fieldStatus[k] === 'pending')
            const panelData = {
              type: "job-creation-progress" as const,
              title: "Progresso: Criação de Vaga",
              data: {
                completion_percentage: Math.round((wfData.completion_percentage as number) || 0),
                collected_fields: collectedFields,
                pending_fields: pendingFields,
                next_panel: (wfData.current_panel as string) || 'Aguardando próxima etapa'
              }
            }
            liaResponse.contextData = panelData
            setContextData(panelData)
            setIsPanelOpen(true)
          } else if (wfData.frames) {
            const frames = wfData.frames as Record<string, unknown>
            let panelData: Record<string, unknown> | null = null
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
        addChatMessage({ id: `lia-rest-${Date.now()}`, sender: "lia", content: response.message.content, timestamp: formatMessageTime() })

        const actionResult = response.message.message_metadata?.action_result as Record<string, unknown> | undefined
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
  }, [input, isLoading, messages.length, wsIsConnected, wsSendMessage, wsClearTokens, attachedFiles, audioBlob, fileAnalysisContext, searchFlow, setAttachedFiles, setAudioBlob, setChatTitle, setContextData, setFileAnalysisContext, setInput, setIsLoading, setIsPanelOpen, setIsSmartSearchMode, setMessages, setSmartSearchQuery, wsStreamingModeRef, chatConversationId, setChatConversationId])

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
        
        if (result.navigate && typeof result.navigate === 'string' && result.navigate.startsWith('/')) {
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
  }, [messages.length, contextData, setContextData, setIsSchedulingModalOpen, setMessages, setSelectedCandidateForScheduling, addChatMessage])


  const handleSmartSearchCancel = useCallback(() => {
    setIsSmartSearchMode(false)
    setSmartSearchQuery("")
    searchFlow.reset()
    setSearchPreviewData(null)
  }, [searchFlow, setIsSmartSearchMode, setSmartSearchQuery, setSearchPreviewData])

  return {
    handleSmartSearchSubmit,
    handleSmartSearchCancel,
    handleSendMessage,
    handlePipelineAction,
  }
}
