"use client"

import React from "react"
import { CheckCircle2, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface ThinkingStepsCardProps {
  steps: string[]
}

export function ThinkingStepsCard({ steps }: ThinkingStepsCardProps) {
  if (!steps || steps.length === 0) {
    return (
      <div className="flex items-center gap-2 px-1 py-2">
        <Loader2 className="w-3.5 h-3.5 animate-spin text-wedo-cyan" aria-hidden="true" />
        <span className="text-xs text-lia-text-secondary">
          Pensando...
        </span>
      </div>
    )
  }

  return (
    <div className="animate-fade-in-up rounded-md border border-lia-border-subtle bg-lia-bg-secondary px-3 py-2.5 max-w-[85%] space-y-1.5">
      {steps.map((step, i) => {
        const isActive = i === steps.length - 1

        return (
          <div key={i} className="flex items-start gap-2">
            {isActive ? (
              <Loader2
                className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 animate-spin text-wedo-cyan"
                aria-hidden="true"
              />
            ) : (
              <CheckCircle2
                className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-status-success"
                aria-hidden="true"
              />
            )}
            <span
              className={cn(
                "text-xs leading-5",
                isActive
                  ? "text-lia-text-primary font-medium"
                  : "text-lia-text-secondary"
              )}
            >
              {step}
            </span>
          </div>
        )
      })}
    </div>
  )
}
