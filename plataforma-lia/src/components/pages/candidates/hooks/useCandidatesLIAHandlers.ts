"use client"

import React from "react"
import { callOrchestratedTalentChat, type OrchestratedTalentChatResponse } from "@/lib/api/kanban-assistant"
import { formatScorePercent } from "@/lib/design-tokens"
import type { Candidate } from "../types"
import type { ParsedEntities, SearchMode, SearchMetadata } from "@/components/search/smart-search-input"
import type { SearchFilters } from "@/components/search/advanced-filters-modal"
import type { CommunicationType } from "@/components/modals/unified-communication-modal"
import type { SearchAnalytics } from "@/components/proactive-insight-card"
import type { CalibrationCandidate } from "@/components/calibration-card"
import type { SearchTab } from "./candidates-core"

export interface LIAChatMessage {
  id: string
  type: 'user' | 'lia' | 'proactive_insight' | 'calibration'
  content: string
  timestamp: Date
  metadata?: {
    action_executed?: boolean
    action_result?: Record<string, unknown>
    action_type?: string
    needs_confirmation?: boolean
    needs_params?: boolean
    pending_action_id?: string
    conversation_id?: string
  }
  searchResults?: {
    localCount: number
    globalCount: number
    query: string
  }
  analytics?: SearchAnalytics
  candidates?: CalibrationCandidate[]
}

interface AppRouter {
  push: (href: string) => void
  replace: (href: string) => void
  back: () => void
  refresh: () => void
}

interface AuthUser {
  id?: string
  email?: string
  company?: string
  name?: string
}

export interface CandidatesLIAHandlersContext {
  candidates: Candidate[]
  setCandidates: React.Dispatch<React.SetStateAction<Candidate[]>>
  chatMessages: LIAChatMessage[]
  setChatMessages: React.Dispatch<React.SetStateAction<LIAChatMessage[]>>
  liaPromptValue: string
  setLiaPromptValue: React.Dispatch<React.SetStateAction<string>>
  liaWidth: number
  setLiaWidth: React.Dispatch<React.SetStateAction<number>>
  activeSearchTab: SearchTab
  setActiveSearchTab: React.Dispatch<React.SetStateAction<SearchTab>>
  talentConversationId: string | undefined
  setTalentConversationId: React.Dispatch<React.SetStateAction<string | undefined>>
  liaIsParsingEntities: boolean
  setLiaIsParsingEntities: React.Dispatch<React.SetStateAction<boolean>>
  liaSuggestions: string[]
  setLiaSuggestions: React.Dispatch<React.SetStateAction<string[]>>
  showLiaSuggestions: boolean
  setShowLiaSuggestions: React.Dispatch<React.SetStateAction<boolean>>
  showLiaAssistant: boolean
  setShowLiaAssistant: React.Dispatch<React.SetStateAction<boolean>>
  selectedCandidatesForBatch: Set<string>
  searchResults: {
    local: Candidate[]
    global: Candidate[]
    localCount: number
    globalCount: number
    query: string
    isLoading: boolean
    showGlobalResults: boolean
    globalDismissed: boolean
  }
  lastSearchQuery: string
  activeSearchFilters: SearchFilters
  liaPromptEntities: ParsedEntities
  setLiaPromptEntities: React.Dispatch<React.SetStateAction<ParsedEntities>>
  setShowExpandedLIA: React.Dispatch<React.SetStateAction<boolean>>
  userCollapsedLIA: boolean
  setUserCollapsedLIA: React.Dispatch<React.SetStateAction<boolean>>
  selectedCandidateForLIA: Candidate | null
  setSelectedCandidateForLIA: React.Dispatch<React.SetStateAction<Candidate | null>>
  showLIAPromptForCandidate: boolean
  setShowLIAPromptForCandidate: React.Dispatch<React.SetStateAction<boolean>>
  selectedCandidate: Candidate | null
  setSelectedCandidate: React.Dispatch<React.SetStateAction<Candidate | null>>
  showQuickViewModal: boolean
  setShowQuickViewModal: React.Dispatch<React.SetStateAction<boolean>>
  showComparisonModal: boolean
  setShowComparisonModal: React.Dispatch<React.SetStateAction<boolean>>
  setShowScheduleModal: React.Dispatch<React.SetStateAction<boolean>>
  setUnifiedModalCandidate: React.Dispatch<React.SetStateAction<Candidate | null>>
  setUnifiedModalType: React.Dispatch<React.SetStateAction<CommunicationType>>
  setUnifiedModalOpen: React.Dispatch<React.SetStateAction<boolean>>
  setShowAddToListModal: React.Dispatch<React.SetStateAction<boolean>>
  setSelectedCandidatesForBatch: React.Dispatch<React.SetStateAction<Set<string>>>
  isLIAThinking: boolean
  setIsLIAThinking: React.Dispatch<React.SetStateAction<boolean>>
  handleStartWSITextScreening: (candidate: Candidate) => void
  handleOpenWSIModal: (candidate: Candidate) => void
  openUnifiedModal: (candidate: Candidate, type: CommunicationType) => void
  handleCandidateClick: (candidate: Candidate) => void
  executeSearch: (
    query: string,
    entities?: ParsedEntities,
    mode?: SearchMode,
    metadata?: SearchMetadata,
    usePearch?: boolean
  ) => Promise<void>
  talentFunnel: {
    toggleFavoriteCandidate: (id: string, note?: string) => void
  }
  toast: (opts: { title: string; description?: string; variant?: "destructive" | "default" }) => void
  user: AuthUser | null
  router: AppRouter
}

export function useCandidatesLIAHandlers(ctx: CandidatesLIAHandlersContext) {
  const {
    candidates,
    setChatMessages,
    setLiaPromptValue,
    activeSearchTab,
    setActiveSearchTab,
    talentConversationId,
    setTalentConversationId,
    selectedCandidatesForBatch,
    setSelectedCandidatesForBatch,
    searchResults,
    lastSearchQuery,
    activeSearchFilters,
    setShowScheduleModal,
    setUnifiedModalCandidate,
    setUnifiedModalType,
    setUnifiedModalOpen,
    setShowAddToListModal,
    setIsLIAThinking,
    executeSearch,
    talentFunnel,
    toast,
    user,
  } = ctx

  // 🎯 Handler para quick actions do ProactiveInsightCard
  const handleQuickAction = async (actionId: string, actionType: string) => {
    const liaMessage: LIAChatMessage = {
      id: `lia-action-${Date.now()}`,
      type: 'lia',
      content: '',
      timestamp: new Date()
    }

    switch (actionType) {
      case 'screening':
        liaMessage.content = '🎯 **Iniciando triagem em lote**\n\nPreparando triagem WSI para os candidatos selecionados...'
        setChatMessages(prev => [...prev, liaMessage])
        toast({
          title: "Triagem WSI",
          description: "Funcionalidade de triagem em lote será implementada em breve."
        })
        break

      case 'assign':
        liaMessage.content = '📋 **Atribuir candidatos a vaga**\n\nSelecione os candidatos e escolha a vaga para atribuição.'
        setChatMessages(prev => [...prev, liaMessage])
        if (candidates.length > 0) {
          setSelectedCandidatesForBatch(new Set(candidates.slice(0, 10).map(c => c.id)))
        }
        break

      case 'favorite':
        const candidateIds = candidates.slice(0, 10).map(c => c.id)
        candidateIds.forEach(id => talentFunnel.toggleFavoriteCandidate(id))
        liaMessage.content = `⭐ **${candidateIds.length} candidatos adicionados aos favoritos**\n\nVocê pode acessá-los na aba "Favoritos".`
        setChatMessages(prev => [...prev, liaMessage])
        toast({
          title: "Favoritos atualizados",
          description: `${candidateIds.length} candidatos adicionados aos favoritos`,
        })
        break

      case 'whatsapp':
        liaMessage.content = '📱 **Contato via WhatsApp**\n\nPreparando mensagens personalizadas para contato...'
        setChatMessages(prev => [...prev, liaMessage])
        break

      case 'schedule':
        liaMessage.content = '📅 **Agendamento de entrevistas**\n\nAbrindo modal de agendamento em lote...'
        setChatMessages(prev => [...prev, liaMessage])
        setShowScheduleModal(true)
        break

      case 'refine':
        liaMessage.content = '🔍 **Refinar busca**\n\nDigite novos critérios para refinar sua busca.'
        setChatMessages(prev => [...prev, liaMessage])
        setLiaPromptValue('')
        break

      case 'export':
        liaMessage.content = '📊 **Exportando candidatos**\n\nPreparando arquivo para download...'
        setChatMessages(prev => [...prev, liaMessage])
        try {
          const exportData = candidates.map(c => ({
            nome: c.name,
            cargo: c.current_title || c.position,
            empresa: c.current_company,
            email: c.email,
            telefone: c.phone || c.mobile_phone,
            linkedin: c.linkedin_url,
            cidade: c.location_city || c.location,
            score: c.liaAnalysis?.score || c.score
          }))
          const csvContent = [
            Object.keys(exportData[0]).join(','),
            ...exportData.map(row => Object.values(row).map(v => `"${v || ''}"`).join(','))
          ].join('\n')
          const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
          const url = URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = url
          link.download = `candidatos_${new Date().toISOString().split('T')[0]}.csv`
          link.click()

          const successMessage: LIAChatMessage = {
            id: `lia-export-success-${Date.now()}`,
            type: 'lia',
            content: `✅ **Exportação concluída!**\n\n${exportData.length} candidatos exportados para CSV.`,
            timestamp: new Date()
          }
          setChatMessages(prev => [...prev, successMessage])
        } catch (error) {
        }
        break

      default:
        liaMessage.content = `Ação "${actionId}" será implementada em breve.`
        setChatMessages(prev => [...prev, liaMessage])
    }
  }

  // 🎯 Handler para mensagens orquestradas do chat de talentos
  const handleOrchestratedTalentMessage = async (message: string): Promise<OrchestratedTalentChatResponse> => {
    const selectedIds = Array.from(selectedCandidatesForBatch)

    const candidatesForContext = candidates.slice(0, 50).map(c => ({
      id: c.id,
      name: c.name,
      current_title: c.current_title || c.position,
      current_company: c.current_company,
      location: c.location_city || c.location,
      skills: c.skills || [],
      experience_years: c.years_of_experience,
      lia_score: c.liaAnalysis?.score || c.score,
      wsi_score: c.lia_score,
      source: c.source,
      // Campos adicionais para análises completas
      work_model: c.work_model_preference || c.workModel,
      is_remote: c.is_remote,
      willing_to_relocate: c.willing_to_relocate,
      salary_expectation_clt: c.salary_expectation_clt || c.desired_salary_min,
      salary_expectation_pj: c.salary_expectation_pj,
      languages: c.languages,
      seniority_level: c.seniority_level,
      gender: c.gender,
      status: c.status,
      is_active: c.is_active,
      technical_skills: c.technical_skills,
      soft_skills: c.soft_skills,
    }))

    const searchContextData = {
      query: searchResults.query || ctx.liaPromptValue,
      mode: activeSearchTab,
      total_results: searchResults.localCount + (searchResults.showGlobalResults ? searchResults.globalCount : 0),
      local_results: searchResults.localCount,
      global_results: searchResults.globalCount,
      active_filters: activeSearchFilters as Record<string, unknown>
    }

    try {
      const response = await callOrchestratedTalentChat({
        message,
        candidates: candidatesForContext,
        selected_candidate_ids: selectedIds.length > 0 ? selectedIds : undefined,
        search_context: searchContextData,
        target_job: undefined,
        conversation_id: talentConversationId,
        company_id: user?.company || 'default',
      })
      if (response.conversation_id) {
        setTalentConversationId(response.conversation_id)
      }

      if (response.ui_action) {
        handleTalentUIAction(response.ui_action, response.ui_action_params)
      }

      if (response.action_executed && response.action_result) {
        toast({
          title: "Ação executada",
          description: response.action_type ? `${response.action_type} concluída com sucesso` : "Ação concluída com sucesso"
        })
      }

      return response
    } catch (error) {
      return {
        success: false,
        content: 'Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.',
        agent_used: 'Fallback',
        agents_consulted: [],
        intent_detected: 'error',
        confidence: 0,
        suggested_prompts: [],
        actions: [],
        ui_action: null
      }
    }
  }

  // 🎯 Handler para UI actions retornadas pelo orquestrador
  const handleTalentUIAction = (action: string, params?: Record<string, unknown>) => {
    switch (action) {
      case 'start_job_wizard':
        toast({
          title: "Criar Nova Vaga",
          description: "Abrindo wizard de criação de vaga..."
        })
        break
      case 'switch_search_mode':
        if (params?.mode && typeof params.mode === 'string') {
          setActiveSearchTab(params.mode as SearchTab)
        }
        break
      case 'open_communication_modal':
        if (selectedCandidatesForBatch.size > 0) {
          const firstId = Array.from(selectedCandidatesForBatch)[0]
          const candidate = candidates.find(c => c.id === firstId)
          if (candidate) {
            setUnifiedModalCandidate(candidate)
            setUnifiedModalType('email')
            setUnifiedModalOpen(true)
          }
        }
        break
      case 'open_schedule_modal':
        setShowScheduleModal(true)
        break
      case 'open_screening_modal':
        if (selectedCandidatesForBatch.size > 0) {
          const firstId = Array.from(selectedCandidatesForBatch)[0]
          const candidate = candidates.find(c => c.id === firstId)
          if (candidate) {
            setUnifiedModalCandidate(candidate)
            setUnifiedModalType('triagem')
            setUnifiedModalOpen(true)
          }
        }
        break
      case 'trigger_export':
        handleQuickAction('export', 'export')
        break
      case 'open_add_to_list_modal':
        if (selectedCandidatesForBatch.size > 0) {
          setShowAddToListModal(true)
        }
        break
    }
  }

  // 🎯 Handlers para CalibrationCard
  const handleCalibrationLike = async (candidateId: string) => {
    try {
      await fetch('/api/backend-proxy/search/calibration/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_id: candidateId,
          feedback: 'like',
          context: { source: 'chat_calibration' }
        })
      })

      toast({
        title: "Feedback registrado",
        description: "Candidato marcado como interessante",
      })
    } catch (error) {
    }
  }

  const handleCalibrationDislike = async (candidateId: string, reason?: string) => {
    try {
      await fetch('/api/backend-proxy/search/calibration/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_id: candidateId,
          feedback: 'dislike',
          reason,
          context: { source: 'chat_calibration' }
        })
      })

      toast({
        title: "Feedback registrado",
        description: "Preferência salva para calibração",
      })
    } catch (error) {
    }
  }

  // Detecta se o texto é uma pergunta genérica (não uma busca de candidatos)
  const isConversationalMessage = (text: string): boolean => {
    const normalizedText = text.toLowerCase().trim()

    const greetings = [
      /^(oi|olá|ola|hey|hi|hello|e aí|eai|fala|bom dia|boa tarde|boa noite|tudo bem|tudo certo|beleza)[\s!.,?]*$/,
      /^(oi|olá|ola|hey|hi|hello|e aí|eai|fala|bom dia|boa tarde|boa noite)\s+(lia|tudo|como)/,
      /^(obrigad[oa]|valeu|thanks|vlw|brigad[oa])[\s!.,?]*$/,
      /^(tchau|até mais|ate mais|bye|flw|falou)[\s!.,?]*$/,
    ]

    return greetings.some(pattern => pattern.test(normalizedText))
  }

  const isGenericQuestion = (text: string): boolean => {
    const normalizedText = text.toLowerCase().trim()

    const questionPatterns = [
      /^(o que|que tipo|qual|quais|como|por que|quando|onde|quem|quanto|quantos)\s/,
      /^(me explica|explique|pode explicar|poderia explicar)/,
      /^(me ajuda|ajuda|help|pode ajudar|poderia ajudar)/,
      /^(o que você|voce pode|você consegue|vc pode)/,
      /\?$/,
    ]

    const searchKeywords = [
      'desenvolvedor', 'developer', 'programador', 'engenheiro', 'analista',
      'gerente', 'manager', 'coordenador', 'diretor', 'especialista',
      'junior', 'pleno', 'sênior', 'senior', 'trainee', 'estagiário',
      'python', 'java', 'javascript', 'react', 'node', 'angular', 'vue',
      'backend', 'frontend', 'fullstack', 'devops', 'data', 'machine learning',
      'são paulo', 'rio de janeiro', 'belo horizonte', 'remoto', 'híbrido',
      'anos de experiência', 'experiência em', 'conhecimento em',
      'product manager', 'product owner', 'scrum master', 'ux', 'ui',
      'designer', 'marketing', 'vendas', 'sales', 'rh', 'recursos humanos',
      'b2b', 'saas', 'fintech', 'startup'
    ]

    const hasSearchKeywords = searchKeywords.some(keyword =>
      normalizedText.includes(keyword.toLowerCase())
    )

    const isQuestion = questionPatterns.some(pattern => pattern.test(normalizedText))

    return isQuestion && !hasSearchKeywords
  }

  // Handler para mensagens no chat da LIA (perguntas ou buscas)
  // Loading State Ownership:
  // - Comandos de análise: handleAICommand gerencia isLIAThinking
  // - Perguntas genéricas: orquestrador gerencia isLIAThinking (try/finally aqui)
  // - Buscas: executeSearch gerencia setIsLoading (indicador visual diferente)
  const handleLIAChatMessage = async (message: string) => {
    const trimmedMessage = message.trim()
    const normalizedMessage = trimmedMessage.toLowerCase()

    // Comandos de análise redirecionados para handleAICommand (gerencia seu próprio loading)
    const analysisCommands = [
      'analisar potencial', 'potencial de crescimento', 'analise potencial',
      'definir tipo', 'tipo de perfil',
      'resumo executivo', 'resumir busca', 'resumir resultado',
      'pontos a desenvolver', 'pontos a serem desenvolvidos',
      'vagas ideais', 'tipos de vagas',
      'top 5', 'top5', 'melhores candidatos',
      'comparar', 'comparação'
    ]

    // Verificar se é um comando de análise - se for, usar handleAICommand
    const isAnalysisCommand = analysisCommands.some(cmd => normalizedMessage.includes(cmd))

    if (isAnalysisCommand) {
      handleAICommand(trimmedMessage)
      setLiaPromptValue('')
      return
    }

    // Adicionar mensagem do usuário ao chat
    const userMessage: LIAChatMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: trimmedMessage,
      timestamp: new Date()
    }
    setChatMessages(prev => [...prev, userMessage])
    setLiaPromptValue('')

    // Se é saudação/conversacional ou pergunta genérica, usar o orquestrador (não buscar candidatos)
    if (isConversationalMessage(trimmedMessage) || isGenericQuestion(trimmedMessage)) {
      setIsLIAThinking(true)

      try {
        const response = await handleOrchestratedTalentMessage(trimmedMessage)

        if (response.success) {
          const agentInfo = response.agents_consulted?.length > 1
            ? `_Agentes: ${response.agents_consulted.join(', ')}_\n\n`
            : ''

          const liaResponse: LIAChatMessage = {
            id: `lia-response-${Date.now()}`,
            type: 'lia',
            content: agentInfo + response.content,
            timestamp: new Date(),
            metadata: {
              action_executed: response.action_executed,
              action_result: response.action_result as Record<string, unknown> | undefined,
              action_type: response.action_type,
              needs_confirmation: response.needs_confirmation,
              needs_params: response.needs_params,
              pending_action_id: response.pending_action_id,
              conversation_id: response.conversation_id
            }
          }
          setChatMessages(prev => [...prev, liaResponse])

          if (response.suggested_prompts && response.suggested_prompts.length > 0) {
            const suggestionsMessage: LIAChatMessage = {
              id: `lia-suggestions-${Date.now()}`,
              type: 'lia',
              content: `💡 **Sugestões:**\n${response.suggested_prompts.slice(0, 3).map(p => `• ${p}`).join('\n')}`,
              timestamp: new Date()
            }
            setTimeout(() => {
              setChatMessages(prev => [...prev, suggestionsMessage])
            }, 500)
          }
        } else {
          throw new Error('Orchestrator returned unsuccessful response')
        }
      } catch (error) {

        const fallbackContent = isConversationalMessage(trimmedMessage)
          ? `Olá! Sou a LIA, sua assistente de recrutamento. Aqui no Funil de Talentos posso ajudá-lo a:\n\n🔍 **Buscar candidatos** — descreva o perfil desejado\n📊 **Analisar candidatos** — selecione e peça análise\n⚖️ **Comparar perfis** — selecione candidatos e peça comparação\n\nComo posso ajudar?`
          : `Entendi sua pergunta! Posso ajudá-lo a:\n\n🔍 **Buscar candidatos** - descreva o perfil desejado\n📊 **Analisar candidatos** - selecione e peça análise\n📋 **Criar vagas** - diga "criar nova vaga"\n⚖️ **Comparar perfis** - selecione candidatos e peça comparação\n\nComo posso ajudar?`

        const fallbackResponse: LIAChatMessage = {
          id: `lia-response-${Date.now()}`,
          type: 'lia',
          content: fallbackContent,
          timestamp: new Date()
        }
        setChatMessages(prev => [...prev, fallbackResponse])
      } finally {
        setIsLIAThinking(false)
      }
      return
    }

    // Se é uma busca de candidatos, executar normalmente (executeSearch já gerencia seu próprio loading)
    executeSearch(trimmedMessage)
  }

  const handleAICommand = async (command: string) => {
    const trimmedCommand = command.trim().toLowerCase()

    // Adicionar mensagem do usuário ao chat
    const userMessage: LIAChatMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: command,
      timestamp: new Date()
    }
    setChatMessages(prev => [...prev, userMessage])

    // Ativar estado de "pensando"
    setIsLIAThinking(true)

    try {
      // Determinar tipo de comando e processar
      let liaResponse: LIAChatMessage

      // Comandos de resumo de busca
      if (trimmedCommand.includes('resumir') && (trimmedCommand.includes('busca') || trimmedCommand.includes('resultado'))) {
        const totalCandidates = candidates.length

        if (totalCandidates === 0) {
          liaResponse = {
            id: `lia-${Date.now()}`,
            type: 'lia',
            content: `📊 **Resumo da Busca**\n\nNenhum candidato encontrado ainda.\n\n💡 *Faça uma busca digitando o perfil desejado acima, como "Desenvolvedor Python Sênior".*`,
            timestamp: new Date()
          }
        } else {
          const localCount = candidates.filter(c => c.source === 'local' || !c.source).length
          const avgScore = Math.round(candidates.reduce((acc, c) => acc + (c.score || 0), 0) / totalCandidates)
          const topSkills = candidates.flatMap(c => c.skills || c.technical_skills || []).reduce((acc, skill) => {
            if (skill && typeof skill === 'string') {
              acc[skill] = (acc[skill] || 0) + 1
            }
            return acc
          }, {} as Record<string, number>)
          const sortedSkills = Object.entries(topSkills).sort((a, b) => b[1] - a[1]).slice(0, 5)
          const locations = [...new Set(candidates.map(c => c.location || c.location_city).filter(Boolean))]

          const skillsText = sortedSkills.length > 0
            ? sortedSkills.map(([skill, count]) => `• ${skill} (${count})`).join('\n')
            : '• Nenhuma skill identificada nos perfis'
          const locationsText = locations.length > 0
            ? `${locations.slice(0, 3).join(', ')}${locations.length > 3 ? ` e mais ${locations.length - 3}` : ''}`
            : 'Não especificadas'

          liaResponse = {
            id: `lia-${Date.now()}`,
            type: 'lia',
            content: `📊 **Resumo da Busca**\n\nEncontrei **${totalCandidates} candidato${totalCandidates !== 1 ? 's' : ''}** (${localCount} da base local).\n\n**Score médio de compatibilidade:** ${formatScorePercent(avgScore)}\n\n**Top skills mais comuns:**\n${skillsText}\n\n**Localizações:** ${locationsText}\n\n💡 *Posso analisar candidatos específicos ou comparar os selecionados.*`,
            timestamp: new Date()
          }
        }
      }
      // Comando Top 5 candidatos
      else if (trimmedCommand.includes('top 5') || trimmedCommand.includes('top5') || trimmedCommand.includes('melhores candidatos')) {
        if (candidates.length === 0) {
          liaResponse = {
            id: `lia-${Date.now()}`,
            type: 'lia',
            content: `🏆 **Top Candidatos**\n\nNenhum candidato disponível ainda.\n\n💡 *Faça uma busca para encontrar candidatos.*`,
            timestamp: new Date()
          }
        } else {
          const topCandidates = [...candidates].sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, 5)
          const topCount = topCandidates.length
          const topList = topCandidates.map((c, i) => {
            const candidateSkills = c.skills || c.technical_skills || []
            const skillsPreview = candidateSkills.length > 0
              ? ` | Skills: ${candidateSkills.slice(0, 3).join(', ')}${candidateSkills.length > 3 ? '...' : ''}`
              : ''
            return `${i + 1}. **${c.name}** - ${c.position || c.current_title || 'N/A'} @ ${c.current_company || 'N/A'} (Score: ${formatScorePercent(c.score || 0)})${skillsPreview}`
          }).join('\n')

          liaResponse = {
            id: `lia-${Date.now()}`,
            type: 'lia',
            content: `🏆 **Top ${topCount} Candidatos**\n\n${topList}\n\n💡 *Selecione candidatos para análise mais detalhada ou comparação.*`,
            timestamp: new Date()
          }
        }
      }
      // Comando Comparar selecionados
      else if (trimmedCommand.includes('comparar') && (trimmedCommand.includes('selecionado') || selectedCandidatesForBatch.size >= 2)) {
        if (selectedCandidatesForBatch.size < 2) {
          liaResponse = {
            id: `lia-${Date.now()}`,
            type: 'lia',
            content: `⚠️ **Selecione pelo menos 2 candidatos** para fazer a comparação.\n\nClique na checkbox ao lado de cada candidato na tabela.`,
            timestamp: new Date()
          }
        } else {
          const selectedCandidates = candidates.filter(c => selectedCandidatesForBatch.has(c.id))
          if (selectedCandidates.length === 0) {
            liaResponse = {
              id: `lia-${Date.now()}`,
              type: 'lia',
              content: `⚠️ **Candidatos não encontrados**\n\nOs candidatos selecionados não foram localizados. Tente fazer uma nova busca.`,
              timestamp: new Date()
            }
          } else {
            const comparison = selectedCandidates.map(c => {
              const candidateSkills = c.skills || c.technical_skills || []
              const skillsText = candidateSkills.length > 0
                ? candidateSkills.slice(0, 5).join(', ')
                : 'Não informadas'
              const expYears = c.experience ?? c.years_of_experience
              const experienceText = typeof expYears === 'number'
                ? `${expYears} ${expYears === 1 ? 'ano' : 'anos'}`
                : 'Não informado'
              return `**${c.name}**\n• Cargo: ${c.position || c.current_title || 'Não informado'}\n• Empresa: ${c.current_company || 'Não informada'}\n• Experiência: ${experienceText}\n• Score: ${formatScorePercent(c.score || 0)}\n• Skills: ${skillsText}`
            }).join('\n\n')

            liaResponse = {
              id: `lia-${Date.now()}`,
              type: 'lia',
              content: `⚖️ **Comparação de ${selectedCandidates.length} Candidatos**\n\n${comparison}\n\n💡 *Clique no score CV de cada candidato na tabela para ver a análise detalhada.*`,
              timestamp: new Date()
            }
          }
        }
      }
      // Comandos de análise de candidato específico
      else if (
        trimmedCommand.includes('analisar potencial') ||
        trimmedCommand.includes('potencial de crescimento') ||
        trimmedCommand.includes('definir tipo') ||
        trimmedCommand.includes('tipo de perfil') ||
        trimmedCommand.includes('resumo executivo') ||
        trimmedCommand.includes('pontos a desenvolver') ||
        trimmedCommand.includes('vagas ideais')
      ) {
        if (selectedCandidatesForBatch.size === 0) {
          liaResponse = {
            id: `lia-${Date.now()}`,
            type: 'lia',
            content: `⚠️ **Nenhum candidato selecionado**\n\nSelecione um ou mais candidatos na tabela para que eu possa analisar.\n\n💡 Clique na checkbox ao lado do nome do candidato.`,
            timestamp: new Date()
          }
        } else {
          const selectedCandidates = candidates.filter(c => selectedCandidatesForBatch.has(c.id))

          if (selectedCandidates.length === 0) {
            liaResponse = {
              id: `lia-${Date.now()}`,
              type: 'lia',
              content: `⚠️ **Candidatos não encontrados**\n\nOs candidatos selecionados não foram localizados. Tente fazer uma nova busca.`,
              timestamp: new Date()
            }
          } else {
            // Chamar API de análise
            try {
              const candidatesForApi = selectedCandidates.map(c => ({
                id: c.id,
                name: c.name,
                position: c.position || c.current_title || 'Profissional',
                location: c.location || c.location_city || 'Não especificada',
                company: c.current_company || 'Não especificada',
                skills: c.skills || c.technical_skills || [],
                experience_years: c.experience || c.years_of_experience || 0,
                seniority_level: c.seniority_level || 'pleno',
                cv_text: c.resume_text || c.self_introduction || ''
              }))

              // Determinar job_title com fallbacks - garantir que nunca é vazio
              let jobTitleForApi = 'Análise de perfil profissional'
              const queryText = searchResults?.query?.trim()
              const firstPosition = selectedCandidates[0]?.position?.trim() || selectedCandidates[0]?.current_title?.trim()
              if (queryText && queryText.length > 0) {
                jobTitleForApi = queryText
              } else if (firstPosition && firstPosition.length > 0) {
                jobTitleForApi = firstPosition
              }

              const response = await fetch('/api/lia/api/v1/analysis/candidates', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  candidates: candidatesForApi,
                  analysis_type: 'general',
                  job_title: jobTitleForApi
                })
              })

              if (!response.ok) {
                const errorText = await response.text().catch(() => 'Erro desconhecido')

                // Mostrar erro específico ao usuário antes do fallback
                let userErrorMessage = ''
                if (response.status === 422) {
                  userErrorMessage = 'Dados do candidato inválidos ou incompletos.'
                } else if (response.status === 401 || response.status === 403) {
                  userErrorMessage = 'Não autorizado. Verifique suas credenciais.'
                } else if (response.status >= 500) {
                  userErrorMessage = 'Serviço de análise temporariamente indisponível.'
                } else {
                  userErrorMessage = `Erro ${response.status}: ${errorText.substring(0, 80)}`
                }

                throw new Error(userErrorMessage)
              }

              const data = await response.json()
              const results = data.results || []

              if (results.length === 0) {
                liaResponse = {
                  id: `lia-${Date.now()}`,
                  type: 'lia',
                  content: `🧠 **Análise LIA**\n\nNenhum resultado de análise gerado para os candidatos selecionados.\n\n**Possíveis causas:**\n• Perfis com informações insuficientes\n• Erro temporário no serviço de análise\n\n💡 *Tente selecionar candidatos com perfis mais completos.*`,
                  timestamp: new Date()
                }
              } else {
                let analysisContent = `🧠 **Análise LIA**\n\n`

                for (const result of results) {
                  analysisContent += `**${result.candidate_name || 'Candidato'}**\n`
                  analysisContent += `• **Arquétipo:** ${result.archetype || 'Executor Confiável'}\n`
                  analysisContent += `• **Score LIA:** ${formatScorePercent(result.lia_score || 0)}\n`
                  analysisContent += `• **Fit de Personalidade:** ${formatScorePercent(result.fit_score || 0)}\n`

                  if (result.strengths?.length > 0) {
                    analysisContent += `• **Pontos fortes:** ${result.strengths.slice(0, 3).join(', ')}\n`
                  }
                  if (result.gaps?.length > 0) {
                    analysisContent += `• **Pontos a desenvolver:** ${result.gaps.slice(0, 2).join(', ')}\n`
                  }
                  if (result.recommendation) {
                    analysisContent += `• **Recomendação:** ${result.recommendation}\n`
                  }
                  if (result.potential_roles?.length > 0) {
                    analysisContent += `• **Vagas ideais:** ${result.potential_roles.slice(0, 3).join(', ')}\n`
                  }
                  analysisContent += `\n`
                }

                liaResponse = {
                  id: `lia-${Date.now()}`,
                  type: 'lia',
                  content: analysisContent,
                  timestamp: new Date()
                }
              }
            } catch (apiError) {
              // Extrair mensagem de erro legível
              const errorMessage = apiError instanceof Error ? apiError.message : 'Erro desconhecido'

              // Fallback com análise local simplificada
              const selectedCandidate = selectedCandidates[0]
              const candidateSkills = selectedCandidate.skills || selectedCandidate.technical_skills || []
              const skillsText = candidateSkills.length > 0
                ? candidateSkills.slice(0, 5).join(', ')
                : 'Não informadas'
              const expYears = selectedCandidate.experience ?? selectedCandidate.years_of_experience
              const experienceText = typeof expYears === 'number'
                ? `${expYears} ${expYears === 1 ? 'ano' : 'anos'}`
                : 'Não informada'

              liaResponse = {
                id: `lia-${Date.now()}`,
                type: 'lia',
                content: `🧠 **Análise de ${selectedCandidate.name}** (modo offline)\n\n**⚠️ Motivo:** ${errorMessage}\n\n**Perfil:** ${selectedCandidate.position || selectedCandidate.current_title || 'Profissional'}\n**Empresa:** ${selectedCandidate.current_company || 'Não informada'}\n**Experiência:** ${experienceText}\n**Skills:** ${skillsText}\n\n**Arquétipo sugerido:** Executor Confiável\n**Potencial:** Alto para funções técnicas\n\n💡 *Esta é uma análise simplificada. Tente novamente mais tarde para análise completa com IA.*`,
                timestamp: new Date()
              }
            }
          }
        }
      }
      // Análises de busca - perguntas sobre os resultados
      else if (trimmedCommand.includes('quantos candidatos') || trimmedCommand.includes('quantos encontrei')) {
        liaResponse = {
          id: `lia-${Date.now()}`,
          type: 'lia',
          content: candidates.length === 0
            ? `📊 **Nenhum candidato encontrado** ainda.\n\n💡 *Faça uma busca para ver resultados.*`
            : `📊 **Total de candidatos:** ${candidates.length}\n\n• Base local: ${candidates.filter(c => c.source === 'local' || !c.source).length}\n• Base global: ${candidates.filter(c => c.source === 'global' || c.source === 'pearch').length}\n\n💡 *Selecione candidatos para análise detalhada.*`,
          timestamp: new Date()
        }
      }
      else if (trimmedCommand.includes('score') && (trimmedCommand.includes('médio') || trimmedCommand.includes('media') || trimmedCommand.includes('lia'))) {
        const avgScore = candidates.length > 0 ? Math.round(candidates.reduce((acc, c) => acc + (c.score || c.lia_score || 0), 0) / candidates.length) : 0
        const highScoreCount = candidates.filter(c => (c.score || c.lia_score || 0) >= 70).length
        liaResponse = {
          id: `lia-${Date.now()}`,
          type: 'lia',
          content: candidates.length === 0
            ? `📊 **Nenhum candidato** para calcular score médio.\n\n💡 *Faça uma busca primeiro.*`
            : `📊 **Score LIA médio:** ${formatScorePercent(avgScore)}\n\n• Candidatos com score ≥70%: **${highScoreCount}** (${Math.round(highScoreCount/candidates.length*100)}%)\n• Score máximo: ${formatScorePercent(Math.max(...candidates.map(c => c.score || c.lia_score || 0)))}\n• Score mínimo: ${formatScorePercent(Math.min(...candidates.map(c => c.score || c.lia_score || 0)))}\n\n💡 *Os candidatos de maior score geralmente têm melhor fit com a vaga.*`,
          timestamp: new Date()
        }
      }
      else if (trimmedCommand.includes('skills') && (trimmedCommand.includes('comuns') || trimmedCommand.includes('mais'))) {
        const allSkills = candidates.flatMap(c => c.skills || c.technical_skills || [])
        const skillCounts = allSkills.reduce((acc, skill) => {
          if (skill && typeof skill === 'string') acc[skill] = (acc[skill] || 0) + 1
          return acc
        }, {} as Record<string, number>)
        const topSkills = Object.entries(skillCounts).sort((a, b) => b[1] - a[1]).slice(0, 10)
        liaResponse = {
          id: `lia-${Date.now()}`,
          type: 'lia',
          content: topSkills.length === 0
            ? `📊 **Nenhuma skill identificada** nos perfis.\n\n💡 *Os candidatos podem não ter skills cadastradas.*`
            : `📊 **Top Skills mais comuns:**\n\n${topSkills.map(([skill, count], i) => `${i+1}. **${skill}** - ${count} candidato${count > 1 ? 's' : ''}`).join('\n')}\n\n💡 *Use essas skills como filtro para refinar sua busca.*`,
          timestamp: new Date()
        }
      }
      else if (trimmedCommand.includes('experiência') && trimmedCommand.includes('média')) {
        const withExp = candidates.filter(c => typeof (c.experience ?? c.years_of_experience) === 'number')
        const avgExp = withExp.length > 0 ? (withExp.reduce((acc, c) => acc + (c.experience ?? c.years_of_experience ?? 0), 0) / withExp.length).toFixed(1) : 0
        liaResponse = {
          id: `lia-${Date.now()}`,
          type: 'lia',
          content: withExp.length === 0
            ? `📊 **Experiência não informada** nos perfis.\n\n💡 *Os candidatos podem não ter anos de experiência cadastrados.*`
            : `📊 **Experiência média:** ${avgExp} anos\n\n• Candidatos com experiência informada: ${withExp.length}/${candidates.length}\n• Mais experiente: ${Math.max(...withExp.map(c => c.experience ?? c.years_of_experience ?? 0))} anos\n• Menos experiente: ${Math.min(...withExp.map(c => c.experience ?? c.years_of_experience ?? 0))} anos\n\n💡 *Filtrar por experiência pode refinar seus resultados.*`,
          timestamp: new Date()
        }
      }
      else if (trimmedCommand.includes('onde estão') || trimmedCommand.includes('localizados') || trimmedCommand.includes('localização')) {
        const locations = candidates.map(c => c.location || c.location_city || c.location_state).filter(Boolean)
        const locationCounts = locations.reduce((acc, loc) => {
          acc[loc as string] = (acc[loc as string] || 0) + 1
          return acc
        }, {} as Record<string, number>)
        const topLocations = Object.entries(locationCounts).sort((a, b) => b[1] - a[1]).slice(0, 8)
        liaResponse = {
          id: `lia-${Date.now()}`,
          type: 'lia',
          content: topLocations.length === 0
            ? `📍 **Localização não informada** nos perfis.\n\n💡 *Os candidatos podem não ter localização cadastrada.*`
            : `📍 **Distribuição por localização:**\n\n${topLocations.map(([loc, count]) => `• **${loc}**: ${count} candidato${count > 1 ? 's' : ''}`).join('\n')}\n\n💡 *${candidates.filter(c => c.is_remote).length} candidatos aceitam trabalho remoto.*`,
          timestamp: new Date()
        }
      }
      else if (trimmedCommand.includes('nota') && trimmedCommand.includes('acima')) {
        const threshold = 70
        const aboveCount = candidates.filter(c => (c.score || c.lia_score || 0) >= threshold).length
        liaResponse = {
          id: `lia-${Date.now()}`,
          type: 'lia',
          content: `📊 **Candidatos com nota LIA ≥${threshold}%:** ${aboveCount}\n\n• Total de candidatos: ${candidates.length}\n• Porcentagem qualificados: ${candidates.length > 0 ? Math.round(aboveCount/candidates.length*100) : 0}%\n\n💡 *Candidatos acima de 70% geralmente são bons matches.*`,
          timestamp: new Date()
        }
      }
      else if (trimmedCommand.includes('pontos fortes') && trimmedCommand.includes('comum')) {
        if (selectedCandidatesForBatch.size === 0) {
          liaResponse = { id: `lia-${Date.now()}`, type: 'lia', content: `⚠️ **Selecione candidatos** para analisar pontos fortes em comum.`, timestamp: new Date() }
        } else {
          const selected = candidates.filter(c => selectedCandidatesForBatch.has(c.id))
          const allSkills = selected.flatMap(c => c.skills || c.technical_skills || [])
          const skillCounts = allSkills.reduce((acc, s) => { if (s) acc[s] = (acc[s] || 0) + 1; return acc }, {} as Record<string, number>)
          const commonSkills = Object.entries(skillCounts).filter(([_, count]) => count >= Math.ceil(selected.length * 0.5)).map(([skill]) => skill)
          liaResponse = {
            id: `lia-${Date.now()}`,
            type: 'lia',
            content: commonSkills.length === 0
              ? `📊 **Nenhuma skill em comum** encontrada entre os ${selected.length} candidatos selecionados.`
              : `📊 **Pontos fortes em comum** (${selected.length} candidatos):\n\n${commonSkills.slice(0, 8).map(s => `• **${s}**`).join('\n')}\n\n💡 *Essas são as skills compartilhadas pela maioria.*`,
            timestamp: new Date()
          }
        }
      }
      else if (trimmedCommand.includes('gaps') || trimmedCommand.includes('competência')) {
        if (selectedCandidatesForBatch.size === 0) {
          liaResponse = { id: `lia-${Date.now()}`, type: 'lia', content: `⚠️ **Selecione candidatos** para identificar gaps de competência.`, timestamp: new Date() }
        } else {
          liaResponse = {
            id: `lia-${Date.now()}`,
            type: 'lia',
            content: `🔍 **Análise de Gaps**\n\nPara identificar gaps precisos, preciso conhecer os requisitos da vaga.\n\n💡 **Sugestão:** Selecione uma vaga no seletor acima para comparar candidatos com os requisitos específicos.`,
            timestamp: new Date()
          }
        }
      }
      else if (trimmedCommand.includes('prioridade') || trimmedCommand.includes('organize')) {
        const sorted = [...candidates].sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, 10)
        liaResponse = {
          id: `lia-${Date.now()}`,
          type: 'lia',
          content: sorted.length === 0
            ? `📊 **Nenhum candidato** para organizar.\n\n💡 *Faça uma busca primeiro.*`
            : `📊 **Candidatos por prioridade:**\n\n${sorted.map((c, i) => `${i+1}. **${c.name}** - Score: ${formatScorePercent(c.score || 0)} | ${c.position || c.current_title || 'N/A'}`).join('\n')}\n\n💡 *Ordenados por score de compatibilidade.*`,
          timestamp: new Date()
        }
      }
      else if (trimmedCommand.includes('melhorar') && trimmedCommand.includes('busca')) {
        liaResponse = {
          id: `lia-${Date.now()}`,
          type: 'lia',
          content: `💡 **Dicas para melhorar sua busca:**\n\n• Adicione **skills específicas** (ex: "Python, AWS")\n• Defina **nível de senioridade** (júnior, pleno, sênior)\n• Especifique **localização** (cidade ou "remoto")\n• Use **palavras-chave** do cargo desejado\n• Tente **termos alternativos** para a mesma função\n\n**Exemplo:** "Desenvolvedor Backend Python sênior São Paulo remoto"`,
          timestamp: new Date()
        }
      }
      else if (trimmedCommand.includes('resuma') && trimmedCommand.includes('perfil') && trimmedCommand.includes('selecionado')) {
        if (selectedCandidatesForBatch.size === 0) {
          liaResponse = { id: `lia-${Date.now()}`, type: 'lia', content: `⚠️ **Selecione candidatos** para resumir seus perfis.`, timestamp: new Date() }
        } else {
          const selected = candidates.filter(c => selectedCandidatesForBatch.has(c.id))
          const summary = selected.map(c => `**${c.name}**\n${c.position || c.current_title || 'Profissional'} @ ${c.current_company || 'N/A'}`).join('\n\n')
          liaResponse = {
            id: `lia-${Date.now()}`,
            type: 'lia',
            content: `📋 **Resumo dos perfis selecionados:**\n\n${summary}\n\n💡 *Para análise detalhada, use "Analisar potencial de crescimento".*`,
            timestamp: new Date()
          }
        }
      }
      // Comando não reconhecido - resposta amigável com orientação
      else {
        liaResponse = {
          id: `lia-${Date.now()}`,
          type: 'lia',
          content: `🤔 Entendi sua solicitação, mas **ainda não consigo responder a esse tipo de pergunta**.\n\nEstou em constante evolução e **em breve serei capaz** de atender você em diversas situações e demandas do seu dia a dia como recrutador!\n\n**Por enquanto, posso ajudar você com:**\n\n📊 **Análises de busca:**\n• Resumir esta busca\n• Top 5 candidatos\n• Skills mais comuns\n• Score médio dos candidatos\n\n👥 **Análise de candidatos selecionados:**\n• Analisar potencial de crescimento\n• Comparar candidatos\n• Pontos fortes em comum\n• Definir tipo de perfil\n\n💡 *Clique em "Mais ideias" para ver todas as opções disponíveis!*`,
          timestamp: new Date()
        }
      }

      setChatMessages(prev => [...prev, liaResponse])
    } catch (error) {
      const errorMessage: LIAChatMessage = {
        id: `lia-error-${Date.now()}`,
        type: 'lia',
        content: `❌ Ocorreu um erro ao processar sua solicitação. Por favor, tente novamente.`,
        timestamp: new Date()
      }
      setChatMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLIAThinking(false)
    }
  }

  return {
    handleQuickAction,
    handleOrchestratedTalentMessage,
    handleTalentUIAction,
    handleCalibrationLike,
    handleCalibrationDislike,
    handleLIAChatMessage,
    handleAICommand,
    isConversationalMessage,
    isGenericQuestion,
  }
}
