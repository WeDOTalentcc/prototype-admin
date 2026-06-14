"use client"

import React from "react"
import {
  Briefcase, Users, Calendar, BarChart2, Mail,
  Plug, Bell, StickyNote, CalendarDays, UserCog, Bot, Search, BarChart3,
  type LucideIcon,
} from "lucide-react"
import { cn } from "@/lib/utils"
import type { ActionType } from "@/hooks/shared/use-action-intent"

interface ModeLabelConfig {
  icon: LucideIcon
  bg: string
  text: string
  border: string
}

const MODE_CONFIG: Record<NonNullable<ActionType>, ModeLabelConfig> = {
  wizard: {
    icon: Briefcase,
    bg: "bg-blue-500/10",
    text: "text-blue-600 dark:text-blue-400",
    border: "border-blue-500/20",
  },
  wsi: {
    icon: Users,
    bg: "bg-emerald-500/10",
    text: "text-emerald-600 dark:text-emerald-400",
    border: "border-emerald-500/20",
  },
  analytics: {
    icon: BarChart2,
    bg: "bg-violet-500/10",
    text: "text-violet-600 dark:text-violet-400",
    border: "border-violet-500/20",
  },
  communication: {
    icon: Mail,
    bg: "bg-amber-500/10",
    text: "text-amber-600 dark:text-amber-400",
    border: "border-amber-500/20",
  },
  ats_integration: {
    icon: Plug,
    bg: "bg-cyan-500/10",
    text: "text-cyan-600 dark:text-cyan-400",
    border: "border-cyan-500/20",
  },
  task_reminder: {
    icon: Bell,
    bg: "bg-orange-500/10",
    text: "text-orange-600 dark:text-orange-400",
    border: "border-orange-500/20",
  },
  note: {
    icon: StickyNote,
    bg: "bg-yellow-500/10",
    text: "text-yellow-600 dark:text-yellow-400",
    border: "border-yellow-500/20",
  },
  calendar: {
    icon: CalendarDays,
    bg: "bg-pink-500/10",
    text: "text-pink-600 dark:text-pink-400",
    border: "border-pink-500/20",
  },
  candidate_field: {
    icon: UserCog,
    bg: "bg-teal-500/10",
    text: "text-teal-600 dark:text-teal-400",
    border: "border-teal-500/20",
  },
  studio_create: {
    icon: Bot,
    bg: "bg-wedo-cyan/10",
    text: "text-wedo-cyan-text dark:text-wedo-cyan",
    border: "border-wedo-cyan/20",
  },
  studio_query: {
    icon: Search,
    bg: "bg-wedo-cyan/10",
    text: "text-wedo-cyan-text dark:text-wedo-cyan",
    border: "border-wedo-cyan/20",
  },
  studio_metrics: {
    icon: BarChart3,
    bg: "bg-wedo-cyan/10",
    text: "text-wedo-cyan-text dark:text-wedo-cyan",
    border: "border-wedo-cyan/20",
  },
}

export interface ModeLabelProps {
  actionType: ActionType
  actionLabel: string | null
  onClear?: () => void
  className?: string
}

export function ModeLabel({ actionType, actionLabel, onClear, className }: ModeLabelProps) {
  if (!actionType || !actionLabel) return null

  const config = MODE_CONFIG[actionType]
  if (!config) return null

  const Icon = config.icon

  return (
    <div
      className={cn(
        "flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium",
        "animate-in fade-in slide-in-from-bottom-1 duration-200",
        config.bg,
        config.text,
        config.border,
        className
      )}
    >
      <Icon className="w-3 h-3 flex-shrink-0" />
      <span className="truncate max-w-[200px]">{actionLabel}</span>
      {onClear && (
        <button
          onClick={onClear}
          className="ml-0.5 hover:opacity-70 transition-opacity"
          aria-label="Sair do modo"
        >
          ×
        </button>
      )}
    </div>
  )
}
