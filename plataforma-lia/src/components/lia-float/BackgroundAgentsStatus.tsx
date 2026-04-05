"use client"

import React, { useState } from "react"
import {
  ChevronDown, ChevronUp, Loader2, CheckCircle2, AlertCircle,
  Search, FileSearch, Mail,
} from "lucide-react"
import { cn } from "@/lib/utils"

export interface BackgroundTask {
  id: string
  type: "sourcing" | "screening" | "communication" | "analysis"
  label: string
  status: "running" | "completed" | "failed"
  progress?: number
  message?: string
  completedAt?: number
  result?: Record<string, unknown>
}

const TASK_ICONS: Record<string, React.ElementType> = {
  sourcing: Search,
  screening: FileSearch,
  communication: Mail,
  analysis: FileSearch,
}

const STATUS_COLORS = {
  running: "text-wedo-cyan",
  completed: "text-status-success",
  failed: "text-status-error",
}

export interface BackgroundAgentsStatusProps {
  tasks: BackgroundTask[]
  onViewResult?: (task: BackgroundTask) => void
  className?: string
}

export function BackgroundAgentsStatus({ tasks, onViewResult, className }: BackgroundAgentsStatusProps) {
  const [isExpanded, setIsExpanded] = useState(true)

  if (tasks.length === 0) return null

  const runningCount = tasks.filter((t) => t.status === "running").length
  const completedCount = tasks.filter((t) => t.status === "completed").length

  return (
    <div className={cn("border-t border-lia-border-subtle", className)}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-2 text-xs text-lia-text-tertiary hover:bg-lia-interactive-hover transition-colors"
      >
        <div className="flex items-center gap-2">
          {runningCount > 0 && (
            <Loader2 className="w-3 h-3 animate-spin text-wedo-cyan" />
          )}
          <span className="font-medium">
            Agentes em Background
            {runningCount > 0 && (
              <span className="ml-1 text-wedo-cyan">({runningCount} ativo{runningCount > 1 ? "s" : ""})</span>
            )}
            {runningCount === 0 && completedCount > 0 && (
              <span className="ml-1 text-status-success">({completedCount} concluído{completedCount > 1 ? "s" : ""})</span>
            )}
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-3.5 h-3.5" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5" />
        )}
      </button>

      {isExpanded && (
        <div className="px-3 pb-2 space-y-1.5 animate-in slide-in-from-top-1 duration-150">
          {tasks.map((task) => {
            const Icon = TASK_ICONS[task.type] || FileSearch
            return (
              <div
                key={task.id}
                className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-lia-bg-secondary border border-lia-border-subtle"
              >
                <Icon className={cn("w-3.5 h-3.5 flex-shrink-0", STATUS_COLORS[task.status])} />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-lia-text-primary truncate">{task.label}</p>
                  {task.status === "running" && task.progress != null && (
                    <div className="mt-1 h-1 rounded-full bg-lia-bg-tertiary overflow-hidden">
                      <div
                        className="h-full rounded-full bg-wedo-cyan transition-[width] duration-300"
                        style={{ width: `${Math.min(100, task.progress)}%` }}
                      />
                    </div>
                  )}
                  {task.message && (
                    <p className="text-[10px] text-lia-text-disabled mt-0.5 truncate">{task.message}</p>
                  )}
                </div>
                {task.status === "running" && (
                  <Loader2 className="w-3 h-3 animate-spin text-wedo-cyan flex-shrink-0" />
                )}
                {task.status === "completed" && (
                  <button
                    onClick={() => onViewResult?.(task)}
                    className="flex items-center gap-1 text-[10px] text-wedo-cyan hover:underline flex-shrink-0"
                  >
                    <CheckCircle2 className="w-3 h-3" />
                    Ver
                  </button>
                )}
                {task.status === "failed" && (
                  <AlertCircle className="w-3 h-3 text-status-error flex-shrink-0" />
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
