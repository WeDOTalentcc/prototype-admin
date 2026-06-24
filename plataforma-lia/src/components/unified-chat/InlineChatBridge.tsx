"use client"

import React from "react"
import { Brain } from "lucide-react"
import { cn } from "@/lib/utils"
import { useLiaFloat } from "@/contexts/lia-float-context"
import type { EntityContext, ChatContextType } from "@/contexts/lia-float-context"

interface Props {
  /** Pre-fill message to send when chat opens */
  initialMessage?: string
  /** Context type for the chat session */
  contextType?: ChatContextType
  /** Entity to associate with the chat (candidate, job) */
  entity?: EntityContext
  /** Visual variant */
  variant?: "button" | "bar"
  /** Additional CSS classes */
  className?: string
  /** Label text */
  label?: string
}

/**
 * InlineChatBridge — Replaces deprecated inline chats (3, 4, 5, 7).
 *
 * Instead of rendering a full chat inline, this component opens the
 * UnifiedChat sidebar with the appropriate context. This ensures:
 * - Single chat implementation (no duplication)
 * - Consistent UX across all pages
 * - Context preserved via LiaFloatContext
 *
 * Replaces (now removed) inline chat surfaces previously rendered by:
 * - jobs page inline chat panel
 * - candidates page compact LIA prompt
 * - kanban super-chat section / LIA sidebar
 * - candidate preview LiaChatModal
 */
export function InlineChatBridge({
  initialMessage,
  contextType,
  entity,
  variant = "bar",
  className,
  label = "Perguntar à IA sobre este contexto",
}: Props) {
  const { open, openWithEntity, setChatContextType } = useLiaFloat()

  const handleOpen = () => {
    if (entity) {
      openWithEntity(entity)
    } else {
      open()
    }
    if (contextType) {
      setChatContextType(contextType)
    }
    // If there's an initial message, dispatch it after sidebar opens
    if (initialMessage) {
      setTimeout(() => {
        window.dispatchEvent(new CustomEvent("lia:prefill-message", {
          detail: { message: initialMessage },
        }))
      }, 200)
    }
  }

  if (variant === "button") {
    return (
      <button
        onClick={handleOpen}
        className={cn(
          "inline-flex items-center gap-2 px-3 py-2 rounded-md",
          "border border-lia-border-subtle bg-lia-bg-primary",
          "text-sm text-lia-text-secondary hover:text-lia-text-primary",
          "hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none",
          "",
          className
        )}
      >
        <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2} />
        {label}
      </button>
    )
  }

  return (
    <div
      className={cn(
        "flex items-center gap-3 px-4 py-3 border border-lia-border-subtle rounded-md",
        "bg-lia-bg-primary hover:bg-lia-bg-secondary cursor-pointer",
        "transition-colors motion-reduce:transition-none",
        className
      )}
      onClick={handleOpen}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === "Enter") handleOpen() }}
    >
      <Brain className="w-5 h-5 text-wedo-cyan flex-shrink-0" strokeWidth={1.5} />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-lia-text-primary font-medium">
          {label}
        </p>
        <p className="text-xs text-lia-text-tertiary">
          Abre o chat lateral com contexto desta página
        </p>
      </div>
    </div>
  )
}
