"use client"

import React from "react"
import { cn } from "@/lib/utils"
import { LIAIcon } from "@/components/ui/lia-icon"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"

interface ChatBubbleBaseProps {
  sender: "lia" | "user"
  timestamp?: string
  userName?: string
  userAvatar?: string
  className?: string
  bubbleClassName?: string
  children: React.ReactNode
  hideLabel?: boolean
  hideTimestamp?: boolean
  hideAvatar?: boolean
  afterBubble?: React.ReactNode
  label?: string
  labelExtra?: React.ReactNode
}

export const ChatBubbleBase = React.memo(function ChatBubbleBase({
  sender,
  timestamp,
  userName,
  userAvatar,
  className,
  bubbleClassName,
  children,
  hideLabel = false,
  hideTimestamp = false,
  hideAvatar = false,
  afterBubble,
  label,
  labelExtra,
}: ChatBubbleBaseProps) {
  const isLia = sender === "lia"
  const userInitials = userName
    ? userName.split(/\s+/).filter(Boolean).map(w => w.charAt(0).toUpperCase()).slice(0, 2).join("")
    : ""

  return (
    <div
      className={cn(
        "flex gap-2.5 animate-in fade-in duration-300",
        isLia ? "justify-start" : "justify-end",
        className
      )}
    >
      {isLia && !hideAvatar && (
        <div className="flex-shrink-0 mt-0.5">
          <LIAIcon size="sm" />
        </div>
      )}

      <div className={cn("flex flex-col gap-1 max-w-[80%]", isLia ? "items-start" : "items-end")}>
        {isLia && !hideLabel && (
          <div className="flex items-center gap-1.5 px-1">
            <span className="text-xs font-semibold text-lia-text-primary">
              {label || "IA"}
            </span>
            {labelExtra}
            {!hideTimestamp && timestamp && (
              <span className="text-xs text-lia-text-tertiary tabular-nums">
                {timestamp}
              </span>
            )}
          </div>
        )}

        <div
          className={cn(
            isLia
              ? "px-3.5 py-2.5 bg-white border border-lia-border-subtle rounded-xl rounded-bl-[4px]"
              : "px-3.5 py-2.5 bg-lia-bg-tertiary border border-lia-border-subtle rounded-xl rounded-br-[4px]",
            bubbleClassName
          )}
        >
          {children}
          {isLia && (
            <div className="mt-1.5 pt-1 border-t border-lia-border-subtle flex items-center gap-1 opacity-50">
              <svg width="10" height="10" viewBox="0 0 16 16" fill="none" className="text-lia-text-tertiary flex-shrink-0">
                <path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1Zm0 2.5a1 1 0 1 1 0 2 1 1 0 0 1 0-2ZM6.5 7h3v4.5h-3V7Z" fill="currentColor"/>
              </svg>
              <span className="text-micro text-lia-text-tertiary">Gerado por IA — pode conter imprecisões · EU AI Act Art. 52</span>
            </div>
          )}
        </div>

        {!isLia && !hideTimestamp && timestamp && (
          <span className="text-xs text-lia-text-tertiary tabular-nums px-1">
            {timestamp}
          </span>
        )}

        {afterBubble}
      </div>

      {!isLia && !hideAvatar && (
        <div className="flex-shrink-0 mt-0.5">
          <Avatar className="h-7 w-7">
            {userAvatar ? (
              <AvatarImage src={userAvatar} alt={userName || "User"} />
            ) : null}
            <AvatarFallback className="bg-lia-interactive-active text-lia-text-secondary text-micro">
              {userInitials || "U"}
            </AvatarFallback>
          </Avatar>
        </div>
      )}
    </div>
  )
})

ChatBubbleBase.displayName = "ChatBubbleBase"
