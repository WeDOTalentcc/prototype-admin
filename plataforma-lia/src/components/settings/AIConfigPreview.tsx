"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { Brain, User } from "lucide-react"
import { cn } from "@/lib/utils"
import { textStyles } from "@/lib/design-tokens"

interface AIConfigPreviewProps {
  tone: string
  compact?: boolean
  className?: string
}

export function AIConfigPreview({ tone, compact = false, className }: AIConfigPreviewProps) {
  const t = useTranslations("settings.aiPreview")

  const TONE_PREVIEWS: Record<string, { question: string; answer: string }> = {
    professional: { question: t("questionDev"), answer: t("answerProfessional") },
    casual:       { question: t("questionDev"), answer: t("answerCasual") },
    concise:      { question: t("questionDev"), answer: t("answerConcise") },
    detailed:     { question: t("questionDev"), answer: t("answerDetailed") },
  }

  const preview = TONE_PREVIEWS[tone] || TONE_PREVIEWS.professional

  return (
    <div className={cn("space-y-2", className)}>
      {!compact && (
        <p className={cn(textStyles.caption, "uppercase tracking-wider")}>{t("previewLabel")}</p>
      )}

      <div className="flex items-start gap-2">
        <div className="w-5 h-5 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-primary flex items-center justify-center flex-shrink-0 mt-0.5">
          <User className="w-3 h-3 text-lia-text-tertiary" aria-hidden="true" />
        </div>
        <p className={cn(textStyles.body, compact ? "text-[10px]" : "text-xs")}>
          {preview.question}
        </p>
      </div>

      <div className="flex items-start gap-2">
        <div className="w-5 h-5 rounded-full bg-wedo-cyan/15 dark:bg-wedo-cyan/20 flex items-center justify-center flex-shrink-0 mt-0.5">
          <Brain className="w-3 h-3 text-wedo-cyan" aria-hidden="true" />
        </div>
        <div
          className={cn(
            "border-l-2 border-wedo-cyan/30 pl-2.5 flex-1",
            compact ? "text-[10px]" : "text-xs"
          )}
        >
          <p className="text-lia-text-primary dark:text-lia-text-primary leading-relaxed">
            {preview.answer}
          </p>
        </div>
      </div>
    </div>
  )
}
