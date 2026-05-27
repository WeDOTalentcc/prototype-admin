"use client"

import { textStyles, previewChipVariants } from '@/lib/design-tokens'
import { getWsiScoreColor } from '@/lib/wsi/visual'
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Brain, Clock } from"lucide-react"
import type { OpinionsData } from './ProfileTabTypes'

interface ProfileLiaOpinionCardProps {
  jobId?: string
  opinionsData: OpinionsData | null
  isLoadingOpinions: boolean
  isAnalyzingWithLia: boolean
  lastAnalysisDate: Date | null
  formatAnalysisDate: (date: Date | null) => string
  handleAnalyzeWithLia: () => void
}

export function ProfileLiaOpinionCard({
  jobId,
  opinionsData,
  isLoadingOpinions,
  isAnalyzingWithLia,
  lastAnalysisDate,
  formatAnalysisDate,
  handleAnalyzeWithLia,
}: ProfileLiaOpinionCardProps) {
  if (!jobId) return null

  if (isLoadingOpinions && !opinionsData) {
    return (
      <div className="bg-lia-bg-primary border border-lia-border-subtle rounded-xl p-3 animate-pulse motion-reduce:animate-none">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-4 h-4 bg-lia-interactive-active rounded-md"></div>
          <div className="w-24 h-4 bg-lia-interactive-active rounded-md"></div>
        </div>
        <div className="space-y-1.5">
          <div className="w-32 h-3 bg-lia-interactive-active rounded-md"></div>
          <div className="w-full h-3 bg-lia-interactive-active rounded-md"></div>
        </div>
      </div>
    )
  }

  if (!(opinionsData?.current_general_opinion || (opinionsData?.vacancy_opinions && opinionsData.vacancy_opinions.length > 0))) {
    return null
  }

  const opinion = opinionsData?.current_general_opinion || opinionsData?.vacancy_opinions?.[0]
  if (!opinion) return null

  const isWsiOpinion = opinion.opinion_type === 'wsi' || opinion.wsi_score !== null
  const displayScore = isWsiOpinion ? opinion.wsi_score : opinion.score

  const getScoreColor = (score: number | null, isWsi: boolean = false) => {
    if (score === null || score === undefined) return 'text-lia-text-secondary'
    if (isWsi) return getWsiScoreColor(score)
    return score >= 80 ? 'text-status-success' : score >= 60 ? 'text-status-warning' : 'text-status-error'
  }

  return (
    <Card className="bg-lia-bg-primary border border-lia-border-subtle">
      <CardHeader className="py-1.5 px-2.5 bg-lia-bg-primary">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <div className="p-0.5 rounded-xl bg-lia-bg-tertiary">
              <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
            </div>
            <CardTitle className={`${textStyles.label} text-lia-text-secondary`}>Parecer IA</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <div className={`flex items-center gap-1 ${textStyles.caption}`}>
              <Clock className="w-3 h-3" />
              <span>{formatAnalysisDate(
                opinionsData?.current_general_opinion?.created_at 
                  ? new Date(opinionsData.current_general_opinion.created_at)
                  : opinionsData?.vacancy_opinions?.[0]?.created_at
                    ? new Date(opinionsData.vacancy_opinions[0].created_at)
                    : lastAnalysisDate
              )}</span>
            </div>
            <Button
              onClick={handleAnalyzeWithLia}
              disabled={isAnalyzingWithLia}
              size="sm"
              variant="ghost"
              className={`gap-1 px-2 py-1 ${textStyles.caption} h-6 hover:bg-lia-bg-tertiary text-lia-text-secondary transition-colors motion-reduce:transition-none disabled:opacity-50`}
            >
              {isAnalyzingWithLia ? (
                <>
                  <div className="w-3 h-3 border-2 border-lia-btn-primary-bg border-t-transparent rounded-full animate-spin motion-reduce:animate-none" />
                  <span>Analisando...</span>
                </>
              ) : (
                <>
                  <Brain className="w-3 h-3 text-wedo-cyan" />
                  <span>Atualizar</span>
                </>
              )}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-2.5 pb-2.5 px-2.5">
        <div className="space-y-2">
          <div className="flex items-center gap-2 flex-wrap">
            {displayScore !== null && displayScore !== undefined && (
              <span className={`${textStyles.label} ${getScoreColor(displayScore, isWsiOpinion)}`}>
                {/* @canonical-allow-100 fallback display for non-WSI legacy opinion (canonical Surface 1) */}
                {isWsiOpinion ? `WSI: ${displayScore.toFixed(1)}/10` : `Nota: ${Math.round(displayScore)}/100`}
              </span>
            )}
            {opinion.archetype && (
              <>
                <span className="lia-text-muted">•</span>
                <Chip variant="neutral" muted className={previewChipVariants.neutral}>{opinion.archetype}</Chip>
              </>
            )}
          </div>
          {opinion.summary && (
            <p className={`${textStyles.caption} text-lia-text-secondary leading-relaxed`}>
              {opinion.summary}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
