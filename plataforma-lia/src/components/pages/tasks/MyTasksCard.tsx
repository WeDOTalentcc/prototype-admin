"use client"

import React from"react"
import { textStyles } from"@/lib/design-tokens"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import {
  CheckCircle2, MessageSquare, Search, Calendar, Clock,
  Sun, Sunset, Loader2, RefreshCw
} from"lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from"@/components/ui/tabs"
import { TaskCard } from"./TaskCard"
import { InterviewCard } from"../InterviewCard"
import type { PendingTask } from"../use-tasks-core"
import type { ScheduledInterview } from"../tasks-page-utils"
import {
  getGreeting, getGreetingIcon, getFormattedDate, getTimeUntilNext
} from"../tasks-page-utils"

type TaskFilter = 'all' | 'feedback' | 'sourcing'

interface MyTasksCardProps {
  pendingTasks: PendingTask[]
  filteredPendingTasks: PendingTask[]
  pendingTaskFilter: string
  setPendingTaskFilter: (filter: TaskFilter) => void
  handleConfirmTask: (task: PendingTask) => void
  handleRejectTask: (task: PendingTask) => void
  todayInterviews: ScheduledInterview[]
  pastInterviews: ScheduledInterview[]
  interviewsLoading: boolean
  interviewsError: string | null
  copiedId: string | null
  fetchInterviews: () => void
  onOpenMeeting: (interview: ScheduledInterview) => void
  onCopyLink: (interview: ScheduledInterview) => void
  onReschedule: (interview: ScheduledInterview) => void
  onReject: (interview: ScheduledInterview) => void
  onOpenJob: (interview: ScheduledInterview) => void
  userName?: string
}

type TaskCardTask = {
  id: string
  type: string
  title: string
  description: string
  priority: string
  dueDate: Date
  candidateName?: string
  relatedJob?: string
}

export function MyTasksCard({
  pendingTasks,
  filteredPendingTasks,
  pendingTaskFilter,
  setPendingTaskFilter,
  handleConfirmTask,
  handleRejectTask,
  todayInterviews,
  pastInterviews,
  interviewsLoading,
  interviewsError,
  copiedId,
  fetchInterviews,
  onOpenMeeting,
  onCopyLink,
  onReschedule,
  onReject,
  onOpenJob,
  userName,
}: MyTasksCardProps) {
  const tasksOnly = filteredPendingTasks.filter(t => t.type !== 'entrevista')
  const morningTasks = tasksOnly.filter(t => t.dueDate.getHours() < 12)
  const afternoonTasks = tasksOnly.filter(t => t.dueDate.getHours() >= 12)

  const nonInterviewTasks = pendingTasks.filter(t => t.type !== 'entrevista')

  const todayOnlyInterviews = todayInterviews.filter(i => i.dateLabel === 'Hoje')
  const morningInterviews = todayOnlyInterviews.filter(i => i.time < '12:00')
  const afternoonInterviews = todayOnlyInterviews.filter(i => i.time >= '12:00')
  const futureInterviews = todayInterviews.filter(i => i.dateLabel !== 'Hoje')
  const scheduledCount = todayOnlyInterviews.length
  const timeUntilNext = getTimeUntilNext(todayOnlyInterviews)

  const renderInterviewCard = (interview: ScheduledInterview, variant: 'active' | 'past') => (
    <InterviewCard
      key={interview.id}
      interview={interview}
      copiedId={copiedId}
      onOpenMeeting={onOpenMeeting}
      onCopyLink={onCopyLink}
      onReschedule={variant === 'active' ? onReschedule : undefined}
      onReject={variant === 'active' ? onReject : undefined}
      onOpenJob={onOpenJob}
      variant={variant}
    />
  )

  return (
    <Card className="border-lia-border-subtle dark:border-lia-border-subtle">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-lia-text-primary" />
            <CardTitle className={`${textStyles.label} font-semibold text-lia-text-primary`}>Minhas Tarefas</CardTitle>
            <Chip density="relaxed" variant="neutral" className="font-sans">
              {nonInterviewTasks.length + todayInterviews.length}
            </Chip>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0 pb-2">
        <Tabs defaultValue="tarefas" className="w-full">
          <TabsList className="grid w-full grid-cols-3 h-8 mb-3 bg-lia-bg-tertiary dark:bg-lia-bg-secondary p-0.5">
            <TabsTrigger value="tarefas" className="text-xs font-open-sans h-7 data-[state=active]:font-semibold data-[state=active]:bg-lia-bg-primary data-[state=active]:text-lia-text-primary dark:data-[state=active]:bg-lia-btn-primary-bg dark:data-[state=active]:text-lia-text-inverse">
              Tarefas ({nonInterviewTasks.length})
            </TabsTrigger>
            <TabsTrigger value="entrevistas" className="text-xs font-open-sans h-7 data-[state=active]:font-semibold data-[state=active]:bg-lia-bg-primary data-[state=active]:text-lia-text-primary dark:data-[state=active]:bg-lia-btn-primary-bg dark:data-[state=active]:text-lia-text-inverse">
              Entrevistas ({todayInterviews.length})
            </TabsTrigger>
            <TabsTrigger value="historico" className="text-xs font-open-sans h-7 data-[state=active]:font-semibold data-[state=active]:bg-lia-bg-primary data-[state=active]:text-lia-text-primary dark:data-[state=active]:bg-lia-btn-primary-bg dark:data-[state=active]:text-lia-text-inverse">
              Histórico ({pastInterviews.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="tarefas" className="mt-0">
            <div className="flex items-center gap-1.5 mb-3 flex-wrap">
              {([
                { key: 'all', label: `Todos (${nonInterviewTasks.length})`, icon: null },
                { key: 'feedback', label: `Feedback (${nonInterviewTasks.filter(t => t.type === 'feedback').length})`, icon: <MessageSquare className="w-2.5 h-2.5" /> },
                { key: 'sourcing', label: `Sourcing (${nonInterviewTasks.filter(t => t.type === 'sourcing').length})`, icon: <Search className="w-2.5 h-2.5" /> },
              ] as const).map(({ key, label, icon }) => (
                <button
                  key={key}
                  onClick={() => setPendingTaskFilter(key)}
                  className={`px-2 py-1 text-xs font-open-sans rounded-full transition-colors motion-reduce:transition-none flex items-center gap-1 ${
                    pendingTaskFilter === key
                      ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text dark:bg-lia-btn-primary-bg font-medium'
                      : 'bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary hover:bg-lia-interactive-active dark:hover:bg-lia-bg-inverse'
                  }`}
                >
                  {icon}
                  {label}
                </button>
              ))}
            </div>

            <div className="max-h-[320px] overflow-y-auto space-y-3">
              {morningTasks.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <div className="w-1.5 h-1.5 rounded-full"></div>
                    <h3 className="text-xs font-open-sans font-semibold text-lia-text-primary">Sessão Manhã</h3>
                    <span className="text-xs font-open-sans text-lia-text-primary">{morningTasks.length} atividades</span>
                  </div>
                  <div className="space-y-1.5">
                    {morningTasks.map((task) => (
                      <TaskCard
                        key={task.id}
                        task={task}
                        onConfirm={(t: TaskCardTask) => handleConfirmTask(task)}
                        onReject={(t: TaskCardTask) => handleRejectTask(task)}
                      />
                    ))}
                  </div>
                </div>
              )}

              {afternoonTasks.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <div className="w-1.5 h-1.5 rounded-full"></div>
                    <h3 className="text-xs font-open-sans font-semibold text-lia-text-primary">Sessão Tarde</h3>
                    <span className="text-xs font-open-sans text-lia-text-primary">{afternoonTasks.length} atividades</span>
                  </div>
                  <div className="space-y-1.5">
                    {afternoonTasks.map((task) => (
                      <TaskCard
                        key={task.id}
                        task={task}
                        onConfirm={(t: TaskCardTask) => handleConfirmTask(task)}
                        onReject={(t: TaskCardTask) => handleRejectTask(task)}
                      />
                    ))}
                  </div>
                </div>
              )}

              {tasksOnly.length === 0 && (
                <div className="text-center py-8">
                  <CheckCircle2 className="w-12 h-12 mx-auto text-lia-text-muted mb-3" />
                  <p className="text-sm font-medium text-lia-text-primary mb-1">Nenhuma tarefa pendente</p>
                  <p className="text-xs text-lia-text-secondary">Todas as tarefas foram concluídas</p>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="entrevistas" className="mt-0">
            <div className="flex items-center gap-2 mb-2 px-1">
              {getGreetingIcon()}
              <span className="text-sm font-semibold text-lia-text-primary">
                {getGreeting()}, {userName || 'Recrutador'}
              </span>
              <span className="text-xs text-lia-text-tertiary">
                — {getFormattedDate()}
              </span>
            </div>
            {!interviewsLoading && todayInterviews.length > 0 && (
              <p className="text-xs text-lia-text-tertiary px-1 mb-3">
                <span className="font-[Inter,sans-serif] font-semibold text-lia-text-primary">{scheduledCount}</span> entrevista{scheduledCount !== 1 ? 's' : ''} hoje
                {futureInterviews.length > 0 ? ` · ${futureInterviews.length} próxima${futureInterviews.length !== 1 ? 's' : ''}` : ''}
                {timeUntilNext && (
                  <>
                    <span className="text-lia-text-disabled mx-2">|</span>
                    Próxima em <span className="font-[Inter,sans-serif] font-semibold text-lia-text-primary">{timeUntilNext}</span>
                  </>
                )}
              </p>
            )}

            {interviewsLoading ? (
              <div className="py-12 text-center" role="status" aria-live="polite" aria-label="Carregando...">
                <Loader2 className="w-6 h-6 text-lia-text-muted mx-auto mb-2 animate-spin motion-reduce:animate-none" />
                <p className="text-xs text-lia-text-tertiary">Carregando entrevistas...</p>
              </div>
            ) : interviewsError ? (
              <div className="py-12 text-center">
                <Calendar className="w-10 h-10 text-lia-text-muted mx-auto mb-2" />
                <p className="text-xs font-semibold text-lia-text-secondary mb-1">Erro ao carregar</p>
                <p className="text-xs text-lia-text-tertiary mb-2">{interviewsError}</p>
                <Button size="sm" variant="outline" onClick={fetchInterviews} className="h-7 px-3 text-xs gap-1.5">
                  <RefreshCw className="w-3 h-3" /> Tentar novamente
                </Button>
              </div>
            ) : todayInterviews.length === 0 ? (
              <div className="py-12 text-center">
                <Calendar className="w-10 h-10 text-lia-text-muted mx-auto mb-2" />
                <p className="text-xs font-semibold text-lia-text-secondary mb-1">Nenhuma entrevista agendada</p>
                <p className="text-xs text-lia-text-tertiary">Sua agenda está livre.</p>
              </div>
            ) : (
              <div className="max-h-[400px] overflow-y-auto space-y-2">
                {morningInterviews.length > 0 && (
                  <div className="flex items-center gap-2 pt-1 pb-0.5 px-1">
                    <Sun className="w-3.5 h-3.5 text-status-warning" />
                    <span className="text-xs font-[Inter,sans-serif] font-medium text-lia-text-tertiary uppercase tracking-wider">Manhã</span>
                    <div className="flex-1 border-t border-lia-border-subtle dark:border-lia-border-subtle" />
                  </div>
                )}
                {morningInterviews.map((interview) => renderInterviewCard(interview, 'active'))}
                {afternoonInterviews.length > 0 && (
                  <div className="flex items-center gap-2 pt-2 pb-0.5 px-1">
                    <Sunset className="w-3.5 h-3.5 text-wedo-orange" />
                    <span className="text-xs font-[Inter,sans-serif] font-medium text-lia-text-tertiary uppercase tracking-wider">Tarde</span>
                    <div className="flex-1 border-t border-lia-border-subtle dark:border-lia-border-subtle" />
                  </div>
                )}
                {afternoonInterviews.map((interview) => renderInterviewCard(interview, 'active'))}
                {futureInterviews.length > 0 && (() => {
                  const groupedByDate: Record<string, ScheduledInterview[]> = {}
                  futureInterviews.forEach(i => {
                    if (!groupedByDate[i.dateLabel]) groupedByDate[i.dateLabel] = []
                    groupedByDate[i.dateLabel].push(i)
                  })
                  return Object.entries(groupedByDate).map(([dateLabel, interviews]) => (
                    <React.Fragment key={dateLabel}>
                      <div className="flex items-center gap-2 pt-3 pb-0.5 px-1">
                        <Calendar className="w-3.5 h-3.5 text-lia-text-muted" />
                        <span className="text-xs font-[Inter,sans-serif] font-medium text-lia-text-tertiary uppercase tracking-wider">{dateLabel}</span>
                        <div className="flex-1 border-t border-lia-border-subtle dark:border-lia-border-subtle" />
                      </div>
                      {interviews.map((interview) => renderInterviewCard(interview, 'active'))}
                    </React.Fragment>
                  ))
                })()}
              </div>
            )}
          </TabsContent>

          <TabsContent value="historico" className="mt-0">
            {interviewsLoading ? (
              <div className="py-12 text-center" role="status" aria-live="polite" aria-label="Carregando...">
                <Loader2 className="w-6 h-6 text-lia-text-muted mx-auto mb-2 animate-spin motion-reduce:animate-none" />
                <p className="text-xs text-lia-text-tertiary">Carregando histórico...</p>
              </div>
            ) : interviewsError ? (
              <div className="py-12 text-center">
                <Calendar className="w-10 h-10 text-lia-text-muted mx-auto mb-2" />
                <p className="text-xs font-semibold text-lia-text-secondary mb-1">Erro ao carregar histórico</p>
                <p className="text-xs text-lia-text-tertiary mb-2">{interviewsError}</p>
                <Button size="sm" variant="outline" onClick={fetchInterviews} className="h-7 px-3 text-xs gap-1.5">
                  <RefreshCw className="w-3 h-3" /> Tentar novamente
                </Button>
              </div>
            ) : pastInterviews.length === 0 ? (
              <div className="py-12 text-center">
                <Clock className="w-10 h-10 text-lia-text-muted mx-auto mb-2" />
                <p className="text-xs font-semibold text-lia-text-secondary mb-1">Nenhum histórico</p>
                <p className="text-xs text-lia-text-tertiary">Suas entrevistas passadas aparecerão aqui.</p>
              </div>
            ) : (
              <div className="max-h-[400px] overflow-y-auto space-y-2">
                {pastInterviews.map((interview) => renderInterviewCard(interview, 'past'))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
