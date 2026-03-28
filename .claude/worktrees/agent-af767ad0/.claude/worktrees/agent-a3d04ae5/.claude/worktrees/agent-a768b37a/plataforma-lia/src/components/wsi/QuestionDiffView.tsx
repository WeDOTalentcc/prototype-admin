"use client"

import React from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Check, RotateCcw, ArrowRight } from "lucide-react"
import { cn } from "@/lib/utils"

interface DiffItem {
  question_id: string
  action: "modified" | "added" | "removed"
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
      case "modified":
        return { label: "Modificada", className: "text-[9px] px-1.5 py-0 h-4 border" , style: { backgroundColor: "rgba(96,190,209,0.1)", borderColor: "rgba(96,190,209,0.3)" }}
      case "added":
        return { label: "Nova", className: "text-[9px] px-1.5 py-0 h-4 bg-green-50 text-green-600 border border-green-200" , style: {} }
      case "removed":
        return { label: "Removida", className: "text-[9px] px-1.5 py-0 h-4 bg-red-50 text-red-600 border border-red-200", style: {} }
      default:
        return { label: action, className: "text-[9px] px-1.5 py-0 h-4 bg-gray-100 text-gray-600 border border-gray-200", style: {} }
    }
  }

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex items-center gap-1.5">
        <ArrowRight className="h-3.5 w-3.5 text-gray-500" />
        <span className="text-[11px] font-semibold text-gray-800">Antes / Depois</span>
        <Badge variant="outline" className="text-[9px] px-1.5 py-0 h-4 bg-gray-100 text-gray-600 border-gray-200">
          {diffs.length} alteração(ões)
        </Badge>
      </div>

      <div className="space-y-2">
        {diffs.map((diff, idx) => {
          const badge = getActionBadge(diff.action)
          return (
            <div
              key={diff.question_id || idx}
              className="rounded-md border border-gray-200 overflow-hidden"
            >
              <div className="px-3 py-1.5 bg-gray-50 border-b border-gray-100 flex items-center gap-2">
                <Badge variant="outline" className={badge.className} style={badge.style}>
                  {badge.label}
                </Badge>
                {diff.reason && (
                  <span className="text-[10px] text-gray-500 truncate">{diff.reason}</span>
                )}
              </div>

              {diff.before && (
                <div className="px-3 py-2 border-b border-gray-100" style={{ backgroundColor: "#fafafa" }}>
                  <div className="flex items-start gap-2">
                    <span className="text-[10px] font-medium text-gray-400 mt-0.5 shrink-0">ANTES</span>
                    <p className="text-[11px] text-gray-500 line-through leading-relaxed">
                      {diff.before}
                    </p>
                  </div>
                </div>
              )}

              {diff.after && (
                <div className="px-3 py-2" style={{ backgroundColor: "rgba(96,190,209,0.04)" }}>
                  <div className="flex items-start gap-2">
                    <span className="text-[10px] font-medium shrink-0 text-gray-700">DEPOIS</span>
                    <p className="text-[11px] text-gray-800 leading-relaxed font-medium">
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
          className="h-7 text-[11px] px-3 bg-gray-900 hover:bg-gray-800 text-white"
          onClick={onAccept}
          disabled={disabled}
        >
          <Check className="h-3 w-3 mr-1" />
          Aceitar
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="h-7 text-[11px] px-3 border-gray-200 text-gray-700"
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
