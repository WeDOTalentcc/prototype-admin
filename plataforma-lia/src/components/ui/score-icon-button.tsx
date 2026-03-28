import React from "react"
import { cn } from "@/lib/utils"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface ScoreIconButtonProps {
  id: string // 'geral' | 'triagem' | 'cv' | 'tecnico' | 'ingles' | 'b5'
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>
  value: number | null | undefined
  formattedValue?: string // Valor formatado para exibição (ex: "85%")
  label: string
  onClick: () => void
  disabled?: boolean
  alwaysClickable?: boolean // Para modais como CV e Triagem que podem ser abertos mesmo sem score
}

const LIA_SCORE_IDS = ['geral', 'triagem', 'cv']

export function ScoreIconButton({
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
  const activeColor = isLiaScore ? 'var(--gray-950)' : 'var(--gray-600)'
  const inactiveColor = 'var(--gray-400)'

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
        "flex items-center gap-1 transition-all duration-200 outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-gray-400 rounded-full",
        isClickable 
          ? "cursor-pointer hover:scale-105 hover:drop-active:scale-95" 
          : "cursor-default opacity-25"
      )}
      aria-label={tooltipText}
    >
      <Icon 
        className={cn("w-3.5 h-3.5")} 
        style={{ color: isClickable ? activeColor : inactiveColor }} 
      />
      {hasScore && displayValue && (
        <span className="text-xs font-bold text-gray-700 dark:text-gray-300">
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
}
