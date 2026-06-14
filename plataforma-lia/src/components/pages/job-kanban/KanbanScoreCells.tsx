"use client"

import React from "react"
import {
  Brain, Target, Code, Globe, Fingerprint, Gauge, AlertTriangle,
} from "lucide-react"
import { formatScorePercent } from "@/lib/design-tokens"
import type { KanbanCandidate } from "./KanbanTableCellRenderer.types"
import { useTranslations } from "next-intl"

interface ScoreCellsProps {
  calculateNotaLiaGeral: (candidate: KanbanCandidate) => number | null
  onSetSelectedCandidateForModal: (candidate: KanbanCandidate) => void
  onSetActiveModal: (modal: string) => void
  onSetShowBigFiveModal: (show: boolean) => void
  onOpenTriagem: (candidate: KanbanCandidate) => void
  onOpenAnalysis: (candidate: KanbanCandidate) => void
}

export function renderScoreCell(
  candidate: KanbanCandidate,
  columnId: string,
  props: ScoreCellsProps,
  t: (key: string, params?: Record<string, unknown>) => string
): React.ReactNode | undefined {
  const {
    calculateNotaLiaGeral,
    onSetSelectedCandidateForModal,
    onSetActiveModal,
    onSetShowBigFiveModal,
    onOpenTriagem,
    onOpenAnalysis,
  } = props

  switch (columnId) {
    case 'id':
      return (
        <div className="text-xs font-mono text-lia-text-secondary">
          {(candidate.candidateCode as string | undefined) || (candidate.id as string | undefined)?.substring(0, 6).toUpperCase()}
        </div>
      )

    case 'score': {
      const ranking = calculateNotaLiaGeral(candidate)
      const hasNotaGeral = ranking !== null && ranking !== undefined && ranking > 0
      return (
        <div
          className={`flex items-center gap-1 justify-center cursor-pointer group ${hasNotaGeral ? '' : 'opacity-40'}`}
          onClick={(e) => {
            e.stopPropagation()
            if (hasNotaGeral) {
              onSetSelectedCandidateForModal(candidate)
              onSetActiveModal('scoreGeral')
            }
          }}
          title={hasNotaGeral ? t('clickDetails') : t('notEvaluated')}
        >
          <Gauge className={`w-3.5 h-3.5 ${hasNotaGeral ? 'text-lia-btn-primary-bg' : 'text-lia-text-tertiary'}`} strokeWidth={2} />
          <span className={`text-xs font-semibold ${hasNotaGeral ? 'text-lia-text-primary' : 'text-lia-text-tertiary'}`}>
            {hasNotaGeral ? ranking : '—'}
          </span>
        </div>
      )
    }

    case 'liaScore': {
      const hasTriagem = (candidate.liaScore !== null && candidate.liaScore !== undefined) || (candidate.score !== null && candidate.score !== undefined)
      const triagemValue = candidate.liaScore ?? candidate.score
      // Audit task #530 (G23-02 frontend) — selo de modo degradado também na
      // tabela (paridade com KanbanCardScores).
      const isDegraded = hasTriagem && candidate.triagemDegraded === true
      const degradedTooltip = t('degradedModeTooltip')
      return (
        <div
          className={`flex items-center gap-1 justify-center cursor-pointer group ${hasTriagem ? '' : 'opacity-40'}`}
          onClick={(e) => {
            e.stopPropagation()
            if (hasTriagem) {
              onOpenTriagem(candidate)
            }
          }}
          title={isDegraded ? degradedTooltip : (hasTriagem ? t('clickLIAScreening') : t('notEvaluated'))}
        >
          <Brain className={`w-3.5 h-3.5 ${hasTriagem ? 'text-wedo-cyan' : 'text-lia-text-muted'}`} strokeWidth={2} />
          <span className={`text-xs font-semibold ${hasTriagem ? 'text-lia-text-primary' : 'text-lia-text-tertiary'}`}>
            {hasTriagem ? formatScorePercent(triagemValue as number, 0) : '—'}
          </span>
          {isDegraded && (
            <AlertTriangle
              className="w-3 h-3 text-status-warning"
              strokeWidth={2.5}
              aria-label={degradedTooltip}
            />
          )}
        </div>
      )
    }

    case 'fitScore': {
      const hasFitScore = (candidate.skillsMatch !== null && candidate.skillsMatch !== undefined && (candidate.skillsMatch as number) > 0) || (candidate.fitScore !== null && candidate.fitScore !== undefined && (candidate.fitScore as number) > 0)
      const fitValue = candidate.skillsMatch || candidate.fitScore || 0
      return (
        <div
          className={`flex items-center gap-1 justify-center cursor-pointer group ${hasFitScore ? '' : 'opacity-40'}`}
          onClick={(e) => {
            e.stopPropagation()
            if (hasFitScore) {
              onOpenAnalysis(candidate)
            }
          }}
          title={hasFitScore ? t('clickCVAnalysis') : t('notEvaluated')}
        >
          <Target className={`w-3.5 h-3.5 ${hasFitScore ? 'text-lia-btn-primary-bg' : 'text-lia-text-tertiary'}`} strokeWidth={2} />
          <span className={`text-xs font-semibold ${hasFitScore ? 'text-lia-text-primary' : 'text-lia-text-tertiary'}`}>
            {hasFitScore ? formatScorePercent(fitValue as number, 0) : '—'}
          </span>
        </div>
      )
    }

    case 'technicalTestScore': {
      const hasTechnical = candidate.technicalTestScore !== null && candidate.technicalTestScore !== undefined
      return (
        <div
          className={`flex items-center gap-1 justify-center cursor-pointer group ${hasTechnical ? '' : 'opacity-40'}`}
          onClick={(e) => {
            e.stopPropagation()
            if (hasTechnical) {
              onSetSelectedCandidateForModal(candidate)
              onSetActiveModal('testeTecnico')
            }
          }}
          title={hasTechnical ? t('clickDetails') : t('notCompleted')}
        >
          <Code className={`w-3.5 h-3.5 ${hasTechnical ? 'text-lia-text-secondary' : 'text-lia-text-tertiary'}`} strokeWidth={2} />
          {hasTechnical && (
            <span className="text-xs font-semibold text-lia-text-primary">
              {formatScorePercent(candidate.technicalTestScore as number, 0)}
            </span>
          )}
        </div>
      )
    }

    case 'englishTestScore': {
      const hasEnglish = candidate.englishTestScore !== null && candidate.englishTestScore !== undefined
      return (
        <div
          className={`flex items-center gap-1 justify-center cursor-pointer group ${hasEnglish ? '' : 'opacity-40'}`}
          onClick={(e) => {
            e.stopPropagation()
            if (hasEnglish) {
              onSetSelectedCandidateForModal(candidate)
              onSetActiveModal('testeIngles')
            }
          }}
          title={hasEnglish ? t('clickDetails') : t('notCompleted')}
        >
          <Globe className={`w-3.5 h-3.5 ${hasEnglish ? 'text-lia-text-secondary' : 'text-lia-text-tertiary'}`} strokeWidth={2} />
          {hasEnglish && (
            <span className="text-xs font-semibold text-lia-text-primary">
              {formatScorePercent(candidate.englishTestScore as number, 0)}
            </span>
          )}
        </div>
      )
    }

    case 'bigFive': {
      const hasBigFive = candidate.bigFive || candidate.bigFiveScores
      const bigFiveData = candidate.bigFive || candidate.bigFiveScores || {}
      const bigFiveValues = Object.values(bigFiveData).filter((v): v is number => typeof v === 'number')
      const bigFiveAvg = bigFiveValues.length > 0 ? Math.round(bigFiveValues.reduce((a, b) => a + b, 0) / bigFiveValues.length) : null
      return (
        <div
          className={`flex items-center gap-1 justify-center cursor-pointer group ${hasBigFive ? '' : 'opacity-40'}`}
          onClick={(e) => {
            e.stopPropagation()
            if (hasBigFive) {
              onSetSelectedCandidateForModal(candidate)
              onSetShowBigFiveModal(true)
            }
          }}
          title={hasBigFive ? t('clickBigFiveReport') : t('notCompleted')}
        >
          <Fingerprint className={`w-3.5 h-3.5 ${hasBigFive ? 'text-lia-text-secondary' : 'text-lia-text-tertiary'}`} strokeWidth={2} />
          <span className={`text-xs font-semibold ${hasBigFive ? 'text-lia-text-primary' : 'text-lia-text-tertiary'}`}>
            {hasBigFive && bigFiveAvg !== null ? bigFiveAvg : '—'}
          </span>
        </div>
      )
    }

    default:
      return undefined
  }
}
