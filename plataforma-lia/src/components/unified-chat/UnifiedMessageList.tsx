"use client"

import React, { useRef, useEffect } from "react"
import { useTranslations } from "next-intl"
import { Copy, Plus, ThumbsUp, ThumbsDown, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { PlanProgressCard, type ExecutionPlanData } from "@/components/chat/plan-progress-card"
import { TypingIndicator } from "@/components/chat/typing-indicator"
import FlowStepMessage from "@/components/workflow-rail/FlowStepMessage"
import { renderMarkdown } from "@/lib/render-markdown"
import { submitThumbsFeedback } from "@/services/lia-api/feedback-api"
import type { LiaChatMessage } from "@/hooks/chat/use-lia-chat-connection"
import { NavigationHintCard } from "./NavigationHintCard"
import { TastingInsightCard } from "./TastingInsightCard"
import { WeeklyDigestChatMessage } from "@/components/notifications/weekly-digest-chat-message"
import type { WeeklyDigestData } from "@/components/notifications/weekly-digest-notification"
import type { ChatMode } from "./unified-chat-types"

function isWeeklyDigestMeta(meta: Record<string, unknown> | undefined): meta is Record<string, unknown> & { digest: WeeklyDigestData; recruiterName?: string } {
  if (!meta || meta.type !== "weekly_digest") return false
  const d = meta.digest as Record<string, unknown> | undefined
  return d != null && typeof d === "object" && "pipeline" in d && "atRiskJobs" in d && "compliance" in d
}

interface Props {
  mode: ChatMode
  messages: LiaChatMessage[]
  isStreaming: boolean
  streamingContent: string
  isThinking: boolean
  thinkingSteps: string[]
  userName: string
  conversationId?: string | null
  /**
   * Called when the user clicks a clarification option chip (Tier 8 fallback).
   * The handler typically forwards the chip's `value` to sendChatMessage.
   */
  onChipClick?: (value: string) => void
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
  const t = useTranslations('chat.messageActions')
  return (
    <div className="flex items-center gap-0.5 mt-1 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none">
      <button
        className="p-1 rounded hover:bg-lia-interactive-hover text-lia-text-disabled hover:text-lia-text-secondary"
        title={t('copyTitle')}
        aria-label={t('copyAriaLabel')}
        onClick={() => {
          navigator.clipboard.writeText(content)
        }}
      >
        <Copy className="w-3.5 h-3.5" />
      </button>
      <button
        className="p-1 rounded hover:bg-lia-interactive-hover text-lia-text-disabled hover:text-lia-text-secondary"
        title={t('insertTitle')}
        aria-label={t('insertAriaLabel')}
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
        title={t('helpfulTitle')}
        aria-label={t('helpfulAriaLabel')}
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
        title={t('notHelpfulTitle')}
        aria-label={t('notHelpfulAriaLabel')}
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
  onChipClick,
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
      className="flex-1 overflow-y-auto"
    >
      <div
        className={cn(
          "px-4 py-4 space-y-4",
          mode === "fullscreen" ? "max-w-[720px] mx-auto w-full" : ""
        )}
      >
      {messages.map((message) => {
        const isLia = message.sender === "lia"
        const meta = message.metadata
        const hasPlan = message.executionPlan != null
        const hasFlowSteps = meta?.flowSteps != null
        const hasNavHint = meta?.navigation_hint != null
        const hasTastingInsights = Array.isArray(meta?.tasting_insights) && (meta!.tasting_insights as unknown[]).length > 0
        const weeklyDigestMeta = isWeeklyDigestMeta(meta)

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
                {weeklyDigestMeta ? (
                  <WeeklyDigestChatMessage
                    digest={meta!.digest as WeeklyDigestData}
                    recruiterName={meta!.recruiterName as string | undefined}
                  />
                ) : (
                <div
                  className="text-[13px] leading-relaxed text-lia-text-primary lia-markdown-content"
                  dangerouslySetInnerHTML={{
                    __html: renderMarkdown(message.content),
                  }}
                />
                )}

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

                {hasTastingInsights && (
                  <TastingInsightCard
                    insights={meta!.tasting_insights as { module_name: string; module_label: string; insight_type: string; summary: string; cta: string; badge: string }[]}
                  />
                )}

                {/* Clarification option chips (Tier 8 fallback from cascaded_router) */}
                {message.options && message.options.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {message.options.map((opt) => (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => onChipClick?.(opt.value)}
                        className="px-3 py-1 text-[12px] rounded-lg border border-lia-border-default text-lia-text-primary hover:bg-lia-interactive-hover transition-colors"
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
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
                  <p className="text-[13px]">
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
              className="text-[13px] leading-relaxed text-lia-text-primary lia-markdown-content"
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
    </div>
  )
}
