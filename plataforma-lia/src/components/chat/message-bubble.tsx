"use client"

import React, { memo, useMemo } from "react"
import { User, Brain } from "lucide-react"
import { cn } from "@/lib/utils"
import { ActionResultCard } from "@/components/chat/action-result-card"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { MessageFeedback } from "@/components/chat/message-feedback"
import { cleanAgentResponse, parseChatMarkdown, escapeHtml } from "@/lib/chat-format"

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
      dangerouslySetInnerHTML={{ __html: html }}
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
    <div
      className={cn(
        "flex gap-2.5 animate-in fade-in duration-300",
        isLia ? "justify-start" : "justify-end",
        className
      )}
    >
      {isLia && (
        <div className="flex-shrink-0 mt-1">
          <div className="w-7 h-7 rounded-full flex items-center justify-center">
            <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
          </div>
        </div>
      )}

      <div className="flex flex-col gap-1 max-w-[80%]">
        <div
          className={cn(
            "px-3.5 py-2.5",
            isLia
              ? "bg-white dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle rounded-[14px] rounded-bl-[4px]"
              : "bg-gray-100 dark:bg-lia-bg-secondary rounded-[14px] rounded-br-[4px]"
          )}
        >
          <RichTextContent
            html={renderedContent}
            className={cn(
              "text-base-ui leading-relaxed font-['Open_Sans',sans-serif] lia-text-700 dark:text-lia-text-primary"
            )}
          />

          {actionResult && (
            <ActionResultCard
              actionType={actionResult.action_type}
              result={actionResult.result}
              className="mt-2"
            />
          )}
        </div>

        <div className="flex items-center justify-between px-1">
          <span
            className={cn(
              "text-xs font-['Inter',sans-serif] tabular-nums lia-text-400 dark:lia-text-500",
              !isLia && "ml-auto"
            )}
          >
            {timestamp}
          </span>
        </div>

        {isLia && showFeedback && sessionId && messageId && (
          <MessageFeedback
            sessionId={sessionId}
            messageId={messageId}
            originalResponse={content}
            className="px-1"
          />
        )}
      </div>

      {!isLia && (
        <div className="flex-shrink-0 mt-1">
          <Avatar className="h-7 w-7">
            {userAvatar ? (
              <AvatarImage src={userAvatar} alt={userName || "User"} />
            ) : null}
            <AvatarFallback className="bg-gray-200 dark:lia-bg-600 lia-text-600 dark:text-lia-text-secondary text-micro">
              {userName ? userName.charAt(0).toUpperCase() : <User className="w-3.5 h-3.5" />}
            </AvatarFallback>
          </Avatar>
        </div>
      )}
    </div>
  )
})

MessageBubbleComponent.displayName = "MessageBubble"

export const MessageBubble = MessageBubbleComponent
