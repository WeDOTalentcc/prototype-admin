"use client"

import React, { useState } from "react"
import { cn } from "@/lib/utils"
import { Crown, Briefcase, HardHat, ChevronDown, Brain, Loader2 } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export type QualificationLevel = "alta" | "media" | "baixa"

interface QualificationBadgeProps {
  level: QualificationLevel | null
  confidence?: number
  reasoning?: string
  isOverride?: boolean
  onOverride?: (level: QualificationLevel) => void
  isClassifying?: boolean
  onClassify?: () => void
  showOverrideDropdown?: boolean
  size?: "sm" | "md"
}

const levelConfig = {
  alta: {
    label: "Alta",
    icon: Crown,
    className: "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-medium text-lia-text-secondary border border-wedo-purple/20",
    bgStyle: { background: "var(--wedo-purple-bg-10)" },
    darkClassName: "dark:text-wedo-purple dark:border-wedo-purple/30 dark:bg-wedo-purple/20",
    tooltipText: "Vaga de alta qualificação (executiva/especialista). Busca com maior precisão.",
  },
  media: {
    label: "Média",
    icon: Briefcase,
    className: "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-medium text-wedo-orange-text border border-wedo-orange/20",
    bgStyle: { background: "var(--wedo-orange-bg-10)" },
    darkClassName: "dark:text-wedo-orange dark:border-wedo-orange/30 dark:bg-wedo-orange/20",
    tooltipText: "Vaga de qualificação média (pleno/sênior). Busca com precisão balanceada.",
  },
  baixa: {
    label: "Baixa",
    icon: HardHat,
    className: "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-medium text-lia-text-primary border border-lia-border-subtle bg-lia-bg-tertiary",
    bgStyle: {},
    darkClassName: "dark:text-lia-text-secondary dark:border-lia-border-default dark:bg-lia-bg-secondary",
    tooltipText: "Vaga de qualificação básica (júnior/estágio). Busca com alcance amplo.",
  },
}

const levelOptions: { value: QualificationLevel; label: string }[] = [
  { value: "alta", label: "Alta Qualificação" },
  { value: "media", label: "Média Qualificação" },
  { value: "baixa", label: "Baixa Qualificação" },
]

export function QualificationBadge({
  level,
  confidence,
  reasoning,
  isOverride = false,
  onOverride,
  isClassifying = false,
  onClassify,
  showOverrideDropdown = true,
  size = "sm",
}: QualificationBadgeProps) {
  if (isClassifying) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-medium text-lia-text-secondary border border-lia-border-subtle bg-lia-bg-secondary dark:border-lia-border-default dark:bg-lia-bg-secondary">
        <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />
        Classificando...
      </span>
    )
  }

  if (!level) {
    return (
      <button
        onClick={onClassify}
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-medium text-lia-text-tertiary border border-dashed border-lia-border-default hover:border-lia-border-medium hover:text-lia-text-secondary transition-colors motion-reduce:transition-none cursor-pointer dark:border-lia-border-default dark:hover:border-lia-border-medium"
      >
        <Brain className="w-3 h-3 text-wedo-cyan" />
        Classificar
      </button>
    )
  }

  const config = levelConfig[level]
  const Icon = config.icon
  const iconSize = size === "sm" ? "w-3 h-3" : "w-3.5 h-3.5"

  const tooltipContent = (
    <div className="space-y-1 max-w-xs">
      <p className="font-medium">{config.label} Qualificação</p>
      {confidence !== undefined && (
        <p className="text-xs opacity-80">Confiança: {Math.round(confidence * 100)}%</p>
      )}
      {reasoning && <p className="text-xs opacity-80">{reasoning}</p>}
      {isOverride && <p className="text-xs italic opacity-70">Classificação manual</p>}
      <p className="text-xs opacity-60 mt-1">{config.tooltipText}</p>
    </div>
  )

  const badge = (
    <span
      className={cn(config.className, config.darkClassName)}
      style={config.bgStyle}
    >
      <Icon className={iconSize} />
      {config.label}
      {isOverride && <span className="opacity-60 ml-0.5">*</span>}
    </span>
  )

  if (showOverrideDropdown && onOverride) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <span>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="inline-flex items-center gap-0.5 cursor-pointer hover:opacity-80 transition-opacity motion-reduce:transition-none">
                    {badge}
                    <ChevronDown className="w-2.5 h-2.5 text-lia-text-tertiary" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="w-48">
                  {levelOptions.map((option) => {
                    const OptIcon = levelConfig[option.value].icon
                    return (
                      <DropdownMenuItem
                        key={option.value}
                        onClick={() => onOverride(option.value)}
                        className={cn(
                          "flex items-center gap-2 text-xs",
                          level === option.value && "font-semibold"
                        )}
                      >
                        <OptIcon className="w-3.5 h-3.5" />
                        {option.label}
                        {level === option.value && (
                          <span className="ml-auto text-micro text-lia-text-tertiary">atual</span>
                        )}
                      </DropdownMenuItem>
                    )
                  })}
                </DropdownMenuContent>
              </DropdownMenu>
            </span>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="bg-lia-btn-primary-bg text-lia-btn-primary-text text-xs rounded-md p-2">
            {tooltipContent}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>{badge}</TooltipTrigger>
        <TooltipContent side="bottom" className="bg-lia-btn-primary-bg text-lia-btn-primary-text text-xs rounded-md p-2">
          {tooltipContent}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
