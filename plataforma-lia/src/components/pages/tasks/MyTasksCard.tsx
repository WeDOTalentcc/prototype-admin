"use client"

import React from "react"
import { textStyles } from "@/lib/design-tokens"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { CheckCircle2, MessageSquare, Calendar, Search } from "lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ActivityFeed } from "@/components/activity-feed"
import { TaskCard } from "./TaskCard"
import type { PendingTask } from "../use-tasks-core"

type TaskFilter = 'all' | 'feedback' | 'entrevista' | 'sourcing'

interface MyTasksCardProps {
  pendingTasks: PendingTask[]
  filteredPendingTasks: PendingTask[]
  pendingTaskFilter: string
  setPendingTaskFilter: (filter: TaskFilter) => void
  handleConfirmTask: (task: PendingTask) => void
  handleRejectTask: (task: PendingTask) => void
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
}: MyTasksCardProps) {
  const morningTasks = filteredPendingTasks.filter(t => t.dueDate.getHours() < 12)
  const afternoonTasks = filteredPendingTasks.filter(t => t.dueDate.getHours() >= 12)

  return (
    <Card className="border-lia-border-subtle dark:border-lia-border-subtle">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-lia-text-primary" />
            <CardTitle className={`${textStyles.label} font-semibold text-lia-text-primary`}>Minhas Tarefas</CardTitle>
            <Badge variant="outline" className="text-xs font-inter">
              {filteredPendingTasks.length}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0 pb-2">
        <Tabs defaultValue="tarefas" className="w-full">
          <TabsList className="grid w-full grid-cols-2 h-8 mb-3 bg-lia-bg-tertiary dark:bg-lia-bg-secondary p-0.5">
            <TabsTrigger value="tarefas" className="text-xs font-open-sans h-7 data-[state=active]:font-semibold data-[state=active]:bg-lia-bg-primary data-[state=active]:text-lia-text-primary dark:data-[state=active]:bg-lia-btn-primary-bg dark:data-[state=active]:text-lia-text-inverse">
              Tarefas ({filteredPendingTasks.length})
            </TabsTrigger>
            <TabsTrigger value="historico" className="text-xs font-open-sans h-7 data-[state=active]:font-semibold data-[state=active]:bg-lia-bg-primary data-[state=active]:text-lia-text-primary dark:data-[state=active]:bg-lia-btn-primary-bg dark:data-[state=active]:text-lia-text-inverse">
              Histórico
            </TabsTrigger>
          </TabsList>

          <TabsContent value="tarefas" className="mt-0">
            <div className="flex items-center gap-1.5 mb-3 flex-wrap">
              {([
                { key: 'all', label: `Todos (${pendingTasks.length})`, icon: null },
                { key: 'feedback', label: `Feedback (${pendingTasks.filter(t => t.type === 'feedback').length})`, icon: <MessageSquare className="w-2.5 h-2.5" /> },
                { key: 'entrevista', label: `Entrevista (${pendingTasks.filter(t => t.type === 'entrevista').length})`, icon: <Calendar className="w-2.5 h-2.5" /> },
                { key: 'sourcing', label: `Sourcing (${pendingTasks.filter(t => t.type === 'sourcing').length})`, icon: <Search className="w-2.5 h-2.5" /> },
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

              {filteredPendingTasks.length === 0 && (
                <div className="text-center py-8">
                  <CheckCircle2 className="w-12 h-12 mx-auto text-lia-text-disabled mb-3" />
                  <p className="text-sm font-medium text-lia-text-primary mb-1">Nenhuma tarefa pendente</p>
                  <p className="text-xs text-lia-text-secondary">Todas as tarefas foram concluídas</p>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="historico" className="mt-0">
            <ActivityFeed limit={15} className="max-h-content-lg overflow-y-auto" />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
