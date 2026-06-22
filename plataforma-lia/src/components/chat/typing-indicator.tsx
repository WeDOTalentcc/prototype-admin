"use client"

import React from "react"
import { cn } from "@/lib/utils"
import { LIAIcon } from "@/components/ui/lia-icon"

interface TypingIndicatorProps {
  className?: string
}

export function TypingIndicator({ className }: TypingIndicatorProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 animate-in fade-in slide-in-from-bottom-2 duration-300",
        className
      )}
    >
      <div className="flex-shrink-0">
        <LIAIcon size="sm" className="bg-wedo-cyan/10 dark:bg-wedo-cyan-dark/20" />
      </div>

      <div className="flex items-center gap-2 rounded-xl bg-lia-bg-tertiary border border-lia-border-subtle px-4 py-3">
        <span className="text-xs text-lia-text-secondary animate-pulse motion-reduce:animate-none">
          Pensando…
        </span>
      </div>
    </div>
  )
}
