"use client"

import React, { useState } from "react"
import { textStyles } from "@/lib/design-tokens"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Plus, Target, Activity, Loader2, AlertCircle, RefreshCw } from "lucide-react"
import { DailyBriefingCard } from "@/components/daily-briefing-card"
import { ActivityFeed } from "@/components/activity-feed"
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
    uniqueDepartments, loading, error,
  } = state
  const {
    setPendingTaskFilter, setShowJobFilters, setJobSearchTerm, setSelectedDepartments,
    setSelectedUrgencies, setSelectedPublications, setJobSortBy, clearJobFilters,
    handleConfirmTask, handleRejectTask, handleAlertAction, handleLIAAction,
    refetch,
  } = actions

  const [subtitleText, setSubtitleText] = useState<string | null>(null)

  return (
    <>
    <ErrorBoundarySection>
    <div className="h-full flex flex-col bg-lia-bg-primary dark:bg-lia-bg-primary overflow-hidden">
      <div className="p-2 max-w-full overflow-x-auto">

        <div className="flex items-center justify-between mb-1.5">
          <div>
            <h1 className="text-base font-['Open_Sans',sans-serif] font-semibold text-lia-text-primary mb-0.5 flex items-center gap-2">
              <Target className="w-4 h-4 text-lia-text-primary" />
              Tarefas
            </h1>
            <p className={`${textStyles.bodySmall} text-lia-text-secondary`}>
              {subtitleText || 'Carregando resumo do dia...'}
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
            onBriefingLoaded={(briefing) => {
              const candidates = briefing.pipeline?.total_candidates || 0
              const jobs = briefing.pipeline?.active_jobs || 0
              if (candidates > 0 || jobs > 0) {
                setSubtitleText(`Você tem ${candidates} candidato${candidates !== 1 ? 's' : ''} e ${jobs} vaga${jobs !== 1 ? 's' : ''} ativa${jobs !== 1 ? 's' : ''}.`)
              } else {
                setSubtitleText('Seu painel de tarefas e acompanhamento.')
              }
            }}
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

            {error && (
              <div className="flex items-center gap-2 p-3 rounded-md bg-status-warning/10 border border-status-warning/30 text-sm text-status-warning">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span className="flex-1">{error}</span>
                <Button variant="ghost" size="sm" className="h-7 px-2 text-xs" onClick={() => refetch()}>
                  <RefreshCw className="w-3 h-3 mr-1" />
                  Tentar novamente
                </Button>
              </div>
            )}

            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin text-lia-text-secondary" />
                <span className="ml-2 text-sm text-lia-text-secondary">Carregando dados...</span>
              </div>
            ) : (
              <>
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

                <Card className="border-lia-border-subtle dark:border-lia-border-subtle">
                  <CardHeader className="pb-2">
                    <div className="flex items-center gap-2">
                      <Activity className="w-3.5 h-3.5 text-lia-text-primary" />
                      <CardTitle className={`${textStyles.label} font-semibold text-lia-text-primary`}>
                        Atividades Recentes
                      </CardTitle>
                      <Badge variant="outline" className="text-xs font-inter">
                        LIA + Recrutador
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0 pb-2">
                    <ActivityFeed limit={20} className="max-h-[400px] overflow-y-auto" />
                  </CardContent>
                </Card>
              </>
            )}

        </div>
      </div>
    </div>
    </ErrorBoundarySection>
    </>
  )
}
