"use client"

/**
 * AgentActivityTimeline — live "what is the AI doing" feed (Fase 3, Manus-style).
 *
 * Subscribes to the decoupled `lia:agent-activity` window events emitted by
 * useChatSocket (Fase 1) and renders ONE continuous, morphing timeline of the
 * turn: a paced reveal of reasoning + tool steps while the agent works, then a
 * graceful terminal "✓ N ações · Ts" frame that docks into the persistent
 * AgentActivitySummary in the message bubble.
 *
 * 2026-06-04 (timeline continuity pass): the four-box "substitution" feel is
 * gone — a single container morphs through the whole lifecycle.
 *
 * - Reveal is a single adaptive-cadence queue (reasoning + tools): the more
 *   steps are waiting, the faster they appear, so a grouped burst never loses
 *   the race against the final answer, while a lone step still gets a calm beat.
 * - Each step is shown exactly once in its current state, so sub-second tools no
 *   longer flicker running → done; genuinely slow tools still animate spinner →
 *   ✓ in place.
 * - `completed` (driven by the parent on the `message` event) fast-forwards any
 *   still-queued steps (nothing is lost), settles a lingering spinner, shows the
 *   terminal frame, then fires `onFinished` after a short grace so the parent
 *   unmounts gracefully instead of yanking the box mid-turn.
 * - `showFallback=false` makes it render nothing when empty (so it can stay
 *   mounted alongside a streaming answer without a stray spinner).
 */

import React, { useEffect, useMemo, useRef, useState } from "react"
import { Loader2, CheckCircle2, XCircle, Brain } from "lucide-react"
import { useTranslations, useLocale } from "next-intl"
import { cn } from "@/lib/utils"
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
  /** Turn finished — drain remaining queued steps, settle a running spinner,
   *  show the terminal "concluído" frame, then call onFinished after a short
   *  grace. Optional so legacy callers (lia-float) keep the old live behavior. */
  completed?: boolean
  /** Fired once the terminal frame has shown, so the parent can unmount the live
   *  timeline gracefully (instead of yanking it on the `message` event). */
  onFinished?: () => void
}

// Adaptive cadence (ms between reveals) keyed on how many steps are waiting.
const REVEAL_SLOW_MS = 420
const REVEAL_MID_MS = 240
const REVEAL_FAST_MS = 110
const FINISH_GRACE_MS = 750

function revealDelay(queueLen: number): number {
  if (queueLen > 6) return REVEAL_FAST_MS
  if (queueLen > 3) return REVEAL_MID_MS
  return REVEAL_SLOW_MS
}

function formatMs(ms: number): string {
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`
}

export function AgentActivityTimeline({
  fallbackSteps,
  showFallback = true,
  completed = false,
  onFinished,
}: AgentActivityTimelineProps) {
  const t = useTranslations("chat.agentActivity")
  const locale = useLocale()
  const [items, setItems] = useState<ActivityItem[]>([])
  const [phase, setPhase] = useState<"active" | "done">("active")

  const queueRef = useRef<ActivityItem[]>([])
  const seenToolIdsRef = useRef<Set<string>>(new Set())
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const finishTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const phaseRef = useRef<"active" | "done">("active")
  const hadItemsRef = useRef(false)
  const onFinishedRef = useRef(onFinished)

  useEffect(() => {
    onFinishedRef.current = onFinished
  }, [onFinished])

  useEffect(() => {
    function drainOne() {
      const next = queueRef.current.shift()
      if (next) setItems((prev) => [...prev, next])
      if (queueRef.current.length > 0) {
        timerRef.current = setTimeout(
          drainOne,
          revealDelay(queueRef.current.length),
        )
      } else {
        timerRef.current = null
      }
    }

    function scheduleDrain() {
      if (timerRef.current) return
      timerRef.current = setTimeout(drainOne, revealDelay(queueRef.current.length))
    }

    function applyToolFinish(
      id: string,
      name: string,
      status: "ok" | "error",
      durationMs?: number,
    ) {
      // Still waiting in the queue → settle it there so it reveals already-done.
      const queued = queueRef.current.find((i) => i.id === id)
      if (queued) {
        queued.status = status
        queued.durationMs = durationMs
        return
      }
      // Already visible → patch in place (spinner → ✓). Append if the finish
      // somehow arrived without a start (defensive, never fake a missing step).
      setItems((prev) => {
        const idx = prev.findIndex((i) => i.id === id)
        if (idx < 0) {
          return [...prev, { id, kind: "tool", name, status, durationMs }]
        }
        const updated = [...prev]
        updated[idx] = { ...updated[idx], status, durationMs }
        return updated
      })
    }

    function onActivity(e: Event) {
      const detail = (e as CustomEvent).detail as
        | Record<string, unknown>
        | undefined
      if (!detail || !detail.type) return
      const type = String(detail.type)

      // Turn already concluded (terminal frame showing): drop late trailing
      // events of THIS turn — the persistent AgentActivitySummary owns the final
      // record, and resetting here would cancel the pending onFinished hand-off
      // (stuck box). A genuinely NEW turn always flips `completed` true→false
      // first, which fully resets us via the effect below before events arrive.
      if (phaseRef.current === "done") return

      const id = String(detail.tool_id || detail.name || `${type}-${Date.now()}`)
      const name = String(detail.name || "tool")

      if (type === "reasoning_step") {
        queueRef.current.push({
          id: `reason-${id}-${queueRef.current.length}-${Date.now()}`,
          kind: "reasoning",
          name: String(detail.label || ""),
          status: "ok",
        })
        scheduleDrain()
        return
      }

      if (type === "tool_started") {
        if (seenToolIdsRef.current.has(id)) return
        seenToolIdsRef.current.add(id)
        queueRef.current.push({ id, kind: "tool", name, status: "running" })
        scheduleDrain()
        return
      }

      if (type === "tool_finished") {
        seenToolIdsRef.current.add(id)
        applyToolFinish(
          id,
          name,
          detail.status === "error" ? "error" : "ok",
          typeof detail.duration_ms === "number"
            ? (detail.duration_ms as number)
            : undefined,
        )
        return
      }
    }

    window.addEventListener("lia:agent-activity", onActivity)
    return () => {
      window.removeEventListener("lia:agent-activity", onActivity)
      if (timerRef.current) {
        clearTimeout(timerRef.current)
        timerRef.current = null
      }
      if (finishTimerRef.current) {
        clearTimeout(finishTimerRef.current)
        finishTimerRef.current = null
      }
    }
  }, [])

  // Graceful conclusion / re-activation, driven by the parent `completed` flag.
  useEffect(() => {
    if (completed) {
      if (phaseRef.current === "done") return
      // A turn with no reasoning/tool steps has no terminal frame worth holding,
      // so hand off almost immediately (the parent holds the answer during this
      // grace — a long blank for a bare reply would feel like a stall).
      const hadAny = hadItemsRef.current || queueRef.current.length > 0
      const grace = hadAny ? FINISH_GRACE_MS : 120
      // Fast-forward: reveal everything still queued so no reasoning step is
      // lost to the race with the final answer.
      if (timerRef.current) {
        clearTimeout(timerRef.current)
        timerRef.current = null
      }
      if (queueRef.current.length > 0) {
        const rest = queueRef.current.splice(0)
        setItems((prev) => [...prev, ...rest])
      }
      // Settle any tool still spinning at turn end (no stuck spinner).
      setItems((prev) =>
        prev.some((i) => i.status === "running")
          ? prev.map((i) =>
              i.status === "running" ? { ...i, status: "ok" } : i,
            )
          : prev,
      )
      phaseRef.current = "done"
      setPhase("done")
      finishTimerRef.current = setTimeout(() => {
        finishTimerRef.current = null
        onFinishedRef.current?.()
      }, grace)
    } else {
      // (Re)entering an active turn.
      if (finishTimerRef.current) {
        clearTimeout(finishTimerRef.current)
        finishTimerRef.current = null
      }
      if (phaseRef.current === "done") {
        // Coming out of a concluded turn — e.g. a rapid back-to-back send that
        // flips `completed` true→false before the grace window ended. Full reset
        // (items + queue + seen ids + pending reveal) so the previous turn's
        // steps never bleed into the new one.
        if (timerRef.current) {
          clearTimeout(timerRef.current)
          timerRef.current = null
        }
        queueRef.current = []
        seenToolIdsRef.current.clear()
        setItems([])
        phaseRef.current = "active"
        setPhase("active")
      }
    }
  }, [completed])

  const toolCount = useMemo(
    () => items.filter((i) => i.kind === "tool").length,
    [items],
  )
  const totalMs = useMemo(
    () => items.reduce((sum, i) => sum + (i.durationMs || 0), 0),
    [items],
  )
  // Keep the completed-effect's grace decision in sync with revealed steps.
  hadItemsRef.current = items.length > 0

  if (items.length === 0) {
    // Empty: show the unified "thinking" fallback while genuinely working;
    // render nothing once settled or while the answer already streams.
    return showFallback && phase === "active" ? (
      <ThinkingStepsCard steps={fallbackSteps} />
    ) : null
  }

  const isDone = phase === "done"
  // The active line is the last revealed step while the turn is still running —
  // it gets the spotlight (primary text + live icon) so the user reads one phrase
  // at a time, while completed steps recede into a calm muted stack above it.
  const activeIndex = isDone ? -1 : items.length - 1

  return (
    <div
      className="rounded-xl border border-lia-border-subtle bg-lia-bg-tertiary p-3 animate-in fade-in slide-in-from-bottom-1 duration-200"
      role="status"
      aria-live="polite"
    >
      <div className="flex items-center gap-2 mb-2.5">
        {isDone ? (
          <CheckCircle2 className="w-4 h-4 text-status-success shrink-0" />
        ) : (
          <Loader2 className="w-4 h-4 text-wedo-cyan animate-spin motion-reduce:animate-none shrink-0" />
        )}
        <span className="text-xs font-medium text-lia-text-primary">
          {isDone
            ? `${t("reasoning")} · ${t("steps", { count: items.length })}${
                totalMs > 0 ? ` · ${formatMs(totalMs)}` : ""
              }`
            : `${t("working")}${
                toolCount > 0 ? ` · ${t("actions", { count: toolCount })}` : ""
              }`}
        </span>
      </div>

      <ul className="space-y-1.5">
        {items.map((item, idx) => {
          const isActive = idx === activeIndex
          return (
            <li
              key={item.id}
              className={cn(
                "flex items-center gap-2 text-xs animate-in fade-in slide-in-from-left-1 duration-200",
                isActive
                  ? "text-lia-text-primary font-medium"
                  : "text-lia-text-secondary",
              )}
            >
              {item.kind === "reasoning" ? (
                <Brain
                  className={cn(
                    "w-3.5 h-3.5 shrink-0",
                    isActive
                      ? "text-wedo-cyan animate-pulse motion-reduce:animate-none"
                      : "text-lia-text-secondary",
                  )}
                />
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
          )
        })}
      </ul>
    </div>
  )
}
