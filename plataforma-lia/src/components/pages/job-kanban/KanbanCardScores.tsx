// @ts-nocheck
"use client"

import React from "react"
import { ScoreIconButton } from "@/components/ui/score-icon-button"
import { ScoreBreakdownBadgeLazy } from "@/components/score/ScoreBreakdownBadge"
import { formatScorePercent } from "@/lib/design-tokens"
import { Gauge, BrainCircuit, Target, Code, Globe, Fingerprint } from "lucide-react"

interface KanbanCardScoresProps {
  candidate: {
    id: string
    liaScore?: number | null
    score?: number | null
    skillsMatch?: number | null
    fitScore?: number | null
    technicalTestScore?: number | null
    englishTestScore?: number | null
    bigFive?: Record<string, number> | null
    bigFiveScores?: Record<string, number> | null
    [key: string]: unknown
  }
  calculateNotaLiaGeral: (candidate: unknown) => number | null
  _jobIdForSL: string | undefined
  onOpenScoreModal: (candidate: unknown, modalType: "geral" | "triagem" | "cv" | "tecnico" | "ingles" | "b5") => void
}

export function KanbanCardScores({
  candidate,
  calculateNotaLiaGeral,
  _jobIdForSL,
  onOpenScoreModal,
}: KanbanCardScoresProps) {
  const geralScore = calculateNotaLiaGeral(candidate)
  const triagemScore = candidate.liaScore ?? candidate.score
  const cvScore = candidate.skillsMatch || candidate.fitScore
  const tecnicoScore = candidate.technicalTestScore
  const inglesScore = candidate.englishTestScore
  const b5Data = candidate.bigFive || candidate.bigFiveScores
  const b5Score = b5Data
    ? Math.round(
        (Object.values(b5Data).reduce(
          (a: number, b: unknown) => a + (typeof b === "number" ? b : 0),
          0
        ) as number) / Object.values(b5Data).length
      )
    : null

  const scores = [
    { id: "geral", icon: Gauge, value: geralScore, label: "Geral", alwaysClickable: false },
    { id: "triagem", icon: BrainCircuit, value: triagemScore, label: "Triagem", alwaysClickable: true },
    { id: "cv", icon: Target, value: cvScore, label: "CV", alwaysClickable: true },
    { id: "tecnico", icon: Code, value: tecnicoScore, label: "Técnico", alwaysClickable: false },
    { id: "ingles", icon: Globe, value: inglesScore, label: "Inglês", alwaysClickable: false },
    { id: "b5", icon: Fingerprint, value: b5Score, label: "B5", alwaysClickable: false },
  ]

  return (
    <div className="flex items-center gap-1.5 mb-1.5 flex-wrap">
      {scores.map(({ id, icon: Icon, value, label, alwaysClickable }) => (
        <ScoreIconButton
          key={id}
          id={id}
          icon={Icon}
          value={value}
          formattedValue={value ? formatScorePercent(value, 0) : undefined}
          label={label}
          alwaysClickable={alwaysClickable}
          onClick={() =>
            onOpenScoreModal(
              candidate,
              id as "geral" | "triagem" | "cv" | "tecnico" | "ingles" | "b5"
            )
          }
        />
      ))}
      {/* E1 — Score clicável: badge lazy com detalhamento da rubrica */}
      {geralScore != null && _jobIdForSL && candidate.id && (
        <ScoreBreakdownBadgeLazy
          score={geralScore}
          jobId={_jobIdForSL}
          candidateId={String(candidate.id)}
          size="sm"
        />
      )}
    </div>
  )
}
