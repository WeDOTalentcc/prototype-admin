"use client"

import React from "react"
import { useLocale } from "next-intl"
import { cn } from "@/lib/utils"
import { Brain } from "lucide-react"
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
    // Padrão de mercado: feedback imediato com mesma tipografia dos steps.
    // Ícone Brain pulsando + "Pensando" + dots — idêntico ao spotlight ativo.
    const label = locale?.toLowerCase().startsWith("en") ? "Thinking" : "Pensando"
    return (
      <div
        className="flex items-center gap-2 animate-in fade-in duration-200"
        role="status"
        aria-live="polite"
      >
        <Brain
          className="w-3.5 h-3.5 shrink-0 text-lia-text-secondary animate-pulse motion-reduce:animate-none"
          aria-hidden="true"
        />
        <span className="text-xs text-lia-text-secondary">{label}</span>
        <ActivityDots className="shrink-0" />
      </div>
    )
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
