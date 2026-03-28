"use client"

import React, { useState, useEffect } from "react"
import {
  Brain, Loader2, CheckCircle, Star, ChevronRight,
  FileText, Search, Target, ArrowRight, Calendar
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

// Thinking Indicator Component
export const ThinkingIndicator = ({ message }: { message?: string }) => {
  const [dots, setDots] = useState("")

  useEffect(() => {
    const interval = setInterval(() => {
      setDots(prev => prev.length >= 3 ? "" : prev + ".")
    }, 500)
    return () => clearInterval(interval)
  }, [])

  return (
    <div
      className="flex items-center gap-3 p-3 bg-gray-100 dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700 mb-3 animate-fade-in-up"
    >
      <div className="flex items-center justify-center w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full">
        <Brain className="w-4 h-4 text-wedo-cyan animate-pulse" />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
            Pensando{dots}
          </span>
        </div>
        {message && (
          <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
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
  status: "pending" | "processing" | "completed" | "error"
  details?: string
  icon?: React.ComponentType<{ className?: string }>
}

export const ProgressSteps = ({ steps, currentStep }: {
  steps: ProgressStep[]
  currentStep?: string
}) => {
  return (
    <div
      className="bg-gray-100 dark:bg-gray-800 rounded-md p-4 mb-3 border border-gray-200 dark:border-gray-700 animate-fade-in-up"
    >
      <div className="space-y-3">
        {steps.map((step, index) => {
          const Icon = step.icon || FileText
          const isActive = step.id === currentStep
          const isCompleted = step.status === "completed"
          const isProcessing = step.status === "processing"
          const isError = step.status === "error"

          return (
            <div
              key={step.id}
              className={`flex items-center gap-3 p-2 rounded-md transition-colors ${
                isActive ? 'bg-gray-200 dark:bg-gray-700' : ''
              }`}
              style={{
                animation: `fadeInRight 0.3s ease-out ${index * 0.1}s backwards`
              }}
            >
              <div className={`flex items-center justify-center w-6 h-6 rounded-full transition-colors ${
                isCompleted ? 'bg-gray-700 text-white dark:bg-gray-300 dark:text-gray-950' :
                isProcessing ? 'bg-gray-600 text-white dark:bg-gray-400 dark:text-gray-950' :
                isError ? 'bg-gray-500 text-white dark:bg-gray-500 dark:text-white' :
                'bg-gray-300 text-gray-600 dark:bg-gray-600 dark:text-gray-300'
              }`}>
                {isCompleted ? (
                  <CheckCircle className="w-4 h-4" />
                ) : isProcessing ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <Icon className="w-3 h-3" />
                )}
              </div>

              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-medium ${
                    isCompleted ? 'text-gray-950 dark:text-gray-50' :
                    isProcessing ? 'text-gray-950 dark:text-gray-50' :
                    isError ? 'text-gray-800 dark:text-gray-200' :
                    'text-gray-600 dark:text-gray-400'
                  }`}>
                    {step.label}
                  </span>
                  {isProcessing && (
                    <Badge variant="outline" className="text-xs bg-gray-200 text-gray-800 border-gray-300 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600">
                      Em andamento
                    </Badge>
                  )}
                </div>
                {step.details && (
                  <p className="text-xs text-gray-800 dark:text-gray-200 mt-1">
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
  status: "executing" | "completed" | "error"
  output?: string
}) => {
  return (
    <div
      className="bg-gray-100 dark:bg-gray-800 rounded-md p-3 mb-3 font-mono text-sm border border-gray-200 dark:border-gray-700 animate-scale-in-delayed"
    >
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-2 h-2 rounded-full ${
          status === "executing" ? 'bg-gray-500 dark:bg-gray-400 animate-pulse' :
          status === "completed" ? 'bg-gray-700 dark:bg-gray-300' :
          'bg-gray-600 dark:bg-gray-400'
        }`} />
        <span className="text-gray-800 dark:text-gray-200 text-xs">Executando comando:</span>
      </div>

      <div className="text-gray-950 dark:text-gray-50 mb-2">
        $ {command}
      </div>

      {output && (
        <div className="text-gray-600 dark:text-gray-400 text-xs">
          {output}
        </div>
      )}

      {status === "executing" && (
        <div className="flex items-center gap-2 mt-2">
          <Loader2 className="w-3 h-3 animate-spin text-gray-600 dark:text-gray-400" />
          <span className="text-xs text-gray-800 dark:text-gray-200">Processando...</span>
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
  status: "creating" | "created"
}) => {
  return (
    <div
      className="flex items-center gap-3 p-3 bg-gray-100 dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700 mb-3 animate-fade-in-up"
    >
      <div className="flex items-center justify-center w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full">
        {status === "creating" ? (
          <Loader2 className="w-4 h-4 text-gray-600 dark:text-gray-400 animate-spin" />
        ) : (
          <CheckCircle className="w-4 h-4 text-gray-800 dark:text-gray-200" />
        )}
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
            {status === "creating" ? "Criando" : "Criado"}: {fileName}
          </span>
        </div>
        <p className="text-xs text-gray-600 dark:text-gray-400">
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
    { id: "analyze_more", label: "Analisar mais candidatos", icon: Search },
    { id: "create_shortlist", label: "Criar shortlist", icon: Target },
    { id: "schedule_interviews", label: "Agendar entrevistas", icon: Calendar },
    { id: "export_report", label: "Exportar relatório", icon: FileText }
  ]

  return (
    <div
      className="space-y-3 animate-fade-in-up"
    >
      {/* Completion Message */}
      <div className="flex items-start gap-3 p-4 bg-gray-100 dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700">
        <CheckCircle className="w-5 h-5 text-gray-800 dark:text-gray-200 mt-0.5" />
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-950 dark:text-gray-50">
            ✅ {message}
          </p>
        </div>
      </div>

      {/* Rating System */}
      <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700">
        <p className="text-sm font-medium text-gray-950 dark:text-gray-50 mb-3">
          Como você avalia este resultado?
        </p>
        <div className="flex items-center gap-2 mb-4">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              onClick={() => handleRating(star)}
              className={`p-1 rounded transition-colors ${
                star <= rating ? 'text-gray-800 dark:text-gray-200' : 'text-gray-600 hover:text-gray-800 dark:hover:text-gray-200'
              }`}
            >
              <Star className={`w-5 h-5 ${star <= rating ? 'fill-current' : ''}`} />
            </button>
          ))}
          {hasRated && (
            <span className="text-sm text-gray-600 dark:text-gray-400 ml-2">
              Obrigada pelo feedback!
            </span>
          )}
        </div>

        {/* Follow-up Actions */}
        <div>
          <p className="text-sm font-medium text-gray-950 dark:text-gray-50 mb-3">
            Próximos passos sugeridos:
          </p>
          <div className="space-y-2">
            {followUpActions.map((action) => {
              const Icon = action.icon
              return (
                <button
                  key={action.id}
                  onClick={() => onFollowUp?.(action.id)}
                  className="w-full flex items-center gap-3 p-3 text-left hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors group"
                >
                  <Icon className="w-4 h-4 text-gray-600 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-300" />
                  <span className="text-sm text-gray-800 dark:text-gray-200 group-hover:text-gray-950 dark:group-hover:text-gray-50">
                    {action.label}
                  </span>
                  <ArrowRight className="w-3 h-3 text-gray-600 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-300 ml-auto" />
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
        className="flex items-center gap-2 w-full p-3 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
      >
        <ChevronRight className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
        <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
          {title}
        </span>
      </button>

      {isExpanded && (
        <div
          className="overflow-hidden animate-slide-in-up"
        >
          <div className="p-4 border-l-2 border-gray-300 dark:border-gray-600 ml-6 mt-2">
            {children}
          </div>
        </div>
      )}
    </div>
  )
}
