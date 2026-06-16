"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { ScoreIconButton } from "@/components/ui/score-icon-button"
import { formatScorePercent } from "@/lib/design-tokens"
import { Gauge, BrainCircuit, Target, Code, Globe, Fingerprint, AlertTriangle } from "lucide-react"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

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
    // Audit task #530 (G23-02 frontend) — flag de modo degradado da triagem,
    // populada por useKanbanDataEffects a partir do endpoint candidates/scores.
    triagemDegraded?: boolean
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
  const t = useTranslations('kanban')
  return (
    <>
{/* Scores - Todos os 6 indicadores (Geral, Triagem, CV, Técnico, Inglês, B5) */}
{(() => {
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
    { id: "geral", icon: Gauge, value: geralScore, label: t('scoreGeral'), alwaysClickable: false },
    { id: "triagem", icon: BrainCircuit, value: triagemScore, label: t('scoreTriagem'), alwaysClickable: true },
    { id: "cv", icon: Target, value: cvScore, label: t('scoreCV'), alwaysClickable: true },
    { id: "tecnico", icon: Code, value: tecnicoScore, label: t('scoreTecnico'), alwaysClickable: false },
    { id: "ingles", icon: Globe, value: inglesScore, label: t('scoreIngles'), alwaysClickable: false },
    { id: "b5", icon: Fingerprint, value: b5Score, label: t('scoreB5'), alwaysClickable: false },
  ]

  return (
    <div className="flex items-center gap-1.5 mb-1.5 flex-wrap">
      {scores.map(({ id, icon: Icon, value, label, alwaysClickable }) => {
        // Audit task #530 (G23-02 frontend) — selo de modo degradado ao lado
        // do score de triagem WSI quando a Camada 2 (semântica) não rodou.
        const showDegraded =
          id === "triagem" && triagemScore != null && candidate.triagemDegraded === true
        return (
          <div key={id} className="flex items-center gap-0.5">
            <ScoreIconButton
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
            {showDegraded && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span
                      role="img"
                      aria-label={t('degradedModeTooltip')}
                      className="inline-flex"
                    >
                      <AlertTriangle className="h-3 w-3 text-status-warning" strokeWidth={2.5} />
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{t('degradedModeTooltip')}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </div>
        )
      })}
    </div>
  )
})()}

{/* Informações do candidato - Alinhadas à esquerda */}
    </>
  )
}
