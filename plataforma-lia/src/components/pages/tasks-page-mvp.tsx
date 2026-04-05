"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Calendar, Clock, Sun, Sunset, Loader2, RefreshCw,
  LayoutDashboard
} from "lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useTasksInterviews } from "./useTasksInterviews"
import { InterviewCard } from "./InterviewCard"
import {
  getGreeting, getGreetingIcon, getFormattedDate, getTimeUntilNext,
  type ScheduledInterview
} from "./tasks-page-utils"

interface TasksPageMVPProps {
  onNavigate?: (page: string) => void
}

export function TasksPageMVP({ onNavigate }: TasksPageMVPProps = {}) {
  const {
    todayInterviews,
    pastInterviews,
    isLoading,
    error,
    copiedId,
    fetchInterviews,
    handleOpenMeeting,
    handleCopyLink,
    handleReschedule,
    handleReject,
    handleOpenJob,
  } = useTasksInterviews(onNavigate)

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
      onOpenMeeting={handleOpenMeeting}
      onCopyLink={handleCopyLink}
      onReschedule={variant === 'active' ? handleReschedule : undefined}
      onReject={variant === 'active' ? handleReject : undefined}
      onOpenJob={handleOpenJob}
      variant={variant}
    />
  )

  return (
    <div className="h-full flex flex-col bg-lia-bg-primary dark:bg-lia-bg-primary overflow-hidden">
      <div className="flex-shrink-0 px-4 pt-3 pb-0 bg-lia-bg-primary dark:bg-lia-bg-primary">
        <div className="flex items-center justify-between mb-0.5">
          <div className="flex items-center gap-3">
            <div>
              <h1 className="text-xl font-['Open_Sans',sans-serif] font-semibold text-lia-text-primary flex items-center gap-2">
                <LayoutDashboard className="w-5 h-5 text-lia-text-secondary" />
                Tarefas
              </h1>
            </div>
          </div>
        </div>
      </div>
      <div className="flex-shrink-0 px-4 pt-2 pb-1">
        <div className="flex items-center gap-2 mb-0.5">
          {getGreetingIcon()}
          <h1 className="text-lg font-[Open_Sans,sans-serif] font-semibold text-lia-text-primary">
            {getGreeting()}, Ana
          </h1>
        </div>
        <p className="text-base-ui font-[Open_Sans,sans-serif] text-lia-text-tertiary pl-7">
          Sua agenda — {getFormattedDate()}
        </p>
        {!isLoading && todayInterviews.length > 0 && (
          <p className="text-xs font-[Open_Sans,sans-serif] text-lia-text-tertiary pl-7 mt-1">
            <span className="font-[Inter,sans-serif] font-semibold text-lia-text-primary">{scheduledCount}</span> entrevista{scheduledCount !== 1 ? 's' : ''} hoje{futureInterviews.length > 0 ? ` · ${futureInterviews.length} próxima${futureInterviews.length !== 1 ? 's' : ''}` : ''}
            {timeUntilNext && (
              <>
                <span className="text-lia-text-disabled mx-2">|</span>
                Próxima em <span className="font-[Inter,sans-serif] font-semibold text-lia-text-primary">{timeUntilNext}</span>
              </>
            )}
          </p>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-4 pt-3 pb-4">
        <Tabs defaultValue="entrevistas" className="w-full">
          <TabsList className="grid w-full grid-cols-2 h-9 bg-lia-bg-tertiary dark:bg-lia-bg-secondary p-1 rounded-md">
            <TabsTrigger
              value="entrevistas"
              className="text-sm-ui font-[Open_Sans,sans-serif] h-7 rounded-md data-[state=active]:font-semibold data-[state=active]:bg-lia-bg-primary data-[state=active]:text-lia-text-primary data-[state=active]:shadow-lia-sm dark:data-[state=active]:bg-lia-btn-primary-bg dark:data-[state=active]:text-lia-text-inverse"
            >
              Entrevistas ({todayInterviews.length})
            </TabsTrigger>
            <TabsTrigger
              value="historico"
              className="text-sm-ui font-[Open_Sans,sans-serif] h-7 rounded-md data-[state=active]:font-semibold data-[state=active]:bg-lia-bg-primary data-[state=active]:text-lia-text-primary data-[state=active]:shadow-lia-sm dark:data-[state=active]:bg-lia-btn-primary-bg dark:data-[state=active]:text-lia-text-inverse"
            >
              Histórico ({pastInterviews.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="entrevistas" className="mt-3">
            {isLoading ? (
              <div className="py-16 text-center" role="status" aria-live="polite" aria-label="Carregando...">
                <Loader2 className="w-8 h-8 text-lia-text-disabled mx-auto mb-3 animate-spin motion-reduce:animate-none" />
                <p className="text-base-ui font-[Open_Sans,sans-serif] text-lia-text-tertiary">Carregando entrevistas...</p>
              </div>
            ) : error ? (
              <div className="py-16 text-center">
                <Calendar className="w-12 h-12 text-lia-text-disabled mx-auto mb-3" />
                <p className="text-base-ui font-semibold text-lia-text-secondary mb-1">Erro ao carregar</p>
                <p className="text-xs text-lia-text-tertiary mb-3">{error}</p>
                <Button size="sm" variant="outline" onClick={fetchInterviews} className="h-7 px-3 text-xs gap-1.5">
                  <RefreshCw className="w-3 h-3" /> Tentar novamente
                </Button>
              </div>
            ) : todayInterviews.length === 0 ? (
              <div className="py-16 text-center">
                <Calendar className="w-12 h-12 text-lia-text-disabled mx-auto mb-3" />
                <p className="text-base-ui font-semibold text-lia-text-secondary mb-1">Nenhuma entrevista agendada</p>
                <p className="text-xs text-lia-text-tertiary">Sua agenda está livre.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {morningInterviews.length > 0 && (
                  <div className="flex items-center gap-2 pt-1 pb-0.5 px-1">
                    <Sun className="w-3.5 h-3.5 text-status-warning" />
                    <span className="text-xs font-[Inter,sans-serif] font-medium text-lia-text-disabled uppercase tracking-wider">Manhã</span>
                    <div className="flex-1 border-t border-lia-border-subtle dark:border-lia-border-subtle" />
                  </div>
                )}
                {morningInterviews.map((interview) => renderInterviewCard(interview, 'active'))}
                {afternoonInterviews.length > 0 && (
                  <div className="flex items-center gap-2 pt-2 pb-0.5 px-1">
                    <Sunset className="w-3.5 h-3.5 text-wedo-orange" />
                    <span className="text-xs font-[Inter,sans-serif] font-medium text-lia-text-disabled uppercase tracking-wider">Tarde</span>
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
                        <Calendar className="w-3.5 h-3.5 text-lia-text-disabled" />
                        <span className="text-xs font-[Inter,sans-serif] font-medium text-lia-text-disabled uppercase tracking-wider">{dateLabel}</span>
                        <div className="flex-1 border-t border-lia-border-subtle dark:border-lia-border-subtle" />
                      </div>
                      {interviews.map((interview) => renderInterviewCard(interview, 'active'))}
                    </React.Fragment>
                  ))
                })()}
              </div>
            )}
          </TabsContent>

          <TabsContent value="historico" className="mt-3">
            {pastInterviews.length === 0 ? (
              <div className="py-16 text-center">
                <Clock className="w-12 h-12 text-lia-text-disabled mx-auto mb-3" />
                <p className="text-base-ui font-semibold text-lia-text-secondary mb-1">Nenhum histórico</p>
                <p className="text-xs text-lia-text-tertiary">Suas entrevistas passadas aparecerão aqui.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {pastInterviews.map((interview) => renderInterviewCard(interview, 'past'))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>

    </div>
  )
}
