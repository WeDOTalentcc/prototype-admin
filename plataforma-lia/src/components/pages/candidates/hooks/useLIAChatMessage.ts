"use client"

import React from "react"
import { callOrchestratedTalentChat, type OrchestratedTalentChatResponse } from "@/lib/api/kanban-assistant"
import { isConversationalMessage, isGenericQuestion } from "./liaMessageUtils"
import type { Candidate } from "../types"
import type { LIAChatMessage, CandidatesLIAHandlersContext } from "./useCandidatesLIAHandlers"
import type { SearchFilters } from "@/components/search/advanced-filters-modal"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { useLiaChatContext } from "@/contexts/lia-float-context"
import { formatMessageTime } from "@/hooks/chat/lia-chat-connection-types"
import { useTranslations } from "next-intl"

type SearchTab = 'ia-natural' | 'similar' | 'job-description' | 'boolean' | 'arquetipos' | 'filtros'

export function useLIAChatMessage(
  ctx: CandidatesLIAHandlersContext,
  handleAICommand: (command: string) => void,
  handleTalentUIAction: (action: string, params?: Record<string, unknown>) => void,
) {
  const { companyId: resolvedCompanyId } = useCompanyId()
  const t = useTranslations('candidates.liaChatMessage')

  const {
    switchChatContext,
    sendOrchestratedMessage,
    addChatMessage,
  } = useLiaChatContext()

  const {
    candidates,
    setChatMessages,
    setLiaPromptValue,
    activeSearchTab,
    setActiveSearchTab,
    talentConversationId: localTalentConversationId,
    setTalentConversationId,
    selectedCandidatesForBatch,
    searchResults,
    activeSearchFilters,
    setIsLIAThinking,
    executeSearch,
    user,
  } = ctx

  const talentConversationId = localTalentConversationId

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
      const rawResponse = await sendOrchestratedMessage(
        message,
        async (convId) => {
          const result = await callOrchestratedTalentChat({
            message,
            candidates: candidatesForContext,
            selected_candidate_ids: selectedIds.length > 0 ? selectedIds : undefined,
            search_context: searchContextData,
            target_job: undefined,
            conversation_id: convId ?? undefined,
            company_id: resolvedCompanyId || '',
          })
          return result as unknown as { content: string; conversation_id?: string | null; [key: string]: unknown }
        },
        {
          extractResponseMetadata: (raw) => {
            const r = raw as unknown as OrchestratedTalentChatResponse
            return {
              intent: r.intent_detected,
              confidence: r.confidence,
              agent: r.agent_used,
              suggested_prompts: r.suggested_prompts,
              actions: r.actions,
              action_executed: r.action_executed,
              action_result: r.action_result,
              action_type: r.action_type,
              ui_action: r.ui_action,
              needs_confirmation: r.needs_confirmation,
              needs_params: r.needs_params,
              pending_action_id: r.pending_action_id,
              conversation_id: r.conversation_id,
            }
          },
        },
      )
      const response = rawResponse as unknown as OrchestratedTalentChatResponse

      if (response.conversation_id) {
        setTalentConversationId(response.conversation_id)
      }

      if (response.ui_action) {
        handleTalentUIAction(response.ui_action, response.ui_action_params)
      }

      if (response.action_executed && response.action_result) {
        const { toast } = await import("sonner")
        toast.success(t('actionExecuted'), { description: response.action_type ? `${response.action_type}` : undefined })
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
    // Ensure unified context is set to candidates before any send
    switchChatContext("talent_chat")

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

    setLiaPromptValue('')

    if (isConversationalMessage(trimmedMessage) || isGenericQuestion(trimmedMessage)) {
      setIsLIAThinking(true)

      try {
        const response = await handleOrchestratedTalentMessage(trimmedMessage)

        if (response.success) {
          if (response.suggested_prompts && response.suggested_prompts.length > 0) {
            setTimeout(() => {
              addChatMessage({
                id: `lia-suggestions-${Date.now()}`,
                sender: 'lia',
                content: `💡 **${t('suggestions')}:**\n${response.suggested_prompts.slice(0, 3).map(p => `• ${p}`).join('\n')}`,
                timestamp: formatMessageTime(),
              })
            }, 500)
          }
        } else {
          throw new Error('Orchestrator returned unsuccessful response')
        }
      } catch (error) {

        const fallbackContent = t('fallbackError')

        addChatMessage({
          id: `lia-response-${Date.now()}`,
          sender: 'lia',
          content: fallbackContent,
          timestamp: formatMessageTime(),
        })
      } finally {
        setIsLIAThinking(false)
      }
      return
    }

    addChatMessage({
      id: `user-search-${Date.now()}`,
      sender: 'user',
      content: trimmedMessage,
      timestamp: formatMessageTime(),
    })
    executeSearch(trimmedMessage)
  }

  return {
    handleOrchestratedTalentMessage,
    handleLIAChatMessage,
  }
}
