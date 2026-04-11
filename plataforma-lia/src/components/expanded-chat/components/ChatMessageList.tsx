"use client"

/**
 * ChatMessageList — renderização da lista de mensagens do chat LIA.
 * Extraído de expanded-chat-modal.tsx (Sprint 4.3 — 2026-03-27).
 * Portabilidade Vue: props → defineProps; callbacks → emit.
 */

import React from "react"
import { CheckCircle2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { cleanAgentResponse, parseChatMarkdown } from "@/lib/chat-format"
import { ChatBubbleBase } from "@/components/chat/chat-bubble-base"
import { useAuthStore } from "@/stores/auth-store"
import { MessageFeedback } from "@/components/chat/message-feedback"
import { ParecerLIACard } from "@/components/chat/parecer-lia-card"
import { ActionResultCard } from "@/components/chat/action-result-card"
import { PlanProgressCard, type ExecutionPlanData } from "@/components/chat/plan-progress-card"
import { DetectedFieldsCard } from "@/components/chat/detected-fields-card"
import { CompetenciesChatMessage } from "@/components/job-creation/competencies-chat-message"
import { VacancySearchResults } from "@/components/job-creation/vacancy-search-results"
import { VacancyFullSummary } from "@/components/job-creation/vacancy-full-summary"
import { ToolConfirmationMessage } from "./tool-confirmation-message"
import { ToolExecutionFeedback } from "./tool-execution-feedback"
import { useExpandedChatContext, type TechnicalSkill, type BehavioralCompetency } from "../ExpandedChatContext"
import { formatTimestamp, formatSalaryAnalysisText } from "../utils/message-format-utils"
import type { Message, FastTrackState } from "../types"
import type { ToolExecutionResult } from "../hooks"
import { sanitizeHtml } from "@/lib/sanitize"

interface ChatMessageListProps {
  messages: Message[]
  isTypingEffect: boolean
  displayedText: string
  conversationId: string | null
  inputRef: React.RefObject<HTMLTextAreaElement>
  isSearchingVacancies: boolean
  onSetInputValue: (value: string) => void
  onSetMessages: React.Dispatch<React.SetStateAction<Message[]>>
  onSetIsLoading: (loading: boolean) => void
  onSetActiveToolConfirmationMessageId: (id: string | null) => void
  onSetFastTrackState: (state: FastTrackState) => void
  onSetCompetencySuggestions: (val: null) => void
  onFastTrackVacancySelect: (id: string) => void
  onProactiveAccept: (actionId: string, messageId: string) => void
  onProactiveReject: (actionId: string, messageId: string) => void
  toolCalling: {
    confirmToolCall: () => Promise<ToolExecutionResult>
    cancelToolCall: () => void
    rollbackLastTool: () => Promise<ToolExecutionResult | null>
    isExecuting: boolean
  }
}

export function ChatMessageList({
  messages,
  isTypingEffect,
  displayedText,
  conversationId,
  inputRef,
  isSearchingVacancies,
  onSetInputValue,
  onSetMessages,
  onSetIsLoading,
  onSetActiveToolConfirmationMessageId,
  onSetFastTrackState,
  onSetCompetencySuggestions,
  onFastTrackVacancySelect,
  onProactiveAccept,
  onProactiveReject,
  toolCalling,
}: ChatMessageListProps) {
  const {
    technicalSkills: currentTechnicalSkills,
    behavioralCompetencies: currentBehavioralCompetencies,
    addTechnicalSkill,
    addBehavioralCompetency,
    setCurrentStage,
  } = useExpandedChatContext()

  const authUser = useAuthStore((s) => s.user)
  const userDisplayName = authUser?.name || authUser?.email || "Usuário"

  function formatMessageContent(content: string, isCurrentlyTyping: boolean, messageId: string) {
    const isLastTypingMessage = isCurrentlyTyping && messages[messages.length - 1]?.id === messageId
    const textToShow = isLastTypingMessage && displayedText.length > 0 ? displayedText : content
    const cleaned = cleanAgentResponse(textToShow)
    const html = parseChatMarkdown(cleaned)
    return <div dangerouslySetInnerHTML={{ __html: sanitizeHtml(html) }} />
  }

  function renderFeedback(messageId: string, content: string) {
    return (
      <MessageFeedback
        sessionId={conversationId || 'default-session'}
        messageId={messageId}
        originalResponse={content}
        className="mt-2"
      />
    )
  }

  return (
    <div className="space-y-3" aria-atomic="false">
      {messages.map((message, index) => (
        <div
          key={message.id}
          data-testid="chat-message"
          data-role={message.role}
          className={cn(
            "flex animate-in fade-in-0 slide-in-from-bottom-2 duration-300",
            message.role === 'user' ? "justify-end" : "justify-start",
            message.role === 'system' && "justify-center"
          )}
          style={{animationDelay: `${Math.min(index * 50, 200)}ms`}}
        >
          {message.role === 'system' ? (
            <div className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-full",
              "bg-lia-bg-tertiary/80/60",
              "border border-lia-border-subtle/50/50",
              "max-w-[80%]"
            )}>
              <CheckCircle2 className="w-3 h-3 text-wedo-green flex-shrink-0" />
              <span className="text-micro text-lia-text-secondary font-['Inter',sans-serif]">
                {message.content}
              </span>
            </div>
          ) : message.role === 'user' ? (
            <ChatBubbleBase
              sender="user"
              timestamp={formatTimestamp(message.timestamp)}
              userName={userDisplayName}
            >
              <p className="text-xs text-lia-text-primary leading-relaxed">{message.content}</p>
            </ChatBubbleBase>
          ) : message.messageType === 'parecer-lia' && message.parecerData ? (
            <ChatBubbleBase
              sender="lia"
              timestamp={formatTimestamp(message.timestamp)}
              afterBubble={renderFeedback(message.id, message.content)}
              bubbleClassName="bg-transparent p-0"
            >
              <p className="text-xs text-lia-text-primary mb-3">{message.content}</p>
              <ParecerLIACard
                data={message.parecerData}
                onAcceptSuggestion={(suggestion) => {
                  onSetInputValue(suggestion)
                  if (inputRef?.current) inputRef.current.focus()
                }}
              />
            </ChatBubbleBase>
          ) : message.messageType === 'compensation' ? (
            <ChatBubbleBase
              sender="lia"
              timestamp={formatTimestamp(message.timestamp)}
              afterBubble={renderFeedback(message.id, message.content)}
            >
              <div className="text-xs text-lia-text-primary leading-relaxed whitespace-pre-wrap">
                {formatSalaryAnalysisText(message.compensationAnalysis || null)}
              </div>
            </ChatBubbleBase>
          ) : message.messageType === 'competencies' ? (
            <CompetenciesChatMessage
              technicalSkills={message.competenciesSuggestions?.technicalSkills || []}
              behavioralCompetencies={message.competenciesSuggestions?.behavioralCompetencies || []}
              isLoading={false}
              onAccept={() => {
                const suggestions = message.competenciesSuggestions
                if (suggestions) {
                  suggestions.technicalSkills.forEach(skill => {
                    if (currentTechnicalSkills.some(s => s.name.toLowerCase() === skill.name.toLowerCase())) return
                    const newSkill: TechnicalSkill = {
                      id: `tech-${Date.now()}-${Math.random()}`,
                      name: skill.name,
                      level: skill.level,
                      required: skill.required,
                      category: skill.category,
                      weight: skill.weight,
                      weightJustification: skill.weightJustification,
                      isWeightInferred: true,
                    }
                    addTechnicalSkill(newSkill)
                  })
                  suggestions.behavioralCompetencies.forEach(comp => {
                    if (currentBehavioralCompetencies.some(c => c.name.toLowerCase() === comp.name.toLowerCase())) return
                    const newComp: BehavioralCompetency = {
                      id: `behav-${Date.now()}-${Math.random()}`,
                      name: comp.name,
                      weight: comp.weight,
                      justification: comp.justification,
                      enabled: true,
                      weightJustification: comp.weightJustification,
                      isWeightInferred: true,
                    }
                    addBehavioralCompetency(newComp)
                  })
                  onSetMessages(prev => prev.filter(m => m.id !== message.id))
                  onSetCompetencySuggestions(null)
                  const confirmMessage: Message = {
                    id: `lia-confirm-${Date.now()}`,
                    role: 'assistant',
                    content: '✅ Competências adicionadas com sucesso! Você pode revisar e ajustar os pesos no painel da direita.',
                    timestamp: new Date(),
                  }
                  onSetMessages(prev => [...prev, confirmMessage])
                }
              }}
              onAdjust={() => {
                setCurrentStage('competencies')
                onSetMessages(prev => prev.filter(m => m.id !== message.id))
              }}
            />
          ) : message.messageType === 'vacancy-search' ? (
            <VacancySearchResults
              vacancies={message.vacancySearchResults || []}
              isLoading={isSearchingVacancies}
              onSelect={(vacancy) => {
                onSetFastTrackState('reviewing')
                const userSelectMessage: Message = {
                  id: `user-select-${Date.now()}`,
                  role: 'user',
                  content: `Quero usar a vaga "${vacancy.title}"`,
                  timestamp: new Date(),
                }
                onSetMessages(prev => [...prev, userSelectMessage])
                onFastTrackVacancySelect(vacancy.id)
              }}
            />
          ) : message.messageType === 'vacancy-summary' ? (
            <VacancyFullSummary
              vacancy={message.vacancyFullDetails || null}
              editableFields={['salary_range', 'location', 'work_model', 'benefits']}
              lockedFields={['technical_skills', 'behavioral_competencies', 'screening_questions']}
              isLoading={false}
            />
          ) : message.messageType === 'tool-confirmation' && message.toolCall ? (
            <ChatBubbleBase
              sender="lia"
              timestamp={formatTimestamp(message.timestamp)}
            >
              <ToolConfirmationMessage
                toolCall={message.toolCall}
                onConfirm={async () => {
                  onSetIsLoading(true)
                  try {
                    const result = await toolCalling.confirmToolCall()
                    const feedbackMessage: Message = {
                      id: `tool-feedback-${Date.now()}`,
                      role: 'assistant',
                      content: result.success ? `✅ ${result.message}` : `❌ ${result.error || result.message}`,
                      timestamp: new Date(),
                      messageType: 'tool-execution-feedback',
                      toolExecutionResult: result,
                    }
                    onSetMessages(prev => [...prev, feedbackMessage])
                    onSetActiveToolConfirmationMessageId(null)
                  } catch (error) {
                    const errorMessage: Message = {
                      id: `tool-error-${Date.now()}`,
                      role: 'assistant',
                      content: 'Tive um problema ao executar a ação. Por favor, tente novamente.',
                      timestamp: new Date(),
                    }
                    onSetMessages(prev => [...prev, errorMessage])
                    onSetActiveToolConfirmationMessageId(null)
                  } finally {
                    onSetIsLoading(false)
                  }
                }}
                onCancel={() => {
                  toolCalling.cancelToolCall()
                  onSetActiveToolConfirmationMessageId(null)
                  const cancelMessage: Message = {
                    id: `tool-cancel-${Date.now()}`,
                    role: 'assistant',
                    content: 'Tudo bem, cancelei a ação. Se precisar de algo mais, é só me avisar!',
                    timestamp: new Date(),
                  }
                  onSetMessages(prev => [...prev, cancelMessage])
                }}
                isExecuting={toolCalling.isExecuting}
              />
            </ChatBubbleBase>
          ) : message.messageType === 'tool-execution-feedback' && message.toolExecutionResult ? (
            <ChatBubbleBase
              sender="lia"
              timestamp={formatTimestamp(message.timestamp)}
              afterBubble={renderFeedback(message.id, message.content)}
            >
              <ToolExecutionFeedback
                result={message.toolExecutionResult}
                isExecuting={false}
                canRollback={message.toolExecutionResult.success}
                onRollback={async () => {
                  const result = await toolCalling.rollbackLastTool()
                  if (result && result.success) {
                    const rollbackMessage: Message = {
                      id: `rollback-${Date.now()}`,
                      role: 'assistant',
                      content: '↩️ Ação desfeita com sucesso!',
                      timestamp: new Date(),
                    }
                    onSetMessages(prev => [...prev, rollbackMessage])
                  }
                }}
              />
            </ChatBubbleBase>
          ) : message.messageType === 'action-result' && message.actionType ? (
            <ChatBubbleBase
              sender="lia"
              timestamp={formatTimestamp(message.timestamp)}
              labelExtra={
                <span className="text-micro px-1.5 py-0.5 rounded-full bg-wedo-cyan/10 text-wedo-cyan font-['Inter',sans-serif]">ação executada</span>
              }
              afterBubble={renderFeedback(message.id, message.content)}
            >
              <ActionResultCard
                actionType={message.actionType}
                result={(message.actionResult || {}) as Record<string, unknown> & { candidate_id?: string; candidate_name?: string; from_stage?: string; to_stage?: string; subject?: string; datetime?: string; moved_at?: string; sent_at?: string; scheduled_at?: string; simulated?: boolean; action?: string }}
              />
              {message.content && (
                <p className="text-xs text-lia-text-primary mt-1.5 leading-relaxed">
                  {message.content}
                </p>
              )}
            </ChatBubbleBase>
          ) : message.messageType === 'proactive' && message.proactiveData ? (
            <ChatBubbleBase
              sender="lia"
              timestamp={formatTimestamp(message.timestamp)}
              labelExtra={
                <span className="text-micro px-1.5 py-0.5 rounded-full bg-wedo-cyan/10 text-wedo-cyan font-['Inter',sans-serif]">sugestão proativa</span>
              }
              bubbleClassName="bg-transparent p-0"
            >
              <div className={cn(
                "rounded-md border-l-4 p-2.5 mb-1",
                message.proactiveData.severity === 'urgent' ? "border-l-status-error bg-status-error/5" :
                message.proactiveData.severity === 'warning' ? "border-l-status-warning bg-status-warning/5" :
                "border-l-wedo-cyan bg-wedo-cyan/5"
              )}>
                <p className="text-xs text-lia-text-primary leading-relaxed">{message.content}</p>
              </div>
              <div className="flex items-center gap-2 mt-1.5">
                <button
                  onClick={() => onProactiveAccept(message.proactiveData!.actionId, message.id)}
                  className="px-3 py-1 text-xs font-medium rounded-md bg-wedo-cyan/15 text-wedo-cyan hover:bg-wedo-cyan/25 transition-colors motion-reduce:transition-none font-['Inter',sans-serif]"
                >
                  {message.proactiveData.actionLabel}
                </button>
                <button
                  onClick={() => onProactiveReject(message.proactiveData!.actionId, message.id)}
                  className="px-3 py-1 text-xs rounded-md text-lia-text-secondary hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none font-['Inter',sans-serif]"
                >
                  Ignorar
                </button>
              </div>
            </ChatBubbleBase>
          ) : message.messageType === 'detected-fields' && message.detectedFields && message.detectedFields.length > 0 ? (
            <ChatBubbleBase
              sender="lia"
              hideTimestamp
              hideLabel
              bubbleClassName="bg-transparent p-0"
            >
              <DetectedFieldsCard
                fields={message.detectedFields}
                onEdit={(fieldLabel) => {
                  if (inputRef.current) {
                    inputRef.current.focus()
                    onSetInputValue(`Alterar ${fieldLabel}: `)
                  }
                }}
              />
            </ChatBubbleBase>
          ) : message.isProcessing ? (
            <div
              className={cn(
                "px-3 py-2 rounded-md text-xs transition-colors duration-300",
                message.processingState === 'completed' ? "bg-lia-bg-tertiary text-lia-text-primary" : "bg-lia-bg-secondary text-lia-text-secondary"
              )}
            >
              <div className="flex items-center gap-2">
                {message.processingState !== 'completed' && (
                  <div className="w-3 h-3 border-2 border-lia-btn-primary-bg border-t-transparent rounded-full animate-spin motion-reduce:animate-none" />
                )}
                <span>{message.content}</span>
              </div>
            </div>
          ) : (
            <ChatBubbleBase
              sender="lia"
              timestamp={formatTimestamp(message.timestamp)}
              className="group"
              afterBubble={
                !message.isTyping ? (
                  <div className="mt-2 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none">
                    <MessageFeedback
                      sessionId={conversationId || 'default-session'}
                      messageId={message.id}
                      originalResponse={message.content}
                      onFeedbackSubmitted={(type) => {
                      }}
                    />
                  </div>
                ) : undefined
              }
            >
              <div className="text-xs text-lia-text-primary space-y-1 leading-relaxed break-words overflow-wrap-anywhere">
                {formatMessageContent(message.content, message.isTyping || false, message.id)}
                {message.isTyping && messages[messages.length - 1]?.id === message.id && isTypingEffect && (
                  <span className="inline-block w-1.5 h-3.5 bg-wedo-cyan animate-pulse motion-reduce:animate-none ml-0.5" />
                )}
              </div>
              {message.executionPlan && (
                <PlanProgressCard plan={message.executionPlan} />
              )}
              {message.execution_plan && (
                <PlanProgressCard plan={message.execution_plan} />
              )}
              {message.detectedFieldsData && message.detectedFieldsData.length > 0 && (
                <DetectedFieldsCard
                  fields={message.detectedFieldsData}
                  onEdit={(fieldLabel) => {
                    if (inputRef.current) {
                      inputRef.current.focus()
                      onSetInputValue(`Alterar ${fieldLabel}: `)
                    }
                  }}
                />
              )}
            </ChatBubbleBase>
          )}
        </div>
      ))}
    </div>
  )
}
