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
      <span className="w-1 h-1 rounded-full bg-lia-text-secondary/60 animate-bounce [animation-delay:-0.3s] motion-reduce:animate-none" />
      <span className="w-1 h-1 rounded-full bg-lia-text-secondary/60 animate-bounce [animation-delay:-0.15s] motion-reduce:animate-none" />
      <span className="w-1 h-1 rounded-full bg-lia-text-secondary/60 animate-bounce motion-reduce:animate-none" />
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
        <Brain
          className="w-3.5 h-3.5 text-lia-text-secondary animate-pulse motion-reduce:animate-none shrink-0"
          aria-hidden="true"
        />
        <span className="text-xs text-lia-text-secondary">
          {t("thinking")}
        </span>
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
