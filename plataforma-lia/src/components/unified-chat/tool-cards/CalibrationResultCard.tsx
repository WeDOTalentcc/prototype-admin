"use client"

import React from 'react'
import { PanelRight } from 'lucide-react'
import { useToolSurface } from '@/contexts/ToolSurfaceContext'

export interface CalibrationCandidate {
  id: string
  name: string
  score: number
  stage?: string | null
}

interface CalibrationResultCardProps {
  candidates: CalibrationCandidate[]
  averageScore: number
  onOpenPanel?: () => void
}

function ScoreBar({ score }: { score: number }) {
  const color =
    score >= 80 ? 'bg-green-500' :
    score >= 60 ? 'bg-yellow-500' : 'bg-red-400'
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-xs text-gray-500 dark:text-gray-400">{score}</span>
    </div>
  )
}

function CandidateScoreRow({ candidate }: { candidate: CalibrationCandidate }) {
  return (
    <div className="flex items-center gap-2 py-1.5">
      <div className="size-7 shrink-0 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center text-xs font-medium text-gray-600 dark:text-gray-300">
        {candidate.name.charAt(0).toUpperCase()}
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">{candidate.name}</p>
        {candidate.stage && (
          <p className="truncate text-xs text-gray-500 dark:text-gray-400">{candidate.stage}</p>
        )}
      </div>
      <ScoreBar score={candidate.score} />
    </div>
  )
}

export function CalibrationResultCard({ candidates, averageScore, onOpenPanel }: CalibrationResultCardProps) {
  const surface = useToolSurface()

  if (surface === 'panel') {
    return (
      <div className="flex flex-col gap-0.5 px-1 py-2">
        <div className="mb-3 flex items-center gap-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Score médio</span>
          <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">{averageScore}</span>
        </div>
        {candidates.map(c => <CandidateScoreRow key={c.id} candidate={c} />)}
      </div>
    )
  }

  const preview = candidates.slice(0, 3)
  const remaining = candidates.length - preview.length

  return (
    <div className="mt-1 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-3 space-y-1">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Calibração</span>
          <span className="text-lg font-bold text-gray-900 dark:text-gray-100">{averageScore}%</span>
        </div>
        {onOpenPanel && (
          <button
            onClick={onOpenPanel}
            className="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 hover:underline"
          >
            Ver detalhe <PanelRight className="size-3" />
          </button>
        )}
      </div>
      {preview.map(c => <CandidateScoreRow key={c.id} candidate={c} />)}
      {remaining > 0 && (
        <p className="text-xs text-gray-400 dark:text-gray-500 pt-1">+{remaining} outros</p>
      )}
    </div>
  )
}
