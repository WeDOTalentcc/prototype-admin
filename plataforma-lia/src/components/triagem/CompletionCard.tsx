"use client"

import React from "react"
import { cn } from "@/lib/utils"
import { CheckCircle2 } from "lucide-react"
import type { TriagemCompletionSummary } from "@/components/triagem/types"

interface CompletionCardProps {
  candidateName: string
  summary: TriagemCompletionSummary
  onClose?: () => void
  className?: string
}

export function CompletionCard({ candidateName, summary, onClose, className }: CompletionCardProps) {
  return (
    <div
      className={cn(
 "flex-1 flex items-center justify-center px-4 py-8",
        className
      )}
    >
      <div className="w-full max-w-md bg-white dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl shadow-lia-sm p-6 space-y-6">
        <div className="flex flex-col items-center gap-3 text-center">
          <div className="w-12 h-12 rounded-full bg-status-success/15 dark:bg-status-success/30 flex items-center justify-center">
            <CheckCircle2 className="w-7 h-7 text-status-success dark:text-status-success" />
          </div>
          <h2 className="text-lg font-semibold text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif]">
            Triagem concluída com sucesso!
          </h2>
          <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary font-['Open_Sans',sans-serif]">
            Obrigada, {candidateName}! Suas respostas foram registradas.
          </p>
        </div>

        <div className="flex items-center justify-center gap-4 text-xs text-lia-text-tertiary dark:text-lia-text-tertiary font-['Inter',sans-serif]">
          <span>{summary.questionsAnswered} perguntas respondidas</span>
          <span className="w-1 h-1 rounded-full bg-lia-border-default dark:bg-lia-border-medium" />
          <span>{summary.durationMinutes} minutos</span>
        </div>

        {summary.nextSteps.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif]">
              Próximos passos:
            </h3>
            <ul className="space-y-2" aria-label="Próximos passos">
              {summary.nextSteps.map((step, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-sm text-lia-text-secondary dark:text-lia-text-tertiary font-['Open_Sans',sans-serif]"
                >
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-elevated flex items-center justify-center text-micro font-['Inter',sans-serif] font-medium text-lia-text-tertiary dark:text-lia-text-tertiary mt-0.5">
                    {i + 1}
                  </span>
                  {step}
                </li>
              ))}
            </ul>
          </div>
        )}

        {onClose && (
          <button
            type="button"
            onClick={onClose}
            aria-label="Fechar triagem"
            className="w-full h-10 flex items-center justify-center rounded-lg bg-white dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-primary text-sm font-medium border border-lia-border-default dark:border-lia-border-default hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-elevated transition-colors motion-reduce:transition-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 focus:outline-none font-['Open_Sans',sans-serif]"
          >
            Fechar
          </button>
        )}

        <div className="pt-2 border-t border-lia-border-subtle dark:border-lia-border-subtle text-center">
          <span className="text-micro text-lia-text-disabled font-['Open_Sans',sans-serif]">
            Powered by <span className="text-wedo-cyan font-medium">LIA</span> · WeDOTalent
          </span>
        </div>
      </div>
    </div>
  )
}
