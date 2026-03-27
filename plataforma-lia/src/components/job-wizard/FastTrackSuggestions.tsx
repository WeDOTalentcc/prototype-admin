/**
 * FastTrackSuggestions Component
 * 
 * Displays similar jobs in the sidebar panel for Fast Track selection.
 * Follows LIA Conversational Philosophy:
 * - Data displayed in sidebar, not modal
 * - Action buttons for final actions only
 * - Preview with collapsible sections
 */
'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { 
  Zap, 
  ChevronDown, 
  ChevronRight, 
  CheckCircle2, 
  Clock, 
  MapPin,
  Briefcase,
  Code,
  Users,
  DollarSign,
  HelpCircle,
  Loader2
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import type { FastTrackSuggestion } from '@/hooks/useFastTrack'

interface FastTrackSuggestionsProps {
  suggestions: FastTrackSuggestion[]
  selectedJob: FastTrackSuggestion | null
  isLoading: boolean
  onSelectJob: (job: FastTrackSuggestion) => void
  onDismiss?: () => void
}

export function FastTrackSuggestions({
  suggestions,
  selectedJob,
  isLoading,
  onSelectJob,
  onDismiss,
}: FastTrackSuggestionsProps) {
  const [expandedJobId, setExpandedJobId] = useState<string | null>(null)
  
  if (isLoading) {
    return (
      <div className="p-4 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-100 dark:bg-gray-800">
        <div className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span className="text-sm">Buscando vagas similares...</span>
        </div>
      </div>
    )
  }
  
  if (suggestions.length === 0) {
    return null
  }
  
  const toggleExpand = (jobId: string) => {
    setExpandedJobId(expandedJobId === jobId ? null : jobId)
  }
  
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return ''
    return new Date(dateStr).toLocaleDateString('pt-BR', { 
      month: 'short', 
      year: 'numeric' 
    })
  }
  
  const formatSalary = (min?: number, max?: number) => {
    if (!min && !max) return null
    const formatK = (n: number) => `${(n / 1000).toFixed(0)}k`
    if (min && max) return `R$ ${formatK(min)} - ${formatK(max)}`
    if (min) return `A partir de R$ ${formatK(min)}`
    return `Até R$ ${formatK(max!)}`
  }
  
  const getMatchBadgeColor = (score: number) => {
    if (score >= 0.9) return 'bg-status-success/20 text-status-success border-status-success/30/30'
    if (score >= 0.8) return 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600'
    return 'bg-status-warning/20 text-status-warning border-status-warning/30/30'
  }
  
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-gray-700 dark:text-gray-300" />
          <span className="text-sm font-medium text-white">Fast Track Disponível</span>
        </div>
        <Badge variant="outline" className="text-xs border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">
          {suggestions.length} {suggestions.length === 1 ? 'vaga' : 'vagas'}
        </Badge>
      </div>
      
      <div className="space-y-2">
        {suggestions.map((job) => {
          const isExpanded = expandedJobId === job.job_id
          const isSelected = selectedJob?.job_id === job.job_id
          const salary = formatSalary(job.salary_min, job.salary_max)
          
          return (
            <div 
              key={job.job_id}
              className={cn(
                "border rounded-md transition-all duration-200",
                isSelected 
                  ? "border-gray-900 dark:border-gray-50 bg-gray-100 dark:bg-gray-800" 
                  : "border-neutral-700 bg-neutral-800/50 hover:border-neutral-600"
              )}
            >
              <button
                onClick={() => {
                  onSelectJob(job)
                  toggleExpand(job.job_id)
                }}
                className="w-full p-3 text-left"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-white truncate">
                        {job.job_title}
                      </span>
                      <Badge 
                        variant="outline" 
                        className={cn("text-xs shrink-0", getMatchBadgeColor(job.similarity_score))}
                      >
                        {Math.round(job.similarity_score * 100)}% match
                      </Badge>
                    </div>
                    
                    <div className="flex items-center gap-3 mt-1 text-xs text-neutral-400">
                      {job.department && (
                        <span className="flex items-center gap-1">
                          <Briefcase className="w-3 h-3" />
                          {job.department}
                        </span>
                      )}
                      {job.created_at && (
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatDate(job.created_at)}
                        </span>
                      )}
                    </div>
                    
                    {job.time_to_fill_days && job.outcome_status === 'hired' && (
                      <div className="flex items-center gap-1 mt-1 text-xs text-status-success">
                        <CheckCircle2 className="w-3 h-3" />
                        Contratado em {job.time_to_fill_days} dias
                      </div>
                    )}
                  </div>
                  
                  <div className="text-neutral-500">
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4" />
                    ) : (
                      <ChevronRight className="w-4 h-4" />
                    )}
                  </div>
                </div>
              </button>
              
              {isExpanded && (
                <div className="px-3 pb-3 space-y-3 border-t border-neutral-700/50 pt-3">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {job.location && (
                      <div className="flex items-center gap-1 text-neutral-400">
                        <MapPin className="w-3 h-3" />
                        <span>{job.location}</span>
                      </div>
                    )}
                    {job.work_model && (
                      <div className="flex items-center gap-1 text-neutral-400">
                        <Briefcase className="w-3 h-3" />
                        <span className="capitalize">{job.work_model}</span>
                      </div>
                    )}
                    {salary && (
                      <div className="flex items-center gap-1 text-neutral-400 col-span-2">
                        <DollarSign className="w-3 h-3" />
                        <span>{salary}</span>
                      </div>
                    )}
                  </div>
                  
                  {job.skills && job.skills.length > 0 && (
                    <div>
                      <div className="flex items-center gap-1 text-xs text-neutral-500 mb-1">
                        <Code className="w-3 h-3" />
                        <span>Skills ({job.skills.length})</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {job.skills.slice(0, 5).map((skill) => (
                          <Badge 
                            key={skill} 
                            variant="outline" 
                            className="text-xs bg-neutral-800 border-neutral-700 text-neutral-300"
                          >
                            {skill}
                          </Badge>
                        ))}
                        {job.skills.length > 5 && (
                          <Badge 
                            variant="outline" 
                            className="text-xs bg-neutral-800 border-neutral-700 text-neutral-500"
                          >
                            +{job.skills.length - 5}
                          </Badge>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {job.behavioral_competencies && job.behavioral_competencies.length > 0 && (
                    <div>
                      <div className="flex items-center gap-1 text-xs text-neutral-500 mb-1">
                        <Users className="w-3 h-3" />
                        <span>Comportamentais ({job.behavioral_competencies.length})</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {job.behavioral_competencies.slice(0, 3).map((comp, idx) => {
                          const compName = typeof comp === 'string' ? comp : comp.name
                          return (
                            <Badge 
                              key={`${compName}-${idx}`}
                              variant="outline" 
                              className="text-xs bg-neutral-800 border-neutral-700 text-neutral-300"
                            >
                              {compName}
                            </Badge>
                          )
                        })}
                        {job.behavioral_competencies.length > 3 && (
                          <Badge 
                            variant="outline" 
                            className="text-xs bg-neutral-800 border-neutral-700 text-neutral-500"
                          >
                            +{job.behavioral_competencies.length - 3}
                          </Badge>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {job.wsi_questions && job.wsi_questions.length > 0 && (
                    <div className="flex items-center gap-1 text-xs text-neutral-400">
                      <HelpCircle className="w-3 h-3" />
                      <span>{job.wsi_questions.length} perguntas WSI configuradas</span>
                    </div>
                  )}
                  
                  <p className="text-xs text-neutral-500 italic mt-2">
                    Responda no chat se quiser usar esta vaga como base
                  </p>
                </div>
              )}
            </div>
          )
        })}
      </div>
      
      <button
        onClick={onDismiss}
        className="text-xs text-neutral-500 hover:text-neutral-400 transition-colors"
      >
        Criar do zero
      </button>
    </div>
  )
}

export default FastTrackSuggestions
