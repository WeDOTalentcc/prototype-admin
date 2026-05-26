"use client"

import React from "react"
import * as Icons from "lucide-react"
import { useTranslations } from "next-intl"
import { badgeStyles } from "@/lib/design-tokens"
import { StudioCardShell } from "../StudioCardShell"
import type { AgentTemplate } from "./types"

interface TemplateCardProps {
  template: AgentTemplate
  onSelect: (template: AgentTemplate) => void
}

/**
 * Sprint visual 2026-05-25 (Paulo, Opção A canonical):
 *  - Consume <StudioCardShell> canonical (slots) em vez de layout próprio.
 *  - Badge "Popular": cyan → wedo-purple (insight-purple #9860D1). Cyan é
 *    exclusiva da assistente quando age (white-label decision, memory
 *    `project_white_label_ai_assistant.md`). Studio neutro.
 */
export function TemplateCard({ template, onSelect }: TemplateCardProps) {
  const t = useTranslations("agents.customAgents")
  const IconComponent = ((Icons as unknown as Record<string, React.ComponentType<{ className?: string }>>)[template.icon] || Icons.Bot)

  const badges = template.tags.includes("popular") ? (
    <span className={badgeStyles.purple}>{t("popular")}</span>
  ) : undefined

  const metaSlot = (
    <div className="flex items-center gap-1.5 flex-wrap">
      <span className={badgeStyles.default}>
        {t("categories." + template.category) || template.category}
      </span>
      <span className={badgeStyles.default}>
        {t("toolsCount", { count: template.allowed_tools.length })}
      </span>
    </div>
  )

  const bodySlot = (
    <p className="text-xs text-lia-text-secondary leading-relaxed line-clamp-2">
      {template.description}
    </p>
  )

  return (
    <StudioCardShell
      icon={<IconComponent className="w-4 h-4 text-graphite" />}
      title={template.name}
      badges={badges}
      bodySlot={bodySlot}
      metaSlot={metaSlot}
      asButton
      onClick={() => onSelect(template)}
      ariaLabel={template.name}
      data-testid={`template-card-${template.id ?? template.name}`}
    />
  )
}
