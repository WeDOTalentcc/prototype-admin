"use client"

import React, { useState } from "react"
import { cn } from "@/lib/utils"
import { AlertTriangle, CheckCircle, Send } from "lucide-react"

// --- Types ---

export interface WizardJDReviewPanelProps {
  rawJD: string
  enrichedJD: string
  qualityScore?: number
  fairnessWarnings?: string[]
  onAccept: () => void
  onRequestChanges: (feedback: string) => void
}

// --- Helpers ---

function QualityBadge({ score }: { score: number }) {
  let colorClass: string
  let label: string

  if (score >= 80) {
    colorClass = "bg-green-100 text-green-700 border-green-200"
    label = `Ótimo · ${score}/100`
  } else if (score >= 60) {
    colorClass = "bg-amber-100 text-amber-700 border-amber-200"
    label = `Adequado · ${score}/100`
  } else {
    colorClass = "bg-red-100 text-red-700 border-red-200"
    label = `Crítico · ${score}/100`
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border",
        colorClass
      )}
    >
      <CheckCircle className="w-3 h-3" />
      {label}
    </span>
  )
}

/**
 * Naive diff highlight: wrap lines present in enriched but not in raw with
 * a subtle green background. Uses a line-by-line heuristic — good enough
 * for a side-panel preview; not a full Myers diff.
 */
function EnrichedWithDiff({
  rawJD,
  enrichedJD,
}: {
  rawJD: string
  enrichedJD: string
}) {
  const rawLines = new Set(rawJD.split("\n").map((l) => l.trim()).filter(Boolean))
  const enrichedLines = enrichedJD.split("\n")

  return (
    <div className="space-y-0.5">
      {enrichedLines.map((line, i) => {
        const trimmed = line.trim()
        const isNew = trimmed.length > 0 && !rawLines.has(trimmed)
        return (
          <p
            key={i}
            className={cn(
              "text-xs leading-relaxed",
              isNew
                ? "bg-green-50 text-green-900 px-1 rounded"
                : "text-foreground"
            )}
          >
            {line || " "}
          </p>
        )
      })}
    </div>
  )
}

// --- Main Component ---

/**
 * WizardJDReviewPanel (HITL gate 1) — Onda 26-27 E.3
 *
 * Shows original vs enriched JD side-by-side.
 * Recruiter can accept or request changes with free-text feedback.
 */
export function WizardJDReviewPanel({
  rawJD,
  enrichedJD,
  qualityScore,
  fairnessWarnings = [],
  onAccept,
  onRequestChanges,
}: WizardJDReviewPanelProps) {
  const [feedback, setFeedback] = useState("")

  const handleSend = () => {
    const trimmed = feedback.trim()
    if (!trimmed) return
    onRequestChanges(trimmed)
    setFeedback("")
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-border space-y-2">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base font-semibold text-foreground">
            Revisão da Job Description
          </h2>
          {qualityScore !== undefined && <QualityBadge score={qualityScore} />}
        </div>

        {/* Fairness warnings */}
        {fairnessWarnings.length > 0 && (
          <div className="rounded-md bg-amber-50 border border-amber-200 px-3 py-2 space-y-1">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-700">
              <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
              Avisos de fairness
            </div>
            <ul className="space-y-0.5 ml-5 list-disc">
              {fairnessWarnings.map((w, i) => (
                <li key={i} className="text-xs text-amber-700">
                  {w}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Two-column comparison */}
      <div className="flex-1 overflow-hidden grid grid-cols-2 divide-x divide-border min-h-0">
        {/* Left: Original */}
        <div className="flex flex-col overflow-hidden">
          <div className="flex-shrink-0 px-3 py-2 bg-muted/40 border-b border-border">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              Original
            </span>
          </div>
          <div className="flex-1 overflow-y-auto px-3 py-3">
            <p className="text-xs leading-relaxed text-foreground whitespace-pre-wrap">
              {rawJD || (
                <span className="text-muted-foreground italic">Sem conteúdo original.</span>
              )}
            </p>
          </div>
        </div>

        {/* Right: Enriched with diff highlight */}
        <div className="flex flex-col overflow-hidden">
          <div className="flex-shrink-0 px-3 py-2 bg-muted/40 border-b border-border">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              Enriquecida
            </span>
          </div>
          <div className="flex-1 overflow-y-auto px-3 py-3">
            {enrichedJD ? (
              <EnrichedWithDiff rawJD={rawJD} enrichedJD={enrichedJD} />
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center space-y-2">
                  <div className="w-5 h-5 mx-auto border-2 border-primary border-t-transparent rounded-full animate-spin" />
                  <p className="text-xs text-muted-foreground">Enriquecendo...</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="flex-shrink-0 px-4 py-3 border-t border-border bg-background space-y-2">
        {/* Accept button */}
        <button
          onClick={onAccept}
          disabled={!enrichedJD}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <CheckCircle className="w-4 h-4" />
          Aceitar
        </button>

        {/* Request changes row */}
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Refazer com ajustes..."
            className="flex-1 px-3 py-1.5 text-sm rounded border border-border bg-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <button
            onClick={handleSend}
            disabled={!feedback.trim()}
            className="flex items-center justify-center w-8 h-8 rounded bg-primary text-primary-foreground disabled:opacity-40 disabled:cursor-not-allowed hover:bg-primary/90 transition-colors"
            aria-label="Enviar ajustes"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
