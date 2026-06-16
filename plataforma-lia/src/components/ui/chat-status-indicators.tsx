"use client"

import React, { useState, useEffect } from"react"
import {
  Brain, Loader2, CheckCircle, Star, ChevronRight,
  FileText, Search, Target, ArrowRight, Calendar
} from"lucide-react"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"

// Thinking Indicator Component
export const ThinkingIndicator = ({ message }: { message?: string }) => {
  const [dots, setDots] = useState("")

  useEffect(() => {
    const interval = setInterval(() => {
      setDots(prev => prev.length >= 3 ?"" : prev +".")
    }, 500)
    return () => clearInterval(interval)
  }, [])

  return (
    <div
      className="flex items-center gap-3 p-3 bg-lia-bg-tertiary rounded-xl border border-lia-border-subtle mb-3 animate-fade-in-up"
    >
      <div className="flex items-center justify-center w-8 h-8 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full">
        <Brain className="w-4 h-4 text-wedo-cyan animate-pulse motion-reduce:animate-none" />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-lia-text-primary">
            Pensando{dots}
          </span>
        </div>
        {message && (
          <p className="text-xs text-lia-text-secondary mt-1">
            {message}
          </p>
        )}
      </div>
    </div>
  )
}

// Progress Steps Component
interface ProgressStep {
  id: string
  label: string
  status:"pending" |"processing" |"completed" |"error"
  details?: string
  icon?: React.ComponentType<{ className?: string }>
}

export const ProgressSteps = ({ steps, currentStep }: {
  steps: ProgressStep[]
  currentStep?: string
}) => {
  return (
    <div
      className="bg-lia-bg-tertiary rounded-xl p-4 mb-3 border border-lia-border-subtle animate-fade-in-up"
    >
      <div className="space-y-3">
        {steps.map((step, index) => {
          const Icon = step.icon || FileText
          const isActive = step.id === currentStep
          const isCompleted = step.status ==="completed"
          const isProcessing = step.status ==="processing"
          const isError = step.status ==="error"

          return (
            <div
              key={step.id}
              className={`flex items-center gap-3 p-2 rounded-md transition-colors motion-reduce:transition-none ${
 isActive ? 'bg-lia-interactive-active dark:bg-lia-bg-elevated' : ''
              }`}
              style={{animation: `fadeInRight 0.3s ease-out ${index * 0.1}s backwards`}}
            >
              <div className={`flex items-center justify-center w-6 h-6 rounded-full transition-colors motion-reduce:transition-none ${
 isCompleted ? 'bg-lia-text-secondary text-white' :
                isProcessing ? 'bg-lia-text-secondary text-white' :
                isError ? 'bg-lia-border-medium text-white' :
                'bg-lia-border-default text-lia-text-secondary'
              }`}>
                {isCompleted ? (
                  <CheckCircle className="w-4 h-4" />
                ) : isProcessing ? (
                  <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />
                ) : (
                  <Icon className="w-3 h-3" />
                )}
              </div>

              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-medium ${
 isCompleted ? 'text-lia-text-primary' :
                    isProcessing ? 'text-lia-text-primary' :
                    isError ? 'text-lia-text-primary' :
                    'text-lia-text-secondary'
                  }`}>
                    {step.label}
                  </span>
                  {isProcessing && (
                    <Chip density="relaxed" variant="neutral" className="bg-lia-interactive-active dark:bg-lia-bg-elevated text-lia-text-primary border-lia-border-default">
                      Em andamento
                    </Chip>
                  )}
                </div>
                {step.details && (
                  <p className="text-xs text-lia-text-primary mt-1">
                    {step.details}
                  </p>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// Command Execution Indicator
export const CommandExecution = ({
  command,
  status,
  output
}: {
  command: string
  status:"executing" |"completed" |"error"
  output?: string
}) => {
  return (
    <div
      className="bg-lia-bg-tertiary rounded-xl p-3 mb-3 font-mono text-sm border border-lia-border-subtle animate-scale-in-delayed"
    >
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-2 h-2 rounded-full ${
 status ==="executing" ? 'bg-lia-border-medium animate-pulse motion-reduce:animate-none' :
          status ==="completed" ? 'bg-lia-text-secondary' :
          'bg-lia-text-secondary'
        }`} />
        <span className="text-lia-text-primary text-xs">Executando comando:</span>
      </div>

      <div className="text-lia-text-primary mb-2">
        $ {command}
      </div>

      {output && (
        <div className="text-lia-text-secondary text-xs">
          {output}
        </div>
      )}

      {status ==="executing" && (
        <div className="flex items-center gap-2 mt-2" role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
          <span className="text-xs text-lia-text-primary">Processando...</span>
        </div>
      )}
    </div>
  )
}

// File Creation Indicator
export const FileCreationIndicator = ({
  fileName,
  fileType,
  status
}: {
  fileName: string
  fileType: string
  status:"creating" |"created"
}) => {
  return (
    <div
      className="flex items-center gap-3 p-3 bg-lia-bg-tertiary rounded-xl border border-lia-border-subtle mb-3 animate-fade-in-up"
    >
      <div className="flex items-center justify-center w-8 h-8 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full" role="status" aria-live="polite" aria-label="Carregando...">
        {status ==="creating" ? (
          <Loader2 className="w-4 h-4 text-lia-text-secondary animate-spin motion-reduce:animate-none" />
        ) : (
          <CheckCircle className="w-4 h-4 text-lia-text-primary" />
        )}
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-lia-text-secondary" />
          <span className="text-sm font-medium text-lia-text-primary">
            {status ==="creating" ?"Criando" :"Criado"}: {fileName}
          </span>
        </div>
        <p className="text-xs text-lia-text-secondary">
          Tipo: {fileType}
        </p>
      </div>
    </div>
  )
}

// Completion Message with Rating
export const CompletionMessage = ({
  message,
  onRating,
  onFollowUp
}: {
  message: string
  onRating?: (rating: number) => void
  onFollowUp?: (action: string) => void
}) => {
  const [rating, setRating] = useState(0)
  const [hasRated, setHasRated] = useState(false)

  const handleRating = (stars: number) => {
    setRating(stars)
    setHasRated(true)
    onRating?.(stars)
  }

  const followUpActions = [
    { id:"analyze_more", label:"Analisar mais candidatos", icon: Search },
    { id:"create_shortlist", label:"Criar shortlist", icon: Target },
    { id:"schedule_interviews", label:"Agendar entrevistas", icon: Calendar },
    { id:"export_report", label:"Exportar relatório", icon: FileText }
  ]

  return (
    <div
      className="space-y-3 animate-fade-in-up"
    >
      {/* Completion Message */}
      <div className="flex items-start gap-3 p-4 bg-lia-bg-tertiary rounded-xl border border-lia-border-subtle">
        <CheckCircle className="w-5 h-5 text-lia-text-primary mt-0.5" />
        <div className="flex-1">
          <p className="text-sm font-medium text-lia-text-primary">
            ✅ {message}
          </p>
        </div>
      </div>

      {/* Rating System */}
      <div className="p-4 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle">
        <p className="text-sm font-medium text-lia-text-primary mb-3" aria-live="polite" aria-atomic="true">
          Como você avalia este resultado?
        </p>
        <div className="flex items-center gap-2 mb-4">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              onClick={() => handleRating(star)}
              className={`p-1 rounded-md transition-colors motion-reduce:transition-none ${
 star <= rating ? 'text-lia-text-primary' : 'text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse'
              }`}
            >
              <Star className={`w-5 h-5 ${star <= rating ? 'fill-current' : ''}`} />
            </button>
          ))}
          {hasRated && (
            <span className="text-sm text-lia-text-secondary ml-2">
              Obrigada pelo feedback!
            </span>
          )}
        </div>

        {/* Follow-up Actions */}
        <div>
          <p className="text-sm font-medium text-lia-text-primary mb-3">
            Próximos passos sugeridos:
          </p>
          <div className="space-y-2">
            {followUpActions.map((action) => {
              const Icon = action.icon
              return (
                <button
                  key={action.id}
                  onClick={() => onFollowUp?.(action.id)}
                  className="w-full flex items-center gap-3 p-3 text-left hover:bg-lia-interactive-hover rounded-md transition-colors motion-reduce:transition-none group"
                >
                  <Icon className="w-4 h-4 text-lia-text-secondary group-hover:text-lia-text-secondary dark:group-hover:text-lia-text-muted" />
                  <span className="text-sm text-lia-text-primary group-hover:text-lia-text-primary dark:group-hover:text-lia-text-inverse">
                    {action.label}
                  </span>
                  <ArrowRight className="w-3 h-3 text-lia-text-secondary group-hover:text-lia-text-secondary dark:group-hover:text-lia-text-muted ml-auto" />
                </button>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}

// Progressive Disclosure Component
export const ProgressiveDisclosure = ({
  title,
  children,
  defaultExpanded = false
}: {
  title: string
  children: React.ReactNode
  defaultExpanded?: boolean
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  return (
    <div className="mb-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 w-full p-3 bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-xl hover:bg-lia-interactive-active transition-colors motion-reduce:transition-none"
      >
        <ChevronRight className={`w-4 h-4 transition-transform motion-reduce:transition-none ${isExpanded ? 'rotate-90' : ''}`} />
        <span className="text-sm font-medium text-lia-text-primary">
          {title}
        </span>
      </button>

      {isExpanded && (
        <div
          className="overflow-hidden animate-slide-in-up"
        >
          <div className="p-4 border-l-2 border-lia-border-default ml-6 mt-2">
            {children}
          </div>
        </div>
      )}
    </div>
  )
}
