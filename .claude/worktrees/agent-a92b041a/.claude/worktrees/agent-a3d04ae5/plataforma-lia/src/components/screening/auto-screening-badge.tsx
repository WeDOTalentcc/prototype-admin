"use client"

import React from "react"
import { CheckCircle2, Clock, AlertCircle, Zap } from "lucide-react"

interface AutoScreeningBadgeProps {
  status: "pending" | "processing" | "completed" | "failed"
  source: "website" | "manual" | "ats_import" | "referral"
  score?: number
  className?: string
}

export function AutoScreeningBadge({
  status,
  source,
  score,
  className = "",
}: AutoScreeningBadgeProps) {
  if (source !== "website") {
    return null
  }

  const statusConfig = {
    pending: {
      icon: Clock,
      bgColor: "bg-amber-50 dark:bg-amber-900/20",
      textColor: "text-amber-700 dark:text-amber-300",
      dotColor: "bg-amber-500",
    },
    processing: {
      icon: Zap,
      bgColor: "bg-cyan-50 dark:bg-cyan-900/20",
      textColor: "text-cyan-700 dark:text-cyan-300",
      dotColor: "bg-cyan-500 animate-pulse",
    },
    completed: {
      icon: CheckCircle2,
      bgColor: "bg-emerald-50 dark:bg-emerald-900/20",
      textColor: "text-emerald-700 dark:text-emerald-300",
      dotColor: "bg-emerald-500",
    },
    failed: {
      icon: AlertCircle,
      bgColor: "bg-red-50 dark:bg-red-900/20",
      textColor: "text-red-700 dark:text-red-300",
      dotColor: "bg-red-500",
    },
  }

  const config = statusConfig[status]
  const Icon = config.icon

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${config.bgColor} ${config.textColor} ${className}`}
    >
      <div className={`w-1.5 h-1.5 rounded-full ${config.dotColor}`} />
      <Icon className="w-3 h-3" />
      <span>
        {status === "pending" && "Pendente"}
        {status === "processing" && "Processando"}
        {status === "completed" && "Concluído"}
        {status === "failed" && "Falhou"}
      </span>
      {status === "completed" && score !== undefined && (
        <span className="ml-0.5 font-['Inter',sans-serif] font-semibold">
          WSI: {score}
        </span>
      )}
    </div>
  )
}
