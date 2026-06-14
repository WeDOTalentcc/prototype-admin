"use client"

import { useState, useEffect, useCallback } from"react"
import { cn } from"@/lib/utils"
import { Chip } from "@/components/ui/chip"
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from"@/components/ui/collapsible"
import {
  ChevronDown,
  Clock,
  Wrench,
  Loader2,
  Brain,
  Eye,
  Zap,
  Target,
  BarChart3,
} from"lucide-react"

interface TimelineStep {
  iteration: number
  phase: string
  reasoning_summary?: string | null
  tool_used?: string | null
  tool_result_summary?: string | null
  decision?: string | null
  duration_ms: number
  timestamp?: string
}

interface SessionSummary {
  total_steps: number
  tools_used: string[]
  reasoning_summary: string
  confidence: number
  duration_ms: number
  stage_progression?: string | null
}

interface AgentExplainabilityPanelProps {
  sessionId: string
  companyId?: string
  isOpen?: boolean
  onToggle?: () => void
  className?: string
}

const PHASE_CONFIG: Record<
  string,
  { label: string; color: string; bgColor: string; icon: React.ElementType }
> = {
  reasoning: {
    label:"Raciocínio",
    color:"text-wedo-cyan-text",
    bgColor:"bg-wedo-cyan/10/15",
    icon: Brain,
  },
  action: {
    label:"Ação",
    color:"text-status-warning",
    bgColor:"bg-status-warning/15",
    icon: Zap,
  },
  observation: {
    label:"Observação",
    color:"text-status-success",
    bgColor:"bg-status-success/15",
    icon: Eye,
  },
  decision: {
    label:"Decisão",
    color:"text-wedo-purple-text",
    bgColor:"bg-wedo-purple/10/15",
    icon: Target,
  },
}

export function AgentExplainabilityPanel({
  sessionId,
  companyId,
  isOpen: controlledOpen,
  onToggle,
  className,
}: AgentExplainabilityPanelProps) {
  const [internalOpen, setInternalOpen] = useState(false)
  const [steps, setSteps] = useState<TimelineStep[]>([])
  const [summary, setSummary] = useState<SessionSummary | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isOpen = controlledOpen !== undefined ? controlledOpen : internalOpen

  const handleToggle = useCallback(() => {
    if (onToggle) {
      onToggle()
    } else {
      setInternalOpen((prev) => !prev)
    }
  }, [onToggle])

  useEffect(() => {
    if (!isOpen || !sessionId) return

    const fetchData = async () => {
      setLoading(true)
      setError(null)

      try {
        const [timelineRes, summaryRes] = await Promise.all([
          fetch(
            `/api/backend-proxy/explainability?action=timeline&sessionId=${encodeURIComponent(sessionId)}`
          ),
          fetch(
            `/api/backend-proxy/explainability?action=summary&sessionId=${encodeURIComponent(sessionId)}`
          ),
        ])

        if (timelineRes.ok) {
          const timelineData = await timelineRes.json()
          setSteps(
            Array.isArray(timelineData)
              ? timelineData
              : timelineData.steps || timelineData.timeline || []
          )
        }

        if (summaryRes.ok) {
          const summaryData = await summaryRes.json()
          setSummary(summaryData)
        }
      } catch {
        setError("Erro ao carregar dados de explicabilidade")
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [isOpen, sessionId])

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  return (
    <Collapsible
      open={isOpen}
      onOpenChange={handleToggle}
      className={cn("rounded-md border border-lia-border-default/50", className)}
    >
      <CollapsibleTrigger className="flex w-full items-center justify-between rounded-xl bg-lia-btn-primary-bg px-4 py-3 transition-colors motion-reduce:transition-none hover:bg-lia-btn-primary-bg/80">
        <div className="flex items-center gap-2">
          <Brain className="h-4 w-4 text-wedo-cyan" />
          <span className="text-sm font-medium text-lia-text-tertiary font-[Inter]">
            Raciocínio da IA
          </span>
          {summary && !loading && (
            <Chip
              variant="neutral"
              className="ml-2 border-wedo-cyan/30 text-wedo-cyan-text text-micro px-1.5 py-0"
            >
              {summary.total_steps} passos
            </Chip>
          )}
        </div>
        <ChevronDown
          className={cn("h-4 w-4 text-lia-text-tertiary transition-transform duration-200",
            isOpen &&"rotate-180"
          )}
        />
      </CollapsibleTrigger>

      <CollapsibleContent>
        <div className="border-t border-lia-border-default/50 bg-lia-btn-primary-bg px-4 py-3" role="status" aria-live="polite" aria-label="Carregando...">
          {loading && (
            <div className="flex items-center justify-center gap-2 py-8" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="h-5 w-5 animate-spin motion-reduce:animate-none text-wedo-cyan" />
              <span className="text-sm text-lia-text-tertiary">
                Carregando raciocínio...
              </span>
            </div>
          )}

          {error && !loading && (
            <div className="flex items-center justify-center py-8">
              <span className="text-sm text-status-error">{error}</span>
            </div>
          )}

          {!loading && !error && steps.length === 0 && (
            <div className="flex flex-col items-center justify-center gap-2 py-8">
              <Brain className="h-8 w-8 text-wedo-cyan" />
              <span className="text-sm text-lia-text-secondary">
                Nenhum passo de raciocínio disponível
              </span>
            </div>
          )}

          {!loading && !error && steps.length > 0 && (
            <div className="space-y-0">
              {steps.map((step, index) => {
                const phase = PHASE_CONFIG[step.phase] || PHASE_CONFIG.reasoning
                const PhaseIcon = phase.icon
                const isLast = index === steps.length - 1

                return (
                  <div key={step.iteration} className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div
                        className={cn("flex h-6 w-6 items-center justify-center rounded-full text-micro font-bold",
                          isLast
                            ?"bg-wedo-cyan text-lia-text-primary"
                            :"bg-lia-bg-tertiary text-lia-text-disabled"
                        )}
                      >
                        {step.iteration}
                      </div>
                      {!isLast && (
                        <div className="w-px flex-1 bg-lia-bg-tertiary dark:bg-lia-bg-inverse my-1" />
                      )}
                    </div>

                    <div
                      className={cn("mb-3 flex-1 rounded-md bg-lia-btn-primary-bg p-3",
                        isLast &&"mb-0"
                      )}
                    >
                      <div className="flex items-center gap-2 mb-1.5">
                        <div
                          className={cn("flex items-center gap-1 rounded-md px-1.5 py-0.5",
                            phase.bgColor
                          )}
                        >
                          <PhaseIcon
                            className={cn("h-3 w-3", phase.color)}
                          />
                          <span
                            className={cn("text-micro font-semibold",
                              phase.color
                            )}
                          >
                            {phase.label}
                          </span>
                        </div>

                        <div className="ml-auto flex items-center gap-2">
                          {step.tool_used && (
                            <Chip
                              variant="neutral"
                              className="border-lia-border-default text-lia-text-tertiary text-micro px-1.5 py-0 gap-1"
                            >
                              <Wrench className="h-2.5 w-2.5" />
                              {step.tool_used}
                            </Chip>
                          )}
                          <div className="flex items-center gap-1 text-lia-text-secondary">
                            <Clock className="h-3 w-3" />
                            <span className="text-micro">
                              {formatDuration(step.duration_ms)}
                            </span>
                          </div>
                        </div>
                      </div>

                      <p className="text-xs text-lia-text-muted leading-relaxed">
                        {step.reasoning_summary || step.decision || step.tool_result_summary ||""}
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {!loading && !error && summary && (
            <div className="mt-4 grid grid-cols-2 gap-2 rounded-md bg-lia-btn-primary-bg p-3 sm:grid-cols-4">
              <div className="flex flex-col items-center gap-1">
                <BarChart3 className="h-4 w-4 text-wedo-cyan" />
                <span className="text-micro text-lia-text-secondary font-[Inter]">
                  Passos
                </span>
                <span className="text-sm font-semibold text-lia-text-tertiary">
                  {summary.total_steps}
                </span>
              </div>
              <div className="flex flex-col items-center gap-1">
                <Wrench className="h-4 w-4 text-status-warning" />
                <span className="text-micro text-lia-text-secondary font-[Inter]">
                  Ferramentas
                </span>
                <span className="text-sm font-semibold text-lia-text-tertiary">
                  {summary.tools_used?.length || 0}
                </span>
              </div>
              <div className="flex flex-col items-center gap-1">
                <Clock className="h-4 w-4 text-status-success" />
                <span className="text-micro text-lia-text-secondary font-[Inter]">
                  Tempo Total
                </span>
                <span className="text-sm font-semibold text-lia-text-tertiary">
                  {formatDuration(summary.duration_ms)}
                </span>
              </div>
              <div className="flex flex-col items-center gap-1">
                <Target className="h-4 w-4 text-wedo-purple" />
                <span className="text-micro text-lia-text-secondary font-[Inter]">
                  Confiança
                </span>
                <span className="text-sm font-semibold text-wedo-cyan-text">
                  {Math.round(summary.confidence * 100)}%
                </span>
              </div>
            </div>
          )}
        </div>
      </CollapsibleContent>
    </Collapsible>
  )
}
