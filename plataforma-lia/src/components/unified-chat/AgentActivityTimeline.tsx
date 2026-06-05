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
import {
  Loader2,
  CheckCircle2,
  XCircle,
  Brain,
  ChevronRight,
  ChevronDown,
} from "lucide-react"
import { useTranslations, useLocale } from "next-intl"
import { cn } from "@/lib/utils"
import { ThinkingStepsCard } from "./ThinkingStepsCard"
import { phaseLabel, toolLabel, toolIcon } from "./activity-labels"

interface ActivityItem {
  id: string
  kind: "tool" | "reasoning"
  name: string
  status: "running" | "ok" | "error"
  durationMs?: number
}

/**
 * Ícone de uma linha de atividade (estilo Replit/Manus):
 * - erro → X vermelho (sempre destaca)
 * - raciocínio → cérebro (cyan + pulse no foco, esmaecido quando recua)
 * - ferramenta → ícone POR TIPO (lupa, gráfico, lista…); cyan no foco,
 *   esmaecido quando concluída/recolhida.
 */
function ActivityLineIcon({
  item,
  spotlight,
}: {
  item: ActivityItem
  spotlight: boolean
}) {
  const base = "w-3.5 h-3.5 shrink-0"
  if (item.status === "error") {
    return <XCircle className={cn(base, "text-status-error")} aria-hidden="true" />
  }
  if (item.kind === "reasoning") {
    return (
      <Brain
        className={cn(
          base,
          spotlight
            ? "text-wedo-cyan animate-pulse motion-reduce:animate-none"
            : "text-lia-text-secondary",
        )}
        aria-hidden="true"
      />
    )
  }
  const Icon = toolIcon(item.name)
  return (
    <Icon
      className={cn(
        base,
        spotlight
          ? cn(
              "text-wedo-cyan",
              item.status === "running" &&
                "animate-pulse motion-reduce:animate-none",
            )
          : "text-lia-text-secondary",
      )}
      aria-hidden="true"
    />
  )
}

/** Uma linha da timeline. `spotlight` = a ação em foco (texto primário + cyan). */
function ActivityLine({
  item,
  spotlight,
  locale,
}: {
  item: ActivityItem
  spotlight: boolean
  locale: string
}) {
  return (
    <li
      className={cn(
        "flex items-center gap-2 text-xs animate-in fade-in slide-in-from-left-1 duration-200",
        spotlight
          ? "text-lia-text-primary font-medium"
          : "text-lia-text-secondary",
      )}
    >
      <ActivityLineIcon item={item} spotlight={spotlight} />
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
// When the turn already completed we keep revealing remaining steps one-by-one
// (the live, "written-out" feel) — the parent holds the answer until we hand
// off — but on a tighter, budgeted cadence so the answer is never delayed long.
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
  // Fases de raciocínio já vistas neste turno (dedupe — o agentic_loop reemite
  // "understanding"/"composing" a cada iteração). Resetado junto com os tools.
  const seenPhasesRef = useRef<Set<string>>(new Set())
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const finishTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const phaseRef = useRef<"active" | "done">("active")
  const completedRef = useRef(false)
  const everHadItemsRef = useRef(false)
  const scheduleDrainRef = useRef<(() => void) | null>(null)
  const finalizeRef = useRef<(() => void) | null>(null)
  const onFinishedRef = useRef(onFinished)
  // Estilo Replit: enquanto trabalha, as ações concluídas recuam para um contador
  // discreto ("N concluídas"), que o usuário pode expandir. Default recolhido.
  const [showCompleted, setShowCompleted] = useState(false)

  useEffect(() => {
    onFinishedRef.current = onFinished
  }, [onFinished])

  useEffect(() => {
    function finalize() {
      if (phaseRef.current === "done") return
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
      // A turn with no steps has no terminal frame worth holding — hand off
      // almost immediately (the parent holds the answer during this grace, so a
      // long blank for a bare reply would feel like a stall).
      const grace = everHadItemsRef.current ? FINISH_GRACE_MS : 120
      finishTimerRef.current = setTimeout(() => {
        finishTimerRef.current = null
        onFinishedRef.current?.()
      }, grace)
    }
    finalizeRef.current = finalize

    function drainOne() {
      const next = queueRef.current.shift()
      if (next) setItems((prev) => [...prev, next])
      if (queueRef.current.length > 0) {
        timerRef.current = setTimeout(
          drainOne,
          revealDelay(queueRef.current.length, completedRef.current),
        )
      } else {
        timerRef.current = null
        // Queue fully revealed. If the turn already completed, the parent is
        // holding the answer for us — so now show the terminal frame and hand off
        // (this is what lets even a fast turn play its steps out one-by-one).
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
        const phaseKey = String(detail.label || "")
        // Dedupe: cada fase aparece UMA vez por turno (já enfileirada/revelada
        // OU já vista). seenPhasesRef cobre o caso de a fase reaparecer depois
        // de já ter sido drenada da fila para os items.
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
      completedRef.current = true
      // DON'T fast-forward/dump the queue. The parent now holds the answer until
      // our `onFinished`, so we have time to keep revealing the remaining steps
      // one at a time (the live, "written-out" feel the user wants) and only then
      // show the terminal frame and hand off. If the drain loop is already
      // running it will finalize itself when the queue empties; if there's
      // nothing left to reveal, finalize right away.
      if (queueRef.current.length > 0) {
        scheduleDrainRef.current?.()
      } else if (!timerRef.current) {
        finalizeRef.current?.()
      }
    } else {
      // (Re)entering an active turn.
      const wasCompleted = completedRef.current
      completedRef.current = false
      if (finishTimerRef.current) {
        clearTimeout(finishTimerRef.current)
        finishTimerRef.current = null
      }
      if (wasCompleted) {
        // Coming out of a turn that had already completed — e.g. a rapid
        // back-to-back send that flips `completed` true→false. This covers BOTH
        // the fully-concluded case (phase "done") AND the case where the prior
        // turn was still pacing out its queued steps (phase still "active"): in
        // either case a full reset (items + queue + seen ids + pending reveal)
        // is required so the previous turn's steps never bleed into the new one.
        if (timerRef.current) {
          clearTimeout(timerRef.current)
          timerRef.current = null
        }
        queueRef.current = []
        seenToolIdsRef.current.clear()
        seenPhasesRef.current.clear()
        everHadItemsRef.current = false
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

  if (items.length === 0) {
    // Empty: show the unified "thinking" fallback while genuinely working;
    // render nothing once settled or while the answer already streams.
    return showFallback && phase === "active" ? (
      <ThinkingStepsCard steps={fallbackSteps} />
    ) : null
  }

  const isDone = phase === "done"
  // Linha em foco (Replit/Manus): enquanto roda, só a ÚLTIMA ação revelada fica em
  // destaque; as anteriores recuam para o contador discreto. No frame terminal
  // (isDone) a trilha completa é exibida brevemente antes de docar no resumo
  // persistente (AgentActivitySummary), que é a pílula colapsada do histórico.
  const activeIndex = isDone ? -1 : items.length - 1
  const completedItems = isDone ? [] : items.slice(0, activeIndex)
  const spotlightItem = isDone ? null : items[activeIndex]

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

      {isDone ? (
        <ul className="space-y-1.5">
          {items.map((item) => (
            <ActivityLine
              key={item.id}
              item={item}
              spotlight={false}
              locale={locale}
            />
          ))}
        </ul>
      ) : (
        <div className="space-y-1.5">
          {completedItems.length > 0 && (
            <>
              <button
                type="button"
                onClick={() => setShowCompleted((o) => !o)}
                aria-expanded={showCompleted}
                className="flex items-center gap-1 text-[11px] text-lia-text-secondary hover:text-lia-text-primary transition-colors motion-reduce:transition-none"
              >
                {showCompleted ? (
                  <ChevronDown className="w-3 h-3 shrink-0" />
                ) : (
                  <ChevronRight className="w-3 h-3 shrink-0" />
                )}
                <span>{t("done", { count: completedItems.length })}</span>
              </button>
              {showCompleted && (
                <ul className="space-y-1.5 ml-1.5 border-l border-lia-border-subtle/60 pl-2 animate-in fade-in slide-in-from-top-1 duration-200">
                  {completedItems.map((item) => (
                    <ActivityLine
                      key={item.id}
                      item={item}
                      spotlight={false}
                      locale={locale}
                    />
                  ))}
                </ul>
              )}
            </>
          )}
          {spotlightItem && (
            <ul>
              <ActivityLine
                key={spotlightItem.id}
                item={spotlightItem}
                spotlight
                locale={locale}
              />
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
