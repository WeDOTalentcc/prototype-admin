"use client"

/**
 * AgentActivitySummary — persistent, collapsible record of agent activity for a
 * completed turn (Fase 3 / Gap #3). Unlike AgentActivityTimeline (live, unmounts
 * at turn end), this renders inside the finished assistant message from the
 * activity snapshot buffered into `message.metadata.agent_activity`, so the
 * reasoning trail stays in history (Replit/Manus-style) and expands to the full
 * step list on click — never a mute "N ações" that vanishes.
 */

import React, { useMemo, useState } from "react"
import { ChevronDown, ChevronRight, XCircle, Brain, Sparkles } from "lucide-react"
import { useTranslations, useLocale } from "next-intl"
import { cn } from "@/lib/utils"
import { phaseLabel, toolLabel, toolIcon } from "./activity-labels"

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
    <div className="mt-2 rounded-md border border-lia-border-subtle bg-lia-bg-secondary/40 overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex w-full items-center gap-2 px-2.5 py-1.5 text-xs text-lia-text-secondary hover:bg-lia-bg-tertiary/60 hover:text-lia-text-primary transition-colors motion-reduce:transition-none"
      >
        {open ? (
          <ChevronDown className="w-3.5 h-3.5 shrink-0" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 shrink-0" />
        )}
        <Sparkles className="w-3.5 h-3.5 text-wedo-cyan shrink-0" />
        <span className="font-medium text-lia-text-primary">{t("reasoning")}</span>
        <span className="text-lia-text-secondary">
          · {t("steps", { count: items.length })}
          {totalMs > 0 ? ` · ${fmt(totalMs)}` : ""}
        </span>
      </button>

      {open && (
        <ul className="px-3 pb-2.5 pt-0.5 space-y-1.5 border-t border-lia-border-subtle/60 animate-in fade-in slide-in-from-top-1 duration-200">
          {items.map((item, idx) => {
            const ToolIcon = toolIcon(item.name)
            return (
            <li
              key={`${item.name}-${idx}`}
              className={cn(
                "flex items-center gap-2 text-xs text-lia-text-secondary",
                idx === 0 && "pt-1.5",
              )}
            >
              {item.kind === "reasoning" ? (
                <Brain className="w-3.5 h-3.5 text-lia-text-secondary shrink-0" />
              ) : item.status === "error" ? (
                <XCircle className="w-3.5 h-3.5 text-status-error shrink-0" />
              ) : (
                <ToolIcon className="w-3.5 h-3.5 text-lia-text-secondary shrink-0" />
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
            )
          })}
        </ul>
      )}
    </div>
  )
}
