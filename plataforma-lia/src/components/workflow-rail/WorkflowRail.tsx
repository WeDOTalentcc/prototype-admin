"use client"

import React, { useEffect, useRef, useState } from "react"
import { useTranslations } from "next-intl"
import {
  X, Briefcase, Database, Search, ArrowRight, Plus, Zap, ChevronDown,
} from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import { useWorkflowRail, WorkflowEntry, WorkflowStage } from "./useWorkflowRail"

/**
 * WorkflowRail — discreet floating pill anchored above the chat input.
 *
 * - When no workflows exist, the pill collapses to just the "Create job" shortcut.
 * - When workflows exist, the pill shows the most recent flow + a "+N" counter,
 *   with the "Create job" action as a secondary button on the right.
 * - Clicking the flow side opens an anchored popover above the pill listing
 *   every active workflow (replacing the legacy full-width white panel).
 */

interface WorkflowRailProps {
  userId: string
  onNavigate: (path: string) => void
  onCreateJob?: () => void
}

const TYPE_ICON: Record<WorkflowEntry["type"], string> = {
  campaign: "📋",
  pool: "🏊",
  search: "🔍",
}

export default function WorkflowRail({ userId, onNavigate, onCreateJob }: WorkflowRailProps) {
  const { entries, isConnected, dismissEntry } = useWorkflowRail(userId)
  const [isExpanded, setIsExpanded] = useState(false)
  const t = useTranslations("workflowRail")
  const tCreate = useTranslations("workflowRail.createJob")
  const containerRef = useRef<HTMLDivElement | null>(null)

  const hasEntries = entries.length > 0

  // Close popover when clicking outside
  useEffect(() => {
    if (!isExpanded) return
    const onDown = (e: MouseEvent) => {
      if (!containerRef.current) return
      if (!containerRef.current.contains(e.target as Node)) setIsExpanded(false)
    }
    document.addEventListener("mousedown", onDown)
    return () => document.removeEventListener("mousedown", onDown)
  }, [isExpanded])

  // Auto-collapse when last entry disappears
  useEffect(() => {
    if (!hasEntries && isExpanded) setIsExpanded(false)
  }, [hasEntries, isExpanded])

  if (!hasEntries && !onCreateJob) return null

  const latest = entries[0]
  const extraCount = Math.max(0, entries.length - 1)
  const pendingCount = entries.filter(e => e.pendingAction).length

  return (
    <div
      ref={containerRef}
      className="fixed bottom-4 left-1/2 -translate-x-1/2 z-40 pointer-events-none"
    >
      {/* Expanded popover (anchored above the pill) */}
      {isExpanded && hasEntries && (
        <div
          className="pointer-events-auto mb-2 w-[min(480px,calc(100vw-2rem))] max-h-80 overflow-y-auto rounded-xl border border-lia-border-subtle bg-white shadow-xl animate-in fade-in slide-in-from-bottom-1 duration-150"
          role="dialog"
          aria-label={t("popover.title")}
        >
          <div className="px-4 py-3 flex items-center justify-between border-b border-lia-border-subtle">
            <h3 className={textStyles.subtitle}>{t("popover.title")}</h3>
            <div className="flex items-center gap-2">
              {!isConnected && (
                <span className="text-xs text-red-500">{t("popover.disconnected")}</span>
              )}
              <button
                type="button"
                onClick={() => setIsExpanded(false)}
                aria-label={t("popover.close")}
                className="text-lia-text-tertiary hover:text-lia-text-secondary"
              >
                <ChevronDown className="w-4 h-4" />
              </button>
            </div>
          </div>
          <div className="divide-y divide-gray-100">
            {entries.map(entry => (
              <ExpandedEntry
                key={entry.id}
                entry={entry}
                onNavigate={(p) => { setIsExpanded(false); onNavigate(p) }}
                onDismiss={() => dismissEntry(entry.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* The pill itself */}
      <div className="pointer-events-auto inline-flex items-stretch rounded-full border border-lia-border-subtle bg-white shadow-lg max-w-[min(560px,calc(100vw-2rem))] overflow-hidden">
        {hasEntries && (
          <button
            type="button"
            onClick={() => setIsExpanded(v => !v)}
            aria-expanded={isExpanded}
            aria-label={t("pill.summaryAriaLabel", { count: entries.length })}
            className="flex items-center gap-2 pl-4 pr-3 py-2 hover:bg-lia-bg-tertiary/60 transition-colors text-left min-w-0"
          >
            <span aria-hidden="true" className="text-sm">{TYPE_ICON[latest.type]}</span>
            <span className="text-xs font-medium text-lia-text-primary truncate max-w-[160px] sm:max-w-[220px]">
              {latest.name}
            </span>
            {latest.stages?.find(s => s.status === "in_progress") && (
              <>
                <span aria-hidden="true" className="text-lia-text-disabled">·</span>
                <span className="text-xs text-lia-text-tertiary truncate hidden sm:inline">
                  {latest.stages.find(s => s.status === "in_progress")!.label}
                </span>
              </>
            )}
            {pendingCount > 0 && (
              <span
                className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse flex-shrink-0"
                aria-label={t("pill.pendingAriaLabel", { count: pendingCount })}
              />
            )}
            {extraCount > 0 && (
              <span
                className="ml-1 inline-flex items-center justify-center text-[11px] font-medium text-lia-text-secondary bg-lia-bg-tertiary rounded-full px-2 py-0.5 flex-shrink-0"
                aria-label={t("pill.moreAriaLabel", { count: extraCount })}
              >
                +{extraCount}
              </span>
            )}
          </button>
        )}

        {hasEntries && onCreateJob && (
          <span aria-hidden="true" className="w-px self-stretch bg-lia-border-subtle" />
        )}

        {onCreateJob && (
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); onCreateJob() }}
            aria-label={tCreate("ariaLabel")}
            title={tCreate("tooltip")}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-lia-text-primary hover:bg-lia-bg-tertiary/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40 transition-colors whitespace-nowrap"
          >
            <span className="relative inline-flex items-center">
              <Briefcase className="w-4 h-4" aria-hidden="true" />
              <Plus className="w-2.5 h-2.5 absolute -top-0.5 -right-1 bg-white rounded-full" aria-hidden="true" />
            </span>
            <span>{tCreate("label")}</span>
          </button>
        )}
      </div>
    </div>
  )
}

// ---------- Expanded Entry (inside popover) ----------

function ExpandedEntry({
  entry, onNavigate, onDismiss,
}: {
  entry: WorkflowEntry
  onNavigate: (path: string) => void
  onDismiss: () => void
}) {
  const t = useTranslations("workflowRail")
  const typeConfig = {
    campaign: { icon: Briefcase, label: t("types.campaign") },
    pool: { icon: Database, label: t("types.pool") },
    search: { icon: Search, label: t("types.search") },
  }
  const config = typeConfig[entry.type] || typeConfig.campaign
  const Icon = config.icon

  return (
    <div className="px-4 py-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <Icon className="w-4 h-4 text-lia-text-tertiary flex-shrink-0" />
          <span className={`${textStyles.subtitle} truncate`}>{entry.name}</span>
          <span className={`${textStyles.caption} text-lia-text-tertiary flex-shrink-0`}>— {config.label}</span>
        </div>
        {entry.type === "search" && (
          <button
            type="button"
            onClick={onDismiss}
            aria-label={t("entry.dismiss")}
            className="text-lia-text-disabled hover:text-lia-text-tertiary flex-shrink-0"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {entry.stages && entry.stages.length > 0 && (
        <div className="flex items-center gap-1 mb-2 flex-wrap">
          {entry.stages.map((stage, i) => (
            <React.Fragment key={stage.stage}>
              <StageIndicator stage={stage} />
              {i < entry.stages!.length - 1 && (
                <div className={`h-px w-3 ${stage.status === "completed" ? "bg-lia-bg-inverse" : "bg-lia-interactive-active"}`} />
              )}
            </React.Fragment>
          ))}
        </div>
      )}

      {entry.pendingAction && (
        <div className="flex items-center justify-between mt-2 px-2 py-1.5 bg-yellow-50 rounded-md">
          <div className="flex items-center gap-2 min-w-0">
            <Zap className="w-3.5 h-3.5 text-yellow-600 flex-shrink-0" />
            <span className={`${textStyles.caption} text-yellow-800 truncate`}>
              {entry.pendingAction.message}
            </span>
          </div>
          {entry.pendingAction.actionUrl && (
            <button
              type="button"
              onClick={() => onNavigate(entry.pendingAction!.actionUrl!)}
              className="flex items-center gap-1 text-xs text-yellow-700 font-medium hover:text-yellow-900 flex-shrink-0"
            >
              {t("entry.go")} <ArrowRight className="w-3 h-3" />
            </button>
          )}
        </div>
      )}

      {entry.type === "search" && entry.searchResults && (
        <div className="flex items-center gap-2 mt-2 flex-wrap">
          <span className={textStyles.caption}>
            {t("entry.foundCount", { count: entry.searchResults.count })}
          </span>
        </div>
      )}
    </div>
  )
}

// ---------- Stage Indicator ----------

function StageIndicator({ stage }: { stage: WorkflowStage }) {
  const statusStyles = {
    completed: "bg-lia-bg-inverse text-white",
    in_progress: "bg-yellow-100 text-yellow-800 ring-1 ring-yellow-300",
    pending: "bg-lia-bg-tertiary text-lia-text-tertiary",
  }

  return (
    <div className="flex flex-col items-center" title={stage.label}>
      <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${statusStyles[stage.status]}`}>
        {stage.status === "completed" ? "✓" : stage.status === "in_progress" ? "●" : "○"}
      </div>
      <span className="text-[10px] text-lia-text-tertiary mt-0.5 whitespace-nowrap">{stage.label}</span>
      {stage.candidatesCount > 0 && (
        <span className="text-[9px] text-lia-text-tertiary">({stage.candidatesCount})</span>
      )}
    </div>
  )
}
