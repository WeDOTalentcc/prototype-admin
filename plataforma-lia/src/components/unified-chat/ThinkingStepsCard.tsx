"use client"

import React from "react"
import { CheckCircle2, Loader2, Sparkles } from "lucide-react"
import { useTranslations, useLocale } from "next-intl"
import { cn } from "@/lib/utils"
import { phaseLabel } from "./activity-labels"

interface ThinkingStepsCardProps {
  steps: string[]
}

/** Animated "thinking..." dots — gives the empty/initial state a live pulse. */
function ThinkingDots() {
  return (
    <span className="inline-flex gap-0.5 items-center" aria-hidden="true">
      <span className="w-1 h-1 rounded-full bg-wedo-cyan/70 animate-bounce [animation-delay:-0.3s] motion-reduce:animate-none" />
      <span className="w-1 h-1 rounded-full bg-wedo-cyan/70 animate-bounce [animation-delay:-0.15s] motion-reduce:animate-none" />
      <span className="w-1 h-1 rounded-full bg-wedo-cyan/70 animate-bounce motion-reduce:animate-none" />
    </span>
  )
}

export function ThinkingStepsCard({ steps }: ThinkingStepsCardProps) {
  const t = useTranslations("chat.agentActivity")
  const locale = useLocale()

  if (!steps || steps.length === 0) {
    return (
      <div
        className="flex items-center gap-2 px-1 py-2 animate-in fade-in duration-200"
        role="status"
        aria-live="polite"
      >
        <Sparkles className="w-3.5 h-3.5 text-wedo-cyan animate-pulse motion-reduce:animate-none shrink-0" aria-hidden="true" />
        <span className="text-xs text-lia-text-secondary">{t("thinking")}</span>
        <ThinkingDots />
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
                className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 animate-spin text-wedo-cyan motion-reduce:animate-none"
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
              {phaseLabel(step, locale)}
            </span>
          </div>
        )
      })}
    </div>
  )
}
