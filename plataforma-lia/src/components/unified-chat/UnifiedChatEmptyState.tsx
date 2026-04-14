"use client"

import React from "react"
import { Brain } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ChatMode } from "./unified-chat-types"
import { ChatWorkflowReels } from "@/components/ui/chat-workflow-reels"
import { useTranslations } from 'next-intl'

interface Props {
  mode: ChatMode
  onSuggestionClick: (prompt: string) => void
}

export function UnifiedChatEmptyState({ mode, onSuggestionClick }: Props) {
  const isCompact = mode === "sidebar" || mode === "floating"
  const t = useTranslations('chat')

  return (
    <div className={cn(
      "flex flex-col items-center justify-center flex-1 px-6",
      isCompact ? "py-8 gap-4" : "py-12 gap-6"
    )}>
      <div className={cn(
        "rounded-full border border-lia-border-subtle flex items-center justify-center bg-lia-bg-primary",
        isCompact ? "w-12 h-12" : "w-16 h-16"
      )}>
        <Brain
          className={cn("text-wedo-cyan", isCompact ? "w-6 h-6" : "w-8 h-8")}
          strokeWidth={1.5}
        />
      </div>

      <h2 className={cn(
        "font-semibold text-lia-text-primary text-center",
        isCompact ? "text-base" : "text-xl"
      )}>
        {t("greeting")}
      </h2>

      <div className={cn(
        "w-full",
        isCompact ? "max-w-[280px]" : "max-w-[640px]"
      )}>
        <ChatWorkflowReels
          onSelect={onSuggestionClick}
          compact={isCompact}
        />
      </div>
    </div>
  )
}
