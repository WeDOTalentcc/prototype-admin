"use client"

import React from "react"
import { Brain } from "lucide-react"
import { cn } from "@/lib/utils"
import { useLiaChatContext } from "@/contexts/lia-float-context"

interface Props {
  onOpen: () => void
}

/**
 * UnifiedChatBubble — Notion-style floating button to open the chat.
 * Shows when chat is closed. Minimal, clean, with subtle notification dot.
 */
export function UnifiedChatBubble({ onOpen }: Props) {
  const { chatIsConnected } = useLiaChatContext()

  return (
    <button
      onClick={onOpen}
      className={cn(
        "fixed bottom-6 left-6 z-50",
        "w-14 h-14 rounded-full",
        "bg-transparent",
        "flex items-center justify-center",
        "transition-transform motion-reduce:transition-none",
        "hover:scale-110",
        "focus-visible:outline-none",
        "group"
      )}
      title="Abrir LIA (⌘⇧K)"
      aria-label="Abrir chat com a LIA"
    >
      <Brain
        className="w-9 h-9 text-wedo-cyan drop-shadow-lia-md group-hover:drop-shadow-lia-lg transition-all motion-reduce:transition-none"
        strokeWidth={2}
      />

      {/* Connection dot */}
      {chatIsConnected && (
        <span className="absolute top-0.5 right-0.5 w-2 h-2 rounded-full bg-status-success" />
      )}
    </button>
  )
}
