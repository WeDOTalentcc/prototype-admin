"use client"

import React, { useState } from "react"
import { Info, ShieldCheck, ShieldAlert, Brain, ChevronDown, ChevronUp } from "lucide-react"
import { cn } from "@/lib/utils"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import {
  useDecisionExplanation,
  type DecisionItem,
} from "@/hooks/use-decision-explanation"

interface DecisionExplainerProps {
  candidateId: string
  jobId: string
  variant?: "icon" | "button" | "link"
  size?: "sm" | "md"
  className?: string
}

function ConfidenceBar({ value, level }: { value: number | null; level: string | null }) {
  if (value == null) return null
  const percent = Math.round(value * 100)
  const colorClass =
    level === "high"
      ? "bg-status-success"
      : level === "medium"
        ? "bg-wedo-orange"
        : "bg-status-error"

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-lia-text-secondary w-20">Confianca</span>
      <div className="flex-1 h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all", colorClass)}
          style={{ width: `${percent}%` }}
        />
      </div>
      <span className="text-xs font-medium w-10 text-right">{percent}%</span>
    </div>
  )
}

function FairnessBadge({ status }: { status: string }) {
  const passed = status === "passed"
  return (
    <Chip
      variant={passed ? "success" : "warning"}
      className="gap-1 text-xs"
    >
      {passed ? (
        <ShieldCheck className="w-3 h-3" aria-hidden="true" />
      ) : (
        <ShieldAlert className="w-3 h-3" aria-hidden="true" />
      )}
      {passed ? "Fairness OK" : "Revisar fairness"}
    </Chip>
  )
}

function DecisionCard({ decision }: { decision: DecisionItem }) {
  const [expanded, setExpanded] = useState(false)
  const { explanation, result } = decision

  return (
    <div className="border border-lia-border-subtle rounded-lg p-3 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-wedo-cyan" aria-hidden="true" />
          <span className="text-xs font-medium">{decision.agent}</span>
          <Chip variant="neutral" muted className="text-xs">
            {decision.type.replace(/_/g, " ")}
          </Chip>
        </div>
        <div className="flex items-center gap-2">
          {result.score != null && (
            <span className="text-sm font-semibold">{result.score.toFixed(1)}</span>
          )}
          <FairnessBadge status={explanation.fairness_check} />
        </div>
      </div>

      <ConfidenceBar value={explanation.confidence} level={explanation.confidence_level} />

      {explanation.reasoning.length > 0 && (
        <div className="space-y-1">
          <p className="text-xs text-lia-text-secondary font-medium">Raciocinio da IA:</p>
          <ul className="space-y-1">
            {explanation.reasoning.slice(0, expanded ? undefined : 3).map((r, i) => (
              <li key={i} className="text-xs text-lia-text-primary pl-3 border-l-2 border-wedo-cyan/30">
                {r}
              </li>
            ))}
          </ul>
          {explanation.reasoning.length > 3 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-xs text-wedo-cyan hover:underline flex items-center gap-1"
            >
              {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              {expanded ? "Ver menos" : `+ ${explanation.reasoning.length - 3} mais`}
            </button>
          )}
        </div>
      )}

      {explanation.factors.length > 0 && (
        <div className="space-y-1">
          <p className="text-xs text-lia-text-secondary font-medium">Fatores avaliados:</p>
          <div className="grid gap-1">
            {explanation.factors.map((f, i) => (
              <div
                key={i}
                className="flex items-center justify-between text-xs bg-gray-50 dark:bg-gray-800 rounded px-2 py-1"
              >
                <span className="font-medium">{f.factor}</span>
                {f.match && (
                  <span className="text-lia-text-secondary truncate max-w-[200px]">{f.match}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {Object.keys(explanation.calibration_weights_used).length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {Object.entries(explanation.calibration_weights_used).map(([dim, weight]) => (
            <Chip key={dim} variant="neutral" className="text-xs">
              {dim}: {(weight * 100).toFixed(0)}%
            </Chip>
          ))}
        </div>
      )}

      {decision.human_reviewed && (
        <Chip variant="neutral" className="text-xs border-wedo-coral/30 text-wedo-coral">
          Revisado por humano
          {decision.human_override && ` (override: ${decision.human_override})`}
        </Chip>
      )}

      {decision.timestamp && (
        <p className="text-[10px] text-lia-text-tertiary">
          {new Date(decision.timestamp).toLocaleString("pt-BR")}
        </p>
      )}
    </div>
  )
}

export function DecisionExplainer({
  candidateId,
  jobId,
  variant = "icon",
  size = "sm",
  className,
}: DecisionExplainerProps) {
  const { data, loading, error, fetchExplanation } = useDecisionExplanation()
  const [open, setOpen] = useState(false)

  const handleOpen = (isOpen: boolean) => {
    setOpen(isOpen)
    if (isOpen && !data) {
      fetchExplanation(candidateId, jobId)
    }
  }

  const trigger =
    variant === "icon" ? (
      <Button
        variant="ghost"
        size="icon"
        className={cn("h-7 w-7", className)}
        title="Explicar decisao"
      >
        <Info className="w-4 h-4 text-wedo-cyan" />
      </Button>
    ) : variant === "link" ? (
      <button
        className={cn(
          "text-xs text-wedo-cyan hover:underline flex items-center gap-1",
          className
        )}
      >
        <Info className="w-3 h-3" aria-hidden="true" />
        Explicar decisao
      </button>
    ) : (
      <Button
        variant="outline"
        size={size === "sm" ? "sm" : "default"}
        className={cn("gap-1", className)}
      >
        <Info className="w-4 h-4" aria-hidden="true" />
        Explicar decisao
      </Button>
    )

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-base">
            <Brain className="w-5 h-5 text-wedo-cyan" aria-hidden="true" />
            Explicacao da Decisao
          </DialogTitle>
        </DialogHeader>

        {loading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-2 border-wedo-cyan border-t-transparent" />
          </div>
        )}

        {error && (
          <div className="text-sm text-status-error bg-red-50 dark:bg-red-900/20 rounded-lg p-3">
            {error}
          </div>
        )}

        {data && (
          <div className="space-y-3">
            <p className="text-xs text-lia-text-secondary">
              {data.total_decisions} decisao(oes) registrada(s) para este candidato.
            </p>

            {data.decisions.map((d) => (
              <DecisionCard key={d.decision_id} decision={d} />
            ))}

            <p className="text-[10px] text-lia-text-tertiary border-t border-lia-border-subtle pt-2">
              {data.decisions[0]?.explanation.transparency_note}
            </p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
