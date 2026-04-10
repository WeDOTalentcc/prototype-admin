"use client"

import type { TechnicalSkillSuggestion, BehavioralCompetencySuggestion } from "@/components/job-creation/competencies-chat-message"
import {
  orchestrateWizardMessage,
  orchestratorProcess,
  liaApi,
} from "@/services/lia-api"
import type { Message } from "../types"
import type { SendMessageHandlersContext } from './useSendMessageHandlers'
import type { ToolCall } from "./useToolCalling"
import {
  INITIAL_JOB_CREATION_MESSAGE,
} from "../index"

interface EvaluationStepResult {
  compensation_analysis?: unknown
  technical_skills?: Array<{
    name?: string
    level?: string
    weight?: number
    weight_justification?: string
    source?: string
    required?: boolean
    category?: string
  }>
  behavioral_competencies?: Array<{
    name?: string
    weight?: number
    justification?: string
    weight_justification?: string
    source?: string
  }>
  [key: string]: unknown
}

export function useSendMessageAPIDispatchers(ctx: SendMessageHandlersContext) {
  const {
    messages,
    setMessages,
    setIsLoading,
    conversationId,
    setConversationId,
    user,
    resolvedCompanyId,
    currentStage,
    setCurrentStage,
    isInJobCreationMode,
    onOrchestratedMessage,
    basicInfoFields,
    detectedCriteria,
    technicalSkills,
    behavioralCompetencies,
    setCompensationAnalysis,
    setCompetencySuggestions,
    setInternalJobCreationMode,
    setDynamicInitialMessage,
    setDisplayedText,
    buildCollectedData,
    processOrchestratorResponse,
    extractCriteriaFromText,
    typeText,
    generateLLMContext,
    generateCriteriaResponse,
    callEvaluationStep,
    contextSwitching,
    conversationMemory,
    toolCalling,
    setActiveToolConfirmationMessageId,
  } = ctx

  const _handleWizardAPICall = async (content: string, processingMessageId: string): Promise<void> => {
    setIsLoading(true)

    try {
      setTimeout(() => {
        setMessages(msgs => msgs.map(m =>
          m.id === processingMessageId
            ? { ...m, content: 'Analisando...', processingState: 'analyzing' as const }
            : m
        ))
      }, 300)

      const collectedData = buildCollectedData()
      const conversationHistory = messages.slice(-10).map(m => ({ role: m.role, content: m.content }))
      const panelChangesContext = generateLLMContext()
      const enhancedMessage = panelChangesContext ? `${content}\n\n${panelChangesContext}` : content

      if (conversationMemory.conversationId) {
        conversationMemory.addMessage('user', content).catch((err) => { console.warn('[useSendMessageAPIDispatchers] addMessage(user) fire-and-forget failed', err) })
      }

      const orchestratorResult = await orchestrateWizardMessage({
        message: enhancedMessage,
        current_stage: currentStage,
        collected_data: collectedData,
        conversation_history: conversationHistory,
        conversation_id: conversationMemory.conversationId || undefined,
        company_id: resolvedCompanyId ?? undefined,
        user_id: user?.email || undefined
      })

      await processOrchestratorResponse(orchestratorResult, processingMessageId)
      setIsLoading(false)

      if (currentStage === 'input-evaluation' && orchestratorResult.confidence >= 0.7) {
        const evaluationContext = {
          job_title: basicInfoFields.cargo || detectedCriteria.cargo || undefined,
          seniority: detectedCriteria.senioridadeIdiomas || undefined,
          department: basicInfoFields.area || detectedCriteria.departamento || undefined,
          location: basicInfoFields.localidade || detectedCriteria.localizacao || undefined,
          work_model: basicInfoFields.modeloTrabalho || detectedCriteria.modeloTrabalho || undefined,
          technical_skills: technicalSkills.filter(s => s.required).map(s => s.name),
          behavioral_skills: behavioralCompetencies.filter(c => c.enabled).map(c => c.name),
        }
        callEvaluationStep(content, evaluationContext).then((evalResult) => {
          if (evalResult?.compensation_analysis) setCompensationAnalysis(evalResult.compensation_analysis)
          const suggestions = evalResult?.suggestions as EvaluationStepResult | undefined
          if (suggestions?.technical_skills || suggestions?.behavioral_competencies) {
            const technicalSuggestions: TechnicalSkillSuggestion[] = (suggestions.technical_skills || []).map((skill) => ({
              name: skill.name || '', level: (skill.level as TechnicalSkillSuggestion['level']) || 'Intermediário', weight: skill.weight || 3,
              weightJustification: skill.weight_justification || 'Baseado em análise de mercado',
              source: (skill.source as TechnicalSkillSuggestion['source']) || 'market_benchmark', required: skill.required ?? true, category: (skill.category as TechnicalSkillSuggestion['category']) || 'tool'
            }))
            const behavioralSuggestions: BehavioralCompetencySuggestion[] = (suggestions.behavioral_competencies || []).map((comp) => ({
              name: comp.name || '', weight: comp.weight || 3, justification: comp.justification || '',
              weightJustification: comp.weight_justification || 'Baseado em histórico da empresa', source: (comp.source as BehavioralCompetencySuggestion['source']) || 'company_history'
            }))
            if (technicalSuggestions.length > 0 || behavioralSuggestions.length > 0) {
              setCompetencySuggestions({ technicalSkills: technicalSuggestions, behavioralCompetencies: behavioralSuggestions })
              setTimeout(() => {
                const competenciesMessage: Message = {
                  id: `lia-competencies-${Date.now()}`,
                  role: 'assistant',
                  content: '',
                  timestamp: new Date(),
                  messageType: 'competencies',
                  competenciesSuggestions: { technicalSkills: technicalSuggestions, behavioralCompetencies: behavioralSuggestions }
                }
                setMessages(prev => [...prev, competenciesMessage])
              }, 1000)
            }
          }
        }).catch((err) => { console.warn('[useSendMessageAPIDispatchers] callEvaluationStep fire-and-forget failed', err) })
      }
    } catch (error) {
      const newCriteria = extractCriteriaFromText(content)
      const fallbackText = generateCriteriaResponse(newCriteria)
      const fallbackFieldsData: Array<{ label: string; value: string; confidence?: "high" | "medium" | "low" }> = []
      if (newCriteria.cargo) fallbackFieldsData.push({ label: "Cargo", value: newCriteria.cargo, confidence: "high" })
      if (newCriteria.senioridadeIdiomas) fallbackFieldsData.push({ label: "Senioridade", value: newCriteria.senioridadeIdiomas, confidence: "medium" })
      if (newCriteria.modeloTrabalho) fallbackFieldsData.push({ label: "Modelo", value: newCriteria.modeloTrabalho, confidence: "medium" })
      if (newCriteria.localizacao) fallbackFieldsData.push({ label: "Localização", value: newCriteria.localizacao, confidence: "medium" })
      if (newCriteria.competenciasTecnicas?.length > 0) fallbackFieldsData.push({ label: "Skills Técnicas", value: newCriteria.competenciasTecnicas.slice(0, 5).join(", "), confidence: "medium" })
      if (newCriteria.tipoContrato) fallbackFieldsData.push({ label: "Contrato", value: newCriteria.tipoContrato, confidence: "low" })
      setMessages(msgs => msgs.filter(m => m.id !== processingMessageId))
      const fallbackMessage: Message = {
        id: `fallback-${Date.now()}`,
        role: 'assistant',
        content: fallbackText,
        timestamp: new Date(),
        isTyping: true,
        detectedFieldsData: fallbackFieldsData.length > 0 ? fallbackFieldsData : undefined
      }
      setMessages(msgs => [...msgs, fallbackMessage])
      setDisplayedText("")
      setTimeout(() => { typeText(fallbackText, fallbackMessage.id) }, 300)
      setIsLoading(false)
    }
  }

  const _handleGeneralAPICall = async (content: string, _processingMessageId: string): Promise<void> => {
    setIsLoading(true)
    try {
      let responseText = "Entendi! Estou processando as informações..."

      if (onOrchestratedMessage) {
        const orchestratedResponse = await onOrchestratedMessage(content.trim())
        responseText = orchestratedResponse.content
        if (orchestratedResponse.ui_action === 'start_job_wizard') {
          setInternalJobCreationMode(true)
          setCurrentStage('input-evaluation')
          if (orchestratedResponse.ui_action_params?.['initial_message']) {
            setDynamicInitialMessage(INITIAL_JOB_CREATION_MESSAGE)
          }
        }
      } else {
        if (!conversationMemory.conversationId && user?.email) {
          await conversationMemory.initConversation(user.email, 'general')
        }
        const conversationContext = await conversationMemory.getContext()
        if (conversationMemory.conversationId) {
          conversationMemory.addMessage('user', content.trim()).catch((err) => { console.warn('[useSendMessageAPIDispatchers] addMessage(user/general) fire-and-forget failed', err) })
        }
        const orchestratorResponse = await orchestratorProcess({
          user_id: user?.email || 'demo-user',
          message: content.trim(),
          conversation_id: conversationMemory.conversationId || conversationId || undefined,
          context_type: 'general',
          context_id: conversationMemory.conversationId || undefined,
          conversation_context: conversationContext || undefined,
        })

        if (orchestratorResponse.success) {
          if (orchestratorResponse.conversation_id && !conversationId) {
            setConversationId(orchestratorResponse.conversation_id)
          }
          responseText = String(orchestratorResponse.message || orchestratorResponse.result?.message || responseText)
          if (conversationMemory.conversationId) {
            conversationMemory.addMessage('assistant', responseText, orchestratorResponse.intent).catch((err) => { console.warn('[useSendMessageAPIDispatchers] addMessage(assistant) fire-and-forget failed', err) })
          }
          const suggestedToolCall = orchestratorResponse.suggested_tool_call || orchestratorResponse.result?.suggested_tool_call
          if (suggestedToolCall) {
            const stc = suggestedToolCall as Record<string, unknown>
            const toolCall: ToolCall = {
              tool_name: String(stc.tool_name),
              parameters: (stc.parameters || {}) as Record<string, unknown>,
              requires_confirmation: stc.requires_confirmation !== false,
              confirmation_message: String(stc.confirmation_message || responseText),
            }
            if (toolCall.requires_confirmation) {
              toolCalling.suggestToolCall(toolCall)
              const confirmationMessageId = `tool-confirm-${Date.now()}`
              setActiveToolConfirmationMessageId(confirmationMessageId)
              const confirmationMessage: Message = {
                id: confirmationMessageId,
                role: 'assistant',
                content: responseText,
                timestamp: new Date(),
                messageType: 'tool-confirmation',
                toolCall: toolCall,
              }
              setMessages(prev => [...prev, confirmationMessage])
              setIsLoading(false)
              return
            } else {
              setIsLoading(true)
              try {
                const result = await toolCalling.executeToolDirectly(toolCall.tool_name, toolCall.parameters)
                const feedbackMessage: Message = {
                  id: `tool-feedback-${Date.now()}`,
                  role: 'assistant',
                  content: result.success ? `✅ ${result.message}` : `❌ ${result.error || result.message}`,
                  timestamp: new Date(),
                  messageType: 'tool-execution-feedback',
                  toolExecutionResult: result,
                }
                setMessages(prev => [...prev, feedbackMessage])
                setIsLoading(false)
                return
              } catch (error) {
              }
            }
          }
        } else {
          const response = await liaApi.sendMessage({
            content: content.trim(),
            conversation_id: conversationId || undefined,
            user_id: 'demo-user'
          })
          if (response.conversation?.id && !conversationId) setConversationId(response.conversation.id)
          responseText = response.message?.content || responseText
        }
      }

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: responseText,
        timestamp: new Date(),
        isTyping: true
      }
      setMessages(prev => [...prev, assistantMessage])
      setDisplayedText("")
      setTimeout(() => { typeText(responseText, assistantMessage.id) }, 300)

    } catch (error) {
      extractCriteriaFromText(content)
      const errorText = "Entendi as informações! Detectei alguns critérios da vaga. Continue adicionando mais detalhes ou avance para a próxima etapa."
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: errorText,
        timestamp: new Date(),
        isTyping: true
      }
      setMessages(prev => [...prev, errorMessage])
      setDisplayedText("")
      setTimeout(() => { typeText(errorText, errorMessage.id) }, 300)
    } finally {
      setIsLoading(false)
    }
  }

  return {
    _handleWizardAPICall,
    _handleGeneralAPICall,
  }
}
