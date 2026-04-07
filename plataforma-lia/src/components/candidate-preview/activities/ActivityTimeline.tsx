"use client"

import React from "react"
import { Activity } from "lucide-react"
import { Activity as ActivityData } from "@/data/demo-activities"
import type { ActivityViewType } from "./ActivityFilters"

interface ActivityTimelineProps {
  filteredActivities: ActivityData[]
  activityView: ActivityViewType
  candidateName: string
  renderActivityCard: (activity: ActivityData, isTimeline: boolean) => React.ReactNode
}

export function ActivityTimeline({
  filteredActivities,
  activityView,
  candidateName,
  renderActivityCard,
}: ActivityTimelineProps) {
  if (activityView === 'timeline') {
    return (
      <div className="relative">
        {filteredActivities.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 px-4">
            <div className="w-16 h-16 bg-lia-bg-tertiary rounded-full flex items-center justify-center mb-4">
              <Activity className="w-8 h-8 text-lia-text-secondary" />
            </div>
            <h3 className="text-sm font-medium text-lia-text-primary mb-2">Nenhuma atividade registrada ainda</h3>
            <p className="text-xs text-lia-text-primary text-center max-w-xs">As atividades aparecerão aqui conforme o processo avança</p>
          </div>
        )}

        {filteredActivities.length > 0 && (
          <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-wedo-green opacity-20"></div>
        )}

        {filteredActivities.length > 0 && (() => {
          const groupedActivities: { [key: string]: typeof filteredActivities } = {}
          filteredActivities.forEach(activity => {
            let dateKey = activity.date
            if (activity.date.includes('Hoje')) dateKey = 'Hoje'
            else if (activity.date.includes('Ontem')) dateKey = 'Ontem'
            else if (activity.date.includes('2 dias')) dateKey = 'Esta Semana'
            else if (activity.date.includes('3 dias')) dateKey = 'Esta Semana'
            else if (activity.date.includes('4 dias')) dateKey = 'Esta Semana'
            else if (activity.date.includes('5 dias')) dateKey = 'Esta Semana'
            else if (activity.date.includes('6 dias')) dateKey = 'Esta Semana'
            else if (activity.date.includes('semana')) dateKey = 'Últimas Semanas'
            else dateKey = 'Anteriormente'
            if (!groupedActivities[dateKey]) groupedActivities[dateKey] = []
            groupedActivities[dateKey].push(activity)
          })
          const dateOrder = ['Hoje', 'Ontem', 'Esta Semana', 'Últimas Semanas', 'Anteriormente']
          return dateOrder.map(dateKey => {
            if (!groupedActivities[dateKey]) return null
            return (
              <div key={dateKey} className="mb-6">
                <div className="relative flex items-center mb-3">
                  <div className="absolute left-4 w-4 h-4 bg-lia-bg-primary rounded-full border-2 border-lia-border-medium dark:border-lia-border-medium z-10"></div>
                  <h3 className="ml-12 text-xs font-bold text-lia-text-primary">{dateKey}</h3>
                  <div className="ml-3 flex-1 h-px bg-lia-interactive-active"></div>
                </div>
                <div className="space-y-3">
                  {groupedActivities[dateKey].map((activity) => renderActivityCard(activity, true))}
                </div>
              </div>
            )
          }).filter(Boolean)
        })()}

        {filteredActivities.length > 0 && (
          <div className="relative flex items-center mt-6">
            <div className="absolute left-4 w-4 h-4 bg-wedo-green rounded-full z-10"></div>
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
      {filteredActivities.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 px-4">
          <div className="w-16 h-16 bg-lia-bg-tertiary rounded-full flex items-center justify-center mb-4">
            <Activity className="w-8 h-8 text-lia-text-secondary" />
          </div>
          <h3 className="text-sm font-medium text-lia-text-primary mb-2">Nenhuma atividade registrada ainda</h3>
          <p className="text-xs text-lia-text-primary text-center max-w-xs">As atividades aparecerão aqui conforme o processo avança</p>
        </div>
      )}
      {filteredActivities.map((activity) => renderActivityCard(activity, false))}
    </div>
  )
}
