"use client"

import React from "react"
import { textStyles } from "@/lib/design-tokens"
import { Briefcase, CheckCircle2, Clock, Brain } from "lucide-react"

interface TasksMetricsBarProps {
  metrics: {
    total: number
    completed: number
    pending: number
    iaTasks: number
  }
}

export function TasksMetricsBar({ metrics }: TasksMetricsBarProps) {
  return (
    <div className="flex items-center gap-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary p-2 rounded-xl">
      <div className="flex items-center gap-1.5 px-2 py-1 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl">
        <Briefcase className="w-3 h-3 text-lia-text-tertiary" />
        <span className="text-sm font-sans font-medium text-lia-text-primary">{metrics.total}</span>
        <span className={`${textStyles.description}`}>Total</span>
      </div>
      <div className="flex items-center gap-1.5 px-2 py-1 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl">
        <CheckCircle2 className="w-3 h-3 text-emerald-500" />
        <span className="text-sm font-sans font-medium text-lia-text-primary">{metrics.completed}</span>
        <span className={`${textStyles.description}`}>Concluídas</span>
      </div>
      <div className="flex items-center gap-1.5 px-2 py-1 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl">
        <Clock className="w-3 h-3 text-amber-500" />
        <span className="text-sm font-sans font-medium text-lia-text-primary">{metrics.pending}</span>
        <span className={`${textStyles.description}`}>Pendentes</span>
      </div>
      <div className="flex items-center gap-1.5 px-2 py-1 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl">
        <Brain className="w-3 h-3 text-wedo-cyan" />
        <span className="text-sm font-sans font-medium text-lia-text-primary">{metrics.iaTasks}</span>
        <span className={`${textStyles.description}`}>IA</span>
      </div>
    </div>
  )
}
