"use client"

import React from "react"
import { Calendar } from "lucide-react"
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

const tabs = [
  { id: 'workforce', label: 'Planejamento de Contratações', icon: Calendar }
]

export function GoalsPlanningHub({ users = [], onGoalUpdate, activeSubsection }: GoalsPlanningHubProps) {
  const hub = useGoalsPlanningHub({ users, onGoalUpdate, activeSubsection })

  const renderGoals = () => (
    <div className="space-y-4">
      <SmartImportZone
        title="Importar Metas"
        description="Importe metas mensais ou trimestrais por recrutador via planilha. A LIA identifica período, responsável e valores automaticamente."
        importEndpoint="/api/backend-proxy/goals/import"
        templateDownloadEndpoint="/api/backend-proxy/goals/import/template"
        expectedFields={["user_id", "name", "target", "period", "category"]}
        onImportSuccess={hub.fetchGoals}
      />

      <GoalsManagement
        key={hub.goalsRefreshKey}
        users={hub.effectiveUsers}
        onGoalUpdate={(hub.onGoalUpdate || (() => {})) as (userId: string, goals: Record<string, unknown>) => void}
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
