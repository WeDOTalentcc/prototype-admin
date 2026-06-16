"use client"

import React from "react"
import { useLocale } from "next-intl"
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
      className={`inline-flex gap-1 items-center ${className ?? ""}`}
      aria-hidden="true"
    >
      <span className="w-1.5 h-1.5 rounded-full bg-lia-text-secondary animate-[pulse-dot_1.4s_ease-in-out_infinite]" />
      <span className="w-1.5 h-1.5 rounded-full bg-lia-text-secondary animate-[pulse-dot_1.4s_ease-in-out_0.2s_infinite]" />
      <span className="w-1.5 h-1.5 rounded-full bg-lia-text-secondary animate-[pulse-dot_1.4s_ease-in-out_0.4s_infinite]" />
    </span>
  )
}

export function ThinkingStepsCard({ steps }: ThinkingStepsCardProps) {
  const locale = useLocale()

  if (!steps || steps.length === 0) {
    // Silent wait: the AgentActivityTimeline chip appears when the first
    // reasoning_step/tool_started event arrives. Showing "Pensando" here
    // breaks the dynamic progressive flow.
    return null
  }

  const lastIndex = steps.length - 1

  return (
    <div
      className="animate-in fade-in duration-200 space-y-1.5"
      role="status"
      aria-live="polite"
    >
      {steps.map((step, i) => {
        const spotlight = i === lastIndex
        const StepIcon = phaseIcon(step)
        return (
          <div key={i} className="flex items-center gap-2">
            <StepIcon
              className={cn(
                "w-3.5 h-3.5 shrink-0",
                spotlight
                  ? "text-lia-text-secondary animate-pulse motion-reduce:animate-none"
                  : "text-lia-text-secondary/50",
              )}
              aria-hidden="true"
            />
            <span
              className={cn(
                "text-xs",
                spotlight
                  ? "text-lia-text-secondary"
                  : "text-lia-text-secondary/50",
              )}
            >
              {phaseLabel(step, locale)}
            </span>
            {spotlight && <ActivityDots className="shrink-0" />}
          </div>
        )
      })}
    </div>
  )
}
