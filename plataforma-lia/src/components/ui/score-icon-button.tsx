import React from "react"
import { cn } from "@/lib/utils"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface ScoreIconButtonProps {
  id: string
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>
  value: number | null | undefined
  formattedValue?: string
  label: string
  onClick: () => void
  disabled?: boolean
  alwaysClickable?: boolean
}

const LIA_SCORE_IDS = ["geral", "triagem", "cv"]

export const ScoreIconButton = React.memo(function ScoreIconButton({
  id,
  icon: Icon,
  value,
  formattedValue,
  label,
  onClick,
  disabled: externalDisabled,
  alwaysClickable = false
}: ScoreIconButtonProps) {
  const hasScore = value !== null && value !== undefined && value > 0
  const isClickable = alwaysClickable || hasScore
  const isDisabled = externalDisabled || !isClickable
  const displayValue = formattedValue || (hasScore ? String(value) : null)

  const isLiaScore = LIA_SCORE_IDS.includes(id)
  const activeColor = isLiaScore ? "var(--lia-text-primary)" : "var(--lia-text-secondary)"
  const inactiveColor = "var(--lia-border-medium)"

  const tooltipText = hasScore
    ? `${label}: ${displayValue}`
    : alwaysClickable
      ? `${label}: Clique para ver detalhes`
      : `${label}: Não disponível`

  const buttonContent = (
    <button
      type="button"
      onClick={isClickable ? onClick : undefined}
      disabled={isDisabled}
      className={cn(
        "flex items-center gap-1 transition-colors duration-200 outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-lia-border-medium rounded-full",
        isClickable
          ? "cursor-pointer hover:scale-105 hover:drop-active:scale-95"
          : "cursor-default opacity-25"
      )}
      aria-label={tooltipText}
    >
      <Icon
        className={cn("w-3.5 h-3.5")}
        style={{color: isClickable ? activeColor : inactiveColor}}
      />
      {hasScore && displayValue && (
        <span className="text-xs font-bold text-lia-text-secondary">
          {displayValue}
        </span>
      )}
    </button>
  )

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          {buttonContent}
        </TooltipTrigger>
        <TooltipContent>
          <p>{tooltipText}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
})
ScoreIconButton.displayName = "ScoreIconButton"
