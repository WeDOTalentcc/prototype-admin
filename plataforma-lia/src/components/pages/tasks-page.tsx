"use client"

import React, { useState } from "react"
import { textStyles } from "@/lib/design-tokens"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Plus, Activity, Loader2, AlertCircle, RefreshCw, Brain } from "lucide-react"
import { DailyBriefingCard } from "@/components/daily-briefing-card"
import { ActivityFeed } from "@/components/activity-feed"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import { useTasksCore } from "./use-tasks-core"
import { useTasksInterviews } from "./useTasksInterviews"
import { useJWTAuth } from "@/contexts/auth-context"
import { TasksMetricsBar } from "./tasks/TasksMetricsBar"
import { MyTasksCard } from "./tasks/MyTasksCard"
import { ActiveAlertsCard } from "./tasks/ActiveAlertsCard"
import { ActiveJobsCard } from "./tasks/ActiveJobsCard"
import { AgentsCard } from "./tasks/AgentsCard"
import { AgentRunningBanner } from "./tasks/AgentRunningBanner"
import { useProactiveHints } from "@/hooks/proactive/use-proactive-hints"
import dynamic from "next/dynamic"
// C5.4 (2026-05-29): lazy-load DecisionTreeDrawer (Radix Sheet + reasoning query)
// so its chunk only downloads when an execution is actually opened. Combined with
// the conditional mount below (drawer rendered only when activeExecutionId !== null),
// this keeps the drawer out of the tasks-page initial bundle.
const DecisionTreeDrawer = dynamic(
  () =>
    import("@/components/pages-agent-studio/decision-tree").then(
      (m) => m.DecisionTreeDrawer,
    ),
  { ssr: false },
)

interface TasksPageProps {
  onNavigate?: (page: string) => void
}

export function TasksPage({ onNavigate }: TasksPageProps = {}) {
  const { user } = useJWTAuth()
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

  const {
    todayInterviews,
    pastInterviews,
    isLoading: interviewsLoading,
    error: interviewsError,
    copiedId,
    fetchInterviews,
    handleOpenMeeting,
    handleCopyLink,
    handleReschedule,
    handleReject: handleInterviewReject,
    handleOpenJob,
  } = useTasksInterviews(onNavigate)

  const [subtitleText, setSubtitleText] = useState<string | null>(null)
  const [activityActorFilter, setActivityActorFilter] = useState<'todos' | 'lia' | 'recrutador'>('todos')
  // Onda 2 F2 — Drawer canonical Onda 1 disparado por AgentsCard.
  const [activeExecutionId, setActiveExecutionId] = useState<string | null>(null)

  // F2 hints proativas urgentes (severity high|critical) para exibir no Decidir
  const { hints: proactiveHints } = useProactiveHints()
  const urgentHints = proactiveHints
    .filter((h) => h.severity === "high" || h.severity === "critical")
    .slice(0, 5)

  return (
    <>
    <ErrorBoundarySection>
    <div className="h-full flex flex-col bg-lia-bg-primary dark:bg-lia-bg-primary overflow-hidden">
      <div className="p-3 max-w-full overflow-x-auto">

        <div className="flex items-center justify-between mb-1.5">
          <div>
            <h1 className="text-lg font-semibold text-lia-text-primary mb-0.5">
              Tarefas
            </h1>
            <p className={`${textStyles.bodySmall} text-lia-text-secondary`}>
              {subtitleText || 'Carregando resumo do dia...'}
            </p>
          </div>
          <Button
            className="gap-1.5 h-7 px-2.5 font-open-sans text-xs hover:bg-lia-interactive-hover transition-colors cursor-pointer"
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

            {/* Onda 2 F3 — banner global "N agentes trabalhando agora". */}
            <AgentRunningBanner />

            <TasksMetricsBar metrics={metrics} />

            {error && (
              <div className="flex items-center gap-2 p-3 rounded-xl bg-status-warning/10 border border-status-warning/30 text-sm text-status-warning">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span className="flex-1">{error}</span>
                <Button variant="ghost" size="sm" className="h-7 px-2 text-xs hover:bg-lia-interactive-hover transition-colors cursor-pointer" onClick={() => refetch()}>
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
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                  <MyTasksCard
                    pendingTasks={pendingTasks}
                    filteredPendingTasks={filteredPendingTasks}
                    pendingTaskFilter={pendingTaskFilter}
                    setPendingTaskFilter={setPendingTaskFilter}
                    handleConfirmTask={handleConfirmTask}
                    handleRejectTask={handleRejectTask}
                    todayInterviews={todayInterviews}
                    pastInterviews={pastInterviews}
                    interviewsLoading={interviewsLoading}
                    interviewsError={interviewsError}
                    copiedId={copiedId}
                    fetchInterviews={fetchInterviews}
                    onOpenMeeting={handleOpenMeeting}
                    onCopyLink={handleCopyLink}
                    onReschedule={handleReschedule}
                    onReject={handleInterviewReject}
                    onOpenJob={handleOpenJob}
                    userName={user?.name?.split(' ')[0] || 'Recrutador'}
                  />

                  {urgentHints.length > 0 && (
                    <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-primary p-3 space-y-2">
                      <div className="flex items-center gap-2">
                        <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                        <h3 className="text-xs font-semibold text-lia-text-primary">Sugestão automática</h3>
                      </div>
                      {urgentHints.map((hint) => (
                        <div key={hint.id} className="p-2.5 rounded-lg border border-lia-border-subtle bg-lia-bg-secondary/50">
                          <p className="text-xs font-medium text-lia-text-primary leading-tight">{hint.title}</p>
                          <p className="text-micro text-lia-text-secondary mt-0.5 leading-tight">{hint.message}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  <ActiveAlertsCard
                    activeAlerts={activeAlerts}
                    onAlertAction={handleAlertAction}
                    textStyles={textStyles}
                  />

                  {/* Onda 2 F2 — AgentsCard 5º card no Decidir.
                     Drawer canonical Onda 1 controlado pelo state desta page. */}
                  <AgentsCard
                    onOpenDecisionTree={(execId) => setActiveExecutionId(execId)}
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
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Activity className="w-3.5 h-3.5 text-wedo-cyan" />
                        <CardTitle className={`${textStyles.label} font-semibold text-lia-text-primary`}>
                          Atividades Recentes
                        </CardTitle>
                      </div>
                      <div className="flex gap-1">
                        {([
                          { key: 'todos', label: 'Todos' },
                          { key: 'lia', label: 'LIA' },
                          { key: 'recrutador', label: 'Recrutador' },
                        ] as const).map(({ key, label }) => (
                          <Button
                            key={key}
                            variant={activityActorFilter === key ? 'primary' : 'ghost'}
                            size="sm"
                            className="h-6 px-2 text-xs hover:bg-lia-interactive-hover transition-colors cursor-pointer"
                            onClick={() => setActivityActorFilter(key)}
                          >
                            {label}
                          </Button>
                        ))}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0 pb-2">
                    <ActivityFeed
                      limit={20}
                      actorFilter={activityActorFilter === 'todos' ? undefined : activityActorFilter}
                      className="max-h-[400px] overflow-y-auto"
                    />
                  </CardContent>
                </Card>
              </>
            )}

        </div>
      </div>
    </div>
    </ErrorBoundarySection>
    {/* Onda 2 F2 — Drawer canonical Onda 1, montado no nível da page para
       não competir com modais filhos por z-index nem por focus trap.
       C5.4: mount condicional (só quando há execução ativa) habilita o
       lazy-load do chunk dinâmico — o drawer mantém executionId não-null. */}
    {activeExecutionId !== null && (
      <DecisionTreeDrawer
        executionId={activeExecutionId}
        onClose={() => setActiveExecutionId(null)}
      />
    )}
    </>
  )
}
