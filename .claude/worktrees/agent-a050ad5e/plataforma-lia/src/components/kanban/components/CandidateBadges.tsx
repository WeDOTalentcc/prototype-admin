'use client'

import React from 'react'
import {
  Send,
  Calendar,
  CheckCircle,
  AlertCircle,
  Clock,
  FileText,
  Loader2,
  Eye,
  Brain,
  AlertTriangle,
  Check,
  UserPlus,
  type LucideIcon
} from 'lucide-react'
import { cn } from '@/lib/design-tokens'
import { getCandidateBadges } from '../utils/badge-utils'

const ICON_MAP: Record<string, LucideIcon> = {
  'send': Send,
  'calendar': Calendar,
  'check-circle': CheckCircle,
  'alert-circle': AlertCircle,
  'clock': Clock,
  'file-text': FileText,
  'loader': Loader2,
  'eye': Eye,
  'brain': Brain,
  'alert-triangle': AlertTriangle,
  'check': Check,
  'user-plus': UserPlus,
}

const COLOR_CLASSES: Record<string, string> = {
  cyan: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
  amber: 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  red: 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  green: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  gray: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
}

interface CandidateBadgesProps {
  subStatus?: string
  actionBehavior?: string
  stageId?: string
  needsAction?: boolean
  lastActionDate?: string
  slaHours?: number
  compact?: boolean
}

export function CandidateBadges({
  subStatus,
  actionBehavior,
  stageId,
  needsAction,
  lastActionDate,
  slaHours,
  compact = false
}: CandidateBadgesProps) {
  const badges = getCandidateBadges({ subStatus, actionBehavior, stageId, needsAction, lastActionDate, slaHours })

  if (badges.length === 0) return null

  return (
    <div className="flex flex-wrap gap-1">
      {badges.map((badge, i) => {
        const IconComponent = ICON_MAP[badge.icon]
        return (
          <span
            key={i}
            className={cn(
              "inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-medium",
              compact && "text-[9px] px-1 py-0",
              COLOR_CLASSES[badge.color]
            )}
          >
            {IconComponent && <IconComponent className={cn("w-3 h-3", compact && "w-2.5 h-2.5")} />}
            {badge.label}
          </span>
        )
      })}
    </div>
  )
}
