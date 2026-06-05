"use client"

import React, { useState } from "react"
import { Brain, Sparkles, ChevronRight, ChevronDown } from "lucide-react"
import { useTranslations, useLocale } from "next-intl"
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
  const [showCompleted, setShowCompleted] = useState(false)

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

  // Linha em foco (Replit/Manus): só o último passo fica em destaque; os
  // anteriores recuam para um contador discreto, expansível sob demanda.
  const lastIndex = steps.length - 1
  const completed = steps.slice(0, lastIndex)
  const active = steps[lastIndex]

  return (
    <div className="animate-fade-in-up rounded-md border border-lia-border-subtle bg-lia-bg-secondary px-3 py-2.5 max-w-[85%] space-y-1.5">
      {completed.length > 0 && (
        <>
          <button
            type="button"
            onClick={() => setShowCompleted((o) => !o)}
            aria-expanded={showCompleted}
            className="flex items-center gap-1 text-[11px] text-lia-text-secondary hover:text-lia-text-primary transition-colors motion-reduce:transition-none"
          >
            {showCompleted ? (
              <ChevronDown className="w-3 h-3 shrink-0" />
            ) : (
              <ChevronRight className="w-3 h-3 shrink-0" />
            )}
            <span>{t("done", { count: completed.length })}</span>
          </button>
          {showCompleted && (
            <div className="space-y-1.5 ml-1.5 border-l border-lia-border-subtle/60 pl-2 animate-in fade-in slide-in-from-top-1 duration-200">
              {completed.map((step, i) => (
                <div key={i} className="flex items-start gap-2">
                  <Brain
                    className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-secondary"
                    aria-hidden="true"
                  />
                  <span className="text-xs leading-5 text-lia-text-secondary">
                    {phaseLabel(step, locale)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      <div className="flex items-start gap-2">
        <Brain
          className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 animate-pulse text-wedo-cyan motion-reduce:animate-none"
          aria-hidden="true"
        />
        <span className="text-xs leading-5 text-lia-text-primary font-medium">
          {phaseLabel(active, locale)}
        </span>
      </div>
    </div>
  )
}
