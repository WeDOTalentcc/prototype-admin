"use client"

import React from "react"
import * as Icons from "lucide-react"
import { useTranslations } from "next-intl"
import { badgeStyles, buttonStyles } from "@/lib/design-tokens"
import { cn } from "@/lib/utils"
import { summarizeCapabilities } from "@/lib/agents/tool-capabilities"
import { AgentConversationPreview } from "../AgentConversationPreview"
import type { AgentTemplate, ContextLevel } from "./types"

interface TemplateCardProps {
  template: AgentTemplate
  onSelect: (template: AgentTemplate) => void
  /** Optional: customize action (secondary). Defaults to onSelect. */
  onCustomize?: (template: AgentTemplate) => void
  /** Optional: preview action (ghost). Defaults to onSelect. */
  onPreview?: (template: AgentTemplate) => void
}

/**
 * Redesign 2026-05-30 (Paulo, crítica do recrutador): card didático com pegada
 * ElevenLabs dentro do design system "Quiet Operator".
 *
 *  - Descrição = herói: texto completo, sem truncação, hierarquia de destaque.
 *  - Identidade do agente: avatar tonal (powder bg + graphite icon) — dá "cara
 *    de agente". NUNCA cyan (white-label Studio: cor de marca reservada à
 *    assistente da plataforma quando ela age).
 *  - Metadados traduzidos para valor de recrutador: capacidades em PT
 *    (summarizeCapabilities) + linha discreta "Análise · Processa até N etapas".
 *    Nada de "Ferramentas: 4 / Passos máx: 8 / Contexto: Padrão" (jargão).
 *  - 3 botões claros: "Usar agora" (primary) / "Ajustar antes" (secondary) /
 *    "Ver detalhes" (ghost).
 *  - Flat-by-default: sem shadow em repouso; hover adiciona shadow-lia-md + lift.
 */

const DEPTH_VALUE_KEY: Record<ContextLevel, string> = {
  minimal: "depthValue.minimal",
  standard: "depthValue.standard",
  full: "depthValue.full",
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

  // Capacidades de alto nível em PT (2-3 bullets), derivadas das tools.
  const capabilities = summarizeCapabilities(template.allowed_tools)

  const testIdSuffix = template.id ?? template.name

  return (
    <div
      data-testid={`template-card-${testIdSuffix}`}
      className={cn(
        "group relative flex flex-col rounded-xl p-5",
        "bg-lia-bg-primary border border-lia-border-subtle",
        "transition-shadow duration-200 hover:shadow-lia-md",
        "dark:bg-lia-bg-secondary dark:border-lia-border-subtle",
      )}
    >
      {/* Header: avatar tonal + categoria + badge Popular */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-powder text-graphite dark:bg-lia-bg-tertiary dark:text-lia-text-primary"
            aria-hidden="true"
          >
            <IconComponent className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <h4 className="text-base font-semibold leading-tight text-lia-text-primary truncate">
              {template.name}
            </h4>
            <span className={cn(badgeStyles.default, "mt-1")}>
              {t("categories." + template.category) || template.category}
            </span>
          </div>
        </div>
        {template.tags.includes("popular") && (
          <span className={cn(badgeStyles.purple, "shrink-0")}>{t("popular")}</span>
        )}
      </div>

      {/* Descrição — herói: texto completo, sem truncação */}
      <p className="mt-4 text-sm leading-relaxed text-lia-text-primary">
        {template.description}
      </p>

      {/* O que faz — capacidades de alto nível em PT */}
      {capabilities.length > 0 && (
        <div className="mt-4">
          <p className="text-[10px] uppercase tracking-wide font-semibold text-lia-text-disabled">
            {tRich("capabilitiesEyebrow")}
          </p>
          <ul className="mt-1.5 space-y-1">
            {capabilities.map((cap) => (
              <li
                key={cap}
                className="flex items-start gap-2 text-xs text-lia-text-secondary"
              >
                <span
                  className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-lia-text-disabled"
                  aria-hidden="true"
                />
                <span>{cap}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Metadado discreto traduzido: profundidade + etapas */}
      <p className="mt-3 text-[11px] text-lia-text-disabled">
        {tRich("depthEyebrow")}: {tRich(DEPTH_VALUE_KEY[template.context_level])}
        {" · "}
        {tRich("stepsValue", { count: template.max_steps })}
      </p>

      {/* Nota sutil */}
      <p className="mt-3 text-[11px] leading-snug text-lia-text-secondary">
        {tRich("alert.personalize")}
      </p>

      {/* Veja em ação — conversa-exemplo compact, recolhida por padrão
          (Fase 3 Sprint 2). Decisão de densidade: o card já é rico (descrição
          herói + capacidades + metadado). Manter calmo no repouso e revelar a
          conversa inline sob demanda (sem modal) respeita o "Quiet Operator"
          e a 90/10. O modal de detalhe mostra a versão full. */}
      <details className="group mt-3" data-testid={`template-card-conversation-${testIdSuffix}`}>
        <summary className="flex cursor-pointer list-none items-center gap-1.5 text-[11px] font-medium text-lia-text-secondary transition-colors hover:text-lia-text-primary">
          <Icons.ChevronRight
            className="h-3.5 w-3.5 transition-transform group-open:rotate-90"
            aria-hidden="true"
          />
          {t("seeInActionLabel")}
        </summary>
        <div className="mt-2">
          <AgentConversationPreview
            slug={template.slug}
            category={template.category}
            compact
          />
        </div>
      </details>

      {/* Ações */}
      <div className="mt-auto pt-4 flex items-center gap-2">
        <button
          type="button"
          onClick={handleUse}
          className={cn(buttonStyles.primary, "text-xs py-1.5 px-3")}
          data-testid={`template-card-use-${testIdSuffix}`}
        >
          {tRich("actions.use")}
        </button>
        <button
          type="button"
          onClick={handleCustomize}
          className={cn(buttonStyles.secondary, "text-xs py-1.5 px-3")}
          data-testid={`template-card-customize-${testIdSuffix}`}
        >
          {tRich("actions.customize")}
        </button>
        <button
          type="button"
          onClick={handlePreview}
          className={cn(buttonStyles.ghost, "text-xs py-1.5 px-3 ml-auto")}
          data-testid={`template-card-preview-${testIdSuffix}`}
        >
          {tRich("actions.preview")}
        </button>
      </div>
    </div>
  )
}
