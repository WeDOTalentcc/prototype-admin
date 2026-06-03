"use client"

/**
 * AgentActivityTimeline — live "what is the AI doing" feed (Fase 3, Manus-style).
 *
 * Subscribes to the decoupled `lia:agent-activity` window events emitted by
 * useChatSocket (Fase 1) and renders a rich timeline of tool calls as they run:
 * a spinner while a tool is running, ✓/✗ + duration when it finishes, and
 * reasoning step labels.
 *
 * State resets naturally per turn: the parent only mounts this while
 * `isThinking` is true, so a fresh mount = a fresh turn (no manual reset / done
 * event needed). When there is no structured activity yet it falls back to the
 * existing <ThinkingStepsCard> so there is zero regression for plain spinners.
 */

import React, { useEffect, useMemo, useState } from "react"
import { Loader2, CheckCircle2, XCircle, Brain } from "lucide-react"
import { useTranslations } from "next-intl"
import { ThinkingStepsCard } from "./ThinkingStepsCard"

interface ActivityItem {
  id: string
  kind: "tool" | "reasoning"
  name: string
  status: "running" | "ok" | "error"
  durationMs?: number
}

interface AgentActivityTimelineProps {
  fallbackSteps: string[]
}

function humanizeTool(name: string): string {
  return name.replace(/[_-]+/g, " ").trim()
}

function formatMs(ms: number): string {
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`
}

export function AgentActivityTimeline({ fallbackSteps }: AgentActivityTimelineProps) {
  const t = useTranslations("chat.agentActivity")
  const [items, setItems] = useState<ActivityItem[]>([])

  useEffect(() => {
    function onActivity(e: Event) {
      const detail = (e as CustomEvent).detail as Record<string, unknown> | undefined
      if (!detail || !detail.type) return
      const type = String(detail.type)
      const id = String(detail.tool_id || detail.name || `${type}-${Date.now()}`)
      const name = String(detail.name || "tool")

      setItems((prev) => {
        if (type === "tool_started") {
          if (prev.some((i) => i.id === id)) return prev
          return [...prev, { id, kind: "tool", name, status: "running" }]
        }
        if (type === "tool_finished") {
          const next: ActivityItem = {
            id,
            kind: "tool",
            name,
            status: detail.status === "error" ? "error" : "ok",
            durationMs:
              typeof detail.duration_ms === "number" ? detail.duration_ms : undefined,
          }
          const idx = prev.findIndex((i) => i.id === id)
          if (idx >= 0) {
            const updated = [...prev]
            updated[idx] = next
            return updated
          }
          return [...prev, next]
        }
        if (type === "reasoning_step") {
          return [
            ...prev,
            {
              id: `reason-${prev.length}`,
              kind: "reasoning",
              name: String(detail.label || ""),
              status: "ok",
            },
          ]
        }
        return prev
      })
    }

    window.addEventListener("lia:agent-activity", onActivity)
    return () => window.removeEventListener("lia:agent-activity", onActivity)
  }, [])

  const toolCount = useMemo(
    () => items.filter((i) => i.kind === "tool").length,
    [items],
  )

  if (items.length === 0) {
    return <ThinkingStepsCard steps={fallbackSteps} />
  }

  return (
    <div
      className="rounded-xl border border-lia-border-subtle bg-lia-bg-tertiary p-3 animate-in fade-in slide-in-from-bottom-1 duration-200"
      role="status"
      aria-live="polite"
    >
      <div className="flex items-center gap-2 mb-2">
        <Loader2 className="w-4 h-4 text-wedo-cyan animate-spin motion-reduce:animate-none shrink-0" />
        <span className="text-xs font-medium text-lia-text-primary">
          {t("working")}
          {toolCount > 0 ? ` · ${t("actions", { count: toolCount })}` : ""}
        </span>
      </div>

      <ul className="space-y-1.5">
        {items.map((item) => (
          <li
            key={item.id}
            className="flex items-center gap-2 text-xs text-lia-text-secondary animate-in fade-in slide-in-from-left-1 duration-200"
          >
            {item.kind === "reasoning" ? (
              <Brain className="w-3.5 h-3.5 text-lia-text-secondary shrink-0" />
            ) : item.status === "running" ? (
              <Loader2 className="w-3.5 h-3.5 text-wedo-cyan animate-spin motion-reduce:animate-none shrink-0" />
            ) : item.status === "error" ? (
              <XCircle className="w-3.5 h-3.5 text-status-error shrink-0" />
            ) : (
              <CheckCircle2 className="w-3.5 h-3.5 text-status-success shrink-0" />
            )}
            <span className="truncate">
              {item.kind === "tool" ? humanizeTool(item.name) : item.name}
            </span>
            {item.durationMs != null && (
              <span className="ml-auto tabular-nums text-lia-text-secondary">
                {formatMs(item.durationMs)}
              </span>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
