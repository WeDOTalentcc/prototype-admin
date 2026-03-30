"use client"

import React from "react"
import { cn } from "@/lib/utils"
import { ClipboardCheck } from "lucide-react"

interface ConfirmationCardProps {
  questionsAnswered: number
  durationMinutes: number
  onConfirm: () => void
  onReview: () => void
  isSubmitting?: boolean
  className?: string
}

export function ConfirmationCard({
  questionsAnswered,
  durationMinutes,
  onConfirm,
  onReview,
  isSubmitting = false,
  className,
}: ConfirmationCardProps) {
  return (
    <div
      className={cn(
 "mx-4 my-4 bg-white dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md shadow-lia-sm p-5 space-y-4",
        className
      )}
      role="dialog"
      aria-label="Confirmação de finalização"
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 rounded-md bg-gray-100 dark:bg-lia-bg-elevated flex items-center justify-center">
          <ClipboardCheck className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-secondary" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif]">
            Chegamos ao final!
          </h3>
          <p className="text-xs text-lia-text-tertiary dark:text-lia-text-tertiary mt-1 font-['Open_Sans',sans-serif]">
            Quer revisar algo antes de concluir?
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 text-xs text-lia-text-tertiary dark:text-lia-text-tertiary font-['Inter',sans-serif]">
        <span>{questionsAnswered} perguntas respondidas</span>
        <span className="w-1 h-1 rounded-full bg-gray-300" />
        <span>{durationMinutes} minutos</span>
      </div>

      <div className="flex gap-3">
        <button
          type="button"
          onClick={onReview}
          disabled={isSubmitting}
          aria-label="Quero revisar minhas respostas"
          className="flex-1 h-10 flex items-center justify-center rounded-md bg-white dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-primary text-sm font-medium border border-lia-border-default dark:border-lia-border-default hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors motion-reduce:transition-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:outline-none font-['Open_Sans',sans-serif]"
        >
          Quero revisar
        </button>
        <button
          type="button"
          onClick={onConfirm}
          disabled={isSubmitting}
          aria-label="Finalizar triagem"
          className="flex-1 h-10 flex items-center justify-center rounded-md bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 dark:hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors motion-reduce:transition-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:outline-none font-['Open_Sans',sans-serif]"
        >
          {isSubmitting ? "Finalizando..." : "Finalizar Triagem"}
        </button>
      </div>
    </div>
  )
}
