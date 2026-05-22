"use client"

import { useState } from"react"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import {
  Users, Calendar, MessageSquare, ArrowRight, X, Eye, Mail, Phone,
  AlertTriangle, Clock, CheckCircle, ChevronDown, ChevronUp, Briefcase,
  Filter, FileText
} from"lucide-react"

interface PipelineAction {
  id: string
  label: string
  icon: string
  action: string
  variant?: string
}

interface StaleCandidateData {
  id: string
  name: string
  email: string
  current_title: string
  current_company: string
  status: string
  status_label: string
  days_stale: number
  stale_message: string
  urgency:"critical" |"high" |"normal"
  lia_score: number | null
  actions: PipelineAction[]
  last_activity: string | null
}

interface PipelineGroup {
  job_id: string | null
  job_title: string
  job_department: string
  candidates: StaleCandidateData[]
}

interface PipelineReportData {
  total_stale: number
  critical_count: number
  stale_threshold_days: number
  generated_at: string
  groups: PipelineGroup[]
  summary: {
    message: string
    urgency:"high" |"medium" |"low"
  }
}

interface PipelineReportProps {
  data: PipelineReportData
  onAction: (candidateId: string, actionId: string, candidateName: string) => void
  onClose: () => void
}

const getActionIcon = (iconName: string) => {
  const icons: Record<string, React.ComponentType<{ className?: string }>> = {"filter": Filter,"calendar": Calendar,"message-square": MessageSquare,"arrow-right": ArrowRight,"file-text": FileText,"phone": Phone,"check": CheckCircle,"x": X,"mail": Mail,"eye": Eye
  }
  return icons[iconName] || ArrowRight
}

const getUrgencyStyles = (urgency: string) => {
  switch (urgency) {
    case"critical":
      return {
        bg:"bg-status-error/10 dark:bg-status-error/20",
        border:"border-status-error/30 dark:border-status-error/30",
        badge:" dark:bg-status-error dark:text-status-error",
        icon:"text-status-error"
      }
    case"high":
      return {
        bg:"bg-status-warning/10 dark:bg-status-warning/20",
        border:"border-status-warning/30 dark:border-status-warning/30",
        badge:" dark:bg-status-warning dark:text-status-warning",
        icon:"text-status-warning"
      }
    default:
      return {
        bg:"bg-lia-bg-secondary",
        border:"border-lia-border-subtle",
        badge:"bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary",
        icon:"text-lia-text-primary"
      }
  }
}

const CandidateCard = ({ 
  candidate, 
  onAction 
}: { 
  candidate: StaleCandidateData
  onAction: (candidateId: string, actionId: string, candidateName: string) => void
}) => {
  const styles = getUrgencyStyles(candidate.urgency)
  
  return (
    <div className={`p-4 rounded-md border ${styles.bg} ${styles.border} transition-colors motion-reduce:transition-none`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="font-medium text-lia-text-primary truncate">
              {candidate.name}
            </h4>
            {candidate.lia_score && (
              <Chip density="relaxed" variant="neutral" className="shrink-0 border-lia-text-primary text-lia-text-secondary">
                LIA {candidate.lia_score}%
              </Chip>
            )}
          </div>
          <p className="text-sm text-lia-text-secondary truncate">
            {candidate.current_title ||"Cargo não informado"}
            {candidate.current_company && ` • ${candidate.current_company}`}
          </p>
        </div>
        <Chip variant="neutral" muted className={`${styles.badge} shrink-0 ml-2`}>
          {candidate.status_label}
        </Chip>
      </div>
      
      <div className="flex items-center gap-2 mb-3">
        <Clock className={`w-4 h-4 ${styles.icon}`} />
        <span className="text-sm text-lia-text-secondary">
          {candidate.stale_message}
        </span>
        {candidate.urgency ==="critical" && (
          <AlertTriangle className="w-4 h-4 text-status-error" />
        )}
      </div>
      
      <div className="flex flex-wrap gap-2">
        {candidate.actions.slice(0, 3).map((action) => {
          const IconComponent = getActionIcon(action.icon)
          const isDestructive = action.variant ==="destructive"
          
          return (
            <Button
              key={action.id}
              size="sm"
              variant={isDestructive ?"outline" :"primary"}
              className={`h-8 text-xs ${
 isDestructive 
                  ?"border-status-error/30 text-status-error hover:bg-status-error/10 dark:border-status-error/30 dark:text-status-error dark:hover:bg-status-error/30" 
                  :"bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary hover:bg-lia-interactive-active border-0"
              }`}
              onClick={() => onAction(candidate.id, action.id, candidate.name)}
            >
              <IconComponent className="w-3 h-3 mr-1" />
              {action.label}
            </Button>
          )
        })}
      </div>
    </div>
  )
}

const JobGroup = ({ 
  group, 
  onAction,
  defaultExpanded = true
}: { 
  group: PipelineGroup
  onAction: (candidateId: string, actionId: string, candidateName: string) => void
  defaultExpanded?: boolean
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)
  
  return (
    <div className="border rounded-xl overflow-hidden border-lia-border-subtle">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none bg-lia-bg-tertiary dark:bg-lia-bg-secondary"
      >
        <div className="flex items-center gap-3">
          <Briefcase className="w-5 h-5 text-lia-text-secondary" />
          <div className="text-left">
            <h3 className="font-medium text-lia-text-primary">
              {group.job_title}
            </h3>
            <p className="text-sm text-lia-text-primary">
              {group.job_department} • {group.candidates.length} candidato{group.candidates.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Chip density="relaxed" variant="neutral" >
            {group.candidates.filter(c => c.urgency ==="critical").length} críticos
          </Chip>
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-lia-text-secondary" />
          ) : (
            <ChevronDown className="w-5 h-5 text-lia-text-secondary" />
          )}
        </div>
      </button>
      
      {isExpanded && (
        <div className="p-4 space-y-3 border-t border-lia-border-subtle">
          {group.candidates.map((candidate) => (
            <CandidateCard
              key={candidate.id}
              candidate={candidate}
              onAction={onAction}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export function PipelineReport({ data, onAction, onClose }: PipelineReportProps) {
  const getSummaryStyles = () => {
    switch (data.summary.urgency) {
      case"high":
        return"bg-status-error/10 dark:bg-status-error/20 border-status-error/30 dark:border-status-error/30"
      case"medium":
        return"bg-status-warning/10 dark:bg-status-warning/20 border-status-warning/30 dark:border-status-warning/30"
      default:
        return"bg-status-success/10 dark:bg-status-success/20 border-status-success/30 dark:border-status-success/30"
    }
  }

  return (
    <div className="space-y-4 font-open-sans">
      <div className={`p-4 rounded-md border ${getSummaryStyles()}`}>
        <div className="flex items-center gap-3 mb-2">
          <Users className="w-5 h-5 text-lia-text-secondary" />
          <span className="font-medium text-lia-text-primary">
            Relatório de Pipeline
          </span>
        </div>
        <p className="text-sm text-lia-text-primary">
          {data.summary.message}
        </p>
        <div className="flex gap-4 mt-3 text-sm">
          <div className="flex items-center gap-1">
            <span className="text-lia-text-primary">Total:</span>
            <span className="font-semibold text-lia-text-primary">{data.total_stale}</span>
          </div>
          {data.critical_count > 0 && (
            <div className="flex items-center gap-1">
              <AlertTriangle className="w-4 h-4 text-status-error" />
              <span className="text-lia-text-primary">Críticos:</span>
              <span className="font-semibold text-status-error dark:text-status-error">{data.critical_count}</span>
            </div>
          )}
        </div>
      </div>

      <div className="space-y-3">
        {data.groups.map((group, index) => (
          <JobGroup
            key={group.job_id || `ungrouped-${index}`}
            group={group}
            onAction={onAction}
            defaultExpanded={index === 0}
          />
        ))}
      </div>

      {data.total_stale === 0 && (
        <div className="text-center py-8">
          <CheckCircle className="w-12 h-12 text-status-success mx-auto mb-3" />
          <h3 className="font-medium text-lia-text-primary mb-1">
            Pipeline em dia!
          </h3>
          <p className="text-sm text-lia-text-primary">
            Todos os candidatos estão sendo acompanhados ativamente.
          </p>
        </div>
      )}
    </div>
  )
}
