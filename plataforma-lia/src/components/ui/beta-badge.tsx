"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { FlaskConical } from "lucide-react"

/**
 * BetaBadge — canonical neutral DS variant (Sprint visual 2026-05-26).
 *
 * White-label decision (memory `project_white_label_ai_assistant.md` +
 * DESIGN.md "LIA Cyan Exclusivity Rule"): cyan e EXCLUSIVA da assistente
 * quando age. Studio (onde cliente cria SEUS agentes) usa neutros DS.
 *
 * Fix Sprint visual: bg-wedo-cyan + text-white -> bg-lia-bg-inverse +
 * text-lia-text-on-inverse. Neutro dark canonical (slate-800-ish) garante
 * contraste alto sem usurpar identidade cyan da IA. Cascateia automaticamente
 * para os 8 consumers de BetaBadge (AgentStudioPage, AgentCard,
 * AIAgentBuilder, AgentCreationPreview, AgentActivityCard,
 * AgentChatCard, AgentDetailsPanel, TestDebugPanel).
 */
export interface BetaBadgeProps {
  label?: string
  size?: "sm" | "md"
  className?: string
}

export const BetaBadge = React.memo(function BetaBadge({
  label = "BETA",
  size = "sm",
  className,
}: BetaBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-0.5 rounded-full font-semibold tracking-wide leading-none",
        "bg-lia-bg-inverse text-lia-text-on-inverse",
        size === "sm" && "px-1 py-[1px] text-[6px]",
        size === "md" && "px-1.5 py-[1px] text-[7px]",
        className,
      )}
    >
      {size === "md" && (
        <FlaskConical className="w-2 h-2 flex-shrink-0" />
      )}
      {label}
    </span>
  )
})
BetaBadge.displayName = "BetaBadge"
