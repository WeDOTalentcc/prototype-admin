"use client"

import React, { useRef, useEffect } from "react"
import { Copy, Plus, ThumbsUp, ThumbsDown, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { PlanProgressCard, type ExecutionPlanData } from "@/components/chat/plan-progress-card"
import { TypingIndicator } from "@/components/chat/typing-indicator"
import FlowStepMessage from "@/components/workflow-rail/FlowStepMessage"
import { renderMarkdown } from "@/lib/render-markdown"
import { submitThumbsFeedback } from "@/services/lia-api/feedback-api"
import type { LiaChatMessage } from "@/hooks/use-lia-chat-connection"
import { NavigationHintCard } from "./NavigationHintCard"
import type { ChatMode } from "./unified-chat-types"

interface Props {
  mode: ChatMode
  messages: LiaChatMessage[]
  isStreaming: boolean
  streamingContent: string
  isThinking: boolean
  thinkingSteps: string[]
  userName: string
  conversationId?: string | null
}

function MessageActions({
  messageId,
  content,
  conversationId,
}: {
  messageId: string
  content: string
  conversationId?: string | null
}) {
  return (
    <div className="flex items-center gap-0.5 mt-1 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none">
      <button
        className="p-1 rounded hover:bg-lia-interactive-hover text-lia-text-disabled hover:text-lia-text-secondary"
        title="Copiar"
        aria-label="Copiar resposta"
        onClick={() => {
          navigator.clipboard.writeText(content)
        }}
      >
        <Copy className="w-3.5 h-3.5" />
      </button>
      <button
        className="p-1 rounded hover:bg-lia-interactive-hover text-lia-text-disabled hover:text-lia-text-secondary"
        title="Inserir"
        aria-label="Inserir na conversa"
        onClick={() => {
          window.dispatchEvent(
            new CustomEvent("lia:prefill-message", {
              detail: { message: content },
            })
          )
        }}
      >
        <Plus className="w-3.5 h-3.5" />
      </button>
      <button
        className="p-1 rounded hover:bg-lia-interactive-hover text-lia-text-disabled hover:text-lia-text-secondary"
        title="Útil"
        aria-label="Marcar como útil"
        onClick={() => {
          if (conversationId) {
            submitThumbsFeedback(conversationId, messageId, "up")
          }
        }}
      >
        <ThumbsUp className="w-3.5 h-3.5" />
      </button>
      <button
        className="p-1 rounded hover:bg-lia-interactive-hover text-lia-text-disabled hover:text-lia-text-secondary"
        title="Não útil"
        aria-label="Marcar como não útil"
        onClick={() => {
          if (conversationId) {
            submitThumbsFeedback(conversationId, messageId, "down")
          }
        }}
      >
        <ThumbsDown className="w-3.5 h-3.5" />
      </button>
    </div>
  )
}

export function UnifiedMessageList({
  mode,
  messages,
  isStreaming,
  streamingContent,
  isThinking,
  thinkingSteps,
  userName,
  conversationId,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages.length, streamingContent, isThinking])

  return (
    <div
      ref={containerRef}
      className={cn(
        "flex-1 overflow-y-auto px-4 py-4 space-y-4",
        mode === "fullscreen" ? "max-w-[720px] mx-auto w-full" : ""
      )}
    >
      {messages.map((message) => {
        const isLia = message.sender === "lia"
        const meta = message.metadata
        const hasPlan = message.executionPlan != null
        const hasFlowSteps = meta?.flowSteps != null
        const hasNavHint = meta?.navigation_hint != null

        return (
          <div
            key={message.id}
            className={cn(
              "group",
              isLia ? "" : "flex justify-end"
            )}
          >
            {isLia ? (
              /* LIA message — Notion style: plain text, no bubble bg, left-aligned */
              <div className="max-w-[90%]">
                <div
                  className="text-sm leading-relaxed text-lia-text-primary lia-markdown-content"
                  dangerouslySetInnerHTML={{
                    __html: renderMarkdown(message.content),
                  }}
                />

                {/* Execution plan */}
                {hasPlan && (
                  <PlanProgressCard
                    plan={message.executionPlan as unknown as ExecutionPlanData}
                  />
                )}

                {/* Flow steps (workflow visual) */}
                {hasFlowSteps && (
                  <FlowStepMessage
                    steps={meta!.flowSteps as unknown as import("@/components/workflow-rail/FlowStepMessage").FlowStep[]}
                    question={meta!.flowQuestion as string | undefined}
                    compact
                  />
                )}

                {/* Navigation hint (e.g., "Go to Agent Studio") */}
                {hasNavHint && (
                  <NavigationHintCard
                    hint={meta!.navigation_hint as { page: string; entity_id?: string }}
                  />
                )}

                {/* Notion-style action icons */}
                <MessageActions
                  messageId={message.id}
                  content={message.content}
                  conversationId={conversationId}
                />
              </div>
            ) : (
              /* User message — Notion style: dark pill, right-aligned */
              <div className="max-w-[80%]">
                <div className="inline-block px-4 py-2.5 rounded-xl bg-lia-bg-inverse dark:bg-lia-bg-tertiary text-white dark:text-lia-text-primary">
                  <p className="text-sm">
                    {message.content}
                  </p>
                </div>
              </div>
            )}
          </div>
        )
      })}

      {/* Streaming indicator */}
      {isStreaming && streamingContent && (
        <div className="group">
          <div className="max-w-[90%]">
            <div
              className="text-sm leading-relaxed text-lia-text-primary lia-markdown-content"
              dangerouslySetInnerHTML={{
                __html: renderMarkdown(streamingContent),
              }}
            />
          </div>
        </div>
      )}

      {/* Thinking indicator */}
      {isThinking && !streamingContent && (
        <div className="flex items-center gap-2">
          <TypingIndicator />
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
