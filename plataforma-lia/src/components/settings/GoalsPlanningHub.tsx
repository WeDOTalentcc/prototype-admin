"use client"

import React from "react"
import { Calendar } from "lucide-react"
import { useTranslations } from "next-intl"
import { GoalsManagement } from "./goals-management"
import { SmartImportZone } from "./SmartImportZone"
import { tabStyles } from '@/lib/design-tokens'
import { useGoalsPlanningHub } from "./useGoalsPlanningHub"
import { WorkforceSection } from "./WorkforceSection"

interface GoalsPlanningHubProps {
  users?: { id: string; name?: string; email?: string; role?: string; [key: string]: unknown }[]
  onGoalUpdate?: (userId: string, goals: Record<string, unknown>) => void
  activeSubsection?: string
}

export function GoalsPlanningHub({ users = [], onGoalUpdate, activeSubsection }: GoalsPlanningHubProps) {
  const t = useTranslations('settings.goals')
  const hub = useGoalsPlanningHub({ users, onGoalUpdate, activeSubsection })

  const tabs = [
    { id: 'workforce', label: t('tabWorkforce'), icon: Calendar }
  ]

  const renderGoals = () => (
    <div className="space-y-4">
      <SmartImportZone
        title={t('importGoalsTitle')}
        description={t('importGoalsDescription')}
        importEndpoint="/api/backend-proxy/goals/import"
        templateDownloadEndpoint="/api/backend-proxy/goals/import/template"
        expectedFields={["user_id", "name", "target", "period", "category"]}
        onImportSuccess={hub.fetchGoals}
      />

      <GoalsManagement
        key={hub.goalsRefreshKey}
        users={hub.effectiveUsers as unknown as { id: string; name: string; email?: string; role?: string; department?: string; isActive?: boolean; avatar?: string }[]}
        onGoalUpdate={(hub.onGoalUpdate || (() => {})) as unknown as (userId: string, goals: import('./use-goals-management').UserGoal[]) => void}
      />
    </div>
  )

  const renderContent = () => {
    switch (hub.activeTab) {
      case 'workforce':
        return <WorkforceSection hub={hub} />
      default:
        return <WorkforceSection hub={hub} />
    }
  }

  return (
    <div className="space-y-3">
      <div className={tabStyles.pillContainer}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => hub.setActiveTab(tab.id)}
            className={hub.activeTab === tab.id ? tabStyles.pillActive : tabStyles.pill}
          >
            <tab.icon className={tabStyles.pillIcon} />
            {tab.label}
          </button>
        ))}
      </div>

      {renderContent()}
    </div>
  )
}
