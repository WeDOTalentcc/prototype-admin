"use client"

import React, { memo, useMemo } from "react"
import { cn } from "@/lib/utils"
import { ActionResultCard } from "@/components/chat/action-result-card"
import { ChatBubbleBase } from "@/components/chat/chat-bubble-base"
import { MessageFeedback } from "@/components/chat/message-feedback"
import { cleanAgentResponse, parseChatMarkdown, escapeHtml } from "@/lib/chat-format"
import { sanitizeHtml } from "@/lib/sanitize"

interface MessageBubbleProps {
  sender: "lia" | "user"
  content: string
  timestamp: string
  actionResult?: {
    action_type: string
    result: Record<string, unknown>
  }
  userName?: string
  userAvatar?: string
  className?: string
  sessionId?: string
  messageId?: string
  showFeedback?: boolean
}

function RichTextContent({ html, className }: { html: string; className?: string }) {
  return (
    <div
      className={className}
      dangerouslySetInnerHTML={{ __html: sanitizeHtml(html) }}
    />
  )
}

const MessageBubbleComponent = memo(function MessageBubble({
  sender,
  content,
  timestamp,
  actionResult,
  userName,
  userAvatar,
  className,
  sessionId,
  messageId,
  showFeedback = true,
}: MessageBubbleProps) {
  const isLia = sender === "lia"

  const renderedContent = useMemo(() => {
    if (isLia) {
      const cleaned = cleanAgentResponse(content)
      return parseChatMarkdown(cleaned)
    }
    return escapeHtml(content).replace(/\n/g, "<br/>")
  }, [content, isLia])

  return (
    <ChatBubbleBase
      sender={sender}
      timestamp={timestamp}
      userName={userName}
      userAvatar={userAvatar}
      className={className}
      afterBubble={
        isLia && showFeedback && sessionId && messageId ? (
          <MessageFeedback
            sessionId={sessionId}
            messageId={messageId}
            originalResponse={content}
            className="px-1"
          />
        ) : undefined
      }
    >
      <RichTextContent
        html={renderedContent}
        className={cn(
          "text-xs leading-relaxed text-lia-text-primary"
        )}
      />

      {actionResult && (
        <ActionResultCard
          actionType={actionResult.action_type}
          result={actionResult.result}
          className="mt-2"
        />
      )}

      {isLia && (
        <div className="mt-1.5 pt-1 border-t border-lia-border-subtle flex items-center gap-1 opacity-50">
          <svg width="10" height="10" viewBox="0 0 16 16" fill="none" className="text-lia-text-tertiary flex-shrink-0">
            <path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1Zm0 2.5a1 1 0 1 1 0 2 1 1 0 0 1 0-2ZM6.5 7h3v4.5h-3V7Z" fill="currentColor"/>
          </svg>
          <span className="text-micro text-lia-text-tertiary">Gerado por IA — EU AI Act Art. 52</span>
        </div>
      )}
    </ChatBubbleBase>
  )
})

MessageBubbleComponent.displayName = "MessageBubble"

export const MessageBubble = MessageBubbleComponent
