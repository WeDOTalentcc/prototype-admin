"use client"

import React from "react"
import { callOrchestratedTalentChat, type OrchestratedTalentChatResponse } from "@/lib/api/kanban-assistant"
import { isConversationalMessage, isGenericQuestion } from "./liaMessageUtils"
import type { Candidate } from "../types"
import type { LIAChatMessage, CandidatesLIAHandlersContext } from "./useCandidatesLIAHandlers"
import type { SearchFilters } from "@/components/search/advanced-filters-modal"

type SearchTab = 'ia-natural' | 'similar' | 'job-description' | 'boolean' | 'arquetipos' | 'filtros'

export function useLIAChatMessage(
  ctx: CandidatesLIAHandlersContext,
  handleAICommand: (command: string) => void,
  handleTalentUIAction: (action: string, params?: Record<string, unknown>) => void,
) {
  const {
    candidates,
    setChatMessages,
    setLiaPromptValue,
    activeSearchTab,
    setActiveSearchTab,
    talentConversationId,
    setTalentConversationId,
    selectedCandidatesForBatch,
    searchResults,
    activeSearchFilters,
    setIsLIAThinking,
    executeSearch,
    user,
  } = ctx

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
        const { toast } = await import("sonner")
        toast.success("Ação executada", { description: response.action_type ? `${response.action_type}` : undefined })
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

  const handleLIAChatMessage = async (message: string) => {
    const trimmedMessage = message.trim()
    const normalizedMessage = trimmedMessage.toLowerCase()

    const analysisCommands = [
      'analisar potencial', 'potencial de crescimento', 'analise potencial',
      'definir tipo', 'tipo de perfil',
      'resumo executivo', 'resumir busca', 'resumir resultado',
      'pontos a desenvolver', 'pontos a serem desenvolvidos',
      'vagas ideais', 'tipos de vagas',
      'top 5', 'top5', 'melhores candidatos',
      'comparar', 'comparação'
    ]

    const isAnalysisCommand = analysisCommands.some(cmd => normalizedMessage.includes(cmd))

    if (isAnalysisCommand) {
      handleAICommand(trimmedMessage)
      setLiaPromptValue('')
      return
    }

    const userMessage: LIAChatMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: trimmedMessage,
      timestamp: new Date()
    }
    setChatMessages(prev => [...prev, userMessage])
    setLiaPromptValue('')

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

    executeSearch(trimmedMessage)
  }

  return {
    handleOrchestratedTalentMessage,
    handleLIAChatMessage,
  }
}
