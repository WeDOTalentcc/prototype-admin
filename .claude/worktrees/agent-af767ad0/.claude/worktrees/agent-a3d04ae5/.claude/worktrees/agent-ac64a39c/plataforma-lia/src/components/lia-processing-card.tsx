"use client"

import React, { useState } from 'react'
import { 
  Brain, 
  Search, 
  FileText, 
  Brain, 
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
    color: 'text-gray-600 dark:text-gray-400',
    bgColor: 'bg-gray-100 dark:bg-gray-800',
    label: 'Pensando...'
  },
  analyzing: {
    icon: BarChart3,
    color: 'text-gray-600 dark:text-gray-400',
    bgColor: 'bg-gray-100 dark:bg-gray-800',
    label: 'Analisando...'
  },
  searching: {
    icon: Search,
    color: 'text-gray-600 dark:text-gray-400',
    bgColor: 'bg-gray-100 dark:bg-gray-800',
    label: 'Buscando...'
  },
  generating: {
    icon: Brain,
    color: 'text-gray-600 dark:text-gray-400',
    bgColor: 'bg-gray-100 dark:bg-gray-800',
    label: 'Gerando...'
  },
  completed: {
    icon: Check,
    color: 'text-emerald-600',
    bgColor: 'bg-emerald-50',
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
      "rounded-md transition-all duration-200",
      isActive && !step.isCompleted ? "bg-gray-50 dark:bg-gray-800/50" : "",
      step.isCompleted ? "opacity-90" : ""
    )}>
      <div 
        className={cn(
          "flex items-center gap-3 px-3 py-2.5 cursor-pointer",
          hasDetails ? "hover:bg-gray-50 dark:hover:bg-gray-800" : ""
        )}
        onClick={hasDetails ? onToggle : undefined}
      >
        <div className={cn(
          "w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0 transition-all",
          step.isCompleted 
            ? "bg-emerald-100 dark:bg-emerald-900/30" 
            : config.bgColor
        )}>
          {isActive && !step.isCompleted ? (
            <Loader2 className={cn("w-4 h-4 animate-spin", config.color)} />
          ) : (
            <Icon className={cn(
              "w-4 h-4",
              step.isCompleted ? "text-emerald-600 dark:text-emerald-400" : config.color
            )} />
          )}
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={cn(
              "text-sm font-medium",
              step.isCompleted 
                ? "text-gray-600 dark:text-gray-400" 
                : "text-gray-800 dark:text-gray-200"
            )}>
              {step.label}
            </span>
            {step.isCompleted && (
              <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
                Concluído
              </span>
            )}
          </div>
          {step.description && (
            <p className="text-xs text-gray-500 mt-0.5 truncate">
              {step.description}
            </p>
          )}
        </div>

        {hasDetails && (
          <button className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
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
          <div className="text-xs text-gray-500 bg-gray-50 dark:bg-gray-800 rounded-md p-2.5 font-mono">
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
      "rounded-2xl border transition-all",
      allCompleted 
        ? "border-emerald-200 dark:border-emerald-800 bg-emerald-50/50 dark:bg-emerald-900/10" 
        : "border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900",
      className
    )}>
      {isCollapsible && (
        <button
          onClick={() => setIsCardExpanded(!isCardExpanded)}
          className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50/50 dark:hover:bg-gray-800/50 rounded-t-2xl transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className={cn(
              "w-8 h-8 rounded-md flex items-center justify-center",
              allCompleted ? "bg-emerald-100 dark:bg-emerald-900/30" : "bg-gray-100 dark:bg-gray-800"
            )}>
              {allCompleted ? (
                <Check className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              ) : (
                <Brain className="w-5 h-5 text-wedo-cyan" />
              )}
            </div>
            <div className="text-left">
              <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">
                {allCompleted ? "Processamento concluído" : "LIA processando..."}
              </span>
              <div className="flex items-center gap-1.5 mt-0.5">
                <div className="h-1 w-16 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    className={cn(
                      "h-full rounded-full transition-all duration-500",
                      allCompleted ? "bg-emerald-500" : "bg-gray-900 dark:bg-gray-50"
                    )}
                    style={{ width: `${(completedCount / steps.length) * 100}%` }}
                  />
                </div>
                <span className="text-[11px] text-gray-500">
                  {completedCount}/{steps.length}
                </span>
              </div>
            </div>
          </div>
          {isCardExpanded ? (
            <ChevronUp className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400" />
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
          "p-1.5 rounded-md transition-all",
          feedback === 'positive'
            ? "bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400"
            : "text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 dark:hover:text-gray-300"
        )}
        title="Resposta útil"
      >
        <ThumbsUp className="w-3.5 h-3.5" />
      </button>
      <button
        onClick={() => handleFeedback(false)}
        className={cn(
          "p-1.5 rounded-md transition-all",
          feedback === 'negative'
            ? "bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400"
            : "text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 dark:hover:text-gray-300"
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
      "inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700",
      className
    )}>
      {status === 'running' && (
        <Loader2 className="w-3 h-3 animate-spin text-gray-600 dark:text-gray-400" />
      )}
      {status === 'completed' && (
        <Check className="w-3 h-3 text-emerald-600" />
      )}
      <span className="text-xs font-mono text-gray-600 dark:text-gray-400 truncate max-w-[300px]">
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
      "inline-flex items-center gap-3 px-3 py-2 rounded-md bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700",
      onDownload && "cursor-pointer hover:border-gray-900 dark:hover:border-gray-50 hover:transition-all",
      className
    )}
    onClick={onDownload}
    >
      <div className="w-8 h-8 rounded-md bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
        <Icon className="w-4 h-4 text-gray-600 dark:text-gray-400" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
          {fileName}
        </div>
        <div className="text-[11px] text-gray-500">
          {status === 'processing' ? 'Processando...' : 
           status === 'finished' ? 'Finalizado' : 'Erro'}
        </div>
      </div>
      {status === 'finished' && (
        <Check className="w-5 h-5 text-emerald-500" />
      )}
      {status === 'processing' && (
        <Loader2 className="w-5 h-5 text-gray-600 dark:text-gray-400 animate-spin" />
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
      "inline-flex items-center gap-2.5 px-4 py-2.5 rounded-2xl",
      config.bgColor,
      className
    )}>
      <div className="w-7 h-7 rounded-md bg-white dark:bg-gray-800 flex items-center justify-center flex-shrink-0">
        <Loader2 className={cn("w-4 h-4 animate-spin", config.color)} />
      </div>
      <span className="text-sm text-gray-600 dark:text-gray-400">
        {message || config.label}
      </span>
    </div>
  )
}
