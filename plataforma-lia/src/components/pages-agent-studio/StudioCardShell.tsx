"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { cardStyles } from "@/lib/design-tokens"

/**
 * Agent Studio canonical card shell — Sprint visual 2026-05-25.
 *
 * Decisão Paulo Opção A canonical: extrair shell estrutural a partir do
 * "card rico" do AgentPanel (Captação > AgentsTab), padronizando cabeçalho,
 * corpo e ações pra todo card do Studio. NÃO substitui cardStyles canonical
 * () — compõe a partir dele.
 *
 * DS aderência ("Quiet Operator", DESIGN.md):
 *  - paper bg + border mist + rounded-md (cardStyles.default/interactive)
 *  - Open Sans (textStyles canonical usadas pelos consumidores)
 *  - flat-by-default, hover lift sutil quando 
 *  - ícone canonical: wrapper w-8 h-8 em bg-powder rounded-md (consistente
 *    com AgentCard + TemplateCard — padroniza após Sprint visual)
 *
 * Slots renderizados condicionalmente:
 *   - header: icon + title + subtitle + badges + statusBadge
 *   - metricsSlot: grid metrics (analisados / aprovados / taxa)
 *   - metaSlot: meta lines (setor / categoria / tools)
 *   - alertSlot: callout sutil ("Sem vínculo", "Pronto pra customizar")
 *   - chipsSlot: strategy chips / tags
 *   - bodySlot: freeform extras (timeline, descrição estendida)
 *   - actionsSlot: footer actions row
 */
export type StudioCardShellProps = {
  icon: React.ReactNode
  title: string
  subtitle?: React.ReactNode
  badges?: React.ReactNode
  statusBadge?: React.ReactNode
  metricsSlot?: React.ReactNode
  metaSlot?: React.ReactNode
  alertSlot?: React.ReactNode
  chipsSlot?: React.ReactNode
  bodySlot?: React.ReactNode
  actionsSlot?: React.ReactNode
  onClick?: () => void
  interactive?: boolean
  className?: string
  /** Render as <button> (default false → renders <div>). Use when entire card is clickable. */
  asButton?: boolean
  /** ARIA label when asButton. */
  ariaLabel?: string
  /** Optional test id. */
  "data-testid"?: string
}

export function StudioCardShell({
  icon,
  title,
  subtitle,
  badges,
  statusBadge,
  metricsSlot,
  metaSlot,
  alertSlot,
  chipsSlot,
  bodySlot,
  actionsSlot,
  onClick,
  interactive,
  className,
  asButton,
  ariaLabel,
  "data-testid": testId,
}: StudioCardShellProps) {
  const baseStyle = interactive || asButton ? cardStyles.interactive : cardStyles.default

  const inner = (
    <>
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-md bg-powder flex items-center justify-center shrink-0">
            {icon}
          </div>
          <div className="min-w-0">
            <h4 className="text-sm font-semibold leading-tight text-lia-text-primary truncate">
              {title}
            </h4>
            {(subtitle || statusBadge) && (
              <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
                {statusBadge}
                {subtitle && (
                  <span className="text-xs text-lia-text-disabled">{subtitle}</span>
                )}
              </div>
            )}
          </div>
        </div>
        {badges && <div className="flex items-center gap-1.5 shrink-0">{badges}</div>}
      </div>

      {/* Body sections */}
      {metricsSlot && <div className="mt-3">{metricsSlot}</div>}
      {metaSlot && <div className="mt-3">{metaSlot}</div>}
      {alertSlot && <div className="mt-3">{alertSlot}</div>}
      {chipsSlot && <div className="mt-3">{chipsSlot}</div>}
      {bodySlot && <div className="mt-3">{bodySlot}</div>}

      {/* Actions footer */}
      {actionsSlot && (
        <div className="mt-3 pt-3 border-t border-lia-border-subtle flex items-center gap-2 flex-wrap">
          {actionsSlot}
        </div>
      )}
    </>
  )

  if (asButton) {
    return (
      <button
        type="button"
        onClick={onClick}
        aria-label={ariaLabel}
        data-testid={testId}
        className={cn(baseStyle, "p-4 text-left w-full flex flex-col", className)}
      >
        {inner}
      </button>
    )
  }

  return (
    <div
      onClick={onClick}
      data-testid={testId}
      className={cn(
        baseStyle,
        "p-4 flex flex-col",
        onClick && "cursor-pointer",
        className,
      )}
    >
      {inner}
    </div>
  )
}
