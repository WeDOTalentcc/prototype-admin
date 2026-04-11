"use client"

import React, { useState } from"react"
import {
  ChevronUp, ChevronDown, X, Briefcase, Database,
  Search, ArrowRight, Plus, Zap
} from"lucide-react"
import { Badge } from"@/components/ui/badge"
import { Button } from"@/components/ui/button"
import { Progress } from"@/components/ui/progress"
import {
  textStyles, badgeStyles, buttonStyles
} from"@/lib/design-tokens"
import { useWorkflowRail, WorkflowEntry, WorkflowStage } from"./useWorkflowRail"

/**
 * WorkflowRail — persistent collapsible bottom bar showing all active workflows.
 *
 * Place in root layout (outside page router) so it persists across navigation.
 *
 * Usage:
 *   // In root layout or app shell:
 *   <WorkflowRail
 *     userId={currentUser.id}
 *     onNavigate={(path) => router.push(path)}
 *   />
 */

interface WorkflowRailProps {
  userId: string
  onNavigate: (path: string) => void
}

export default function WorkflowRail({ userId, onNavigate }: WorkflowRailProps) {
  const { entries, isConnected, dismissEntry } = useWorkflowRail(userId)
  const [isExpanded, setIsExpanded] = useState(false)

  // Don't render if no entries
  if (entries.length === 0) return null

  // Count pending actions across all entries
  const pendingCount = entries.filter(e => e.pendingAction).length

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 transition-all duration-300">
      {/* Collapsed bar */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-2 bg-lia-bg-inverse text-white hover:bg-lia-bg-inverse transition-colors"
      >
        <div className="flex items-center gap-3 overflow-x-auto">
          {entries.slice(0, 3).map(entry => (
            <CollapsedEntry key={entry.id} entry={entry} />
          ))}
          {entries.length > 3 && (
            <span className="text-xs text-lia-text-tertiary">+{entries.length - 3} mais</span>
          )}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0 ml-3">
          {pendingCount > 0 && (
            <Badge className="bg-yellow-500 text-yellow-900 text-xs">{pendingCount} pendente{pendingCount > 1 ?"s" :""}</Badge>
          )}
          {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        </div>
      </button>

      {/* Expanded panel */}
      {isExpanded && (
        <div className="bg-white border-t border-lia-border-subtle shadow-2xl max-h-80 overflow-y-auto">
          <div className="px-4 py-3 flex items-center justify-between">
            <h3 className={textStyles.subtitle}>Fluxos Ativos</h3>
            <div className="flex items-center gap-2">
              {!isConnected && (
                <span className="text-xs text-red-500">Desconectado</span>
              )}
              <button onClick={() => setIsExpanded(false)} className="text-lia-text-tertiary hover:text-lia-text-secondary">
                <ChevronDown className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="divide-y divide-gray-100">
            {entries.map(entry => (
              <ExpandedEntry
                key={entry.id}
                entry={entry}
                onNavigate={onNavigate}
                onDismiss={() => dismissEntry(entry.id)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ---------- Collapsed Entry ----------

function CollapsedEntry({ entry }: { entry: WorkflowEntry }) {
  const icon = entry.type ==="campaign" ?"📋" : entry.type ==="pool" ?"🏊" :"🔍"
  const currentStage = entry.stages?.find(s => s.status ==="in_progress")

  return (
    <div className="flex items-center gap-1.5 text-xs whitespace-nowrap">
      <span>{icon}</span>
      <span className="font-medium truncate max-w-32">{entry.name}</span>
      {currentStage && (
        <span className="text-lia-text-tertiary">{currentStage.label}</span>
      )}
      {entry.pendingAction && (
        <span className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
      )}
    </div>
  )
}

// ---------- Expanded Entry ----------

function ExpandedEntry({
  entry, onNavigate, onDismiss,
}: {
  entry: WorkflowEntry
  onNavigate: (path: string) => void
  onDismiss: () => void
}) {
  const typeConfig = {
    campaign: { icon: Briefcase, label:"Campanha" },
    pool: { icon: Database, label:"Pool" },
    search: { icon: Search, label:"Busca" },
  }
  const config = typeConfig[entry.type] || typeConfig.campaign
  const Icon = config.icon

  return (
    <div className="px-4 py-3">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 text-lia-text-tertiary" />
          <span className={textStyles.subtitle}>{entry.name}</span>
          <span className={`${textStyles.caption} text-lia-text-tertiary`}>— {config.label}</span>
        </div>
        {entry.type ==="search" && (
          <button onClick={onDismiss} className="text-lia-text-disabled hover:text-lia-text-tertiary">
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Stage progress */}
      {entry.stages && entry.stages.length > 0 && (
        <div className="flex items-center gap-1 mb-2">
          {entry.stages.map((stage, i) => (
            <React.Fragment key={stage.stage}>
              <StageIndicator stage={stage} />
              {i < entry.stages!.length - 1 && (
                <div className={`h-px w-3 ${stage.status ==="completed" ?"bg-lia-bg-inverse" :"bg-lia-interactive-active"}`} />
              )}
            </React.Fragment>
          ))}
        </div>
      )}

      {/* Pending action */}
      {entry.pendingAction && (
        <div className="flex items-center justify-between mt-2 px-2 py-1.5 bg-yellow-50 rounded-md">
          <div className="flex items-center gap-2">
            <Zap className="w-3.5 h-3.5 text-yellow-600" />
            <span className={`${textStyles.caption} text-yellow-800`}>
              {entry.pendingAction.message}
            </span>
          </div>
          {entry.pendingAction.actionUrl && (
            <button
              onClick={() => onNavigate(entry.pendingAction!.actionUrl!)}
              className="flex items-center gap-1 text-xs text-yellow-700 font-medium hover:text-yellow-900"
            >
              Ir <ArrowRight className="w-3 h-3" />
            </button>
          )}
        </div>
      )}

      {/* Quick actions for search entries */}
      {entry.type ==="search" && entry.searchResults && (
        <div className="flex items-center gap-2 mt-2">
          <span className={textStyles.caption}>{entry.searchResults.count} encontrados</span>
          <button className="flex items-center gap-1 text-xs text-lia-text-secondary hover:text-lia-text-primary border border-lia-border-subtle rounded px-2 py-1">
            <Plus className="w-3 h-3" /> Vaga
          </button>
          <button className="flex items-center gap-1 text-xs text-lia-text-secondary hover:text-lia-text-primary border border-lia-border-subtle rounded px-2 py-1">
            <Plus className="w-3 h-3" /> Pool
          </button>
          <button className="flex items-center gap-1 text-xs text-lia-text-secondary hover:text-lia-text-primary border border-lia-border-subtle rounded px-2 py-1">
            <Plus className="w-3 h-3" /> Lista
          </button>
        </div>
      )}
    </div>
  )
}

// ---------- Stage Indicator ----------

function StageIndicator({ stage }: { stage: WorkflowStage }) {
  const statusStyles = {
    completed:"bg-lia-bg-inverse text-white",
    in_progress:"bg-yellow-100 text-yellow-800 ring-1 ring-yellow-300",
    pending:"bg-lia-bg-tertiary text-lia-text-tertiary",
  }

  return (
    <div className="flex flex-col items-center" title={stage.label}>
      <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${statusStyles[stage.status]}`}>
        {stage.status ==="completed" ?"✓" : stage.status ==="in_progress" ?"●" :"○"}
      </div>
      <span className="text-[10px] text-lia-text-tertiary mt-0.5 whitespace-nowrap">{stage.label}</span>
      {stage.candidatesCount > 0 && (
        <span className="text-[9px] text-lia-text-tertiary">({stage.candidatesCount})</span>
      )}
    </div>
  )
}
