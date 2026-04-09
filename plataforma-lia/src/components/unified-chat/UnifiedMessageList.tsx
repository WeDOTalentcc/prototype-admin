"use client"

import React, { useRef, useEffect } from "react"
import { Copy, Plus, ThumbsUp, ThumbsDown, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { ChatBubbleBase } from "@/components/chat/chat-bubble-base"
import { PlanProgressCard, type ExecutionPlanData } from "@/components/chat/plan-progress-card"
import { TypingIndicator } from "@/components/chat/typing-indicator"
import { sanitizeHtml } from "@/lib/sanitize"
import type { LiaChatMessage } from "@/hooks/use-lia-chat-connection"
import type { ChatMode } from "./unified-chat-types"

interface Props {
  mode: ChatMode
  messages: LiaChatMessage[]
  isStreaming: boolean
  streamingContent: string
  isThinking: boolean
  thinkingSteps: string[]
  userName: string
}

function MessageActions({ messageId }: { messageId: string }) {
  return (
    <div className="flex items-center gap-0.5 mt-1 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none">
      <button
        className="p-1 rounded hover:bg-lia-interactive-hover text-lia-text-disabled hover:text-lia-text-secondary"
        title="Copiar"
        aria-label="Copiar resposta"
      >
        <Copy className="w-3.5 h-3.5" />
      </button>
      <button
        className="p-1 rounded hover:bg-lia-interactive-hover text-lia-text-disabled hover:text-lia-text-secondary"
        title="Inserir"
        aria-label="Inserir na conversa"
      >
        <Plus className="w-3.5 h-3.5" />
      </button>
      <button
        className="p-1 rounded hover:bg-lia-interactive-hover text-lia-text-disabled hover:text-lia-text-secondary"
        title="Útil"
        aria-label="Marcar como útil"
      >
        <ThumbsUp className="w-3.5 h-3.5" />
      </button>
      <button
        className="p-1 rounded hover:bg-lia-interactive-hover text-lia-text-disabled hover:text-lia-text-secondary"
        title="Não útil"
        aria-label="Marcar como não útil"
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
                  className="text-sm leading-relaxed text-lia-text-primary font-['Open_Sans',sans-serif] lia-markdown-content"
                  dangerouslySetInnerHTML={{
                    __html: sanitizeHtml(message.content),
                  }}
                />

                {/* Execution plan */}
                {message.executionPlan && (
                  <PlanProgressCard
                    plan={message.executionPlan as unknown as ExecutionPlanData}
                  />
                )}

                {/* Notion-style action icons */}
                <MessageActions messageId={message.id} />
              </div>
            ) : (
              /* User message — Notion style: dark pill, right-aligned */
              <div className="max-w-[80%]">
                <div className="inline-block px-4 py-2.5 rounded-2xl bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900">
                  <p className="text-sm font-['Open_Sans',sans-serif]">
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
              className="text-sm leading-relaxed text-lia-text-primary font-['Open_Sans',sans-serif] lia-markdown-content"
              dangerouslySetInnerHTML={{
                __html: sanitizeHtml(streamingContent),
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
