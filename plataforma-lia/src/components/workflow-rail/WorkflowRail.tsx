"use client"

import React, { useEffect, useRef, useState, useCallback } from "react"
import { useTranslations } from "next-intl"
import { ChevronDown, ChevronUp, ArrowRight, Briefcase, Plus, Zap, MessageSquare } from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import { useWorkflowRail, WorkflowEntry } from "./useWorkflowRail"
import {
  FUNNEL_STAGES,
  NEXT_STEPS_MAP,
  FunnelStageKey,
  NextStep,
  mapCampaignStageToFunnelKey,
} from "./workflowRailCatalog"

interface WorkflowRailProps {
  userId: string
  onNavigate: (path: string) => void
  onCreateJob?: () => void
  /** Show a "Back to chat" shortcut — useful when navigating away from /chat */
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

/** Stage chip with hover/focus popover — popover open state is controlled by parent */
interface StageChipProps {
  stageKey: FunnelStageKey
  isCurrent: boolean
  isPast: boolean
  isNext: boolean
  label: string
  Icon: React.ElementType
  accent: string
  accentBg: string
  pendingCount: number
  steps: NextStep[]
  isPopoverOpen: boolean
  onOpenPopover: (key: FunnelStageKey, viaKeyboard: boolean) => void
  onClosePopover: (key: FunnelStageKey, immediate?: boolean) => void
  onNavigateTo: () => void
  onStep: (step: NextStep) => void
  t: ReturnType<typeof useTranslations>
}

function StageChip({
  stageKey,
  isCurrent,
  isPast,
  isNext,
  label,
  Icon,
  accent,
  accentBg,
  pendingCount,
  steps,
  isPopoverOpen,
  onOpenPopover,
  onClosePopover,
  onNavigateTo,
  onStep,
  t,
}: StageChipProps) {
  const firstItemRef = useRef<HTMLButtonElement | null>(null)
  /**
   * Tracks whether the popover was explicitly *activated* via Enter/Space.
   * Plain Tab focus opens the popover visually but keeps focus on the chip.
   * Only an explicit activation (Enter/Space) shifts focus into the popover.
   */
  const activatedByKeyboardRef = useRef(false)

  /* Shift focus into popover only on explicit keyboard activation */
  useEffect(() => {
    if (isPopoverOpen && activatedByKeyboardRef.current) {
      activatedByKeyboardRef.current = false
      setTimeout(() => firstItemRef.current?.focus(), 30)
    }
  }, [isPopoverOpen])

  const handleMouseEnter = useCallback(() => {
    onOpenPopover(stageKey, false)
  }, [stageKey, onOpenPopover])

  const handleMouseLeave = useCallback(() => {
    onClosePopover(stageKey)
  }, [stageKey, onClosePopover])

  /**
   * Tab onto chip → open popover *visually* only; focus stays on the chip button.
   * This lets users Tab through chips without being trapped in the popover.
   */
  const handleFocus = useCallback(() => {
    onOpenPopover(stageKey, false)
  }, [stageKey, onOpenPopover])

  /* Close on Tab blur (unless focus moves within the same chip wrapper) */
  const handleBlur = useCallback((e: React.FocusEvent) => {
    const relatedTarget = e.relatedTarget as Node | null
    const wrapper = e.currentTarget.closest("[data-stage-chip]")
    if (wrapper && relatedTarget && wrapper.contains(relatedTarget)) return
    onClosePopover(stageKey, true)
  }, [stageKey, onClosePopover])

  /**
   * Enter/Space: if popover is already visible, activate it (shift focus in);
   * if it is not visible, open it and activate. Esc always closes.
   */
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault()
      activatedByKeyboardRef.current = true
      if (isPopoverOpen) {
        /* Popover already showing — shift focus into first item immediately */
        setTimeout(() => firstItemRef.current?.focus(), 30)
      } else {
        onOpenPopover(stageKey, true)
      }
    }
    if (e.key === "Escape") {
      onClosePopover(stageKey, true)
    }
  }, [stageKey, isPopoverOpen, onOpenPopover, onClosePopover])

  const chipStyle = isCurrent
    ? { backgroundColor: accent, color: "#fff" }
    : isNext
    ? { backgroundColor: accentBg, color: accent }
    : undefined

  const chipClass = [
    "relative flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium flex-shrink-0 whitespace-nowrap transition-colors",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40",
    isCurrent
      ? "hover:opacity-90"
      : isPast
      ? "bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-bg-tertiary/80"
      : isNext
      ? "hover:opacity-90"
      : "text-lia-text-secondary hover:bg-lia-bg-tertiary/60",
  ].join(" ")

  return (
    <div
      data-stage-chip={stageKey}
      className="relative flex-shrink-0"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Hover/focus popover — appears above the chip */}
      {isPopoverOpen && steps.length > 0 && (
        <div
          role="dialog"
          aria-label={label}
          aria-modal="false"
          className="absolute bottom-[calc(100%+6px)] left-1/2 -translate-x-1/2 z-50 w-56 rounded-xl border border-lia-border-default bg-white shadow-xl animate-in fade-in slide-in-from-bottom-1 duration-100 overflow-hidden"
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
        >
          <div className="px-3 py-2 border-b border-lia-border-subtle/70 flex items-center gap-1.5">
            <Icon className="w-3 h-3 flex-shrink-0" style={{ color: accent }} aria-hidden="true" />
            <span className="text-[11px] font-semibold text-lia-text-primary truncate">{label}</span>
          </div>
          <ul className="py-1" role="list">
            {steps.map((step, idx) => (
              <li key={step.id}>
                <button
                  ref={idx === 0 ? firstItemRef : undefined}
                  type="button"
                  onClick={() => {
                    onClosePopover(stageKey, true)
                    onStep(step)
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Escape") onClosePopover(stageKey, true)
                  }}
                  onBlur={handleBlur}
                  className="w-full flex items-center gap-2.5 px-3 py-1.5 text-left hover:bg-lia-bg-tertiary/70 focus-visible:outline-none focus-visible:bg-lia-bg-tertiary/70 transition-colors group"
                >
                  <span aria-hidden="true" className="text-sm leading-none flex-shrink-0">{step.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="text-[11px] font-medium text-lia-text-primary truncate leading-tight">
                      {t(step.titleKey as Parameters<typeof t>[0])}
                    </div>
                  </div>
                  <ArrowRight className="w-3 h-3 text-lia-text-disabled group-hover:text-lia-text-secondary flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* The chip button itself */}
      <button
        type="button"
        onClick={onNavigateTo}
        onKeyDown={handleKeyDown}
        onFocus={handleFocus}
        onBlur={handleBlur}
        aria-current={isCurrent ? "step" : undefined}
        aria-haspopup={steps.length > 0 ? "dialog" : undefined}
        aria-expanded={steps.length > 0 ? isPopoverOpen : undefined}
        aria-label={label}
        title={label}
        style={chipStyle}
        className={chipClass}
      >
        <Icon className="w-3 h-3" aria-hidden="true" />
        <span>{label}</span>
        {isCurrent && pendingCount > 0 && (
          <span
            aria-label={t("workflowRail.pill.pendingAriaLabel", { count: pendingCount })}
            className="w-1.5 h-1.5 rounded-full bg-yellow-400 animate-pulse flex-shrink-0"
          />
        )}
      </button>
    </div>
  )
}

export default function WorkflowRail({ userId, onNavigate, onCreateJob, showBackToChat = false }: WorkflowRailProps) {
  const { entries, isConnected } = useWorkflowRail(userId)
  const [isExpanded, setIsExpanded] = useState(false)
  const [currentStageKey, setCurrentStageKey] = useState<FunnelStageKey>("initial")
  /** Lifted popover state — only one stage popover open at a time */
  const [openStageKey, setOpenStageKey] = useState<FunnelStageKey | null>(null)
  const t = useTranslations()
  const containerRef = useRef<HTMLDivElement | null>(null)
  const firstNextStepRef = useRef<HTMLButtonElement | null>(null)
  const closeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const hasEntries = entries.length > 0
  const pendingCount = entries.filter(e => e.pendingAction).length

  /* ---- Sync current stage from real-time entries ---- */
  useEffect(() => {
    setCurrentStageKey(deriveCurrentStage(entries))
  }, [entries])

  /* ---- Stage popover open/close with delay (prevents flicker between chips) ---- */
  const handleOpenStagePopover = useCallback((key: FunnelStageKey, _viaKeyboard: boolean) => {
    if (closeTimerRef.current) clearTimeout(closeTimerRef.current)
    setOpenStageKey(key)
  }, [])

  const handleCloseStagePopover = useCallback((key: FunnelStageKey, immediate = false) => {
    if (immediate) {
      if (closeTimerRef.current) clearTimeout(closeTimerRef.current)
      setOpenStageKey(prev => (prev === key ? null : prev))
    } else {
      closeTimerRef.current = setTimeout(() => {
        setOpenStageKey(prev => (prev === key ? null : prev))
      }, 150)
    }
  }, [])

  useEffect(() => () => { if (closeTimerRef.current) clearTimeout(closeTimerRef.current) }, [])

  /* ---- Close expanded panel on outside click ---- */
  useEffect(() => {
    if (!isExpanded) return
    const onDown = (e: MouseEvent) => {
      if (!containerRef.current) return
      if (!containerRef.current.contains(e.target as Node)) setIsExpanded(false)
    }
    document.addEventListener("mousedown", onDown)
    return () => document.removeEventListener("mousedown", onDown)
  }, [isExpanded])

  /* ---- Close expanded panel on Esc ---- */
  useEffect(() => {
    if (!isExpanded) return
    const onKey = (e: globalThis.KeyboardEvent) => { if (e.key === "Escape") setIsExpanded(false) }
    document.addEventListener("keydown", onKey)
    return () => document.removeEventListener("keydown", onKey)
  }, [isExpanded])

  /* ---- Focus first next-step when panel expanded via chevron ---- */
  useEffect(() => {
    if (isExpanded) {
      setTimeout(() => firstNextStepRef.current?.focus(), 50)
    }
  }, [isExpanded])

  /* ---- Auto-collapse when last active entry disappears mid-session ----
   * Only collapse if the user was tracking a real flow (not on the neutral
   * "initial" suggestions state). Keeps "Comece por aqui" reachable when empty.
   */
  const prevHasEntriesRef = useRef(hasEntries)
  useEffect(() => {
    const wasTracking = prevHasEntriesRef.current && currentStageKey !== "initial"
    if (!hasEntries && isExpanded && wasTracking) setIsExpanded(false)
    prevHasEntriesRef.current = hasEntries
  }, [hasEntries, isExpanded, currentStageKey])

  /* ---- Handle next-step action ---- */
  const handleNextStep = useCallback((step: NextStep) => {
    setIsExpanded(false)
    if (step.actionType === "handler") {
      if (step.handlerId === "createJob" && onCreateJob) onCreateJob()
    } else if (step.path) {
      onNavigate(step.path)
    }
    if (step.resultingStage) setCurrentStageKey(step.resultingStage)
  }, [onNavigate, onCreateJob])

  if (!hasEntries && !onCreateJob) return null

  /* ---- Derived values ---- */
  const nextSteps = NEXT_STEPS_MAP[currentStageKey] ?? NEXT_STEPS_MAP.initial
  const currentStageObj = FUNNEL_STAGES.find(s => s.key === currentStageKey)
  const currentStageOrder = currentStageObj?.order ?? 0
  const nextMainStage = FUNNEL_STAGES.find(s => s.order === currentStageOrder + 1)
  const latest = entries[0] as WorkflowEntry | undefined
  const activeFlowName = latest?.name

  return (
    <div
      ref={containerRef}
      className="fixed bottom-4 left-1/2 -translate-x-1/2 z-40 w-[min(720px,calc(100vw-2rem))] pointer-events-none"
    >
      {/* ---- General expanded panel (accessible via chevron) ---- */}
      {isExpanded && (
        <div
          role="dialog"
          aria-label={t("workflowRail.panel.ariaLabel")}
          aria-modal="false"
          className="pointer-events-auto mb-1 rounded-xl border border-lia-border-default bg-white shadow-xl animate-in fade-in slide-in-from-bottom-2 duration-150 overflow-hidden"
        >
          {/* Panel header */}
          <div className="px-4 py-2.5 border-b border-lia-border-subtle flex items-center justify-between">
            <div className="flex items-center gap-2 min-w-0">
              {activeFlowName && (
                <>
                  <span className="text-xs font-medium text-lia-text-primary truncate max-w-[200px]">
                    {activeFlowName}
                  </span>
                  <span aria-hidden="true" className="text-lia-text-secondary">·</span>
                </>
              )}
              <span className={`${textStyles.caption} text-lia-text-secondary`}>
                {t("workflowRail.panel.nextStepsLabel")}
              </span>
              {!isConnected && (
                <span className="text-[10px] text-red-500 ml-1">{t("workflowRail.popover.disconnected")}</span>
              )}
            </div>
            <button
              type="button"
              onClick={() => setIsExpanded(false)}
              aria-label={t("workflowRail.panel.close")}
              className="text-lia-text-secondary hover:text-lia-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40 rounded"
            >
              <ChevronDown className="w-4 h-4" />
            </button>
          </div>

          {/* Pending action banner */}
          {latest?.pendingAction && (
            <div className="mx-3 mt-2 flex items-center gap-2 px-3 py-2 bg-yellow-50 rounded-lg border border-yellow-200">
              <Zap className="w-3.5 h-3.5 text-yellow-600 flex-shrink-0" />
              <span className={`${textStyles.caption} text-yellow-800 truncate flex-1`}>
                {latest.pendingAction.message}
              </span>
              {latest.pendingAction.actionUrl && (
                <button
                  type="button"
                  onClick={() => { setIsExpanded(false); onNavigate(latest!.pendingAction!.actionUrl!) }}
                  className="flex items-center gap-1 text-xs text-yellow-700 font-medium hover:text-yellow-900 flex-shrink-0"
                >
                  {t("workflowRail.entry.go")} <ArrowRight className="w-3 h-3" />
                </button>
              )}
            </div>
          )}

          {/* Next steps list */}
          <ul className="px-3 py-2 space-y-0.5" role="list">
            {nextSteps.map((step, idx) => (
              <li key={step.id}>
                <button
                  ref={idx === 0 ? firstNextStepRef : undefined}
                  type="button"
                  onClick={() => handleNextStep(step)}
                  className="w-full flex items-start gap-3 px-3 py-2.5 rounded-lg text-left hover:bg-lia-bg-tertiary/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40 transition-colors group"
                >
                  <span aria-hidden="true" className="text-base mt-0.5 flex-shrink-0">{step.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium text-lia-text-primary">
                      {t(step.titleKey as Parameters<typeof t>[0])}
                    </div>
                    <div className={`${textStyles.caption} text-lia-text-secondary truncate`}>
                      {t(step.descKey as Parameters<typeof t>[0])}
                    </div>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-lia-text-secondary group-hover:text-lia-text-primary flex-shrink-0 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              </li>
            ))}
          </ul>

          {/* "Next in funnel" preview */}
          {nextMainStage && (
            <div className="px-4 py-2 border-t border-lia-border-subtle/60 flex items-center gap-1.5">
              <ArrowRight className="w-3 h-3 text-lia-text-secondary flex-shrink-0" />
              <span className={`${textStyles.caption} text-lia-text-secondary`}>
                {t("workflowRail.panel.nextInFunnel")}:{" "}
                <span className="inline-flex items-center gap-1 font-medium text-lia-text-primary">
                  <nextMainStage.canonical.Icon className="w-3 h-3" aria-hidden="true" />
                  {t(nextMainStage.labelKey as Parameters<typeof t>[0])}
                </span>
              </span>
            </div>
          )}
        </div>
      )}

      {/* ---- Main bar — single compact line ---- */}
      <div className="pointer-events-auto rounded-2xl border border-lia-border-default bg-white shadow-lg overflow-visible">
        <div className="w-full flex items-center px-3 py-1.5 gap-2">

          {/* "Back to chat" escape hatch — shown when navigating away from /chat */}
          {showBackToChat && (
            <>
              <button
                type="button"
                onClick={() => onNavigate("/chat")}
                aria-label="Voltar para o chat com a LIA"
                title="Voltar para o chat"
                className="flex-shrink-0 p-1 rounded-full text-lia-text-secondary hover:text-lia-text-primary hover:bg-lia-bg-tertiary/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40 transition-colors"
              >
                <MessageSquare className="w-3 h-3" strokeWidth={2.25} />
              </button>
              <div aria-hidden="true" className="w-px h-3.5 bg-lia-border-default flex-shrink-0" />
            </>
          )}

          {/* Active flow name — inline, left side, truncated */}
          {activeFlowName && (
            <>
              <span
                className="text-[11px] font-medium text-lia-text-primary truncate max-w-[120px] flex-shrink-0"
                title={activeFlowName}
              >
                {activeFlowName}
              </span>
              <div aria-hidden="true" className="w-px h-3.5 bg-lia-border-default flex-shrink-0" />
            </>
          )}

          {/* ---- Mobile compact view (< sm): only current stage chip ---- */}
          <div className="flex sm:hidden flex-1 items-center gap-2 min-w-0">
            {currentStageObj ? (
              <StageChip
                stageKey={currentStageObj.key}
                isCurrent={true}
                isPast={false}
                isNext={false}
                label={t(currentStageObj.labelKey as Parameters<typeof t>[0])}
                Icon={currentStageObj.canonical.Icon}
                accent={currentStageObj.canonical.color.accent}
                accentBg={currentStageObj.canonical.color.accentBg}
                pendingCount={pendingCount}
                steps={NEXT_STEPS_MAP[currentStageObj.key] ?? []}
                isPopoverOpen={openStageKey === currentStageObj.key}
                onOpenPopover={handleOpenStagePopover}
                onClosePopover={handleCloseStagePopover}
                onNavigateTo={() => onNavigate(currentStageObj.canonical.navPath)}
                onStep={handleNextStep}
                t={t}
              />
            ) : (
              <span className={`${textStyles.caption} text-lia-text-secondary`}>
                {t("workflowRail.bar.noActiveFlow")}
              </span>
            )}
          </div>

          {/* ---- Desktop full funnel view (≥ sm) — each chip with hover/focus popover ---- */}
          <div className="hidden sm:flex flex-1 items-center min-w-0 overflow-x-auto scrollbar-none gap-0">
            {FUNNEL_STAGES.map((stage, idx) => {
              const isCurrent = stage.key === currentStageKey
              const isPast = stage.order < currentStageOrder
              const isNext = stage.order === currentStageOrder + 1
              const label = t(stage.labelKey as Parameters<typeof t>[0])
              const stageSteps = NEXT_STEPS_MAP[stage.key] ?? []

              return (
                <React.Fragment key={stage.key}>
                  {idx > 0 && (
                    <div
                      aria-hidden="true"
                      className={`h-px w-3 flex-shrink-0 mx-0.5 ${
                        isPast || isCurrent
                          ? "bg-lia-bg-inverse"
                          : "bg-lia-border-default"
                      }`}
                    />
                  )}
                  <StageChip
                    stageKey={stage.key}
                    isCurrent={isCurrent}
                    isPast={isPast}
                    isNext={isNext}
                    label={label}
                    Icon={stage.canonical.Icon}
                    accent={stage.canonical.color.accent}
                    accentBg={stage.canonical.color.accentBg}
                    pendingCount={pendingCount}
                    steps={stageSteps}
                    isPopoverOpen={openStageKey === stage.key}
                    onOpenPopover={handleOpenStagePopover}
                    onClosePopover={handleCloseStagePopover}
                    onNavigateTo={() => onNavigate(stage.canonical.navPath)}
                    onStep={handleNextStep}
                    t={t}
                  />
                </React.Fragment>
              )
            })}
          </div>

          {/* Right side: Criar vaga button + dividers + chevron */}
          <div className="flex items-center gap-1 flex-shrink-0 ml-auto">
            {onCreateJob && (
              <>
                <div aria-hidden="true" className="w-px h-3.5 bg-lia-border-default" />
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); onCreateJob() }}
                  aria-label={t("workflowRail.createJob.ariaLabel")}
                  title={t("workflowRail.createJob.tooltip")}
                  className="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium text-lia-text-primary hover:bg-lia-bg-tertiary/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40 transition-colors whitespace-nowrap"
                >
                  <span className="relative inline-flex items-center">
                    <Briefcase className="w-3 h-3" aria-hidden="true" />
                    <Plus className="w-2 h-2 absolute -top-0.5 -right-1 bg-white rounded-full" aria-hidden="true" />
                  </span>
                  <span className="hidden sm:inline">{t("workflowRail.createJob.label")}</span>
                </button>
              </>
            )}

            <div aria-hidden="true" className="w-px h-3.5 bg-lia-border-default" />

            {/* Expand/collapse toggle — keyboard/secondary access to general panel */}
            <button
              type="button"
              onClick={() => setIsExpanded(v => !v)}
              aria-expanded={isExpanded}
              aria-label={
                isExpanded
                  ? t("workflowRail.bar.collapseAriaLabel")
                  : t("workflowRail.bar.expandAriaLabel")
              }
              className="p-1 rounded text-lia-text-secondary hover:text-lia-text-primary hover:bg-lia-bg-tertiary/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40"
            >
              {isExpanded ? (
                <ChevronDown className="w-3.5 h-3.5" />
              ) : (
                <ChevronUp className="w-3.5 h-3.5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
