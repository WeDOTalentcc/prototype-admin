"use client"

/**
 * AgentActivityTimeline — live "what is the AI doing" feed (Fase 3, Manus-style).
 *
 * Subscribes to the decoupled `lia:agent-activity` window events emitted by
 * useChatSocket (Fase 1) and renders a rich timeline of tool calls as they run:
 * a spinner while a tool is running, ✓/✗ + duration when it finishes, and
 * reasoning step labels.
 *
 * 2026-06-04: reasoning steps are revealed one-by-one (paced) for the Manus
 * "constant movement" feel even when they arrive grouped; tools render
 * immediately (natural execution timing). `showFallback=false` makes it render
 * nothing when empty (so it can stay mounted alongside a streaming answer
 * without a stray spinner). The parent collapses it into AgentActivitySummary
 * ("N ações") once the turn completes.
 */

import React, { useEffect, useMemo, useRef, useState } from "react"
import { Loader2, CheckCircle2, XCircle, Brain } from "lucide-react"
import { useTranslations, useLocale } from "next-intl"
import { ThinkingStepsCard } from "./ThinkingStepsCard"
import { phaseLabel, toolLabel } from "./activity-labels"

interface ActivityItem {
  id: string
  kind: "tool" | "reasoning"
  name: string
  status: "running" | "ok" | "error"
  durationMs?: number
}

interface AgentActivityTimelineProps {
  fallbackSteps: string[]
  /** When false and there are no items yet, render nothing (no stray spinner)
   *  — used while the answer is already streaming. Default true (back-compat). */
  showFallback?: boolean
}

const REASONING_REVEAL_MS = 450

function formatMs(ms: number): string {
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`
}

export function AgentActivityTimeline({
  fallbackSteps,
  showFallback = true,
}: AgentActivityTimelineProps) {
  const t = useTranslations("chat.agentActivity")
  const locale = useLocale()
  const [items, setItems] = useState<ActivityItem[]>([])
  const reasoningQueueRef = useRef<ActivityItem[]>([])
  const drainTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    function startDrain() {
      if (drainTimerRef.current) return
      drainTimerRef.current = setInterval(() => {
        const next = reasoningQueueRef.current.shift()
        if (next) {
          setItems((prev) => [...prev, next])
        } else if (drainTimerRef.current) {
          clearInterval(drainTimerRef.current)
          drainTimerRef.current = null
        }
      }, REASONING_REVEAL_MS)
    }

    function onActivity(e: Event) {
      const detail = (e as CustomEvent).detail as Record<string, unknown> | undefined
      if (!detail || !detail.type) return
      const type = String(detail.type)
      const id = String(detail.tool_id || detail.name || `${type}-${Date.now()}`)
      const name = String(detail.name || "tool")

      if (type === "reasoning_step") {
        // Paced reveal — one card every REASONING_REVEAL_MS (constant movement).
        reasoningQueueRef.current.push({
          id: `reason-${id}-${reasoningQueueRef.current.length}`,
          kind: "reasoning",
          name: String(detail.label || ""),
          status: "ok",
        })
        startDrain()
        return
      }

      // Tools: immediate (natural execution timing — spinner → ✓).
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
        return prev
      })
    }

    window.addEventListener("lia:agent-activity", onActivity)
    return () => {
      window.removeEventListener("lia:agent-activity", onActivity)
      if (drainTimerRef.current) {
        clearInterval(drainTimerRef.current)
        drainTimerRef.current = null
      }
    }
  }, [])

  const toolCount = useMemo(
    () => items.filter((i) => i.kind === "tool").length,
    [items],
  )

  if (items.length === 0) {
    return showFallback ? <ThinkingStepsCard steps={fallbackSteps} /> : null
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
              {item.kind === "tool"
                ? toolLabel(item.name, locale)
                : phaseLabel(item.name, locale)}
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
