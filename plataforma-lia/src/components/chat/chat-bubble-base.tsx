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
            <span className="text-xs font-semibold text-lia-text-primary font-['Inter',sans-serif]">
              {label || "LIA"}
            </span>
            {labelExtra}
            {!hideTimestamp && timestamp && (
              <span className="text-xs text-lia-text-tertiary font-['Inter',sans-serif] tabular-nums">
                {timestamp}
              </span>
            )}
          </div>
        )}

        <div
          className={cn(
            "px-3.5 py-2.5",
            isLia
              ? "bg-wedo-cyan/[0.04] rounded-[14px] rounded-bl-[4px]"
              : "bg-lia-bg-tertiary rounded-[14px] rounded-br-[4px]",
            bubbleClassName
          )}
        >
          {children}
        </div>

        {!isLia && !hideTimestamp && timestamp && (
          <span className="text-xs text-lia-text-tertiary font-['Inter',sans-serif] tabular-nums px-1">
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
