"use client"

import { useState } from "react"
import { ChevronDown, ChevronUp, Brain, Info } from "lucide-react"

interface ScoreBreakdown {
  technical?: number
  behavioral?: number
  cultural_fit?: number
  experience?: number
  [key: string]: number | undefined
}

interface LIAScoreCardProps {
  score: number
  breakdown?: ScoreBreakdown
  candidateName?: string
  jobTitle?: string
  className?: string
}

const DIMENSION_LABELS: Record<string, string> = {
  technical: "Técnico",
  behavioral: "Comportamental",
  cultural_fit: "Fit Cultural",
  experience: "Experiência",
}

const DIMENSION_COLORS: Record<string, string> = {
  technical: "bg-gray-800",
  behavioral: "bg-gray-600",
  cultural_fit: "bg-gray-500",
  experience: "bg-gray-700",
}

function ScoreBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full ${color} rounded-full transition-all duration-500`}
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        />
      </div>
      <span className="text-xs text-gray-500 w-8 text-right tabular-nums">
        {Math.round(value)}%
      </span>
    </div>
  )
}

export function LIAScoreCard({
  score,
  breakdown,
  candidateName,
  jobTitle,
  className = "",
}: LIAScoreCardProps) {
  const [expanded, setExpanded] = useState(false)

  const hasBreakdown = breakdown && Object.keys(breakdown).length > 0
  const scoreColor =
    score >= 80 ? "text-gray-900" : score >= 60 ? "text-gray-600" : "text-gray-400"

  return (
    <div
      className={`border border-gray-200 rounded-md bg-white ${className}`}
      role="region"
      aria-label={`LIA Score${candidateName ? ` para ${candidateName}` : ""}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2">
        <div className="flex items-center gap-2">
          <Brain
            className="w-4 h-4 text-wedo-cyan"
            aria-hidden="true"
          />
          <span className="text-xs font-medium text-gray-700">LIA Score</span>
          {jobTitle && (
            <span className="text-xs text-gray-400 truncate max-w-[120px]">
              — {jobTitle}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`text-sm font-semibold tabular-nums ${scoreColor}`}
            aria-label={`Score: ${score} de 100`}
          >
            {score}
            <span className="text-xs font-normal text-gray-400">/100</span>
          </span>
          {hasBreakdown && (
            <button
              onClick={() => setExpanded((v) => !v)}
              className="p-0.5 rounded hover:bg-gray-100 transition-colors"
              aria-expanded={expanded}
              aria-label={expanded ? "Recolher detalhes do score" : "Ver detalhes do score"}
            >
              {expanded ? (
                <ChevronUp className="w-3.5 h-3.5 text-gray-400" aria-hidden="true" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5 text-gray-400" aria-hidden="true" />
              )}
            </button>
          )}
        </div>
      </div>

      {/* Breakdown expandido */}
      {expanded && hasBreakdown && (
        <div
          className="px-3 pb-3 border-t border-gray-100 pt-2 space-y-2"
          role="list"
          aria-label="Detalhamento do score por dimensão"
        >
          {Object.entries(breakdown!).map(([key, value]) => {
            if (value === undefined || value === null) return null
            const label = DIMENSION_LABELS[key] ?? key
            const color = DIMENSION_COLORS[key] ?? "bg-gray-500"
            return (
              <div key={key} role="listitem">
                <div className="flex items-center justify-between mb-0.5">
                  <span className="text-xs text-gray-600">{label}</span>
                </div>
                <ScoreBar value={value} color={color} />
              </div>
            )
          })}
          <p className="text-micro text-gray-400 pt-1 flex items-center gap-1">
            <Info className="w-3 h-3" aria-hidden="true" />
            Score calculado pela IA — EU AI Act Art. 13
          </p>
        </div>
      )}
    </div>
  )
}

export default LIAScoreCard
