"use client"

import React, { useState, useCallback, useMemo } from "react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"

interface LikertScaleCardProps {
  question: string
  labels?: string[]
  onSelect: (value: number) => void
  disabled?: boolean
  className?: string
}

export function LikertScaleCard({
  question,
  labels,
  onSelect,
  disabled = false,
  className,
}: LikertScaleCardProps) {
  const t = useTranslations("triagem.likertScaleCard")
  const tDefaults = useTranslations("triagem.likertScaleCard.defaultLabels")
  const [selectedValue, setSelectedValue] = useState<number | null>(null)

  const effectiveLabels = useMemo(
    () =>
      labels && labels.length > 0
        ? labels
        : [
            tDefaults("stronglyDisagree"),
            tDefaults("disagree"),
            tDefaults("neutral"),
            tDefaults("agree"),
            tDefaults("stronglyAgree"),
          ],
    [labels, tDefaults]
  )

  const handleSelect = useCallback(
    (value: number) => {
      if (disabled || selectedValue !== null) return
      setSelectedValue(value)
      onSelect(value)
    },
    [disabled, selectedValue, onSelect]
  )

  const groupAria = question || t("groupAria")

  return (
    <div
      className={cn(
 "mx-4 my-2 space-y-3",
        className
      )}
      role="group"
      aria-label={groupAria}
    >
      {question && (
        <p className="text-sm text-lia-text-secondary">
          {question}
        </p>
      )}

      <div className="flex items-center justify-between gap-2">
        {[1, 2, 3, 4, 5].map((value) => {
          const isSelected = selectedValue === value
          return (
            <button
              key={value}
              type="button"
              onClick={() => handleSelect(value)}
              disabled={disabled || (selectedValue !== null && !isSelected)}
              aria-pressed={isSelected}
              aria-label={t("valueAria", { value, label: effectiveLabels[value - 1] || "" })}
              className={cn(
 "flex-1 min-w-[44px] h-11 flex items-center justify-center rounded-lg text-sm font-semibold font-['Inter',sans-serif] transition-colors duration-200 focus:ring-2 focus:ring-lia-btn-primary-bg/20 focus:outline-none",
                isSelected
                  ? "bg-lia-btn-primary-bg text-lia-btn-primary-text border border-lia-btn-primary-bg"
                  : "bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary border border-lia-border-default dark:border-lia-border-default hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-elevated",
                (disabled || (selectedValue !== null && !isSelected)) && "opacity-50 cursor-not-allowed"
              )}
            >
              {value}
            </button>
          )
        })}
      </div>

      <div className="flex justify-between">
        <span className="text-micro text-lia-text-muted">
          {effectiveLabels[0]}
        </span>
        <span className="text-micro text-lia-text-muted">
          {effectiveLabels[effectiveLabels.length - 1]}
        </span>
      </div>
    </div>
  )
}
