"use client"

import React from "react"
import { Minimize2, Layers, Maximize2 } from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { cardStyles } from "@/lib/design-tokens"
import type { ContextLevel } from "./types"

interface ContextLevelSelectProps {
  value: ContextLevel
  onChange: (level: ContextLevel) => void
}

export function ContextLevelSelect({ value, onChange }: ContextLevelSelectProps) {
  const t = useTranslations('agents.customAgents')

  const LEVELS: { value: ContextLevel; label: string; desc: string; icon: React.ReactNode }[] = [
    {
      value: "minimal",
      label: t('minimal'),
      desc: t('minimalDesc'),
      icon: <Minimize2 className="w-4 h-4" />,
    },
    {
      value: "standard",
      label: t('standard'),
      desc: t('standardDesc'),
      icon: <Layers className="w-4 h-4" />,
    },
    {
      value: "full",
      label: t('full'),
      desc: t('fullDesc'),
      icon: <Maximize2 className="w-4 h-4" />,
    },
  ]

  return (
    <div>
      <label className="text-xs font-semibold text-lia-text-primary mb-2 block">
        {t('contextLevel')}
      </label>
      <div className="grid grid-cols-3 gap-2">
        {LEVELS.map((level) => (
          <button
            key={level.value}
            type="button"
            onClick={() => onChange(level.value)}
            className={cn(
              value === level.value ? cardStyles.selected : cardStyles.interactive,
              "p-3 text-left"
            )}
          >
            <div className="flex items-center gap-1.5 mb-1">
              <span className={value === level.value ? "text-graphite" : "text-lia-text-disabled"}>
                {level.icon}
              </span>
              <span className="text-xs font-semibold text-lia-text-primary">{level.label}</span>
            </div>
            <p className="text-xs text-lia-text-secondary leading-tight">{level.desc}</p>
          </button>
        ))}
      </div>
    </div>
  )
}
