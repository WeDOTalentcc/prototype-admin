"use client"

import React from "react"
import { CheckCircle2, AlertCircle, ArrowRight, Search, FileSearch, Mail, FileUp } from "lucide-react"
import { cn } from "@/lib/utils"
import type { BackgroundTask } from "./BackgroundAgentsStatus"

const TASK_ICONS: Record<string, React.ElementType> = {
  sourcing: Search,
  screening: FileSearch,
  communication: Mail,
  analysis: FileSearch,
  // Wizard JD upload progress (Audit B-02 / Task #865) — uses an upload
  // glyph instead of the generic search icon so users immediately know
  // which lane is reporting the success/failure.
  wizard: FileUp,
}

export interface BackgroundTaskNotificationProps {
  task: BackgroundTask
  onViewResult?: (task: BackgroundTask) => void
  onDismiss?: (taskId: string) => void
}

export function BackgroundTaskNotification({
  task,
  onViewResult,
  onDismiss,
}: BackgroundTaskNotificationProps) {
  const Icon = TASK_ICONS[task.type] || FileSearch
  const isSuccess = task.status === "completed"

  return (
    <div
      className={cn(
        "flex items-start gap-3 px-4 py-3 rounded-lg border animate-in slide-in-from-bottom-2 duration-300",
        isSuccess
          ? "bg-status-success/5 border-status-success/20"
          : "bg-status-error/5 border-status-error/20"
      )}
    >
      <div className={cn(
        "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
        isSuccess ? "bg-status-success/10" : "bg-status-error/10"
      )}>
        {isSuccess ? (
          <CheckCircle2 className="w-4 h-4 text-status-success" />
        ) : (
          <AlertCircle className="w-4 h-4 text-status-error" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <Icon className="w-3.5 h-3.5 text-lia-text-tertiary" />
          <p className="text-sm font-medium text-lia-text-primary">
            {isSuccess ? "Tarefa concluída" : "Tarefa falhou"}
          </p>
        </div>
        <p className="text-xs text-lia-text-secondary mt-0.5">{task.label}</p>
        {task.message && (
          <p className="text-xs text-lia-text-tertiary mt-1">{task.message}</p>
        )}
        <div className="flex items-center gap-2 mt-2">
          {isSuccess && onViewResult && (
            <button
              onClick={() => onViewResult(task)}
              className="inline-flex items-center gap-1 text-xs text-wedo-cyan-text hover:underline font-medium"
            >
              Ver resultado
              <ArrowRight className="w-3 h-3" />
            </button>
          )}
          {onDismiss && (
            <button
              onClick={() => onDismiss(task.id)}
              className="text-xs text-lia-text-muted hover:text-lia-text-tertiary transition-colors"
            >
              Dispensar
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
