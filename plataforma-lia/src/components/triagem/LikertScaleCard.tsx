"use client"

import React, { useState, useCallback } from "react"
import { cn } from "@/lib/utils"

interface LikertScaleCardProps {
  question: string
  labels?: string[]
  onSelect: (value: number) => void
  disabled?: boolean
  className?: string
}

const DEFAULT_LABELS = [
  "Discordo totalmente",
  "Discordo",
  "Neutro",
  "Concordo",
  "Concordo totalmente",
]

export function LikertScaleCard({
  question,
  labels = DEFAULT_LABELS,
  onSelect,
  disabled = false,
  className,
}: LikertScaleCardProps) {
  const [selectedValue, setSelectedValue] = useState<number | null>(null)

  const handleSelect = useCallback(
    (value: number) => {
      if (disabled || selectedValue !== null) return
      setSelectedValue(value)
      onSelect(value)
    },
    [disabled, selectedValue, onSelect]
  )

  return (
    <div
      className={cn(
 "mx-4 my-2 space-y-3",
        className
      )}
      role="group"
      aria-label={question}
    >
      <p className="text-sm text-lia-text-secondary">
        {question}
      </p>

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
              aria-label={`${value} - ${labels[value - 1] || ""}`}
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
        <span className="text-micro text-lia-text-disabled">
          {labels[0]}
        </span>
        <span className="text-micro text-lia-text-disabled">
          {labels[labels.length - 1]}
        </span>
      </div>
    </div>
  )
}
