"use client"

import React, { useEffect, useRef, useState, useCallback } from "react"
import { useTranslations } from "next-intl"
import {
  ArrowRight, Zap, Check, X, Sun, Moon,
  ChevronLeft, ChevronRight, MoreHorizontal, GripVertical,
  PanelRight, MessageSquare, Maximize2, Minus,
} from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import { useWorkflowRail, WorkflowEntry } from "./useWorkflowRail"
import { useWorkflowRailStore } from "@/stores/workflow-rail-store"
import { useActiveChatPresence } from "@/hooks/useActiveChatPresence"
import type { ChatMode } from "@/components/unified-chat/unified-chat-types"
import {
  FUNNEL_STAGES,
  NEXT_STEPS_MAP,
  FunnelStageKey,
  NextStep,
  mapCampaignStageToFunnelKey,
} from "./workflowRailCatalog"
import {
  trackWorkflowRailNextStepClick,
  trackWorkflowRailPanelToggle,
  type PanelToggleSource,
} from "./workflowRailAnalytics"
import { loadLastStage, saveLastStage } from "./lastStageStorage"

interface WorkflowRailProps {
  userId: string
  onNavigate: (path: string) => void
  onCreateJob?: () => void
  /** Kept for compatibility; the rail now uses its own collapse/expand model. */
  showBackToChat?: boolean
}

/** Derive the current funnel stage key from the list of active workflow entries. */
function deriveCurrentStage(entries: WorkflowEntry[]): FunnelStageKey {
  if (entries.length === 0) return "initial"
  const latest = entries[0]
  if (latest.type === "search") return "sourcing"
  const inProgress = latest.stages?.find(s => s.status === "in_progress")
  return mapCampaignStageToFunnelKey(inProgress?.stage ?? latest.currentStage)
}

const BALL_SIZE = 36
const DRAG_THRESHOLD = 4 // px before drag is considered a real drag (vs a click)

/** Chat mode → indicator icon + tooltip label. */
const CHAT_MODE_META: Record<ChatMode, { Icon: React.ComponentType<{ className?: string; strokeWidth?: number; "aria-hidden"?: boolean }>; label: string }> = {
  sidebar:    { Icon: PanelRight,     label: "Chat aberto na lateral" },
  floating:   { Icon: MessageSquare,  label: "Chat em janela flutuante" },
  fullscreen: { Icon: Maximize2,      label: "Chat em tela cheia" },
  minimized:  { Icon: Minus,          label: "Chat minimizado" },
}

export default function WorkflowRail({ userId, onNavigate, onCreateJob }: WorkflowRailProps) {
  const { entries, isConnected } = useWorkflowRail(userId)
  const { mode: chatMode, isShowingReels, isChatVisible, focusChat } = useActiveChatPresence()

  // Global UI state (persisted) — toggled from sidebar and from collapse button.
  const enabled = useWorkflowRailStore((s) => s.enabled)
  const expanded = useWorkflowRailStore((s) => s.expanded)
  const setExpanded = useWorkflowRailStore((s) => s.setExpanded)
  const position = useWorkflowRailStore((s) => s.position)
  const setPosition = useWorkflowRailStore((s) => s.setPosition)

  const [isPopoverOpen, setIsPopoverOpen] = useState(false)
  const [currentStageKey, setCurrentStageKey] = useState<FunnelStageKey>("initial")
  const [hoveredKey, setHoveredKey] = useState<FunnelStageKey | null>(null)
  const [canScrollL, setCanScrollL] = useState(false)
  const [canScrollR, setCanScrollR] = useState(false)
  const [isDark, setIsDark] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [mounted, setMounted] = useState(false)
  const t = useTranslations()
  const containerRef = useRef<HTMLDivElement | null>(null)
  const scrollRef = useRef<HTMLDivElement | null>(null)
  const firstNextStepRef = useRef<HTMLButtonElement | null>(null)

  // Drag bookkeeping (refs so handlers stay stable).
  const dragOriginRef = useRef<{ x: number; y: number; px: number; py: number } | null>(null)
  const movedRef = useRef(false)

  const hasEntries = entries.length > 0
  const pendingCount = entries.filter(e => e.pendingAction).length

  /* ---- Avoid hydration mismatch: persisted store reads after mount only ---- */
  useEffect(() => { setMounted(true) }, [])

  /* ---- Hydrate last known stage from localStorage (per user) ----
     Always reset state from storage when the user changes, so the previous
     user's stage never leaks into the new user's session. `hydratedFor`
     gates the persist effect so writes only happen once React has applied
     the hydrated value (and the gate is in state, not a ref, so it triggers
     the persist effect when it flips). `lastSavedRef` tracks the most
     recently persisted value so passive hydration does NOT refresh the
     stored timestamp — staleness reflects last meaningful change only. */
  const [hydratedFor, setHydratedFor] = useState<string | null>(null)
  const lastSavedRef = useRef<{ userId: string; stage: FunnelStageKey } | null>(null)
  useEffect(() => {
    if (!mounted) return
    setHydratedFor(null)
    const stored = loadLastStage(userId)
    lastSavedRef.current = { userId, stage: stored }
    setCurrentStageKey(stored)
    setHydratedFor(userId)
  }, [mounted, userId])

  /* ---- Sync current stage from real-time entries ----
     When there are active entries, derive from them. When there are none,
     keep the last known stage (loaded from storage / set by user actions)
     instead of forcing "initial" on every render. */
  useEffect(() => {
    if (entries.length === 0) return
    setCurrentStageKey(deriveCurrentStage(entries))
  }, [entries])

  /* ---- Persist current stage when it actually changes ----
     Only writes after hydration has completed for the *current* userId
     (preventing a stale stage from a previous user being saved under a
     new user's key when userId switches), and skips writes when the value
     matches what was last saved/loaded so passive page loads don't refresh
     the staleness timestamp. */
  useEffect(() => {
    if (!mounted || !userId) return
    if (hydratedFor !== userId) return
    const last = lastSavedRef.current
    if (last && last.userId === userId && last.stage === currentStageKey) return
    saveLastStage(userId, currentStageKey)
    lastSavedRef.current = { userId, stage: currentStageKey }
  }, [mounted, userId, hydratedFor, currentStageKey])

  /* ---- Helper: toggle popover state and emit a tracked analytics event.
         Use this for *user-initiated* opens/closes. The auto-collapse
         effect (when active entries disappear) bypasses tracking on
         purpose. ---- */
  const setPopoverOpenTracked = useCallback(
    (next: boolean, source: PanelToggleSource) => {
      setIsPopoverOpen((prev) => {
        if (prev !== next) trackWorkflowRailPanelToggle(next, currentStageKey, source)
        return next
      })
    },
    [currentStageKey],
  )

  /** Toggle helper that uses the functional form internally so rapid
   *  successive clicks before a re-render can't drop a transition. */
  const togglePopoverTracked = useCallback(
    (source: PanelToggleSource) => {
      setIsPopoverOpen((prev) => {
        const next = !prev
        trackWorkflowRailPanelToggle(next, currentStageKey, source)
        return next
      })
    },
    [currentStageKey],
  )

  /* ---- Close popover on outside click ---- */
  useEffect(() => {
    if (!isPopoverOpen) return
    const onDown = (e: MouseEvent) => {
      if (!containerRef.current) return
      if (!containerRef.current.contains(e.target as Node)) setPopoverOpenTracked(false, "outside-click")
    }
    document.addEventListener("mousedown", onDown)
    return () => document.removeEventListener("mousedown", onDown)
  }, [isPopoverOpen, setPopoverOpenTracked])

  /* ---- Close popover on Esc ---- */
  useEffect(() => {
    if (!isPopoverOpen) return
    const onKey = (e: globalThis.KeyboardEvent) => { if (e.key === "Escape") setPopoverOpenTracked(false, "escape") }
    document.addEventListener("keydown", onKey)
    return () => document.removeEventListener("keydown", onKey)
  }, [isPopoverOpen, setPopoverOpenTracked])

  /* ---- Focus first next-step when popover opens ---- */
  useEffect(() => {
    if (isPopoverOpen) setTimeout(() => firstNextStepRef.current?.focus(), 50)
  }, [isPopoverOpen])

  /* ---- Auto-collapse popover when last active entry disappears mid-session ---- */
  const prevHasEntriesRef = useRef(hasEntries)
  useEffect(() => {
    const wasTracking = prevHasEntriesRef.current && currentStageKey !== "initial"
    if (!hasEntries && isPopoverOpen && wasTracking) setIsPopoverOpen(false)
    prevHasEntriesRef.current = hasEntries
  }, [hasEntries, isPopoverOpen, currentStageKey])

  /* ---- Scroll overflow detection (chip strip) ---- */
  const updateScroll = useCallback(() => {
    const el = scrollRef.current
    if (!el) return
    setCanScrollL(el.scrollLeft > 4)
    setCanScrollR(el.scrollLeft + el.clientWidth < el.scrollWidth - 4)
  }, [])

  useEffect(() => {
    updateScroll()
    const el = scrollRef.current
    if (!el) return
    el.addEventListener("scroll", updateScroll, { passive: true })
    const ro = new ResizeObserver(updateScroll)
    ro.observe(el)
    return () => { el.removeEventListener("scroll", updateScroll); ro.disconnect() }
  }, [updateScroll, entries.length, hoveredKey, expanded])

  const scrollBy = (dir: 1 | -1) => {
    scrollRef.current?.scrollBy({ left: dir * 140, behavior: "smooth" })
  }

  /* ---- Handle next-step action ---- */
  const handleNextStep = useCallback((step: NextStep) => {
    trackWorkflowRailNextStepClick(currentStageKey, step)
    setPopoverOpenTracked(false, "next-step-click")
    if (step.actionType === "handler") {
      if (step.handlerId === "createJob" && onCreateJob) onCreateJob()
    } else if (step.path) {
      onNavigate(step.path)
    }
    // Always persist on a rail action — even when the resulting stage equals
    // the current one, this refreshes the stored timestamp so the entry stays
    // fresh (and won't be treated as stale on next visit). The state update
    // alone wouldn't trigger the persist effect when the value is unchanged.
    const nextStage = step.resultingStage ?? currentStageKey
    if (step.resultingStage) setCurrentStageKey(step.resultingStage)
    if (userId) saveLastStage(userId, nextStage)
  }, [onNavigate, onCreateJob, userId, currentStageKey, setPopoverOpenTracked])

  /* ---- Drag handlers (used for both ball and expanded bar) ---- */
  const onPointerDown = useCallback((e: React.PointerEvent) => {
    // Ignore drags that start on interactive children (buttons inside the bar).
    const target = e.target as HTMLElement
    if (target.closest("button,a,input")) return
    const el = containerRef.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    dragOriginRef.current = {
      x: e.clientX,
      y: e.clientY,
      px: rect.left,
      py: rect.top,
    }
    movedRef.current = false
    ;(e.currentTarget as HTMLElement).setPointerCapture?.(e.pointerId)
  }, [])

  const onPointerMove = useCallback((e: React.PointerEvent) => {
    const origin = dragOriginRef.current
    if (!origin) return
    const dx = e.clientX - origin.x
    const dy = e.clientY - origin.y
    if (!movedRef.current && Math.hypot(dx, dy) < DRAG_THRESHOLD) return
    movedRef.current = true
    setIsDragging(true)
    // Clamp to viewport with a small padding.
    const el = containerRef.current
    const w = el?.offsetWidth ?? BALL_SIZE
    const h = el?.offsetHeight ?? BALL_SIZE
    const maxX = window.innerWidth - w - 8
    const maxY = window.innerHeight - h - 8
    const nextX = Math.max(8, Math.min(maxX, origin.px + dx))
    const nextY = Math.max(8, Math.min(maxY, origin.py + dy))
    setPosition({ x: nextX, y: nextY })
  }, [setPosition])

  const onPointerUp = useCallback((e: React.PointerEvent) => {
    const wasDragging = movedRef.current
    dragOriginRef.current = null
    movedRef.current = false
    setIsDragging(false)
    ;(e.currentTarget as HTMLElement).releasePointerCapture?.(e.pointerId)
    return wasDragging
  }, [])

  // Click handler for the ball — only if no drag happened.
  const onBallPointerUp = useCallback((e: React.PointerEvent) => {
    const wasDragging = onPointerUp(e)
    if (!wasDragging) setExpanded(true)
  }, [onPointerUp, setExpanded])

  /* ---- Early returns ---- */
  if (!mounted) return null
  if (!enabled) return null
  if (!hasEntries && !onCreateJob) return null
  // Coexistência: se o chat está visível e mostrando o trilho interno
  // (ChatWorkflowReels no empty state), suprime a barra/bolinha global
  // para evitar duplicação visual. O toggle global do sidebar continua
  // mandando — quando desligado, nada aparece de qualquer forma.
  if (isChatVisible && isShowingReels) return null

  /* ---- Derived values ---- */
  const nextSteps = NEXT_STEPS_MAP[currentStageKey] ?? NEXT_STEPS_MAP.initial
  const currentStageObj = FUNNEL_STAGES.find(s => s.key === currentStageKey)
  const currentStageOrder = currentStageObj?.order ?? 0
  const nextMainStage = FUNNEL_STAGES.find(s => s.order === currentStageOrder + 1)
  const latest = entries[0] as WorkflowEntry | undefined
  const activeFlowName = latest?.name
  const currentLabel = currentStageObj
    ? t(currentStageObj.labelKey as Parameters<typeof t>[0])
    : t("workflowRail.bar.noActiveFlow")
  const currentAccent = currentStageObj?.canonical.color.accent ?? "var(--wedo-cyan, #60BED1)"
  const CurrentIcon = currentStageObj?.canonical.Icon

  /* ---- Magnifier (Dock-style) scale based on distance from hovered chip ---- */
  const magnifyScale = (key: FunnelStageKey): number => {
    if (!hoveredKey) return 1
    if (hoveredKey === key) return 1.18
    const hi = FUNNEL_STAGES.findIndex(s => s.key === hoveredKey)
    const ki = FUNNEL_STAGES.findIndex(s => s.key === key)
    const d = Math.abs(hi - ki)
    if (d === 1) return 1.08
    if (d === 2) return 1.03
    return 1
  }

  /* ---- Theme tokens (light default; dark optional) ---- */
  const T = isDark
    ? {
        rail:        "bg-[#0F172A] border-white/10",
        railShadow:  "0 12px 32px -12px rgba(15,23,42,0.55)",
        popover:     "bg-[#0F172A] border-white/10",
        popoverArrow:"bg-[#0F172A] border-white/10",
        textDim:     "text-white/45",
        textMid:     "text-white/70",
        textStrong:  "text-white/95",
        chipHover:   "hover:bg-white/8",
        chipHoverBg: "bg-white/10",
        divider:     "bg-white/15",
        connectorIdle: "rgba(255,255,255,0.10)",
        miniBtn:     "border-white/10 bg-[#0F172A] text-white/70 hover:text-white hover:bg-white/10",
      }
    : {
        rail:        "bg-white border-lia-border-subtle",
        railShadow:  "0 10px 28px -12px rgba(17,24,39,0.18)",
        popover:     "bg-white border-lia-border-subtle",
        popoverArrow:"bg-white border-lia-border-subtle",
        textDim:     "text-lia-text-disabled",
        textMid:     "text-lia-text-secondary",
        textStrong:  "text-lia-text-primary",
        chipHover:   "hover:bg-lia-bg-tertiary/40",
        chipHoverBg: "bg-lia-bg-tertiary/60",
        divider:     "bg-lia-border-subtle",
        connectorIdle: "rgba(0,0,0,0.08)",
        miniBtn:     "border-lia-border-subtle bg-white text-lia-text-secondary hover:text-lia-text-primary hover:bg-lia-bg-tertiary/60",
      }

  /* ---- Positioning (free-floating when user has dragged) ---- */
  const useCustomPosition = position !== null
  // Anti-colisão: quando o chat da LIA está em modo flutuante e o usuário
  // ainda não arrastou a bolinha, deslocamos para o canto inferior esquerdo
  // para não brigar com a bolinha do chat (canto inferior direito).
  const avoidFloatingChat = chatMode === "floating" && !useCustomPosition
  const positionStyle: React.CSSProperties = useCustomPosition
    ? { left: position!.x, top: position!.y }
    : expanded
      ? { left: "50%", bottom: 16, transform: "translateX(-50%)" }
      : avoidFloatingChat
        ? { left: 16, bottom: 80 }
        // Default collapsed position: bottom-right, lifted above LIA chat bubble.
        : { right: 16, bottom: 80 }

  /* ---- Chat presence chip (indicator + click-to-focus) ---- */
  const chatModeMeta = CHAT_MODE_META[chatMode]
  const ChatModeIcon = chatModeMeta.Icon
  const chatPresenceTitle = `${chatModeMeta.label} · clique para focar`

  const cursorClass = isDragging ? "cursor-grabbing" : "cursor-grab"

  /* ---------- COLLAPSED: floating ball (Replit-issues style) ---------- */
  if (!expanded) {
    return (
      <div
        ref={containerRef}
        className="fixed z-40"
        style={positionStyle}
      >
        <button
          type="button"
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onBallPointerUp}
          onPointerCancel={onPointerUp}
          aria-label={`Abrir trilho de fluxo (etapa atual: ${currentLabel})`}
          title={`Abrir trilho · ${currentLabel}`}
          style={{
            backgroundColor: currentAccent,
            width: BALL_SIZE,
            height: BALL_SIZE,
            boxShadow: `0 6px 20px -6px ${currentAccent}66, 0 2px 8px rgba(0,0,0,0.12)`,
            touchAction: "none",
          }}
          className={`relative ${cursorClass} rounded-full text-white flex items-center justify-center
            transition-transform duration-200 ease-out hover:scale-110 active:scale-95
            focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/50 focus-visible:ring-offset-2`}
        >
          {CurrentIcon
            ? <CurrentIcon className="w-4 h-4" strokeWidth={2.5} aria-hidden="true" />
            : <ChevronRight className="w-4 h-4" strokeWidth={2.5} aria-hidden="true" />}

          {/* Pending count badge */}
          {pendingCount > 0 && (
            <span
              aria-label={t("workflowRail.pill.pendingAriaLabel", { count: pendingCount })}
              className="absolute -top-1 -right-1 min-w-[16px] h-[16px] px-1 rounded-full bg-yellow-400 text-[9px] font-bold text-yellow-900 flex items-center justify-center border border-white"
            >
              {pendingCount}
            </span>
          )}

          {/* Disconnected dot */}
          {!isConnected && (
            <span
              aria-hidden="true"
              className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-red-500 border border-white"
            />
          )}
        </button>

        {/* Chat presence indicator — subtle chip glued to the ball.
            Clicking re-focuses the chat in its current mode. */}
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); focusChat() }}
          aria-label={chatPresenceTitle}
          title={chatPresenceTitle}
          className="absolute -top-1 -left-1 w-4 h-4 rounded-full bg-white border border-lia-border-subtle text-lia-text-secondary flex items-center justify-center shadow-sm hover:text-wedo-cyan hover:border-wedo-cyan/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40 transition-colors"
        >
          <ChatModeIcon className="w-2.5 h-2.5" strokeWidth={2.25} aria-hidden={true} />
        </button>
      </div>
    )
  }

  /* ---------- EXPANDED: full bar ---------- */
  return (
    <div
      ref={containerRef}
      className={`fixed z-40 ${useCustomPosition ? "" : "w-[min(1080px,calc(100vw-2rem))]"} pointer-events-none`}
      style={positionStyle}
    >
      {/* ---- Pending action banner (above the rail) ---- */}
      {latest?.pendingAction && (
        <div className="pointer-events-auto mb-2 mx-auto max-w-fit flex items-center gap-2 px-3 py-1.5 bg-yellow-50 rounded-full border border-yellow-200 shadow-sm">
          <Zap className="w-3.5 h-3.5 text-yellow-600 flex-shrink-0" />
          <span className={`${textStyles.caption} text-yellow-800 truncate flex-1 max-w-[420px]`}>
            {latest.pendingAction.message}
          </span>
          {latest.pendingAction.actionUrl && (
            <button
              type="button"
              onClick={() => { setPopoverOpenTracked(false, "pending-action"); onNavigate(latest!.pendingAction!.actionUrl!) }}
              className="flex items-center gap-1 text-xs text-yellow-700 font-medium hover:text-yellow-900 flex-shrink-0"
            >
              {t("workflowRail.entry.go")} <ArrowRight className="w-3 h-3" />
            </button>
          )}
        </div>
      )}

      {/* ---- Rail + popover row (centered) ---- */}
      <div className="relative flex justify-center">
        {/* RAIL — pill-shape, magnifier, horizontal scroll, mini toggle */}
        <div
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
          style={{ boxShadow: T.railShadow, touchAction: "none" }}
          className={`pointer-events-auto rounded-full border ${T.rail} flex items-center pl-1 pr-1.5 py-1 max-w-full transition-colors duration-300 ease-out ${cursorClass}`}
        >
          {/* Drag handle (always visible — also acts as a visual hint) */}
          <span
            aria-hidden="true"
            className={`shrink-0 mr-0.5 flex items-center justify-center w-3 h-5 ${T.textDim}`}
            title="Arraste para mover"
          >
            <GripVertical className="w-3 h-3" strokeWidth={2} />
          </span>

          {/* Collapse button — turns the bar back into a floating ball */}
          <button
            type="button"
            onClick={() => setExpanded(false)}
            aria-label="Recolher trilho"
            title="Recolher para bolinha"
            className={`shrink-0 w-6 h-6 rounded-full border ${T.miniBtn} flex items-center justify-center mr-1 z-10 transition-all duration-300 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40`}
            style={{ color: currentAccent }}
          >
            <ChevronLeft className="w-3 h-3" strokeWidth={2.5} />
          </button>

          {/* Chat presence chip — shows where the chat lives now and focuses it on click. */}
          <button
            type="button"
            onClick={focusChat}
            aria-label={chatPresenceTitle}
            title={chatPresenceTitle}
            className={`shrink-0 w-6 h-6 rounded-full border ${T.miniBtn} flex items-center justify-center mr-1 z-10 transition-all duration-300 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40`}
          >
            <ChatModeIcon className="w-3 h-3" strokeWidth={2.25} aria-hidden={true} />
          </button>

          {/* MOBILE compact: only the current chip (no magnifier/scroll) */}
          <div className="flex sm:hidden items-center gap-1.5 px-1 min-w-0">
            {currentStageObj ? (
              <button
                type="button"
                onClick={() => onNavigate(currentStageObj.canonical.navPath)}
                aria-current="step"
                aria-label={currentLabel}
                style={{ backgroundColor: currentAccent, color: "#fff" }}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold flex-shrink-0 hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40"
              >
                <currentStageObj.canonical.Icon className="w-3.5 h-3.5" aria-hidden="true" />
                <span className="truncate max-w-[120px]">{currentLabel}</span>
                {pendingCount > 0 && (
                  <span
                    aria-label={t("workflowRail.pill.pendingAriaLabel", { count: pendingCount })}
                    className="w-1.5 h-1.5 rounded-full bg-white animate-pulse"
                  />
                )}
              </button>
            ) : (
              <span className={`${textStyles.caption} text-lia-text-tertiary`}>
                {t("workflowRail.bar.noActiveFlow")}
              </span>
            )}
          </div>

          {/* DESKTOP — left scroll arrow */}
          {canScrollL && (
            <button
              type="button"
              onClick={() => scrollBy(-1)}
              aria-label="Rolar para a esquerda"
              className={`hidden sm:flex shrink-0 w-5 h-5 rounded-full border ${T.miniBtn} items-center justify-center mr-0.5 z-10 transition-all duration-300 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40`}
            >
              <ChevronLeft className="w-3 h-3" strokeWidth={2.5} />
            </button>
          )}

          {/* DESKTOP — chip strip with horizontal scroll + magnifier */}
          <div
            ref={scrollRef}
            className="hidden sm:flex items-center gap-0.5 overflow-x-auto py-0.5 min-w-0 [&::-webkit-scrollbar]:hidden"
            style={{ scrollbarWidth: "none", msOverflowStyle: "none", maxWidth: 480 }}
          >
            {FUNNEL_STAGES.map((stage, i) => {
              const isCurrent = stage.key === currentStageKey
              const isPast = stage.order < currentStageOrder
              const isHovered = hoveredKey === stage.key
              const Icon = stage.canonical.Icon
              const accent = stage.canonical.color.accent
              const label = t(stage.labelKey as Parameters<typeof t>[0])
              const scale = magnifyScale(stage.key)
              const prevAccent = i > 0 ? FUNNEL_STAGES[i - 1].canonical.color.accent : accent
              return (
                <React.Fragment key={stage.key}>
                  {i > 0 && (
                    <span
                      aria-hidden="true"
                      className="h-px w-2 rounded-full mx-0.5 shrink-0 transition-colors duration-300 ease-out"
                      style={{
                        background: isPast || isCurrent
                          ? `linear-gradient(90deg, ${prevAccent}, ${accent})`
                          : T.connectorIdle,
                      }}
                    />
                  )}
                  <button
                    type="button"
                    onClick={() => onNavigate(stage.canonical.navPath)}
                    onMouseEnter={() => setHoveredKey(stage.key)}
                    onMouseLeave={() => setHoveredKey(null)}
                    onFocus={() => setHoveredKey(stage.key)}
                    onBlur={() => setHoveredKey(null)}
                    aria-current={isCurrent ? "step" : undefined}
                    aria-label={label}
                    title={label}
                    style={{
                      transform: `scale(${scale})`,
                      transformOrigin: "center bottom",
                      ...(isCurrent
                        ? { backgroundColor: accent, color: "#fff" }
                        : isPast || isHovered
                        ? { color: accent }
                        : {}),
                    }}
                    className={`relative flex items-center gap-1 rounded-full text-[10px] font-semibold whitespace-nowrap shrink-0
                      transition-all duration-300 ease-out
                      focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40
                      ${isCurrent ? "px-1.5 py-0.5" : isHovered ? `px-1.5 py-0.5 ${T.chipHoverBg}` : `px-1 py-0.5 ${T.textDim} ${T.chipHover}`}`}
                  >
                    <span className="relative inline-flex items-center">
                      {isPast && !isHovered ? (
                        <Check className="w-3 h-3" strokeWidth={2.75} aria-hidden="true" />
                      ) : (
                        <Icon className="w-3 h-3" strokeWidth={isCurrent ? 2.5 : 1.85} aria-hidden="true" />
                      )}
                      {isCurrent && pendingCount > 0 && (
                        <span
                          aria-label={t("workflowRail.pill.pendingAriaLabel", { count: pendingCount })}
                          className="absolute -top-1 -right-1 min-w-[12px] h-[12px] px-1 rounded-full bg-yellow-400 text-[8px] font-bold text-yellow-900 flex items-center justify-center"
                        >
                          {pendingCount}
                        </span>
                      )}
                    </span>
                    {isHovered && !isCurrent && <span className="tracking-wide">{label}</span>}
                  </button>
                </React.Fragment>
              )
            })}
          </div>

          {/* DESKTOP — right scroll arrow */}
          {canScrollR && (
            <button
              type="button"
              onClick={() => scrollBy(1)}
              aria-label="Rolar para a direita"
              className={`hidden sm:flex shrink-0 w-5 h-5 rounded-full border ${T.miniBtn} items-center justify-center ml-0.5 z-10 transition-all duration-300 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40`}
            >
              <ChevronRight className="w-3 h-3" strokeWidth={2.5} />
            </button>
          )}

          {/* Active flow inline (desktop) */}
          {activeFlowName && (
            <>
              <span aria-hidden="true" className={`hidden sm:block mx-1.5 h-3.5 w-px ${T.divider} shrink-0`} />
              <span
                className={`hidden sm:block text-[10px] ${T.textMid} truncate max-w-[140px] shrink min-w-0 font-medium`}
                title={activeFlowName}
              >
                {activeFlowName}
              </span>
            </>
          )}

          {/* Connection indicator */}
          {!isConnected && (
            <span
              aria-label={t("workflowRail.popover.disconnected")}
              title={t("workflowRail.popover.disconnected")}
              className="ml-1.5 hidden sm:inline-block w-1.5 h-1.5 rounded-full bg-red-500 shrink-0"
            />
          )}

          {/* Theme toggle (sun / moon) */}
          <button
            type="button"
            onClick={() => setIsDark(v => !v)}
            aria-label={isDark ? "Alternar para tema claro" : "Alternar para tema escuro"}
            title={isDark ? "Tema claro" : "Tema escuro"}
            className={`ml-1.5 shrink-0 w-5 h-5 rounded-full border ${T.miniBtn} flex items-center justify-center transition-all duration-300 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40`}
          >
            {isDark
              ? <Sun className="w-3 h-3" strokeWidth={2.25} />
              : <Moon className="w-3 h-3" strokeWidth={2.25} />}
          </button>

          {/* Mini toggle for popover (the "..." button) */}
          <button
            type="button"
            onClick={() => togglePopoverTracked("toggle-button")}
            aria-expanded={isPopoverOpen}
            aria-label={isPopoverOpen ? t("workflowRail.bar.collapseAriaLabel") : t("workflowRail.bar.expandAriaLabel")}
            className={`ml-1 shrink-0 w-5 h-5 rounded-full border ${T.miniBtn} flex items-center justify-center transition-all duration-300 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40 ${isPopoverOpen ? "rotate-90" : ""}`}
          >
            <MoreHorizontal className="w-3 h-3" strokeWidth={2.5} />
          </button>
        </div>

        {/* SIDE POPOVER (lg+) / TOP POPOVER (< lg) — actions for current stage */}
        {isPopoverOpen && (
          <div
            role="dialog"
            aria-label={t("workflowRail.panel.ariaLabel")}
            aria-modal="false"
            title={currentLabel}
            className={`absolute z-10 pointer-events-auto
              bottom-full mb-2 left-0 right-0 mx-auto max-w-[min(420px,calc(100vw-2rem))]
              lg:bottom-auto lg:top-1/2 lg:-translate-y-1/2 lg:left-full lg:right-auto lg:ml-2 lg:mb-0 lg:mx-0 lg:max-w-[460px]
              rounded-2xl lg:rounded-full border ${T.popover}
              animate-in fade-in zoom-in-95 duration-300`}
            style={{ boxShadow: `${T.railShadow}, 0 0 0 1px ${currentAccent}1A` }}
          >
            {/* Side arrow pointing back to the rail (desktop only) */}
            <span
              aria-hidden="true"
              className={`hidden lg:block absolute -left-1 top-1/2 -translate-y-1/2 w-2 h-2 rotate-45 border-l border-b ${T.popoverArrow}`}
            />

            {/* Mobile-only header (because the popover is detached above the bar) */}
            <div className={`lg:hidden flex w-full items-center justify-between px-3 py-1 border-b ${T.divider}`}>
              <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: currentAccent }}>
                {currentLabel}
              </span>
              <button
                type="button"
                onClick={() => setPopoverOpenTracked(false, "mobile-close")}
                aria-label={t("workflowRail.panel.close")}
                className={`${T.textDim} focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40 rounded transition-colors duration-300 ease-out`}
              >
                <X className="w-3 h-3" />
              </button>
            </div>

            {/* Action buttons — first one is the primary (accent-filled) */}
            <div className="flex flex-col lg:flex-row items-stretch lg:items-center gap-1 px-1.5 py-1.5 lg:py-1">
              {nextSteps.map((step, idx) => {
                const isPrimary = idx === 0
                return (
                  <button
                    key={step.id}
                    ref={idx === 0 ? firstNextStepRef : undefined}
                    type="button"
                    onClick={() => handleNextStep(step)}
                    title={t(step.descKey as Parameters<typeof t>[0])}
                    className={`group inline-flex items-center gap-1 px-2 py-1 lg:py-0.5 rounded-full text-[10px] font-semibold whitespace-nowrap transition-all duration-300 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40
                      ${isPrimary
                        ? "text-white"
                        : `${T.textMid} ${T.chipHover}`}`}
                    style={isPrimary ? { backgroundColor: currentAccent } : undefined}
                  >
                    <span aria-hidden="true" className="text-[11px] leading-none flex-shrink-0">{step.icon}</span>
                    <span className="truncate">{t(step.titleKey as Parameters<typeof t>[0])}</span>
                  </button>
                )
              })}

              {/* Next-in-funnel preview — separator + small chip */}
              {nextMainStage && (
                <>
                  <span aria-hidden="true" className={`hidden lg:block h-3.5 w-px ${T.divider} mx-0.5 shrink-0`} />
                  <button
                    type="button"
                    onClick={() => { setPopoverOpenTracked(false, "next-stage-chip"); onNavigate(nextMainStage.canonical.navPath) }}
                    title={t("workflowRail.panel.nextInFunnel")}
                    className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-medium ${T.textDim} ${T.chipHover} transition-all duration-300 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40`}
                  >
                    <ArrowRight className="w-3 h-3" aria-hidden="true" />
                    <nextMainStage.canonical.Icon className="w-3 h-3" aria-hidden="true" />
                    <span className="truncate">{t(nextMainStage.labelKey as Parameters<typeof t>[0])}</span>
                  </button>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
