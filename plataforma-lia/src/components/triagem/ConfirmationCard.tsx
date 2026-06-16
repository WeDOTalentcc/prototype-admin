"use client"

import React from "react"
import { useTranslations } from "next-intl"
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
  const t = useTranslations("triagem.confirmationCard")
  return (
    <div
      className={cn(
 "mx-4 my-4 bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl shadow-lia-sm p-5 space-y-4",
        className
      )}
      role="dialog"
      aria-label={t("ariaLabel")}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-lia-bg-tertiary dark:bg-lia-bg-elevated flex items-center justify-center">
          <ClipboardCheck className="w-5 h-5 text-lia-text-secondary" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-lia-text-primary">
            {t("title")}
          </h3>
          <p className="text-xs text-lia-text-tertiary mt-1">
            {t("subtitle")}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 text-xs text-lia-text-tertiary font-['Inter',sans-serif]">
        <span>{t("questionsAnswered", { count: questionsAnswered })}</span>
        <span className="w-1 h-1 rounded-full bg-lia-border-default dark:bg-lia-border-medium" />
        <span>{t("minutesSummary", { count: durationMinutes })}</span>
      </div>

      <div className="flex gap-3">
        <button
          type="button"
          onClick={onReview}
          disabled={isSubmitting}
          aria-label={t("reviewAria")}
          className="flex-1 h-10 flex items-center justify-center rounded-lg bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary text-sm font-medium border border-lia-border-default dark:border-lia-border-default hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-elevated disabled:opacity-50 disabled:cursor-not-allowed transition-colors motion-reduce:transition-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 focus:outline-none"
        >
          {t("reviewLabel")}
        </button>
        <button
          type="button"
          onClick={onConfirm}
          disabled={isSubmitting}
          aria-label={t("confirmAria")}
          className="flex-1 h-10 flex items-center justify-center rounded-lg bg-lia-btn-primary-bg text-lia-btn-primary-text text-sm font-medium hover:bg-lia-btn-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors motion-reduce:transition-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 focus:outline-none"
        >
          {isSubmitting ? t("confirmLoading") : t("confirmLabel")}
        </button>
      </div>
    </div>
  )
}
