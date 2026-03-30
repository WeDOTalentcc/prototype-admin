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
            <span className={cn("text-xs", disabled ? "lia-text-400" : "lia-text-500")}>
              {value.length} stage{value.length !== 1 ? 's' : ''} selected
            </span>
          )}
        </div>
        {value.length > 0 && !disabled && (
          <button
            onClick={clearAll}
            className="text-xs lia-text-900 dark:lia-text-50 hover:lia-text-700 dark:hover:lia-text-300 font-medium"
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
                  ? "border-lia-border-subtle bg-gray-100 lia-text-400 cursor-not-allowed"
                  : isSelected 
                    ? "border-gray-900 dark:lia-border-50 bg-gray-100 dark:bg-lia-bg-secondary lia-text-900 dark:lia-text-50" 
                    : "border-lia-border-subtle bg-lia-bg-primary lia-text-600 hover:border-lia-border-default hover:bg-gray-50"
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
