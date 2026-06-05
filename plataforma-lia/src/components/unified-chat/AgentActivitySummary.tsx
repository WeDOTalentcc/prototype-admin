"use client"

/**
 * AgentActivitySummary — registro persistente e clean (estilo Replit) da
 * atividade do agente num turno concluído. Diferente da AgentActivityTimeline
 * (ao vivo, desmonta no fim do turno), renderiza dentro da mensagem finalizada
 * a partir do snapshot em `message.metadata.agent_activity`, mantendo a trilha
 * no histórico. Colapsado: ícones-prévia das ações + contagem (sem card, sem a
 * palavra "Raciocínio"); clica e expande a lista completa.
 */

import React, { useMemo, useState } from "react"
import { ChevronDown, ChevronRight, XCircle } from "lucide-react"
import type { LucideIcon } from "lucide-react"
import { useTranslations, useLocale } from "next-intl"
import { cn } from "@/lib/utils"
import { phaseLabel, toolLabel, toolIcon, phaseIcon } from "./activity-labels"

export interface AgentActivityItem {
  kind: string // "tool" | "reasoning"
  name: string
  status: string // "ok" | "error"
  durationMs?: number
}

interface AgentActivitySummaryProps {
  items: AgentActivityItem[]
}

const MAX_PREVIEW_ICONS = 4

function fmt(ms?: number): string {
  if (ms == null) return ""
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`
}

/** Ícone por TIPO (erro = X vermelho, fase = ícone de raciocínio, tool = ícone
 *  por tipo). O estado é comunicado pela cor no componente que renderiza. */
function iconFor(item: AgentActivityItem): LucideIcon {
  if (item.status === "error") return XCircle
  return item.kind === "reasoning" ? phaseIcon(item.name) : toolIcon(item.name)
}

export function AgentActivitySummary({ items }: AgentActivitySummaryProps) {
  const t = useTranslations("chat.agentActivity")
  const locale = useLocale()
  const [open, setOpen] = useState(false)
  const totalMs = useMemo(
    () => items.reduce((sum, i) => sum + (i.durationMs || 0), 0),
    [items],
  )
  // Só ferramentas → "N ações"; mistura com raciocínio → "N passos".
  const allTools = useMemo(
    () => items.length > 0 && items.every((i) => i.kind === "tool"),
    [items],
  )

  if (!items.length) return null

  const countLabel = allTools
    ? t("actions", { count: items.length })
    : t("steps", { count: items.length })
  const preview = items.slice(0, MAX_PREVIEW_ICONS)

  return (
    <div className="mt-1.5">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="group flex items-center gap-1.5 -mx-1.5 rounded-md px-1.5 py-1 text-xs text-lia-text-secondary hover:bg-lia-bg-secondary/60 hover:text-lia-text-primary transition-colors motion-reduce:transition-none"
      >
        {open ? (
          <ChevronDown className="w-3.5 h-3.5 shrink-0" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 shrink-0" />
        )}
        {!open && (
          <span className="flex items-center gap-1" aria-hidden="true">
            {preview.map((item, idx) => {
              const Icon = iconFor(item)
              return (
                <Icon
                  key={`${item.name}-${idx}`}
                  className={cn(
                    "w-3.5 h-3.5 shrink-0",
                    item.status === "error"
                      ? "text-status-error"
                      : "text-lia-text-secondary",
                  )}
                />
              )
            })}
          </span>
        )}
        <span>
          {countLabel}
          {totalMs > 0 ? ` · ${fmt(totalMs)}` : ""}
        </span>
      </button>

      {open && (
        <ul className="mt-1 space-y-1.5 pl-5 animate-in fade-in slide-in-from-top-1 duration-200">
          {items.map((item, idx) => {
            const Icon = iconFor(item)
            return (
              <li
                key={`${item.name}-${idx}`}
                className="flex items-center gap-2 text-xs text-lia-text-secondary"
              >
                <Icon
                  className={cn(
                    "w-3.5 h-3.5 shrink-0",
                    item.status === "error"
                      ? "text-status-error"
                      : "text-lia-text-secondary",
                  )}
                  aria-hidden="true"
                />
                <span className="truncate">
                  {item.kind === "tool"
                    ? toolLabel(item.name, locale)
                    : phaseLabel(item.name, locale)}
                </span>
                {item.durationMs != null && (
                  <span className="ml-auto tabular-nums">
                    {fmt(item.durationMs)}
                  </span>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
