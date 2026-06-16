import React from "react"
import { Brain } from "lucide-react"
import { ScoreBreakdownBadgeLazy } from "@/components/score/ScoreBreakdownBadge"
import { textStyles } from "@/lib/design-tokens"
import { getPercentageScoreVar } from "@/lib/score-utils"
import type { Candidate } from "@/components/pages/candidates/types"

export function renderMatchScoreCell(candidate: Candidate, searchQuery: string): React.ReactNode {
  const matchScore = candidate.score || 0
  const hasActiveSearch = searchQuery && searchQuery.length > 0

  if (!hasActiveSearch || matchScore === 0) {
    return (
      <div className="flex items-center justify-center">
        <span className={textStyles.label}>—</span>
      </div>
    )
  }

  const getMatchRingColor = getPercentageScoreVar

  const ringColor = getMatchRingColor(matchScore)
  const ringSize = 32
  const strokeWidth = 3
  const radius = (ringSize - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const strokeDashoffset = circumference - (matchScore / 100) * circumference

  return (
    <div data-testid="match-score-cell" className="flex items-center justify-center">
      <div className="relative" style={{width: ringSize, height: ringSize}}>
        {/* Background ring */}
        <svg className="absolute" width={ringSize} height={ringSize}>
          <circle
            cx={ringSize / 2}
            cy={ringSize / 2}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            className="text-lia-text-tertiary"
          />
        </svg>
        {/* Progress ring */}
        <svg className="absolute -rotate-90" width={ringSize} height={ringSize}>
          <circle
            cx={ringSize / 2}
            cy={ringSize / 2}
            r={radius}
            fill="none"
            stroke={ringColor}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-colors motion-reduce:transition-none duration-300"
          />
        </svg>
        {/* Percentage text */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={`${textStyles.label} font-bold`}>
            {matchScore}
          </span>
        </div>
      </div>
    </div>
  )
}

type TranslateFn = (key: string, values?: Record<string, unknown>) => string

export function renderLiaScoreCell(candidate: Candidate, t?: TranslateFn): React.ReactNode {
  const score = candidate.lia_score || 0
  const hasBeenEvaluated = candidate.lia_score && candidate.lia_score > 0

  if (!hasBeenEvaluated) {
    return (
      <div className="relative group cursor-help">
        <span className="text-xs text-lia-text-primary">—</span>
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-50">
          <div className="bg-lia-btn-primary-bg dark:bg-lia-bg-elevated text-white px-3 py-2 rounded-xl text-xs min-w-[180px]">
            <div className="font-semibold mb-1.5 flex items-center gap-1.5">
              <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
              {t ? t('scoreCells.noEvaluation') : "Sem avaliação"}
            </div>
            <div className="text-xs text-lia-text-tertiary">
              {t ? t('scoreCells.noEvaluationDesc') : "Este candidato ainda não participou de nenhum processo seletivo."}
            </div>
            <div className="text-xs text-lia-text-primary mt-1.5">
              {t ? t('scoreCells.liaScoreInfo') : "O Score é calculado quando o candidato é avaliado para uma vaga específica."}
            </div>
            <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-lia-btn-primary-bg dark:border-t-lia-border-strong"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <ScoreBreakdownBadgeLazy
      score={score}
      candidateId={candidate.id}
      jobId={(candidate.additional_data?.job_id as string) ?? ""}
      size="sm"
    />
  )
}
