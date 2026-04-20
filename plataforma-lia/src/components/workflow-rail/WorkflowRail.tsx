"use client"

import React, { useEffect, useRef, useState, useCallback } from "react"
import { useTranslations } from "next-intl"
import { ChevronDown, ChevronUp, ArrowRight, Briefcase, Plus, Zap } from "lucide-react"
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
}

/** Derive the current funnel stage key from the list of active workflow entries. */
function deriveCurrentStage(entries: WorkflowEntry[]): FunnelStageKey {
  if (entries.length === 0) return "initial"
  const latest = entries[0]
  if (latest.type === "search") return "sourcing"
  const inProgress = latest.stages?.find(s => s.status === "in_progress")
  return mapCampaignStageToFunnelKey(inProgress?.stage ?? latest.currentStage)
}

export default function WorkflowRail({ userId, onNavigate, onCreateJob }: WorkflowRailProps) {
  const { entries, isConnected } = useWorkflowRail(userId)
  const [isExpanded, setIsExpanded] = useState(false)
  const [currentStageKey, setCurrentStageKey] = useState<FunnelStageKey>("initial")
  const t = useTranslations()
  const containerRef = useRef<HTMLDivElement | null>(null)
  const firstNextStepRef = useRef<HTMLButtonElement | null>(null)

  const hasEntries = entries.length > 0
  const pendingCount = entries.filter(e => e.pendingAction).length

  /* ---- Sync current stage from real-time entries ---- */
  useEffect(() => {
    setCurrentStageKey(deriveCurrentStage(entries))
  }, [entries])

  /* ---- Close on outside click ---- */
  useEffect(() => {
    if (!isExpanded) return
    const onDown = (e: MouseEvent) => {
      if (!containerRef.current) return
      if (!containerRef.current.contains(e.target as Node)) setIsExpanded(false)
    }
    document.addEventListener("mousedown", onDown)
    return () => document.removeEventListener("mousedown", onDown)
  }, [isExpanded])

  /* ---- Close on Esc ---- */
  useEffect(() => {
    if (!isExpanded) return
    const onKey = (e: globalThis.KeyboardEvent) => { if (e.key === "Escape") setIsExpanded(false) }
    document.addEventListener("keydown", onKey)
    return () => document.removeEventListener("keydown", onKey)
  }, [isExpanded])

  /* ---- Focus first next-step when expanded ---- */
  useEffect(() => {
    if (isExpanded) {
      setTimeout(() => firstNextStepRef.current?.focus(), 50)
    }
  }, [isExpanded])

  /* ---- Auto-collapse when the last active entry disappears mid-session ----
   *
   * We only collapse if:
   * 1. Entries just became empty (hasEntries is false), AND
   * 2. The previous stage was NOT "initial" — meaning the user was tracking a
   *    real flow that just ended, not viewing the neutral entry-point suggestions.
   *
   * This preserves the ability to expand the bar and see suggestions even when
   * there are no active workflows (the "Comece por aqui" / initial state).
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
    // Execute the action
    if (step.actionType === "handler") {
      if (step.handlerId === "createJob" && onCreateJob) {
        onCreateJob()
      }
    } else if (step.path) {
      onNavigate(step.path)
    }
    // Transition to the declarative resulting stage from the catalog
    if (step.resultingStage) {
      setCurrentStageKey(step.resultingStage)
    }
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
      {/* ---- Expanded panel (predictive next steps) ---- */}
      {isExpanded && (
        <div
          role="dialog"
          aria-label={t("workflowRail.panel.ariaLabel")}
          aria-modal="false"
          className="pointer-events-auto mb-1 rounded-xl border border-lia-border-subtle bg-white shadow-xl animate-in fade-in slide-in-from-bottom-2 duration-150 overflow-hidden"
        >
          {/* Panel header */}
          <div className="px-4 py-2.5 border-b border-lia-border-subtle flex items-center justify-between">
            <div className="flex items-center gap-2 min-w-0">
              {activeFlowName && (
                <>
                  <span className="text-xs font-medium text-lia-text-primary truncate max-w-[200px]">
                    {activeFlowName}
                  </span>
                  <span aria-hidden="true" className="text-lia-text-disabled">·</span>
                </>
              )}
              <span className={`${textStyles.caption} text-lia-text-tertiary`}>
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
              className="text-lia-text-tertiary hover:text-lia-text-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40 rounded"
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
                    <div className={`${textStyles.caption} text-lia-text-tertiary truncate`}>
                      {t(step.descKey as Parameters<typeof t>[0])}
                    </div>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-lia-text-disabled group-hover:text-lia-text-secondary flex-shrink-0 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              </li>
            ))}
          </ul>

          {/* "Next in funnel" preview */}
          {nextMainStage && (
            <div className="px-4 py-2 border-t border-lia-border-subtle/60 flex items-center gap-1.5">
              <ArrowRight className="w-3 h-3 text-lia-text-disabled flex-shrink-0" />
              <span className={`${textStyles.caption} text-lia-text-tertiary`}>
                {t("workflowRail.panel.nextInFunnel")}:{" "}
                <span className="inline-flex items-center gap-1 font-medium text-lia-text-secondary">
                  <nextMainStage.canonical.Icon className="w-3 h-3" aria-hidden="true" />
                  {t(nextMainStage.labelKey as Parameters<typeof t>[0])}
                </span>
              </span>
            </div>
          )}
        </div>
      )}

      {/* ---- Main bar ---- */}
      <div className="pointer-events-auto rounded-2xl border border-lia-border-subtle bg-white shadow-lg overflow-hidden">

        {/* Funnel steps row — chips navigate; chevron toggles the expanded panel */}
        <div className="w-full flex items-center px-3 py-2">
          {/* ---- Mobile compact view (< sm): only current stage chip ---- */}
          <div className="flex sm:hidden flex-1 items-center gap-2 min-w-0">
            {currentStageObj ? (
              <button
                type="button"
                onClick={() => onNavigate(currentStageObj.canonical.navPath)}
                aria-current="step"
                aria-label={t(currentStageObj.labelKey as Parameters<typeof t>[0])}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-lia-bg-inverse text-white flex-shrink-0 hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40"
              >
                <currentStageObj.canonical.Icon className="w-3.5 h-3.5" aria-hidden="true" />
                <span>{t(currentStageObj.labelKey as Parameters<typeof t>[0])}</span>
                {pendingCount > 0 && (
                  <span
                    aria-label={t("workflowRail.pill.pendingAriaLabel", { count: pendingCount })}
                    className="w-1.5 h-1.5 rounded-full bg-yellow-400 animate-pulse"
                  />
                )}
              </button>
            ) : (
              <span className={`${textStyles.caption} text-lia-text-tertiary`}>
                {t("workflowRail.bar.noActiveFlow")}
              </span>
            )}
          </div>

          {/* ---- Desktop full funnel view (≥ sm) — each chip is a navigation button ---- */}
          <div className="hidden sm:flex flex-1 items-center min-w-0 overflow-x-auto scrollbar-none">
            {FUNNEL_STAGES.map((stage, idx) => {
              const isCurrent = stage.key === currentStageKey
              const isPast = stage.order < currentStageOrder
              const isNext = stage.order === currentStageOrder + 1
              const Icon = stage.canonical.Icon
              const accent = stage.canonical.color.accent
              const accentBg = stage.canonical.color.accentBg
              const label = t(stage.labelKey as Parameters<typeof t>[0])

              return (
                <React.Fragment key={stage.key}>
                  {idx > 0 && (
                    <div
                      aria-hidden="true"
                      className={`h-px w-3 flex-shrink-0 ${isPast || isCurrent ? "bg-lia-bg-inverse" : "bg-lia-border-subtle"}`}
                    />
                  )}
                  <button
                    type="button"
                    onClick={() => onNavigate(stage.canonical.navPath)}
                    aria-current={isCurrent ? "step" : undefined}
                    aria-label={label}
                    title={label}
                    style={isCurrent ? { backgroundColor: accent, color: "#fff" } : isNext ? { backgroundColor: accentBg, color: accent } : undefined}
                    className={`
                      flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium flex-shrink-0 whitespace-nowrap transition-colors
                      focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40
                      ${isCurrent
                        ? "hover:opacity-90"
                        : isPast
                        ? "bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-bg-tertiary/80"
                        : isNext
                        ? "hover:opacity-90"
                        : "text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-bg-tertiary/60"
                      }
                    `}
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
                </React.Fragment>
              )
            })}
          </div>

          {/* Expand/collapse toggle */}
          <button
            type="button"
            onClick={() => setIsExpanded(v => !v)}
            aria-expanded={isExpanded}
            aria-label={
              isExpanded
                ? t("workflowRail.bar.collapseAriaLabel")
                : t("workflowRail.bar.expandAriaLabel")
            }
            className="ml-2 flex-shrink-0 p-1 rounded text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-bg-tertiary/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40"
          >
            {isExpanded ? (
              <ChevronDown className="w-3.5 h-3.5" />
            ) : (
              <ChevronUp className="w-3.5 h-3.5" />
            )}
          </button>
        </div>

        {/* Bottom strip: active flow name + create-job shortcut */}
        {onCreateJob && (
          <>
            <div aria-hidden="true" className="h-px bg-lia-border-subtle/60" />
            <div className="flex items-center justify-between px-3 py-1.5">
              {activeFlowName ? (
                <span className={`${textStyles.caption} text-lia-text-tertiary truncate max-w-[200px]`}>
                  {activeFlowName}
                </span>
              ) : (
                <span className={`${textStyles.caption} text-lia-text-disabled`}>
                  {t("workflowRail.bar.noActiveFlow")}
                </span>
              )}
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); onCreateJob() }}
                aria-label={t("workflowRail.createJob.ariaLabel")}
                title={t("workflowRail.createJob.tooltip")}
                className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium text-lia-text-primary hover:bg-lia-bg-tertiary/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40 transition-colors whitespace-nowrap"
              >
                <span className="relative inline-flex items-center">
                  <Briefcase className="w-3.5 h-3.5" aria-hidden="true" />
                  <Plus className="w-2 h-2 absolute -top-0.5 -right-0.5 bg-white rounded-full" aria-hidden="true" />
                </span>
                <span>{t("workflowRail.createJob.label")}</span>
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
