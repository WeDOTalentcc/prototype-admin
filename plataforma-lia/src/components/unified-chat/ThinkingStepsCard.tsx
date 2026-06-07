"use client"

import React from "react"
import { Brain } from "lucide-react"
import { useTranslations, useLocale } from "next-intl"
import { phaseLabel, phaseIcon } from "./activity-labels"

interface ThinkingStepsCardProps {
  steps: string[]
}

/**
 * ActivityDots — reticências animadas ("três pontos piscando") indicando
 * processamento ATIVO. Inline, pensado para ir ao final da linha/frase em foco
 * (Paulo 2026-06-06: deixar o reasoning mais dinâmico e mostrar que "ainda está
 * processando" na própria linha, não num bloco separado embaixo). Produtor
 * único do visual — reutilizado pela AgentActivityTimeline (DRY).
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
        className="flex items-center gap-2 px-1 py-2 animate-in fade-in duration-200"
        role="status"
        aria-live="polite"
      >
        <Brain className="w-3.5 h-3.5 text-wedo-cyan animate-pulse motion-reduce:animate-none shrink-0" aria-hidden="true" />
        <span className="text-xs text-lia-text-secondary">{t("thinking")}</span>
        <ActivityDots />
      </div>
    )
  }

  // Estilo Replit/Manus: cada passo aparece empilhado (um abaixo do outro),
  // dando a sensação de evolução em tempo real. Só o ÚLTIMO passo fica em
  // destaque (texto primário + cérebro cyan pulsante); os anteriores recuam
  // para "concluídos" (cérebro esmaecido).
  const lastIndex = steps.length - 1

  return (
    <div
      className="animate-fade-in-up space-y-1.5"
      role="status"
      aria-live="polite"
    >
      {steps.map((step, i) => {
        const spotlight = i === lastIndex
        // Enriquecimento 2026-06-07: icone semantico por passo (phaseIcon) em vez
        // de Brain fixo -> consistente com timeline/summary (mesmo vocabulario).
        const StepIcon = phaseIcon(step)
        return (
          <div key={i} className="flex items-start gap-2">
            <StepIcon
              className={
                spotlight
                  ? "w-3.5 h-3.5 mt-0.5 flex-shrink-0 animate-pulse text-wedo-cyan motion-reduce:animate-none"
                  : "w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-secondary"
              }
              aria-hidden="true"
            />
            <span
              className={
                spotlight
                  ? "text-xs leading-5 text-lia-text-primary font-medium"
                  : "text-xs leading-5 text-lia-text-secondary"
              }
            >
              {phaseLabel(step, locale)}
            </span>
          </div>
        )
      })}
    </div>
  )
}
