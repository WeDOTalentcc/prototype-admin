"use client"

/**
 * AgentActivitySummary — persistent, collapsed summary of agent activity for a
 * completed turn (Fase 3 / Gap #3). Unlike AgentActivityTimeline (live, unmounts
 * at turn end), this renders inside the finished assistant message bubble from
 * the activity snapshot buffered into `message.metadata.agent_activity`, so the
 * "✓ N ações · 2.4s" stays in history and expands to the tool list on click.
 */

import React, { useMemo, useState } from "react"
import { ChevronDown, ChevronRight, CheckCircle2, XCircle, Brain } from "lucide-react"
import { useTranslations, useLocale } from "next-intl"
import { phaseLabel, toolLabel } from "./activity-labels"

export interface AgentActivityItem {
  kind: string // "tool" | "reasoning"
  name: string
  status: string // "ok" | "error"
  durationMs?: number
}

interface AgentActivitySummaryProps {
  items: AgentActivityItem[]
}

function fmt(ms?: number): string {
  if (ms == null) return ""
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`
}

export function AgentActivitySummary({ items }: AgentActivitySummaryProps) {
  const t = useTranslations("chat.agentActivity")
  const locale = useLocale()
  const [open, setOpen] = useState(false)
  const totalMs = useMemo(
    () => items.reduce((sum, i) => sum + (i.durationMs || 0), 0),
    [items],
  )

  if (!items.length) return null

  return (
    <div className="mt-2">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex items-center gap-1.5 text-xs text-lia-text-secondary hover:text-lia-text-primary transition-colors motion-reduce:transition-none"
      >
        {open ? (
          <ChevronDown className="w-3.5 h-3.5 shrink-0" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 shrink-0" />
        )}
        <CheckCircle2 className="w-3.5 h-3.5 text-status-success shrink-0" />
        <span>
          {t("actions", { count: items.length })}
          {totalMs > 0 ? ` · ${fmt(totalMs)}` : ""}
        </span>
      </button>

      {open && (
        <ul className="mt-1.5 ml-5 space-y-1 animate-in fade-in slide-in-from-top-1 duration-200">
          {items.map((item, idx) => (
            <li
              key={`${item.name}-${idx}`}
              className="flex items-center gap-2 text-xs text-lia-text-secondary"
            >
              {item.kind === "reasoning" ? (
                <Brain className="w-3 h-3 text-lia-text-secondary shrink-0" />
              ) : item.status === "error" ? (
                <XCircle className="w-3 h-3 text-status-error shrink-0" />
              ) : (
                <CheckCircle2 className="w-3 h-3 text-status-success shrink-0" />
              )}
              <span className="truncate">
                {item.kind === "tool"
                  ? toolLabel(item.name, locale)
                  : phaseLabel(item.name, locale)}
              </span>
              {item.durationMs != null && (
                <span className="ml-auto tabular-nums">{fmt(item.durationMs)}</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
