"use client"

import React, { useState } from 'react'
import { 
  Brain, 
  Search, 
  FileText, 
  Check, 
  ChevronDown, 
  ChevronUp,
  Loader2,
  ThumbsUp,
  ThumbsDown,
  BarChart3,
  Users,
  Briefcase,
  MessageSquare
} from 'lucide-react'
import { cn } from '@/lib/utils'

export type LIAProcessingState = 
  | 'thinking'
  | 'analyzing'
  | 'searching'
  | 'generating'
  | 'completed'

export interface LIATaskStep {
  id: string
  state: LIAProcessingState
  label: string
  description?: string
  isCompleted: boolean
  isExpanded?: boolean
  details?: string
}

interface LIAProcessingCardProps {
  steps: LIATaskStep[]
  currentStep?: string
  isCollapsible?: boolean
  className?: string
}

const stateConfig: Record<LIAProcessingState, { 
  icon: React.ElementType
  color: string
  bgColor: string
  label: string
}> = {
  thinking: {
    icon: Brain,
    color: 'text-lia-text-secondary',
    bgColor: 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary',
    label: 'Pensando...'
  },
  analyzing: {
    icon: BarChart3,
    color: 'text-lia-text-secondary',
    bgColor: 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary',
    label: 'Analisando...'
  },
  searching: {
    icon: Search,
    color: 'text-lia-text-secondary',
    bgColor: 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary',
    label: 'Buscando...'
  },
  generating: {
    icon: Brain,
    color: 'text-lia-text-secondary',
    bgColor: 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary',
    label: 'Gerando...'
  },
  completed: {
    icon: Check,
    color: 'text-status-success',
    bgColor: 'bg-status-success/10',
    label: 'Concluído'
  }
}

export function LIATaskStepItem({ 
  step, 
  isActive,
  onToggle 
}: { 
  step: LIATaskStep
  isActive: boolean
  onToggle?: () => void
}) {
  const config = stateConfig[step.state]
  const Icon = step.isCompleted ? Check : config.icon
  const hasDetails = !!step.details

  return (
    <div className={cn(
 "rounded-md transition-colors duration-200",
      isActive && !step.isCompleted ? "bg-lia-bg-secondary dark:bg-lia-bg-secondary/50" : "",
      step.isCompleted ? "opacity-90" : ""
    )}>
      <div 
        className={cn(
 "flex items-center gap-3 px-3 py-2.5 cursor-pointer",
          hasDetails ? "hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover" : ""
        )}
        onClick={hasDetails ? onToggle : undefined}
      >
        <div className={cn(
 "w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0 transition-colors",
          step.isCompleted 
            ? "bg-status-success/15" 
            : config.bgColor
        )}>
          {isActive && !step.isCompleted ? (
            <Loader2 className={cn("w-4 h-4 animate-spin motion-reduce:animate-none", config.color)} />
          ) : (
            <Icon className={cn(
 "w-4 h-4",
              step.isCompleted ? "text-status-success dark:text-status-success" : config.color
            )} />
          )}
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={cn(
 "text-sm font-medium",
              step.isCompleted 
                ? "text-lia-text-secondary" 
                : "text-lia-text-primary"
            )}>
              {step.label}
            </span>
            {step.isCompleted && (
              <span className="text-xs text-status-success dark:text-status-success font-medium">
                Concluído
              </span>
            )}
          </div>
          {step.description && (
            <p className="text-xs text-lia-text-secondary mt-0.5 truncate">
              {step.description}
            </p>
          )}
        </div>

        {hasDetails && (
          <button className="p-1 text-lia-text-secondary hover:text-lia-text-secondary dark:hover:text-lia-text-tertiary">
            {step.isExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
        )}
      </div>

      {hasDetails && step.isExpanded && (
        <div className="px-3 pb-3 pl-12">
          <div className="text-xs text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl p-2.5 font-mono">
            {step.details}
          </div>
        </div>
      )}
    </div>
  )
}

export function LIAProcessingCard({ 
  steps, 
  currentStep,
  isCollapsible = true,
  className 
}: LIAProcessingCardProps) {
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set())
  const [isCardExpanded, setIsCardExpanded] = useState(true)

  const toggleStep = (stepId: string) => {
    setExpandedSteps(prev => {
      const next = new Set(prev)
      if (next.has(stepId)) {
        next.delete(stepId)
      } else {
        next.add(stepId)
      }
      return next
    })
  }

  const completedCount = steps.filter(s => s.isCompleted).length
  const allCompleted = completedCount === steps.length

  return (
    <div className={cn(
 "rounded-xl border transition-colors",
      allCompleted 
        ? "border-status-success/30 dark:border-status-success/30 bg-status-success/10/50" 
        : "border-lia-border-default dark:border-lia-border-default bg-lia-bg-primary dark:bg-lia-bg-primary",
      className
    )}>
      {isCollapsible && (
        <button
          onClick={() => setIsCardExpanded(!isCardExpanded)}
          className="w-full flex items-center justify-between px-4 py-3 hover:bg-lia-bg-secondary/50 dark:hover:bg-lia-btn-primary-hover/50 rounded-t-2xl transition-colors motion-reduce:transition-none"
        >
          <div className="flex items-center gap-3">
            <div className={cn(
 "w-8 h-8 rounded-md flex items-center justify-center",
              allCompleted ? "bg-status-success/15" : "bg-lia-bg-tertiary dark:bg-lia-bg-secondary"
            )}>
              {allCompleted ? (
                <Check className="w-5 h-5 text-status-success dark:text-status-success" />
              ) : (
                <Brain className="w-5 h-5 text-wedo-cyan" />
              )}
            </div>
            <div className="text-left">
              <span className="text-sm font-semibold text-lia-text-primary">
                {allCompleted ? "Processamento concluído" : "LIA processando..."}
              </span>
              <div className="flex items-center gap-1.5 mt-0.5">
                <div className="h-1 w-16 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full overflow-hidden">
                  <div 
                    className={cn(
 "h-full rounded-full transition-[width,height] duration-500",
                      allCompleted ? "bg-status-success" : "bg-lia-btn-primary-bg"
                    )}
                    style={{width: `${(completedCount / steps.length) * 100}%`}}
                  />
                </div>
                <span className="text-xs text-lia-text-secondary">
                  {completedCount}/{steps.length}
                </span>
              </div>
            </div>
          </div>
          {isCardExpanded ? (
            <ChevronUp className="w-4 h-4 text-lia-text-secondary" />
          ) : (
            <ChevronDown className="w-4 h-4 text-lia-text-secondary" />
          )}
        </button>
      )}

      {isCardExpanded && (
        <div className={cn(
 "space-y-1",
          isCollapsible ? "px-2 pb-3" : "p-3"
        )}>
          {steps.map((step) => (
            <LIATaskStepItem
              key={step.id}
              step={{
                ...step,
                isExpanded: expandedSteps.has(step.id)
              }}
              isActive={currentStep === step.id}
              onToggle={() => toggleStep(step.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

interface LIAFeedbackButtonsProps {
  messageId: string
  onFeedback?: (messageId: string, isPositive: boolean) => void
  className?: string
}

export function LIAFeedbackButtons({ 
  messageId, 
  onFeedback,
  className 
}: LIAFeedbackButtonsProps) {
  const [feedback, setFeedback] = useState<'positive' | 'negative' | null>(null)

  const handleFeedback = (isPositive: boolean) => {
    const newFeedback = isPositive ? 'positive' : 'negative'
    setFeedback(newFeedback)
    onFeedback?.(messageId, isPositive)
  }

  return (
    <div className={cn("flex items-center gap-1", className)}>
      <button
        onClick={() => handleFeedback(true)}
        className={cn(
 "p-1.5 rounded-md transition-colors",
          feedback === 'positive'
            ? "bg-status-success/15 text-status-success dark:text-status-success"
            : "lia-text-secondary hover:text-lia-text-secondary hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover dark:hover:text-lia-text-tertiary"
        )}
        title="Resposta útil"
      >
        <ThumbsUp className="w-3.5 h-3.5" />
      </button>
      <button
        onClick={() => handleFeedback(false)}
        className={cn(
 "p-1.5 rounded-md transition-colors",
          feedback === 'negative'
            ? "bg-status-error/15 text-status-error dark:bg-status-error/30 dark:text-status-error"
            : "lia-text-secondary hover:text-lia-text-secondary hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover dark:hover:text-lia-text-tertiary"
        )}
        title="Resposta não útil"
      >
        <ThumbsDown className="w-3.5 h-3.5" />
      </button>
    </div>
  )
}

interface LIACommandBadgeProps {
  command: string
  status?: 'running' | 'completed' | 'error'
  className?: string
}

export function LIACommandBadge({ 
  command, 
  status = 'running',
  className 
}: LIACommandBadgeProps) {
  return (
    <div className={cn(
 "inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-lia-bg-tertiary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle",
      className
    )}>
      {status === 'running' && (
        <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
      )}
      {status === 'completed' && (
        <Check className="w-3 h-3 text-status-success" />
      )}
      <span className="text-xs font-mono text-lia-text-secondary truncate max-w-panel-sm">
        {command}
      </span>
    </div>
  )
}

interface LIAFileBadgeProps {
  fileName: string
  fileType?: 'document' | 'video' | 'image' | 'data'
  status?: 'processing' | 'finished' | 'error'
  onDownload?: () => void
  className?: string
}

export function LIAFileBadge({ 
  fileName, 
  fileType = 'document',
  status = 'finished',
  onDownload,
  className 
}: LIAFileBadgeProps) {
  const iconMap = {
    document: FileText,
    video: MessageSquare,
    image: Brain,
    data: BarChart3
  }
  const Icon = iconMap[fileType]

  return (
    <div className={cn(
 "inline-flex items-center gap-3 px-3 py-2 rounded-md bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle",
      onDownload && "cursor-pointer hover:border-lia-btn-primary-bg dark:hover:border-lia-border-subtle transition-colors motion-reduce:transition-none",
      className
    )}
    onClick={onDownload}
    >
      <div className="w-8 h-8 rounded-xl bg-lia-bg-tertiary dark:bg-lia-bg-secondary flex items-center justify-center">
        <Icon className="w-4 h-4 text-lia-text-secondary" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-lia-text-primary truncate">
          {fileName}
        </div>
        <div className="text-xs text-lia-text-secondary">
          {status === 'processing' ? 'Processando...' : 
           status === 'finished' ? 'Finalizado' : 'Erro'}
        </div>
      </div>
      {status === 'finished' && (
        <Check className="w-5 h-5 text-status-success" />
      )}
      {status === 'processing' && (
        <Loader2 className="w-5 h-5 text-lia-text-secondary animate-spin motion-reduce:animate-none" />
      )}
    </div>
  )
}

export function LIASimpleProcessing({ 
  state = 'thinking',
  message,
  className 
}: { 
  state?: LIAProcessingState
  message?: string
  className?: string 
}) {
  const config = stateConfig[state]
  const Icon = config.icon

  return (
    <div className={cn(
 "inline-flex items-center gap-2.5 px-4 py-2.5 rounded-xl",
      config.bgColor,
      className
    )}>
      <div className="w-7 h-7 rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary flex items-center justify-center flex-shrink-0" role="status" aria-live="polite" aria-label="Carregando...">
        <Loader2 className={cn("w-4 h-4 animate-spin motion-reduce:animate-none", config.color)} />
      </div>
      <span className="text-sm text-lia-text-secondary">
        {message || config.label}
      </span>
    </div>
  )
}
