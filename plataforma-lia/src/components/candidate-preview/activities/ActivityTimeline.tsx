"use client"

import React from "react"
import { Activity } from "lucide-react"
import type { LucideIcon } from "lucide-react"
import type { ActivityViewType } from "./ActivityFilters"

/**
 * Minimal shape needed for timeline rendering.
 * No longer imports from @/data/demo-activities — fully decoupled from mock data.
 */
export interface TimelineActivity {
  id: string
  type: string
  icon: LucideIcon
  iconColor: string
  title: string
  author: string
  authorRole?: string
  date: string
  timestamp: Date
  summary?: string
  jobId?: string
  jobTitle?: string
  score?: number
  statusLabel?: string
  status?: "approved" | "completed" | "in-progress" | "rejected" | "pending"
  platform?: string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  details?: Record<string, any>
}

interface ActivityTimelineProps {
  filteredActivities: TimelineActivity[]
  activityView: ActivityViewType
  candidateName: string
  renderActivityCard: (activity: TimelineActivity, isTimeline: boolean) => React.ReactNode
}

function groupByDateLabel(activities: TimelineActivity[]) {
  const groups: Record<string, TimelineActivity[]> = {}
  const now = Date.now()

  for (const a of activities) {
    const daysDiff = Math.floor((now - a.timestamp.getTime()) / (1000 * 60 * 60 * 24))
    let key: string
    if (daysDiff === 0) key = "Hoje"
    else if (daysDiff === 1) key = "Ontem"
    else if (daysDiff <= 6) key = "Esta Semana"
    else if (daysDiff <= 30) key = "Últimas Semanas"
    else key = "Anteriormente"
    if (!groups[key]) groups[key] = []
    groups[key].push(a)
  }
  return groups
}

const DATE_ORDER = ["Hoje", "Ontem", "Esta Semana", "Últimas Semanas", "Anteriormente"]

const EmptyState = () => (
  <div className="flex flex-col items-center justify-center py-12 px-4">
    <div className="w-16 h-16 bg-lia-bg-tertiary rounded-full flex items-center justify-center mb-4">
      <Activity className="w-8 h-8 text-lia-text-secondary" />
    </div>
    <h3 className="text-sm font-medium text-lia-text-primary mb-2">
      Nenhuma atividade registrada ainda
    </h3>
    <p className="text-xs text-lia-text-primary text-center max-w-xs">
      As atividades aparecerão aqui conforme o processo avança
    </p>
  </div>
)

export function ActivityTimeline({
  filteredActivities,
  activityView,
  candidateName,
  renderActivityCard,
}: ActivityTimelineProps) {
  if (activityView === "timeline") {
    const groups = groupByDateLabel(filteredActivities)

    return (
      <div className="relative">
        {filteredActivities.length === 0 && <EmptyState />}

        {filteredActivities.length > 0 && (
          <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-wedo-green opacity-20" />
        )}

        {DATE_ORDER.map((dateKey) => {
          const items = groups[dateKey]
          if (!items?.length) return null
          return (
            <div key={dateKey} className="mb-6">
              <div className="relative flex items-center mb-3">
                <div className="absolute left-4 w-4 h-4 bg-lia-bg-primary rounded-full border-2 border-lia-border-medium z-10" />
                <h3 className="ml-12 text-xs font-semibold text-lia-text-primary">{dateKey}</h3>
                <div className="ml-3 flex-1 h-px bg-lia-interactive-active" />
              </div>
              <div className="space-y-3">
                {items.map((a) => renderActivityCard(a, true))}
              </div>
            </div>
          )
        })}

        {filteredActivities.length > 0 && (
          <div className="relative flex items-center mt-6">
            <div className="absolute left-4 w-4 h-4 bg-wedo-green rounded-full z-10" />
            <span className="ml-12 text-xs text-lia-text-primary">
              Início do processo • {candidateName} adicionado ao banco de talentos
            </span>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-2" data-testid="activity-timeline">
      {filteredActivities.length === 0 && <EmptyState />}
      {filteredActivities.map((a) => renderActivityCard(a, false))}
    </div>
  )
}
