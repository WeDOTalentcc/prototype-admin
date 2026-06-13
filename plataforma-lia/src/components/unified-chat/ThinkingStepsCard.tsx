"use client"

import React from "react"
import { Brain } from "lucide-react"
import { useTranslations, useLocale } from "next-intl"
import { cn } from "@/lib/utils"
import { phaseLabel, phaseIcon } from "./activity-labels"

interface ThinkingStepsCardProps {
  steps: string[]
}

/**
 * ActivityDots — animated ellipsis indicating active processing.
 * Reused by AgentActivityTimeline (DRY).
 */
export function ActivityDots({ className }: { className?: string }) {
  return (
    <span
      className={`inline-flex gap-0.5 items-center ${className ?? ""}`}
      aria-hidden="true"
    >
      <span className="w-1 h-1 rounded-full bg-wedo-cyan animate-bounce [animation-delay:-0.3s] motion-reduce:animate-none" />
      <span className="w-1 h-1 rounded-full bg-wedo-cyan animate-bounce [animation-delay:-0.15s] motion-reduce:animate-none" />
      <span className="w-1 h-1 rounded-full bg-wedo-cyan animate-bounce motion-reduce:animate-none" />
    </span>
  )
}

export function ThinkingStepsCard({ steps }: ThinkingStepsCardProps) {
  const t = useTranslations("chat.agentActivity")
  const locale = useLocale()

  if (!steps || steps.length === 0) {
    return (
      <div
        className="flex items-center gap-2 animate-in fade-in duration-200"
        role="status"
        aria-live="polite"
      >
        <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-wedo-cyan/10 shadow-[0_0_0_2px_rgba(0,190,184,0.15)] animate-pulse motion-reduce:animate-none">
          <Brain className="w-4 h-4 text-wedo-cyan" aria-hidden="true" />
        </div>
        <span className="text-xs text-wedo-cyan flex items-center gap-1">
          {t("thinking")}
          <ActivityDots className="shrink-0" />
        </span>
      </div>
    )
  }

  const lastIndex = steps.length - 1

  return (
    <div
      className="animate-in fade-in duration-200"
      role="status"
      aria-live="polite"
    >
      <div className="flex items-center gap-1 flex-wrap">
        {steps.map((step, i) => {
          const spotlight = i === lastIndex
          const StepIcon = phaseIcon(step)
          return (
            <div
              key={i}
              className={cn(
                "flex items-center justify-center w-7 h-7 rounded-lg transition-all duration-300",
                spotlight
                  ? "bg-wedo-cyan/10 shadow-[0_0_0_2px_rgba(0,190,184,0.15)] animate-pulse motion-reduce:animate-none"
                  : "bg-lia-bg-secondary/60",
              )}
            >
              <StepIcon
                className={cn(
                  "w-4 h-4 transition-colors duration-300",
                  spotlight ? "text-wedo-cyan" : "text-lia-text-secondary",
                )}
                aria-hidden="true"
              />
            </div>
          )
        })}
      </div>
      <span className="text-xs text-wedo-cyan flex items-center gap-1 mt-1">
        {phaseLabel(steps[lastIndex], locale)}
        <ActivityDots className="shrink-0" />
      </span>
    </div>
  )
}
