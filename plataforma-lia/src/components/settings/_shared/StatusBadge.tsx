"use client"

import React from "react"

/**
 * StatusBadge — vocabulário ÚNICO de estado (Fase 5.5).
 *
 * Substitui os badges de TIPO concorrentes ("Prompt"/"Gate") por um indicador
 * de ESTADO consistente em todo o menu Configurações: ● Ativo / ○ Inativo.
 * O significado técnico (fail-closed, injeção em prompt) vai no title (tooltip),
 * não como rótulo concorrente.
 */
export function StatusBadge({
  active,
  title,
  activeLabel = "Ativo",
  inactiveLabel = "Inativo",
}: {
  active: boolean
  title?: string
  activeLabel?: string
  inactiveLabel?: string
}) {
  return (
    <span
      title={title}
      className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-medium ${
        active
          ? "bg-status-success/10 text-status-success border border-status-success/30"
          : "bg-lia-bg-tertiary text-lia-text-tertiary border border-lia-border-subtle"
      } ${title ? "cursor-help" : ""}`}
    >
      <span aria-hidden>{active ? "●" : "○"}</span>
      {active ? activeLabel : inactiveLabel}
    </span>
  )
}
