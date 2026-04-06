"use client"

import React, { memo } from "react"
import {
  Loader2, Clock, Globe, CheckCircle, XCircle
} from "lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { useAuthStore } from "@/stores/auth-store"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { LIAIcon } from "@/components/ui/lia-icon"
import {
  ProgressSteps,
  CommandExecution,
  FileCreationIndicator,
  CompletionMessage,
} from "@/components/ui/chat-status-indicators"
import { ActionResultCard } from "@/components/chat/action-result-card"
import { PlanProgressCard, type ExecutionPlanData } from "@/components/chat/plan-progress-card"
import { TypingIndicator } from "@/components/chat/typing-indicator"
import { Message } from "@/types/chat"
import { sanitizeHtml } from "@/lib/sanitize"

// ──────────────────────────────────────────────────────────────────────────────
// Types
// ──────────────────────────────────────────────────────────────────────────────

interface Props {
  messages: Message[]
  isLoading: boolean
  searchTerm: string
  currentMessageIndex: number
  messagesContainerClass: string
  availableCredits: number
  onRenderChatCard: (message: Message) => React.ReactNode
  onHighlightSearchTerm: (text: string, term: string) => string
  getRelativeTime: (timestamp: string) => string
  onLoadMoreCandidates: (query: string, threadId?: string) => void
  onSendMessage: (customContent?: string) => void
}

// ──────────────────────────────────────────────────────────────────────────────
// Component
// ──────────────────────────────────────────────────────────────────────────────

const ChatMessageListComponent = memo(function ChatMessageList({
  messages,
  isLoading,
  searchTerm,
  currentMessageIndex,
  messagesContainerClass,
  availableCredits,
  onRenderChatCard,
  onHighlightSearchTerm,
  getRelativeTime,
  onLoadMoreCandidates,
  onSendMessage,
}: Props) {
  const authUser = useAuthStore((s) => s.user)
  const userDisplayName = authUser?.name || authUser?.email || "Usuário"
  const userInitials = userDisplayName.charAt(0).toUpperCase()

  return (
    <div className={`${messagesContainerClass} space-y-2.5`}>
      {messages.map((message, index) => {
        const isHighlighted =
          searchTerm &&
          message.content.toLowerCase().includes(searchTerm.toLowerCase())
        const isCurrentMessage = index === currentMessageIndex

        return (
          <div
            key={message.id}
            data-message-id={message.id}
            className={`flex ${message.sender === "lia" ? "justify-end" : "justify-start"} ${
              isCurrentMessage ? "ring-2 ring-lia-btn-primary-bg/20 rounded-md" : ""
            } ${
              isHighlighted
                ? "bg-status-warning/10 dark:bg-status-warning/20 rounded-md p-2"
                : ""
            }`}
          >
            <div
              className={`flex items-start gap-2 ${
                message.sender === "lia"
                  ? "max-w-[80%] flex-row-reverse"
                  : "max-w-[80%]"
              }`}
            >
              {message.sender === "lia" ? (
                <div className="flex-shrink-0 pt-2">
                  <LIAIcon size="sm" />
                </div>
              ) : (
                <Avatar className="w-7 h-7 mt-1 flex-shrink-0">
                  <AvatarImage
                    src={undefined}
                    alt={userDisplayName}
                  />
                  <AvatarFallback className="bg-lia-btn-primary-bg text-lia-btn-primary-text text-xs font-medium">
                    {userInitials}
                  </AvatarFallback>
                </Avatar>
              )}

              {/* Message content */}
              <div
                className={`rounded-md px-3 py-2.5 flex-1 text-lia-text-primary ${message.sender === "user" ? "bg-lia-bg-primary" : "bg-lia-bg-tertiary"}`}
              >
                <div className="flex items-center space-x-2 mb-1">
                  <span
                    className={`text-xs font-medium text-lia-text-primary ${
                      message.sender === "lia" ? "lia-name -ml-1" : ""
                    }`}
                  >
                    {message.sender === "lia" ? "Lia" : userDisplayName}
                  </span>
                  <span
                    className="text-xs text-lia-text-tertiary"
                  >
                    {getRelativeTime(message.timestamp)}
                  </span>
                  {isCurrentMessage && (
                    <Badge variant="secondary" className="text-xs border-0">
                      Selecionada
                    </Badge>
                  )}
                </div>

                {message.type !== "thinking" &&
                  message.type !== "progress" &&
                  message.type !== "command" &&
                  message.type !== "file-creation" && (
                    <div
                      className={`text-sm leading-relaxed text-lia-text-primary ${
                        message.sender === "user"
                          ? "font-open-sans"
                          : "font-['Open_Sans',sans-serif] lia-markdown-content"
                      }`}
                      dangerouslySetInnerHTML={{
                        __html: sanitizeHtml(onHighlightSearchTerm(
                          message.content,
                          searchTerm
                        )),
                      }}
                    />
                  )}


                {message.sender === "lia" &&
                  (message.data as Record<string, any>)

                    ?.action_result && (
                    <div className="mt-3">
                      <ActionResultCard
                        actionType={
                          ((message.data as Record<string, any>)
                            ?.action_result as Record<string, any>)
                            ?.action_type as string ||
                          (message.data as Record<string, any>)
                            ?.action_type as string ||
                          "unknown"
                        }
                        result={
                          (message.data as Record<string, any>)
                            ?.action_result as Record<string, any>
                        }
                      />
                    </div>
                  )}

                {/* Plan Progress Card — shown when orchestrator ran a multi-step plan */}
                {message.sender === "lia" &&
                  (message.data as Record<string, any>)?.execution_plan && (
                    <PlanProgressCard
                      plan={(message.data as Record<string, any>).execution_plan as ExecutionPlanData}
                    />
                  )}


                {/* Global Search Expansion Card */}
                {message.sender === "lia" &&
                  (message.data as Record<string, any>)?.workflow_data &&
                  ((message.data as Record<string, any>)
                    ?.workflow_data as Record<string, any>)

                    ?.search_results && (
                    <Card className="border border-lia-btn-primary-bg bg-lia-bg-secondary mt-4">
                      <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                          <Globe className="w-5 h-5 text-lia-text-secondary mt-0.5 shrink-0" />
                          <div className="flex-1">
                            <h4 className="font-semibold text-sm mb-1 text-wedo-cyan-dark">
                              Expandir para Banco de Dados Global
                            </h4>

                            <p className="text-xs text-wedo-cyan-dark mb-3">
                              {(
                                (
                                  (message.data as Record<string, any>)
                                    ?.workflow_data as Record<string, any>
                                )?.search_results as Record<string, any>
                              )?.local_count > 0

                                ? `Encontramos ${
                                    (
                                      (
                                        (
                                          message.data as Record<
                                            string,
                                            unknown
                                          >
                                        )?.workflow_data as Record<
                                          string,
                                          unknown
                                        >
                                      )?.search_results as Record<
                                        string,
                                        unknown
                                      >
                                    )?.local_count
                                  } candidato(s) localmente.`
                                : `Encontramos apenas ${
                                    (
                                      (
                                        (
                                          message.data as Record<
                                            string,
                                            unknown
                                          >
                                        )?.workflow_data as Record<
                                          string,
                                          unknown
                                        >
                                      )?.search_results as Record<
                                        string,
                                        unknown
                                      >
                                    )?.local_count
                                  } candidato(s) localmente.`}{" "}
                              Posso buscar em nosso banco global com acesso a
                              800M+ perfis profissionais para encontrar mais
                              candidatos qualificados.
                            </p>

                            <div className="bg-lia-bg-primary/60/40 rounded-md p-3 mb-3 space-y-1.5">
                              <div className="flex items-center justify-between text-xs">
                                <span className="text-lia-text-secondary">
                                  Créditos disponíveis:
                                </span>
                                <span className="font-semibold text-lia-text-primary">
                                  {availableCredits} créditos
                                </span>
                              </div>
                              <div className="flex items-center justify-between text-xs">
                                <span className="text-lia-text-secondary">
                                  Esta busca consumirá:
                                </span>
                                <span className="font-semibold text-lia-text-primary">
                                  ~
                                  {((
                                    (
                                      (message.data as Record<string, any>)
                                        ?.workflow_data as Record<
                                        string,
                                        unknown
                                      >
                                    )?.search_results as Record<string, any>
                                  )?.global_credits_estimate as number) || 5}{" "}
                                  créditos
                                </span>
                              </div>
                              <div className="border-t border-lia-border-subtle pt-1.5 flex items-center justify-between text-xs">
                                <span className="text-lia-text-secondary">
                                  Saldo após busca:
                                </span>
                                <span className="font-semibold text-status-success">
                                  {Math.max(
                                    0,
                                    availableCredits -
                                      ((
                                        (
                                          (
                                            message.data as Record<
                                              string,
                                              unknown
                                            >
                                          )?.workflow_data as Record<
                                            string,
                                            unknown
                                          >
                                        )?.search_results as Record<
                                          string,
                                          unknown
                                        >
                                      )?.global_credits_estimate as number ||
                                        5)
                                  )}{" "}
                                  créditos
                                </span>
                              </div>
                            </div>

                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                                onClick={() =>
                                  onLoadMoreCandidates(
                                    (
                                      (
                                        (
                                          message.data as Record<
                                            string,
                                            unknown
                                          >
                                        )?.workflow_data as Record<
                                          string,
                                          unknown
                                        >
                                      )?.search_results as Record<
                                        string,
                                        unknown
                                      >
                                    )?.query as string || "",
                                    (
                                      (
                                        (
                                          message.data as Record<
                                            string,
                                            unknown
                                          >
                                        )?.workflow_data as Record<
                                          string,
                                          unknown
                                        >
                                      )?.search_results as Record<
                                        string,
                                        unknown
                                      >
                                    )?.thread_id as string | undefined
                                  )
                                }
                                disabled={
                                  availableCredits <
                                  (((
                                    (
                                      (
                                        message.data as Record<string, any>
                                      )?.workflow_data as Record<string, any>
                                    )?.search_results as Record<string, any>
                                  )?.global_credits_estimate as number) || 5)
                                }
                              >
                                <CheckCircle className="w-3.5 h-3.5 mr-1" />
                                Sim, buscar
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                className="border-lia-border-default text-lia-text-primary"
                                onClick={() =>
                                  onSendMessage(
                                    "Não obrigado, vou trabalhar com os resultados locais"
                                  )
                                }
                              >
                                <XCircle className="w-3.5 h-3.5 mr-1" />
                                Não obrigado
                              </Button>
                            </div>

                            {availableCredits <
                              (((
                                (
                                  (
                                    message.data as Record<string, any>
                                  )?.workflow_data as Record<string, any>
                                )?.search_results as Record<string, any>
                              )?.global_credits_estimate as number) || 5) && (
                              <p className="text-xs text-status-error dark:text-status-error mt-2">
                                Créditos insuficientes para esta busca.
                              </p>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                {message.type === "thinking" && <TypingIndicator />}

                {message.type === "progress" && message.progressSteps && (
                  <ProgressSteps
                    steps={message.progressSteps}
                    currentStep={message.currentStep}
                  />
                )}

                {message.type === "command" && message.command && (
                  <CommandExecution
                    command={message.command.text}
                    status={message.command.status}
                    output={message.command.output}
                  />
                )}

                {message.type === "file-creation" && message.fileCreation && (
                  <FileCreationIndicator
                    fileName={message.fileCreation.fileName}
                    fileType={message.fileCreation.fileType}
                    status={message.fileCreation.status}
                  />
                )}

                {/* Chat Cards inline */}
                {message.chatCardType && message.chatCardData && (
                  <div className="mt-4">{onRenderChatCard(message)}</div>
                )}

                {/* Completion Message */}
                {message.type === "completion" && message.completion && (
                  <>
                    <div
                      className="text-sm text-lia-text-primary mb-4"
                      dangerouslySetInnerHTML={{
                        __html: sanitizeHtml(onHighlightSearchTerm(
                          message.content,
                          searchTerm
                        )),
                      }}
                    />
                    <CompletionMessage
                      message={message.completion.message}
                      onRating={(_rating) => {
                        // Implementar lógica de rating
                      }}
                      onFollowUp={(_action) => {
                        // Implementar lógica de follow-up
                      }}
                    />
                  </>
                )}

                {/* Approval Block */}
                {message.needsApproval && message.approvalRequest && (
                  <div
                    className="mt-4 p-5 rounded-md bg-stone-50 dark:bg-stone-900/20"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-2">
                        <Clock
                          className="w-4 h-4 text-lia-text-secondary"
                        />
                        <h4
                          className="font-medium text-base text-lia-text-primary"
                        >
                          {message.approvalRequest.title}
                        </h4>
                      </div>
                      <Badge
                        variant="secondary"
                        className="text-xs border-0 bg-lia-bg-primary bg-lia-bg-primary text-lia-text-secondary"
                      >
                        {message.approvalStatus === "pending"
                          ? "Aguardando"
                          : message.approvalStatus}
                      </Badge>
                    </div>
                    <p
                      className="text-sm mb-3 text-lia-text-secondary"
                    >
                      {message.approvalRequest.description}
                    </p>
                    <p
                      className="text-xs mb-4 text-lia-text-tertiary"
                    >
                      👤 {message.approvalRequest.manager}
                    </p>

                    <div className="space-y-2.5 mb-4">
                      {message.approvalRequest.items.map((item, idx) => (
                        <div
                          key={idx}
                          className="flex justify-between text-sm py-1.5"
                        >
                          <span className="text-lia-text-secondary">
                            {item.label}:
                          </span>
                          <span
                            className="font-medium text-lia-text-primary"
                          >
                            {item.value}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Action buttons */}
                {message.actions && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {message.actions.map((action, idx) => {
                      const isApproveAction =
                        action.label.toLowerCase().includes("aprovar") ||
                        action.label.toLowerCase().includes("confirm")
                      const isScheduleAction =
                        action.label.toLowerCase().includes("agenda") ||
                        action.label.toLowerCase().includes("calendar")
                      const isRejectAction =
                        action.label.toLowerCase().includes("rejeitar") ||
                        action.label.toLowerCase().includes("não")

                      let buttonStyle = {
                        backgroundColor: "var(--lia-bg-secondary)",
                        color: "var(--lia-text-primary)",
                        borderColor: "var(--lia-border-default)",
                      }
                      let iconColor = "var(--lia-text-tertiary)"

                      if (isApproveAction) {
                        buttonStyle = {
                          backgroundColor: "var(--lia-bg-secondary)",
                          color: "var(--wedo-green)",
                          borderColor: "var(--wedo-green)",
                        }
                        iconColor = "var(--wedo-green)"
                      } else if (isScheduleAction) {
                        buttonStyle = {
                          backgroundColor: "var(--lia-bg-secondary)",
                          color: "var(--wedo-orange)",
                          borderColor: "var(--wedo-orange)",
                        }
                        iconColor = "var(--wedo-orange)"
                      } else if (isRejectAction) {
                        buttonStyle = {
                          backgroundColor: "var(--lia-bg-secondary)",
                          color: "var(--status-error)",
                          borderColor: "var(--status-error)",
                        }
                        iconColor = "var(--status-error)"
                      }

                      const IconComponent = action.icon

                      return (
                        <Button
                          key={idx}
                          variant="ghost"
                          size="sm"
                          className="text-xs transition-transform motion-reduce:transition-none duration-200 hover:scale-105 font-medium"
                          style={{backgroundColor: buttonStyle.backgroundColor,
                            color: buttonStyle.color,
                            border: `1px solid ${buttonStyle.borderColor}`}}
                        >
                          {IconComponent && (
                            <IconComponent
                              className="w-3 h-3 mr-1"
                              style={{color: iconColor} as React.CSSProperties}
                            />
                          )}
                          {action.label}
                        </Button>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        )
      })}

      {/* Loading indicator */}
      {isLoading && (
        <div className="flex justify-start">
          <div className="flex items-start gap-1 max-w-4xl">
            <div className="flex-shrink-0 pt-4">
              <LIAIcon size="md" />
            </div>
            <div
              className="rounded-md p-5 flex-1 bg-lia-bg-tertiary"
            >
              <div className="flex items-center space-x-2" role="status" aria-live="polite" aria-label="Carregando...">
                <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                <span
                  className="text-sm text-lia-text-secondary"
                >
                  LIA está digitando...
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
})

ChatMessageListComponent.displayName = "ChatMessageList"

export const ChatMessageList = ChatMessageListComponent
