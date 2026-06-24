"use client"

import React from "react"
import { PanelRight } from "lucide-react"
import { useToolSurface } from "@/contexts/ToolSurfaceContext"

export interface CandidateSummary {
  id: string
  name: string
  currentTitle?: string | null
  matchScore?: number | null
  avatarUrl?: string | null
}

interface CandidateResultCardProps {
  candidates: CandidateSummary[]
  totalCount: number
  query?: string
  onOpenPanel?: () => void
}

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 80
      ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
      : score >= 60
        ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
        : "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300"
  return (
    <span className={`shrink-0 rounded px-1.5 py-0.5 text-xs font-medium ${color}`}>
      {score}%
    </span>
  )
}

function CandidateRow({ candidate }: { candidate: CandidateSummary }) {
  return (
    <div className="flex items-center gap-2 py-1.5">
      <div className="size-7 shrink-0 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center text-xs font-medium text-gray-600 dark:text-gray-300">
        {candidate.name.charAt(0).toUpperCase()}
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">
          {candidate.name}
        </p>
        {candidate.currentTitle && (
          <p className="truncate text-xs text-gray-500 dark:text-gray-400">
            {candidate.currentTitle}
          </p>
        )}
      </div>
      {candidate.matchScore != null && <ScoreBadge score={candidate.matchScore} />}
    </div>
  )
}

export function CandidateResultCard({
  candidates,
  totalCount,
  query,
  onOpenPanel,
}: CandidateResultCardProps) {
  const surface = useToolSurface()

  if (surface === "panel") {
    return (
      <div className="flex flex-col gap-0.5 px-1 py-2">
        <p className="mb-2 text-xs text-gray-500 dark:text-gray-400 font-medium">
          {totalCount} candidatos{query ? ` para "${query}"` : ""}
        </p>
        {candidates.map((c) => (
          <CandidateRow key={c.id} candidate={c} />
        ))}
      </div>
    )
  }

  const preview = candidates.slice(0, 3)
  const remaining = totalCount - preview.length

  return (
    <div className="mt-1 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-3 space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
          {totalCount} candidatos encontrados{query ? ` para "${query}"` : ""}
        </span>
        {onOpenPanel && (
          <button
            onClick={onOpenPanel}
            className="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 hover:underline"
          >
            Ver todos <PanelRight className="size-3" />
          </button>
        )}
      </div>
      {preview.map((c) => (
        <CandidateRow key={c.id} candidate={c} />
      ))}
      {remaining > 0 && (
        <p className="text-xs text-gray-400 dark:text-gray-500 pt-1">
          +{remaining} outros
        </p>
      )}
    </div>
  )
}
