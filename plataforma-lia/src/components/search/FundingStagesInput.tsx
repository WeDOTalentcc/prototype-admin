"use client"

import { useCallback } from "react"
import { cn } from "@/lib/utils"

interface FundingStagesInputProps {
  value: string[]
  onChange: (stages: string[]) => void
  disabled?: boolean
}

const FUNDING_STAGES = [
  { value: 'pre-seed', label: 'Pre-Seed' },
  { value: 'seed', label: 'Seed' },
  { value: 'series-a', label: 'Series A' },
  { value: 'series-b', label: 'Series B' },
  { value: 'series-c', label: 'Series C' },
  { value: 'series-d-plus', label: 'Series D+' },
  { value: 'growth', label: 'Growth' },
  { value: 'ipo', label: 'IPO' },
  { value: 'acquired', label: 'Acquired' },
  { value: 'private-equity', label: 'Private Equity' },
]

export function FundingStagesInput({
  value,
  onChange,
  disabled = false,
}: FundingStagesInputProps) {
  const toggleStage = useCallback((stage: string) => {
    if (disabled) return
    if (value.includes(stage)) {
      onChange(value.filter(s => s !== stage))
    } else {
      onChange([...value, stage])
    }
  }, [value, onChange, disabled])

  const clearAll = useCallback(() => {
    if (disabled) return
    onChange([])
  }, [onChange, disabled])

  return (
    <div className={cn("space-y-3", disabled && "pointer-events-none")}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {value.length > 0 && (
            <span className={cn("text-xs", disabled ? "text-lia-text-tertiary" : "text-lia-text-secondary")}>
              {value.length} stage{value.length !== 1 ? 's' : ''} selected
            </span>
          )}
        </div>
        {value.length > 0 && !disabled && (
          <button
            onClick={clearAll}
            className="text-xs text-lia-text-primary hover:text-lia-text-primary font-medium"
          >
            Clear all
          </button>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        {FUNDING_STAGES.map(stage => {
          const isSelected = value.includes(stage.value)
          return (
            <button
              key={stage.value}
              disabled={disabled}
              onClick={() => toggleStage(stage.value)}
              className={cn(
                "px-3 py-1.5 rounded-full text-xs font-medium border transition-[width,height]",
                disabled
                  ? "border-lia-border-subtle bg-lia-bg-tertiary text-lia-text-tertiary cursor-not-allowed"
                  : isSelected 
                    ? "border-lia-btn-primary-bg dark:border-lia-border-subtle bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary" 
                    : "border-lia-border-subtle bg-lia-bg-primary text-lia-text-secondary hover:border-lia-border-default hover:bg-lia-bg-secondary"
              )}
            >
              {stage.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default FundingStagesInput
