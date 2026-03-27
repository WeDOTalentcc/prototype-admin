"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Users, Calendar, MessageSquare, ArrowRight, X, Eye, Mail, Phone,
  AlertTriangle, Clock, CheckCircle, ChevronDown, ChevronUp, Briefcase,
  Filter, FileText
} from "lucide-react"

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
  urgency: "critical" | "high" | "normal"
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
    urgency: "high" | "medium" | "low"
  }
}

interface PipelineReportProps {
  data: PipelineReportData
  onAction: (candidateId: string, actionId: string, candidateName: string) => void
  onClose: () => void
}

const getActionIcon = (iconName: string) => {
  const icons: Record<string, any> = {
    "filter": Filter,
    "calendar": Calendar,
    "message-square": MessageSquare,
    "arrow-right": ArrowRight,
    "file-text": FileText,
    "phone": Phone,
    "check": CheckCircle,
    "x": X,
    "mail": Mail,
    "eye": Eye
  }
  return icons[iconName] || ArrowRight
}

const getUrgencyStyles = (urgency: string) => {
  switch (urgency) {
    case "critical":
      return {
        bg: "bg-red-50 dark:bg-red-900/20",
        border: "border-red-200 dark:border-red-800",
        badge: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
        icon: "text-red-500"
      }
    case "high":
      return {
        bg: "bg-amber-50 dark:bg-amber-900/20",
        border: "border-amber-200 dark:border-amber-800",
        badge: "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300",
        icon: "text-amber-500"
      }
    default:
      return {
        bg: "bg-gray-50 dark:bg-gray-800/50",
        border: "border-gray-200 dark:border-gray-700",
        badge: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
        icon: "text-gray-800 dark:text-gray-200"
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
    <div className={`p-4 rounded-md border ${styles.bg} ${styles.border} transition-all`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="font-medium text-gray-950 dark:text-gray-50 truncate">
              {candidate.name}
            </h4>
            {candidate.lia_score && (
              <Badge variant="outline" className="text-xs shrink-0 border-gray-900 dark:border-gray-50 text-gray-600 dark:text-gray-400">
                LIA {candidate.lia_score}%
              </Badge>
            )}
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
            {candidate.current_title || "Cargo não informado"}
            {candidate.current_company && ` • ${candidate.current_company}`}
          </p>
        </div>
        <Badge className={`${styles.badge} shrink-0 ml-2`}>
          {candidate.status_label}
        </Badge>
      </div>
      
      <div className="flex items-center gap-2 mb-3">
        <Clock className={`w-4 h-4 ${styles.icon}`} />
        <span className="text-sm text-gray-600 dark:text-gray-400">
          {candidate.stale_message}
        </span>
        {candidate.urgency === "critical" && (
          <AlertTriangle className="w-4 h-4 text-red-500" />
        )}
      </div>
      
      <div className="flex flex-wrap gap-2">
        {candidate.actions.slice(0, 3).map((action) => {
          const IconComponent = getActionIcon(action.icon)
          const isDestructive = action.variant === "destructive"
          
          return (
            <Button
              key={action.id}
              size="sm"
              variant={isDestructive ? "outline" : "default"}
              className={`h-8 text-xs ${
                isDestructive 
                  ? "border-red-300 text-red-600 hover:bg-red-50 dark:border-red-700 dark:text-red-400 dark:hover:bg-red-900/30" 
                  : "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 border-0"
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
    <div className="border rounded-md overflow-hidden" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
        style={{ backgroundColor: 'var(--eleven-bg-message)' }}
      >
        <div className="flex items-center gap-3">
          <Briefcase className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          <div className="text-left">
            <h3 className="font-medium text-gray-950 dark:text-gray-50">
              {group.job_title}
            </h3>
            <p className="text-sm text-gray-800 dark:text-gray-200">
              {group.job_department} • {group.candidates.length} candidato{group.candidates.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs">
            {group.candidates.filter(c => c.urgency === "critical").length} críticos
          </Badge>
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-600" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-600" />
          )}
        </div>
      </button>
      
      {isExpanded && (
        <div className="p-4 space-y-3 border-t" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
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
      case "high":
        return "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800"
      case "medium":
        return "bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800"
      default:
        return "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800"
    }
  }

  return (
    <div className="space-y-4 font-open-sans">
      <div className={`p-4 rounded-md border ${getSummaryStyles()}`}>
        <div className="flex items-center gap-3 mb-2">
          <Users className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          <span className="font-medium text-gray-950 dark:text-gray-50">
            Relatório de Pipeline
          </span>
        </div>
        <p className="text-sm text-gray-800 dark:text-gray-200">
          {data.summary.message}
        </p>
        <div className="flex gap-4 mt-3 text-sm">
          <div className="flex items-center gap-1">
            <span className="text-gray-800 dark:text-gray-200">Total:</span>
            <span className="font-semibold text-gray-950 dark:text-gray-50">{data.total_stale}</span>
          </div>
          {data.critical_count > 0 && (
            <div className="flex items-center gap-1">
              <AlertTriangle className="w-4 h-4 text-red-500" />
              <span className="text-gray-800 dark:text-gray-200">Críticos:</span>
              <span className="font-semibold text-red-600 dark:text-red-400">{data.critical_count}</span>
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
          <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
          <h3 className="font-medium text-gray-950 dark:text-gray-50 mb-1">
            Pipeline em dia!
          </h3>
          <p className="text-sm text-gray-800 dark:text-gray-200">
            Todos os candidatos estão sendo acompanhados ativamente.
          </p>
        </div>
      )}
    </div>
  )
}
