"use client"

import React, { useState, useCallback } from "react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import type { TriagemMessageOption } from "@/components/triagem/types"

interface MultipleChoiceCardProps {
  question: string
  options: TriagemMessageOption[]
  onSelect: (optionId: string, optionLabel: string) => void
  disabled?: boolean
  className?: string
}

export function MultipleChoiceCard({
  question,
  options,
  onSelect,
  disabled = false,
  className,
}: MultipleChoiceCardProps) {
  const t = useTranslations("triagem.multipleChoiceCard")
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const handleSelect = useCallback(
    (option: TriagemMessageOption) => {
      if (disabled || selectedId) return
      setSelectedId(option.id)
      onSelect(option.id, option.label)
    },
    [disabled, selectedId, onSelect]
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
      <div className="flex flex-col gap-2">
        {options.map((option) => {
          const isSelected = selectedId === option.id
          return (
            <button
              key={option.id}
              type="button"
              onClick={() => handleSelect(option)}
              disabled={disabled || (!!selectedId && !isSelected)}
              aria-pressed={isSelected}
              aria-label={option.label}
              className={cn(
 "w-full min-h-[44px] px-4 py-3 text-sm text-left rounded-lg font-medium transition-colors duration-200 focus:ring-2 focus:ring-lia-btn-primary-bg/20 focus:outline-none",
                isSelected
                  ? "bg-lia-btn-primary-bg text-lia-btn-primary-text border border-lia-btn-primary-bg"
                  : "bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary border border-lia-border-default dark:border-lia-border-default hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-elevated",
                (disabled || (!!selectedId && !isSelected)) && "opacity-50 cursor-not-allowed"
              )}
            >
              {option.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}
