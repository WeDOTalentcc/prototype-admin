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

      <div className="flex items-center gap-3 rounded-xl bg-lia-bg-tertiary border border-lia-border-subtle px-4 py-3">
        <div className="flex items-center gap-1">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="w-2 h-2 rounded-full bg-wedo-cyan dark:bg-wedo-cyan"
              style={{animation: "typingDot 1.4s ease-in-out infinite",
                animationDelay: `${i * 0.2}s`}}
            />
          ))}
        </div>
        <span className="text-xs text-lia-text-secondary animate-pulse motion-reduce:animate-none">
          IA está pensando...
        </span>
      </div>

      <style jsx>{`
        @keyframes typingDot {
          0%, 60%, 100% {
            transform: translateY(0);
            opacity: 0.4;
          }
          30% {
            transform: translateY(-4px);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  )
}
