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
      <div className="w-full max-w-md bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md shadow-sm p-6 space-y-6">
        <div className="flex flex-col items-center gap-3 text-center">
          <div className="w-12 h-12 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
            <CheckCircle2 className="w-7 h-7 text-green-600 dark:text-green-400" />
          </div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 font-['Open_Sans',sans-serif]">
            Triagem concluída com sucesso!
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 font-['Open_Sans',sans-serif]">
            Obrigada, {candidateName}! Suas respostas foram registradas.
          </p>
        </div>

        <div className="flex items-center justify-center gap-4 text-xs text-gray-500 dark:text-gray-400 font-['Inter',sans-serif]">
          <span>{summary.questionsAnswered} perguntas respondidas</span>
          <span className="w-1 h-1 rounded-full bg-gray-300 dark:bg-gray-600" />
          <span>{summary.durationMinutes} minutos</span>
        </div>

        {summary.nextSteps.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 font-['Open_Sans',sans-serif]">
              Próximos passos:
            </h3>
            <ul className="space-y-2" aria-label="Próximos passos">
              {summary.nextSteps.map((step, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400 font-['Open_Sans',sans-serif]"
                >
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-[10px] font-['Inter',sans-serif] font-medium text-gray-500 dark:text-gray-400 mt-0.5">
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
            className="w-full h-10 flex items-center justify-center rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm font-medium border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:outline-none font-['Open_Sans',sans-serif]"
          >
            Fechar
          </button>
        )}

        <div className="pt-2 border-t border-gray-100 dark:border-gray-700 text-center">
          <span className="text-[10px] text-gray-400 dark:text-gray-500 font-['Open_Sans',sans-serif]">
            Powered by <span className="text-[#60BED1] font-medium">LIA</span> · WeDOTalent
          </span>
        </div>
      </div>
    </div>
  )
}
