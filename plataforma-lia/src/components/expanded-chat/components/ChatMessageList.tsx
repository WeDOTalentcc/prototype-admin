"use client"

/**
 * ChatMessageList — renderização da lista de mensagens do chat LIA.
 * Extraído de expanded-chat-modal.tsx (Sprint 4.3 — 2026-03-27).
 * Portabilidade Vue: props → defineProps; callbacks → emit.
 */

import React from "react"
import { Brain, User, CheckCircle2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { cleanAgentResponse, parseChatMarkdown } from "@/lib/chat-format"
import { MessageFeedback } from "@/components/chat/message-feedback"
import { ParecerLIACard } from "@/components/chat/parecer-lia-card"
import { ActionResultCard } from "@/components/chat/action-result-card"
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

  function formatMessageContent(content: string, isCurrentlyTyping: boolean, messageId: string) {
    const isLastTypingMessage = isCurrentlyTyping && messages[messages.length - 1]?.id === messageId
    const textToShow = isLastTypingMessage && displayedText.length > 0 ? displayedText : content
    const cleaned = cleanAgentResponse(textToShow)
    const html = parseChatMarkdown(cleaned)
    return <div dangerouslySetInnerHTML={{ __html: html }} />
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
          style={{ animationDelay: `${Math.min(index * 50, 200)}ms` }}
        >
          {message.role === 'system' ? (
            /* System Message - Field update notification */
            <div className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-full",
              "bg-gray-100/80 dark:bg-gray-800/60",
              "border border-gray-200/50 dark:border-gray-700/50",
              "max-w-[80%]"
            )}>
              <CheckCircle2 className="w-3 h-3 text-wedo-green flex-shrink-0" />
              <span
                className="text-micro text-gray-600 dark:text-gray-400"
                style={{ fontFamily: '"Inter", sans-serif' }}
              >
                {message.content}
              </span>
            </div>
          ) : message.role === 'user' ? (
            /* User Message */
            <div className="flex items-start gap-2.5 max-w-[70%]">
              <div className="flex flex-col items-end gap-1 flex-1">
                <div
                  className="px-3.5 py-2.5 rounded-[14px] rounded-br-[4px] bg-gray-100 dark:bg-gray-800"
                 
                >
                  <p className="text-base-ui text-gray-700 dark:text-gray-200 leading-relaxed">{message.content}</p>
                </div>
                <span className="text-xs text-gray-400 px-1" style={{ fontFamily: '"Inter", sans-serif' }}>
                  {formatTimestamp(message.timestamp)}
                </span>
              </div>
              <div className="flex-shrink-0 w-7 h-7 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center mt-0.5">
                <User className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400" />
              </div>
            </div>
          ) : message.messageType === 'parecer-lia' && message.parecerData ? (
            <div className="flex items-start gap-2 max-w-[90%]">
              <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
              </div>
              <div className="pt-1 flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-2">
                  <span className="text-xs font-bold text-gray-800 dark:text-gray-200" style={{ fontFamily: '"Inter", sans-serif' }}>LIA</span>
                  <span className="text-xs text-gray-400" style={{ fontFamily: '"Inter", sans-serif' }}>{formatTimestamp(message.timestamp)}</span>
                </div>
                <p className="text-base-ui text-gray-700 dark:text-gray-300 mb-3">{message.content}</p>
                <ParecerLIACard
                  data={message.parecerData}
                  onAcceptSuggestion={(suggestion) => {
                    onSetInputValue(suggestion)
                    if (inputRef?.current) inputRef.current.focus()
                  }}
                />
                <MessageFeedback
                  sessionId={conversationId || 'default-session'}
                  messageId={message.id}
                  originalResponse={message.content}
                  className="mt-2"
                />
              </div>
            </div>
          ) : message.messageType === 'compensation' ? (
            /* Compensation Analysis */
            <div className="flex items-start gap-2 max-w-[85%]">
              <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
              </div>
              <div className="pt-1 flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-1">
                  <span className="text-xs font-bold text-gray-800" style={{ fontFamily: '"Inter", sans-serif' }}>LIA</span>
                  <span className="text-xs text-gray-400" style={{ fontFamily: '"Inter", sans-serif' }}>{formatTimestamp(message.timestamp)}</span>
                </div>
                <div className="text-base-ui text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {formatSalaryAnalysisText(message.compensationAnalysis || null)}
                </div>
                <MessageFeedback
                  sessionId={conversationId || 'default-session'}
                  messageId={message.id}
                  originalResponse={message.content}
                  className="mt-2"
                />
              </div>
            </div>
          ) : message.messageType === 'competencies' ? (
            /* Competencies Suggestions Chat Message */
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
            /* Fast Track - Vacancy Search Results */
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
            /* Fast Track - Vacancy Full Summary */
            <VacancyFullSummary
              vacancy={message.vacancyFullDetails || null}
              editableFields={['salary_range', 'location', 'work_model', 'benefits']}
              lockedFields={['technical_skills', 'behavioral_competencies', 'screening_questions']}
              isLoading={false}
            />
          ) : message.messageType === 'tool-confirmation' && message.toolCall ? (
            /* Tool Confirmation Message */
            <div className="flex items-start gap-2 max-w-[85%]">
              <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
              </div>
              <div className="pt-1 flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-1">
                  <span className="text-xs font-bold text-gray-800" style={{ fontFamily: '"Inter", sans-serif' }}>LIA</span>
                  <span className="text-xs text-gray-400" style={{ fontFamily: '"Inter", sans-serif' }}>{formatTimestamp(message.timestamp)}</span>
                </div>
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
                      console.error('[ToolCalling] Error:', error)
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
              </div>
            </div>
          ) : message.messageType === 'tool-execution-feedback' && message.toolExecutionResult ? (
            /* Tool Execution Feedback */
            <div className="flex items-start gap-2 max-w-[85%]">
              <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
              </div>
              <div className="pt-1 flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-1">
                  <span className="text-xs font-bold text-gray-800" style={{ fontFamily: '"Inter", sans-serif' }}>LIA</span>
                  <span className="text-xs text-gray-400" style={{ fontFamily: '"Inter", sans-serif' }}>{formatTimestamp(message.timestamp)}</span>
                </div>
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
                <MessageFeedback
                  sessionId={conversationId || 'default-session'}
                  messageId={message.id}
                  originalResponse={message.content}
                  className="mt-2"
                />
              </div>
            </div>
          ) : message.messageType === 'action-result' && message.actionType ? (
            /* Action Result */
            <div className="flex items-start gap-2 max-w-[85%]">
              <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
              </div>
              <div className="pt-1 flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-1">
                  <span className="text-micro font-bold text-chat-cyan" style={{ fontFamily: '"Inter", sans-serif' }}>LIA</span>
                  <span className="text-micro px-1.5 py-0.5 rounded-full bg-chat-cyan/10 text-chat-cyan" style={{ fontFamily: '"Inter", sans-serif' }}>ação executada</span>
                  <span className="text-xs text-gray-400" style={{ fontFamily: '"Inter", sans-serif' }}>{formatTimestamp(message.timestamp)}</span>
                </div>
                <ActionResultCard
                  actionType={message.actionType}
                  result={(message.actionResult || {}) as Record<string, unknown> & { candidate_id?: string; candidate_name?: string; from_stage?: string; to_stage?: string; subject?: string; datetime?: string; moved_at?: string; sent_at?: string; scheduled_at?: string; simulated?: boolean; action?: string }}
                />
                {message.content && (
                  <p className="text-base-ui text-gray-600 dark:text-gray-400 mt-1.5 leading-relaxed">
                    {message.content}
                  </p>
                )}
                <MessageFeedback
                  sessionId={conversationId || 'default-session'}
                  messageId={message.id}
                  originalResponse={message.content}
                  className="mt-2"
                />
              </div>
            </div>
          ) : message.messageType === 'proactive' && message.proactiveData ? (
            /* Proactive Suggestion */
            <div className="flex items-start gap-2 max-w-[85%]">
              <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
              </div>
              <div className="pt-1 flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-1">
                  <span className="text-micro font-bold text-chat-cyan" style={{ fontFamily: '"Inter", sans-serif' }}>LIA</span>
                  <span className="text-micro px-1.5 py-0.5 rounded-full bg-chat-cyan/10 text-chat-cyan" style={{ fontFamily: '"Inter", sans-serif' }}>sugestão proativa</span>
                  <span className="text-xs text-gray-400" style={{ fontFamily: '"Inter", sans-serif' }}>{formatTimestamp(message.timestamp)}</span>
                </div>
                <div className={cn(
                  "rounded-md border-l-4 p-2.5 mb-1",
                  message.proactiveData.severity === 'urgent' ? "border-l-status-error bg-status-error/5" :
                  message.proactiveData.severity === 'warning' ? "border-l-status-warning bg-status-warning/5" :
                  "border-l-chat-cyan bg-chat-cyan/5"
                )}>
                  <p className="text-xs text-gray-800 dark:text-gray-200 leading-relaxed">{message.content}</p>
                </div>
                <div className="flex items-center gap-2 mt-1.5">
                  <button
                    onClick={() => onProactiveAccept(message.proactiveData!.actionId, message.id)}
                    className="px-3 py-1 text-xs font-medium rounded bg-chat-cyan/15 text-chat-cyan hover:bg-chat-cyan/25 transition-colors"
                    style={{ fontFamily: '"Inter", sans-serif' }}
                  >
                    {message.proactiveData.actionLabel}
                  </button>
                  <button
                    onClick={() => onProactiveReject(message.proactiveData!.actionId, message.id)}
                    className="px-3 py-1 text-xs rounded text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                    style={{ fontFamily: '"Inter", sans-serif' }}
                  >
                    Ignorar
                  </button>
                </div>
              </div>
            </div>
          ) : message.messageType === 'detected-fields' && message.detectedFields && message.detectedFields.length > 0 ? (
            <div className="flex items-start gap-2 max-w-[85%]">
              <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
              </div>
              <div className="pt-1 flex-1 min-w-0">
                <DetectedFieldsCard
                  fields={message.detectedFields}
                  onEdit={(fieldLabel) => {
                    if (inputRef.current) {
                      inputRef.current.focus()
                      onSetInputValue(`Alterar ${fieldLabel}: `)
                    }
                  }}
                />
              </div>
            </div>
          ) : message.isProcessing ? (
            /* Processing Message */
            <div
              className={cn(
                "px-3 py-2 rounded-md text-xs transition-all duration-300",
                message.processingState === 'completed' ? "bg-gray-100 text-gray-800" : "bg-gray-50 text-gray-500"
              )}
             
            >
              <div className="flex items-center gap-2">
                {message.processingState !== 'completed' && (
                  <div className="w-3 h-3 border-2 border-gray-900 dark:border-gray-50 border-t-transparent rounded-full animate-spin" />
                )}
                <span>{message.content}</span>
              </div>
            </div>
          ) : (
            /* LIA Message - Standardized bubble */
            <div
              className="max-w-[85%] group overflow-hidden"
             
            >
              <div className="flex items-start gap-2.5">
                <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
                </div>
                <div className="flex-1 min-w-0 overflow-hidden flex flex-col gap-1">
                  <div className="flex items-center gap-1.5 px-1">
                    <span className="text-xs font-bold text-gray-800" style={{ fontFamily: '"Inter", sans-serif' }}>LIA</span>
                    <span className="text-xs text-gray-400" style={{ fontFamily: '"Inter", sans-serif' }}>{formatTimestamp(message.timestamp)}</span>
                  </div>
                  <div className="px-3.5 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-[14px] rounded-bl-[4px]">
                    <div className="text-base-ui text-gray-700 dark:text-gray-200 space-y-1 leading-relaxed break-words overflow-wrap-anywhere">
                      {formatMessageContent(message.content, message.isTyping || false, message.id)}
                      {message.isTyping && messages[messages.length - 1]?.id === message.id && isTypingEffect && (
                        <span className="inline-block w-1.5 h-3.5 bg-chat-cyan animate-pulse ml-0.5" />
                      )}
                    </div>
                  </div>
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
                  {!message.isTyping && (
                    <div className="mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <MessageFeedback
                        sessionId={conversationId || 'default-session'}
                        messageId={message.id}
                        originalResponse={message.content}
                        onFeedbackSubmitted={(type) => {
                          console.log(`Feedback type ${type} submitted for message ${message.id}`)
                        }}
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
