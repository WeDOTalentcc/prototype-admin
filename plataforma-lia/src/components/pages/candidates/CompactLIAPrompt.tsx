/**
 * @deprecated Use UnifiedChat (sidebar mode) via InlineChatBridge instead.
 * This component is replaced by the unified chat architecture (Phase 6).
 * Migration: import { InlineChatBridge } from "@/components/unified-chat"
 */
"use client"

import React from "react"
import { Brain } from "lucide-react"
import { ThinkingDots } from "@/components/ui/thinking-dots"
import { LIAToolbarBrainButton } from "@/components/ui/lia-toolbar-brain-button"
import { useLiaFloat } from "@/contexts/lia-float-context"

export interface CompactLIAPromptProps {
  isLIAThinking: boolean
  liaPromptValue: string
  setLiaPromptValue: (value: string) => void
  setShowExpandedLIA: (value: boolean) => void
  onAICommand: (cmd: string) => void
}

export function CompactLIAPrompt({
  isLIAThinking,
}: CompactLIAPromptProps) {
  const { open } = useLiaFloat()

  return (
    <div data-testid="compact-lia-prompt" className="flex items-center gap-2">
      <LIAToolbarBrainButton
        isOpen={false}
        onClick={open}
        isThinking={isLIAThinking}
      />

      {isLIAThinking && (
        <div className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-xl animate-fade-in bg-lia-interactive-active/30 border border-wedo-cyan/20">
          <Brain className="w-3 h-3 animate-pulse motion-reduce:animate-none text-wedo-cyan" />
          <span className="font-medium text-lia-text-primary">LIA está pensando</span>
          <div className="flex gap-0.5">
            <ThinkingDots dotClassName="bg-lia-border-medium" size="sm" />
          </div>
        </div>
      )}
    </div>
  )
}
