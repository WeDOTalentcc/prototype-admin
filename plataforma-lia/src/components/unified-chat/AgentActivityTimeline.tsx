"use client"

/**
 * AgentActivityTimeline — live "what is the AI doing" feed (Replit-style).
 *
 * Horizontal icon strip: each step appears as a chip that slides in from the
 * left. The active chip pulses cyan; completed chips fade to muted. A chevron
 * toggles between compact (icons only + active label) and expanded (full
 * vertical list with labels and durations).
 *
 * Subscribes to `lia:agent-activity` window events emitted by useChatSocket.
 */

import React, { useEffect, useRef, useState } from "react"
import { ChevronDown, ChevronRight, XCircle } from "lucide-react"
import { useLocale } from "next-intl"
import { cn } from "@/lib/utils"
import { ThinkingStepsCard, ActivityDots } from "./ThinkingStepsCard"
import { phaseLabel, toolLabel, toolIcon, phaseIcon } from "./activity-labels"

interface ActivityItem {
  id: string
  kind: "tool" | "reasoning"
  name: string
  status: "running" | "ok" | "error"
  durationMs?: number
}

interface AgentActivityTimelineProps {
  fallbackSteps: string[]
  showFallback?: boolean
  completed?: boolean
  onFinished?: () => void
}

const REVEAL_SLOW_MS = 420
const REVEAL_MID_MS = 240
const REVEAL_FAST_MS = 110
const FINISH_GRACE_MS = 750
const COMPLETION_REVEAL_MS = 300

function revealDelay(queueLen: number, finishing = false): number {
  if (finishing) {
    return Math.max(
      REVEAL_FAST_MS,
      Math.min(COMPLETION_REVEAL_MS, Math.floor(900 / Math.max(1, queueLen))),
    )
  }
  if (queueLen > 6) return REVEAL_FAST_MS
  if (queueLen > 3) return REVEAL_MID_MS
  return REVEAL_SLOW_MS
}

const _FB_TOOL_START = /^🔧\s*/
const _FB_TOOL_DONE = /^✓\s*/

function deriveItemsFromFallback(steps: string[]): ActivityItem[] {
  const out: ActivityItem[] = []
  const toolIdx = new Map<string, number>()
  for (const raw of steps) {
    const step = (raw ?? "").trim()
    if (!step) continue
    if (_FB_TOOL_START.test(step)) {
      const name = step.replace(_FB_TOOL_START, "").replace(/…$/, "").trim()
      if (!name) continue
      if (!toolIdx.has(name)) {
        toolIdx.set(name, out.length)
        out.push({ id: `fb-tool-${name}`, kind: "tool", name, status: "running" })
      }
    } else if (_FB_TOOL_DONE.test(step)) {
      const name = step.replace(_FB_TOOL_DONE, "").trim()
      if (!name) continue
      const at = toolIdx.get(name)
      if (at != null) out[at].status = "ok"
      else {
        toolIdx.set(name, out.length)
        out.push({ id: `fb-tool-${name}`, kind: "tool", name, status: "ok" })
      }
    } else {
      out.push({ id: `fb-reason-${out.length}`, kind: "reasoning", name: step, status: "ok" })
    }
  }
  return out
}

function formatMs(ms: number): string {
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`
}

function ItemIcon({ item, active }: { item: ActivityItem; active: boolean }) {
  if (item.status === "error") {
    return <XCircle className="w-4 h-4 text-status-error" aria-hidden="true" />
  }
  const Icon = item.kind === "reasoning" ? phaseIcon(item.name) : toolIcon(item.name)
  return (
    <Icon
      className={cn(
        "w-4 h-4 transition-colors duration-300",
        active
          ? "text-lia-text-secondary"
          : "text-lia-text-secondary",
      )}
      aria-hidden="true"
    />
  )
}

function HorizontalChip({
  item,
  active,
  entering,
}: {
  item: ActivityItem
  active: boolean
  entering: boolean
}) {
  return (
    <div
      className={cn(
        "flex items-center justify-center w-7 h-7 rounded-lg transition-all duration-300",
        active
          ? "bg-lia-bg-secondary animate-pulse motion-reduce:animate-none"
          : "bg-lia-bg-secondary/60",
        entering && "animate-in fade-in zoom-in-75 slide-in-from-left-2 duration-300",
      )}
    >
      <ItemIcon item={item} active={active} />
    </div>
  )
}

function ExpandedLine({
  item,
  active,
  locale,
}: {
  item: ActivityItem
  active: boolean
  locale: string
}) {
  return (
    <li
      className={cn(
        "flex items-center gap-2 text-xs animate-in fade-in slide-in-from-left-1 duration-200",
        active ? "text-lia-text-secondary" : "text-lia-text-secondary/50",
      )}
    >
      <ItemIcon item={item} active={active} />
      <span className="truncate">
        {item.kind === "tool" ? toolLabel(item.name, locale) : phaseLabel(item.name, locale)}
      </span>
      {active && <ActivityDots className="shrink-0" />}
      {item.durationMs != null && (
        <span className="ml-auto tabular-nums text-lia-text-secondary">
          {formatMs(item.durationMs)}
        </span>
      )}
    </li>
  )
}

export function AgentActivityTimeline({
  fallbackSteps,
  showFallback = true,
  completed = false,
  onFinished,
}: AgentActivityTimelineProps) {
  const locale = useLocale()
  const [items, setItems] = useState<ActivityItem[]>([])
  const [phase, setPhase] = useState<"active" | "done">("active")
  const [expanded, setExpanded] = useState(false)

  const queueRef = useRef<ActivityItem[]>([])
  const seenToolIdsRef = useRef<Set<string>>(new Set())
  const seenPhasesRef = useRef<Set<string>>(new Set())
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const finishTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const phaseRef = useRef<"active" | "done">("active")
  const completedRef = useRef(false)
  const everHadItemsRef = useRef(false)
  const scheduleDrainRef = useRef<(() => void) | null>(null)
  const finalizeRef = useRef<(() => void) | null>(null)
  const onFinishedRef = useRef(onFinished)
  const enteringIdsRef = useRef<Set<string>>(new Set())

  useEffect(() => {
    onFinishedRef.current = onFinished
  }, [onFinished])

  useEffect(() => {
    function finalize() {
      if (phaseRef.current === "done") return
      setItems((prev) =>
        prev.some((i) => i.status === "running")
          ? prev.map((i) => (i.status === "running" ? { ...i, status: "ok" } : i))
          : prev,
      )
      phaseRef.current = "done"
      setPhase("done")
      const grace = everHadItemsRef.current ? FINISH_GRACE_MS : 120
      finishTimerRef.current = setTimeout(() => {
        finishTimerRef.current = null
        onFinishedRef.current?.()
      }, grace)
    }
    finalizeRef.current = finalize

    function drainOne() {
      const next = queueRef.current.shift()
      if (next) {
        enteringIdsRef.current.add(next.id)
        setTimeout(() => enteringIdsRef.current.delete(next.id), 350)
        setItems((prev) => [...prev, next])
      }
      if (queueRef.current.length > 0) {
        timerRef.current = setTimeout(
          drainOne,
          revealDelay(queueRef.current.length, completedRef.current),
        )
      } else {
        timerRef.current = null
        if (completedRef.current) finalize()
      }
    }

    function scheduleDrain() {
      if (timerRef.current) return
      timerRef.current = setTimeout(
        drainOne,
        revealDelay(queueRef.current.length, completedRef.current),
      )
    }
    scheduleDrainRef.current = scheduleDrain

    function applyToolFinish(
      id: string,
      name: string,
      status: "ok" | "error",
      durationMs?: number,
    ) {
      const queued = queueRef.current.find((i) => i.id === id)
      if (queued) {
        queued.status = status
        queued.durationMs = durationMs
        return
      }
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
      const detail = (e as CustomEvent).detail as Record<string, unknown> | undefined
      if (!detail || !detail.type) return
      const type = String(detail.type)
      if (phaseRef.current === "done") return

      const id = String(detail.tool_id || detail.name || `${type}-${Date.now()}`)
      const name = String(detail.name || "tool")

      if (type === "reasoning_step") {
        const phaseKey = String(detail.label || "")
        if (seenPhasesRef.current.has(phaseKey)) return
        seenPhasesRef.current.add(phaseKey)
        everHadItemsRef.current = true
        queueRef.current.push({
          id: `reason-${id}-${queueRef.current.length}-${Date.now()}`,
          kind: "reasoning",
          name: phaseKey,
          status: "ok",
        })
        scheduleDrain()
        return
      }

      if (type === "tool_started") {
        if (seenToolIdsRef.current.has(id)) return
        seenToolIdsRef.current.add(id)
        everHadItemsRef.current = true
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
          typeof detail.duration_ms === "number" ? (detail.duration_ms as number) : undefined,
        )
        return
      }
    }

    window.addEventListener("lia:agent-activity", onActivity)
    return () => {
      window.removeEventListener("lia:agent-activity", onActivity)
      if (timerRef.current) { clearTimeout(timerRef.current); timerRef.current = null }
      if (finishTimerRef.current) { clearTimeout(finishTimerRef.current); finishTimerRef.current = null }
    }
  }, [])

  useEffect(() => {
    if (completed) {
      if (phaseRef.current === "done") return
      completedRef.current = true
      if (queueRef.current.length > 0) {
        scheduleDrainRef.current?.()
      } else if (!timerRef.current) {
        finalizeRef.current?.()
      }
    } else {
      const wasCompleted = completedRef.current
      completedRef.current = false
      if (finishTimerRef.current) { clearTimeout(finishTimerRef.current); finishTimerRef.current = null }
      if (wasCompleted) {
        if (timerRef.current) { clearTimeout(timerRef.current); timerRef.current = null }
        queueRef.current = []
        seenToolIdsRef.current.clear()
        seenPhasesRef.current.clear()
        everHadItemsRef.current = false
        enteringIdsRef.current.clear()
        setItems([])
        setExpanded(false)
        phaseRef.current = "active"
        setPhase("active")
      }
    }
  }, [completed])

  const fbItems = React.useMemo(() => deriveItemsFromFallback(fallbackSteps), [fallbackSteps])
  const [fbReveal, setFbReveal] = useState(0)
  useEffect(() => {
    if (fbItems.length === 0) { if (fbReveal !== 0) setFbReveal(0); return }
    if (fbReveal + 1 >= fbItems.length) return
    const tmr = setTimeout(() => setFbReveal((n) => n + 1), revealDelay(fbItems.length - fbReveal))
    return () => clearTimeout(tmr)
  }, [fbItems, fbReveal])

  const displayItems = items.length > 0 ? items : fbItems.slice(0, fbReveal + 1)
  const isUsingFallback = items.length === 0

  if (displayItems.length === 0) {
    if (!(showFallback && phase === "active")) return null
    return <ThinkingStepsCard steps={fallbackSteps} />
  }

  const isDone = phase === "done"
  const activeIndex = isDone ? -1 : displayItems.length - 1
  const activeItem = activeIndex >= 0 ? displayItems[activeIndex] : null

  return (
    <div className="animate-in fade-in slide-in-from-bottom-1 duration-200">
      <div className="flex items-start gap-1.5">
        {displayItems.length > 1 && (
          <button
            type="button"
            onClick={() => setExpanded((o) => !o)}
            aria-expanded={expanded}
            className="mt-0.5 p-0.5 rounded hover:bg-lia-bg-secondary/60 transition-colors shrink-0"
            aria-label={expanded ? "Colapsar detalhes" : "Expandir detalhes"}
          >
            {expanded ? (
              <ChevronDown className="w-3.5 h-3.5 text-lia-text-secondary" />
            ) : (
              <ChevronRight className="w-3.5 h-3.5 text-lia-text-secondary" />
            )}
          </button>
        )}

        {!expanded && (
          <div className="flex flex-col gap-1 min-w-0">
            <div className="flex items-center gap-1 flex-wrap" role="status" aria-live="polite">
              {displayItems.map((item, idx) => (
                <HorizontalChip
                  key={item.id}
                  item={item}
                  active={!isDone && idx === activeIndex}
                  entering={enteringIdsRef.current.has(item.id)}
                />
              ))}
            </div>
            {activeItem && !isDone && (
              <span className="text-xs text-lia-text-secondary flex items-center gap-1 truncate">
                {activeItem.kind === "tool"
                  ? toolLabel(activeItem.name, locale)
                  : phaseLabel(activeItem.name, locale)}
                <ActivityDots className="shrink-0" />
              </span>
            )}
            {isDone && (
              <span className="text-xs text-lia-text-secondary">
                {displayItems.length} {displayItems.every((i) => i.kind === "tool") ? "actions" : "passos"}
              </span>
            )}
          </div>
        )}

        {expanded && (
          <ul className="space-y-1.5 min-w-0 flex-1" role="status" aria-live="polite">
            {displayItems.map((item, idx) => (
              <ExpandedLine
                key={item.id}
                item={item}
                active={!isDone && idx === activeIndex}
                locale={locale}
              />
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
