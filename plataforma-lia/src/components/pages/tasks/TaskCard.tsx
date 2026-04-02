"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  CheckCircle, XCircle,
  MessageSquare, Calendar, Search, FileText, Users,
  Play, User, Briefcase
} from "lucide-react"
import { getTaskPriorityStyle, getPriorityLabel, getTaskTypeIcon } from "../task-helpers"

interface Task {
  id: string
  type: string
  title: string
  description: string
  priority: string
  dueDate: Date
  candidateName?: string
  relatedJob?: string
}

interface TaskCardProps {
  task: Task
  onConfirm: (task: Task) => void
  onReject: (task: Task) => void
}

export const TaskCard = React.memo(function TaskCard({ task, onConfirm, onReject }: TaskCardProps) {
  return (
    <div className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-2.5 transition-colors motion-reduce:transition-none bg-lia-bg-primary dark:bg-lia-bg-primary">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start gap-2 flex-1">
          <div className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0 bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
            {getTaskTypeIcon(task.type as any) /* TODO: fix type */}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 flex-wrap mb-0.5">
              <span className="text-xs font-inter font-medium text-lia-text-primary">
                {task.dueDate.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
              </span>
              <h4 className="text-xs font-inter font-semibold text-lia-text-primary">
                {task.title}
              </h4>
              <Badge
                className={`border-0 text-xs py-0 px-1.5 font-medium ${getTaskPriorityStyle(task.priority as any) ?? ""}`} /* TODO: fix type */
              >
                {getPriorityLabel(task.priority as any) /* TODO: fix type */}
              </Badge>
            </div>
            <p className="text-xs font-open-sans text-lia-text-primary mb-1 line-clamp-1">
              {task.description}
            </p>
            <div className="flex items-center gap-2 text-xs text-lia-text-primary">
              {task.candidateName && (
                <span className="flex items-center gap-0.5">
                  <User className="w-2.5 h-2.5" />
                  {task.candidateName}
                </span>
              )}
              {task.relatedJob && (
                <span className="flex items-center gap-0.5">
                  <Briefcase className="w-2.5 h-2.5" />
                  {task.relatedJob}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-1 flex-shrink-0">
          {task.type === 'feedback' && (
            <div className="flex items-center gap-1">
              <Button
                size="sm"
                onClick={() => onConfirm(task)}
                className="h-5 px-2 text-xs gap-1 border-0"
                style={{backgroundColor: 'var(--wedo-green-light, #f0fdf4)', color: 'var(--lia-text-primary)'}}
              >
                <MessageSquare className="w-2.5 h-2.5" />
                Avaliar
              </Button>
              <Button size="sm" variant="outline" className="h-5 px-2 text-xs gap-1">
                <FileText className="w-2.5 h-2.5" />
                Ver CV
              </Button>
            </div>
          )}
          {task.type === 'entrevista' && (
            <div className="flex items-center gap-1">
              <Button
                size="sm"
                onClick={() => onConfirm(task)}
                className="h-5 px-2 text-xs gap-1 border-0"
                style={{backgroundColor: 'var(--wedo-green-light, #f0fdf4)', color: 'var(--lia-text-primary)'}}
              >
                <Play className="w-2.5 h-2.5" />
                Iniciar
              </Button>
              <Button size="sm" variant="outline" className="h-5 px-2 text-xs gap-1">
                <FileText className="w-2.5 h-2.5" />
                Ver CV
              </Button>
            </div>
          )}
          {task.type === 'sourcing' && (
            <div className="flex items-center gap-1">
              <Button
                size="sm"
                onClick={() => onConfirm(task)}
                className="h-5 px-2 text-xs gap-1 border-0"
                style={{backgroundColor: 'var(--wedo-green-light, #f0fdf4)', color: 'var(--lia-text-primary)'}}
              >
                <Search className="w-2.5 h-2.5" />
                Buscar
              </Button>
              <Button size="sm" variant="outline" className="h-5 px-2 text-xs gap-1">
                <Users className="w-2.5 h-2.5" />
                Ver Perfis
              </Button>
            </div>
          )}
          <div className="flex items-center gap-1">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onConfirm(task)}
              className="h-5 px-1.5 text-xs gap-0.5"
            >
              <CheckCircle className="w-2.5 h-2.5" />
              Confirmar
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onReject(task)}
              className="h-5 px-1.5 text-xs gap-0.5 text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
            >
              <XCircle className="w-2.5 h-2.5" />
              Rejeitar
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
})

export default TaskCard
