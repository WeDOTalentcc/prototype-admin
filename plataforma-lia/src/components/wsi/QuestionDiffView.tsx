"use client"

import React from"react"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Check, RotateCcw, ArrowRight } from"lucide-react"
import { cn } from"@/lib/utils"

interface DiffItem {
  question_id: string
  action:"modified" |"added" |"removed"
  before?: string
  after?: string
  reason?: string
}

interface QuestionDiffViewProps {
  diffs: DiffItem[]
  onAccept: () => void
  onRequestAnother: () => void
  disabled?: boolean
  className?: string
}

export function QuestionDiffView({
  diffs,
  onAccept,
  onRequestAnother,
  disabled = false,
  className
}: QuestionDiffViewProps) {
  if (!diffs || diffs.length === 0) return null

  const getActionBadge = (action: string) => {
    switch (action) {
      case"modified":
        return { label:"Modificada", className:"text-micro px-1.5 py-0 h-4 flex items-center border bg-wedo-cyan/10 border-wedo-cyan/30" , style: {} }
      case"added":
        return { label:"Nova", className:"text-micro px-1.5 py-0 h-4 flex items-center  border border-status-success/30" , style: {} }
      case"removed":
        return { label:"Removida", className:"text-micro px-1.5 py-0 h-4 flex items-center  border border-status-error/30", style: {} }
      default:
        return { label: action, className:"text-micro px-1.5 py-0 h-4 flex items-center bg-lia-bg-tertiary text-lia-text-secondary border border-lia-border-subtle", style: {} }
    }
  }

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex items-center gap-1.5">
        <ArrowRight className="h-3.5 w-3.5 text-lia-text-secondary" />
        <span className="text-xs font-semibold text-lia-text-primary">Antes / Depois</span>
        <Chip variant="neutral" className="text-micro px-1.5 py-0 h-4 flex items-center bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-subtle">
          {diffs.length} alteração(ões)
        </Chip>
      </div>

      <div className="space-y-2">
        {diffs.map((diff, idx) => {
          const badge = getActionBadge(diff.action)
          return (
            <div
              key={diff.question_id || idx}
              className="rounded-xl border border-lia-border-subtle overflow-hidden"
            >
              <div className="px-3 py-1.5 bg-lia-bg-secondary flex items-center gap-2">
                <Chip variant="neutral" className={badge.className} style={badge.style}>
                  {badge.label}
                </Chip>
                {diff.reason && (
                  <span className="text-micro text-lia-text-secondary truncate">{diff.reason}</span>
                )}
              </div>

              {diff.before && (
                <div className="px-3 py-2">
                  <div className="flex items-start gap-2">
                    <span className="text-micro font-medium text-lia-text-secondary mt-0.5 shrink-0">ANTES</span>
                    <p className="text-xs text-lia-text-secondary line-through leading-relaxed">
                      {diff.before}
                    </p>
                  </div>
                </div>
              )}

              {diff.after && (
                <div className="px-3 py-2 bg-wedo-cyan/[.04]">
                  <div className="flex items-start gap-2">
                    <span className="text-micro font-medium shrink-0 text-lia-text-secondary">DEPOIS</span>
                    <p className="text-xs text-lia-text-primary leading-relaxed font-medium">
                      {diff.after}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      <div className="flex items-center gap-2 pt-1">
        <Button
          size="sm"
          className="h-7 text-xs px-3 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
          onClick={onAccept}
          disabled={disabled}
        >
          <Check className="h-3 w-3 mr-1" />
          Aceitar
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="h-7 text-xs px-3 border-lia-border-subtle text-lia-text-secondary"
          onClick={onRequestAnother}
          disabled={disabled}
        >
          <RotateCcw className="h-3 w-3 mr-1" />
          Pedir outro ajuste
        </Button>
      </div>
    </div>
  )
}

export default QuestionDiffView
