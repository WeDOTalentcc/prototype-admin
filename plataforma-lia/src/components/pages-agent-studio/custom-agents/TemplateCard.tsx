"use client"

import React from "react"
import * as Icons from "lucide-react"
import { Info } from "lucide-react"
import { useTranslations } from "next-intl"
import { badgeStyles, buttonStyles } from "@/lib/design-tokens"
import { cn } from "@/lib/utils"
import { StudioCardShell } from "../StudioCardShell"
import type { AgentTemplate, ContextLevel } from "./types"

interface TemplateCardProps {
  template: AgentTemplate
  onSelect: (template: AgentTemplate) => void
  /** Optional: customize action (outline). Defaults to onSelect. */
  onCustomize?: (template: AgentTemplate) => void
  /** Optional: preview action (ghost). Defaults to onSelect. */
  onPreview?: (template: AgentTemplate) => void
}

/**
 * Sprint visual 2026-05-26 (Paulo, Opção 2 — rich layout completo):
 *  - 3 métricas inline: Ferramentas / Passos máx / Contexto.
 *  - Alert sutil "Personalize antes de ativar" (neutral DS).
 *  - 3 botões hierarquia: Usar template (primary Ink) + Customizar (outline) +
 *    Preview (ghost). Card NÃO é asButton (botões internos individuais).
 *  - Consume <StudioCardShell> canonical com metaSlot + alertSlot + actionsSlot.
 *  - White-label: NUNCA cyan (memory project_white_label_ai_assistant).
 */

const CONTEXT_LABEL_KEY: Record<ContextLevel, string> = {
  minimal: "contextValue.minimal",
  standard: "contextValue.standard",
  full: "contextValue.full",
}

export function TemplateCard({
  template,
  onSelect,
  onCustomize,
  onPreview,
}: TemplateCardProps) {
  const t = useTranslations("agents.customAgents")
  const tRich = useTranslations("agents.customAgents.template.rich")
  const IconComponent = ((Icons as unknown as Record<string, React.ComponentType<{ className?: string }>>)[template.icon] || Icons.Bot)

  const handleUse = (e?: React.MouseEvent) => {
    e?.stopPropagation()
    onSelect(template)
  }
  const handleCustomize = (e?: React.MouseEvent) => {
    e?.stopPropagation()
    ;(onCustomize ?? onSelect)(template)
  }
  const handlePreview = (e?: React.MouseEvent) => {
    e?.stopPropagation()
    ;(onPreview ?? onSelect)(template)
  }

  const badges = template.tags.includes("popular") ? (
    <span className={badgeStyles.purple}>{t("popular")}</span>
  ) : undefined

  const metaSlot = (
    <div className="flex items-center gap-1.5 flex-wrap">
      <span className={badgeStyles.default}>
        {t("categories." + template.category) || template.category}
      </span>
    </div>
  )

  const metricsSlot = (
    <dl
      className="grid grid-cols-3 gap-2 text-xs"
      data-testid={`template-card-metrics-${template.id ?? template.name}`}
    >
      <div className="flex flex-col">
        <dt className="text-[10px] uppercase tracking-wide text-lia-text-secondary font-medium">
          {tRich("metricsLabel.tools")}
        </dt>
        <dd className="text-sm font-semibold text-lia-text-primary tabular-nums">
          {template.allowed_tools.length}
        </dd>
      </div>
      <div className="flex flex-col">
        <dt className="text-[10px] uppercase tracking-wide text-lia-text-secondary font-medium">
          {tRich("metricsLabel.maxSteps")}
        </dt>
        <dd className="text-sm font-semibold text-lia-text-primary tabular-nums">
          {template.max_steps}
        </dd>
      </div>
      <div className="flex flex-col">
        <dt className="text-[10px] uppercase tracking-wide text-lia-text-secondary font-medium">
          {tRich("metricsLabel.context")}
        </dt>
        <dd className="text-sm font-semibold text-lia-text-primary">
          {tRich(CONTEXT_LABEL_KEY[template.context_level])}
        </dd>
      </div>
    </dl>
  )

  const alertSlot = (
    <div
      className="flex items-start gap-2 rounded-md border border-lia-border-subtle bg-lia-bg-tertiary px-2.5 py-1.5"
      role="note"
    >
      <Info
        className="w-3 h-3 text-lia-text-secondary mt-0.5 flex-shrink-0"
        aria-hidden="true"
      />
      <p className="text-[11px] leading-snug text-lia-text-secondary">
        {tRich("alert.personalize")}
      </p>
    </div>
  )

  const bodySlot = (
    <p className="text-xs text-lia-text-secondary leading-relaxed line-clamp-2">
      {template.description}
    </p>
  )

  const actionsSlot = (
    <>
      <button
        type="button"
        onClick={handleUse}
        className={cn(buttonStyles.primary, "text-xs py-1.5 px-3")}
        data-testid={`template-card-use-${template.id ?? template.name}`}
      >
        {tRich("actions.use")}
      </button>
      <button
        type="button"
        onClick={handleCustomize}
        className={cn(buttonStyles.outline, "text-xs py-1.5 px-3")}
        data-testid={`template-card-customize-${template.id ?? template.name}`}
      >
        {tRich("actions.customize")}
      </button>
      <button
        type="button"
        onClick={handlePreview}
        className={cn(buttonStyles.ghost, "text-xs py-1.5 px-3 ml-auto")}
        data-testid={`template-card-preview-${template.id ?? template.name}`}
      >
        {tRich("actions.preview")}
      </button>
    </>
  )

  return (
    <StudioCardShell
      icon={<IconComponent className="w-4 h-4 text-lia-text-primary" />}
      title={template.name}
      badges={badges}
      metaSlot={metaSlot}
      bodySlot={bodySlot}
      metricsSlot={metricsSlot}
      alertSlot={alertSlot}
      actionsSlot={actionsSlot}
      data-testid={`template-card-${template.id ?? template.name}`}
    />
  )
}
