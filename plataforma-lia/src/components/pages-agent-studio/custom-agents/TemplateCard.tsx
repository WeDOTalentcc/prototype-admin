"use client"

import React from "react"
import * as Icons from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { cardStyles, badgeStyles, textStyles } from "@/lib/design-tokens"
import type { AgentTemplate } from "./types"

interface TemplateCardProps {
  template: AgentTemplate
  onSelect: (template: AgentTemplate) => void
}

export function TemplateCard({ template, onSelect }: TemplateCardProps) {
  const t = useTranslations('agents.customAgents')
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const IconComponent = ((Icons as any)[template.icon] || Icons.Bot) as React.ComponentType<{ className?: string }>

  return (
    <button
      type="button"
      onClick={() => onSelect(template)}
      className={cn(
        cardStyles.interactive,
        "p-4 text-left w-full flex flex-col gap-2 group"
      )}
    >
      <div className="flex items-start justify-between">
        <div className="w-9 h-9 rounded-md bg-powder flex items-center justify-center shrink-0">
          <IconComponent className="w-4 h-4 text-graphite" />
        </div>
        {template.tags.includes("popular") && (
          <span className={badgeStyles.cyan}>{t('popular')}</span>
        )}
      </div>

      <div>
        <h4 className={cn(textStyles.subtitle, "text-sm font-semibold leading-tight")}>
          {template.name}
        </h4>
        <p className={cn(textStyles.caption, "mt-1 text-xs leading-relaxed line-clamp-2")}>
          {template.description}
        </p>
      </div>

      <div className="flex items-center gap-1.5 mt-auto pt-1">
        <span className={cn(badgeStyles.default, "text-[10px]")}>
          {t('categories.' + template.category) || template.category}
        </span>
        <span className={cn(badgeStyles.default, "text-[10px]")}>
          {t('toolsCount', { count: template.allowed_tools.length })}
        </span>
      </div>
    </button>
  )
}
