'use client'

import React, { memo } from 'react'
import { Chip } from '@/components/ui/chip'
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

const COLOR_TO_VARIANT: Record<string, 'neutral' | 'warning' | 'danger' | 'success' | 'info'> = {
  cyan: 'info',
  amber: 'warning',
  red: 'danger',
  green: 'success',
  gray: 'neutral',
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

const CandidateBadges = memo(function CandidateBadges({
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
          <Chip
            key={i}
            variant={COLOR_TO_VARIANT[badge.color]}
            muted={badge.color === 'gray'}
            className={cn("gap-1", compact &&"px-1 py-0")}
          >
            {IconComponent && <IconComponent className={cn("w-3 h-3", compact &&"w-2.5 h-2.5")} />}
            {badge.label}
          </Chip>
        )
      })}
    </div>
  )
})
CandidateBadges.displayName = 'CandidateBadges'

export { CandidateBadges }
