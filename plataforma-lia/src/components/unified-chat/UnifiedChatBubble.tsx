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
        "fixed bottom-6 right-6 z-30",
        "w-12 h-12 rounded-full",
        "bg-lia-bg-primary border border-lia-border-subtle",
        "flex items-center justify-center",
        "hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none",
        "group"
      )}
      title="Abrir LIA (⌘⇧K)"
      aria-label="Abrir chat com a LIA"
    >
      <Brain
        className="w-5 h-5 text-wedo-cyan group-hover:scale-110 transition-transform motion-reduce:transition-none"
        strokeWidth={1.5}
      />

      {/* Connection dot */}
      {chatIsConnected && (
        <span className="absolute top-0.5 right-0.5 w-2 h-2 rounded-full bg-status-success" />
      )}
    </button>
  )
}
