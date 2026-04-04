"use client"

import React from "react"
import { textStyles } from "@/lib/design-tokens"
import { Button } from "@/components/ui/button"
import { Plus, Target } from "lucide-react"
import { DailyBriefingCard } from "@/components/daily-briefing-card"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import { useTasksCore } from "./use-tasks-core"
import { TasksMetricsBar } from "./tasks/TasksMetricsBar"
import { MyTasksCard } from "./tasks/MyTasksCard"
import { ActiveAlertsCard } from "./tasks/ActiveAlertsCard"
import { ActiveJobsCard } from "./tasks/ActiveJobsCard"

interface TasksPageProps {
  onNavigate?: (page: string) => void
}

export function TasksPage({ onNavigate }: TasksPageProps = {}) {
  const { state, actions } = useTasksCore(onNavigate)
  const {
    pendingTasks, activeAlerts, filteredPendingTasks, filteredAndSortedJobs, metrics,
    pendingTaskFilter, showJobFilters, jobSearchTerm, selectedDepartments,
    selectedUrgencies, selectedPublications, jobSortBy, activeJobFiltersCount,
    uniqueDepartments,
  } = state
  const {
    setPendingTaskFilter, setShowJobFilters, setJobSearchTerm, setSelectedDepartments,
    setSelectedUrgencies, setSelectedPublications, setJobSortBy, clearJobFilters,
    handleConfirmTask, handleRejectTask, handleAlertAction, handleLIAAction,
  } = actions

  return (
    <>
    <ErrorBoundarySection>
    <div className="h-full flex flex-col bg-lia-bg-primary dark:bg-lia-bg-primary overflow-hidden">
      <div className="p-2 max-w-full overflow-x-auto">

        <div className="flex items-center justify-between mb-1.5">
          <div>
            <h1 className="text-base font-['Open_Sans',sans-serif] font-semibold text-lia-text-primary mb-0.5 flex items-center gap-2">
              <Target className="w-4 h-4 text-lia-text-primary" />
              Painel de Controle
            </h1>
            <p className={`${textStyles.bodySmall} text-lia-text-secondary`}>
              Você tem 30 novos candidatos e 4 vagas abertas.
            </p>
          </div>
          <Button
            className="gap-1.5 h-7 px-2.5 font-open-sans text-xs"
            onClick={() => {
              if (onNavigate) {
                onNavigate('Chat com LIA')
                setTimeout(() => {
                  window.dispatchEvent(new CustomEvent('lia-new-task'))
                }, 100)
              }
            }}
          >
            <Plus className="w-3.5 h-3.5" />
            Nova Tarefa
          </Button>
        </div>

        <div className="mb-2">
          <DailyBriefingCard
            onNavigate={onNavigate}
            onActionClick={(action, context) => {
              if (action === 'open_pipeline_chat') {
                if (onNavigate) {
                  onNavigate('Chat com LIA')
                  setTimeout(() => {
                    window.dispatchEvent(new CustomEvent('lia-open-pipeline', {
                      detail: context
                    }))
                  }, 100)
                }
              }
            }}
          />
        </div>

        <div className="space-y-2">

            <TasksMetricsBar metrics={metrics} />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
              <MyTasksCard
                pendingTasks={pendingTasks}
                filteredPendingTasks={filteredPendingTasks}
                pendingTaskFilter={pendingTaskFilter}
                setPendingTaskFilter={setPendingTaskFilter}
                handleConfirmTask={handleConfirmTask}
                handleRejectTask={handleRejectTask}
              />

              <ActiveAlertsCard
                activeAlerts={activeAlerts}
                onAlertAction={handleAlertAction}
                textStyles={textStyles}
              />
            </div>

            <ActiveJobsCard
              filteredAndSortedJobs={filteredAndSortedJobs}
              jobSearchTerm={jobSearchTerm}
              setJobSearchTerm={setJobSearchTerm}
              showJobFilters={showJobFilters}
              setShowJobFilters={setShowJobFilters}
              activeJobFiltersCount={activeJobFiltersCount}
              jobSortBy={jobSortBy}
              setJobSortBy={setJobSortBy}
              selectedDepartments={selectedDepartments}
              setSelectedDepartments={setSelectedDepartments}
              selectedUrgencies={selectedUrgencies}
              setSelectedUrgencies={setSelectedUrgencies}
              selectedPublications={selectedPublications}
              setSelectedPublications={setSelectedPublications}
              uniqueDepartments={uniqueDepartments}
              clearJobFilters={clearJobFilters}
              handleLIAAction={handleLIAAction}
              onNavigate={onNavigate}
            />

        </div>
      </div>
    </div>
    </ErrorBoundarySection>
    </>
  )
}
