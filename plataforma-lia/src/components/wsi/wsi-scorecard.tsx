"use client"

import { useState, useEffect } from"react"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Progress } from"@/components/ui/progress"
import {
  Brain, Target, MessageSquare, TrendingUp, AlertTriangle,
  CheckCircle, ChevronDown, ChevronUp, Award, BarChart3,
  Star, AlertCircle, FileText, Loader2
} from"lucide-react"
import { liaApi, WSIResultsResponse } from"@/services/lia-api"
import { useTranslations } from "next-intl"
import { useLocale } from "next-intl"
import {
  WSI_DISPLAY_SCALE,
  getWsiVisualState,
  getWsiVisualStateForClassification,
  wsiPercent,
  wsiClassificationI18nKey,
} from "@/lib/wsi/visual"

interface WSIScorecardProps {
  candidateId: string
  candidateName?: string
  compact?: boolean
  showHistory?: boolean
  onViewDetails?: (resultId: string) => void
}

interface ScoreDisplay {
  value: number
  label: string
  color: string
  bgColor: string
}

export function WSIScorecard({
  candidateId,
  candidateName,
  compact = false,
  showHistory = false,
  onViewDetails
}: WSIScorecardProps) {
  const t = useTranslations('screening.wsi')
  const locale = useLocale()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<WSIResultsResponse | null>(null)
  const [expanded, setExpanded] = useState(!compact)

  // Escala WSI 0-10 (Task #512). Cores e cutoffs vêm do helper canônico
  // `lib/wsi/visual.ts` — não duplicar thresholds aqui.
  const getClassificationLabel = (classification: string) => {
    const key = wsiClassificationI18nKey(classification)
    if (t.has(`classification.${key}` as never)) {
      return t(`classification.${key}` as never)
    }
    return t('classification.medio')
  }

  const getScoreDisplay = (score: number): ScoreDisplay => {
    const v = getWsiVisualState(score)
    return { value: score, label: getClassificationLabel(v.classification), color: v.text, bgColor: v.bg }
  }

  const getClassificationBadge = (classification: string) => {
    const v = getWsiVisualStateForClassification(classification)
    return { color: v.text, bgColor: v.bg }
  }

  const getClassificationConfig = (classification: string) => {
    const v = getWsiVisualStateForClassification(classification)
    return { label: getClassificationLabel(classification), color: v.text, bgColor: v.bg }
  }

   
  useEffect(() => {
    loadResults()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [candidateId])

  const loadResults = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await liaApi.wsiGetCandidateResults(candidateId)
      setResults(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : t('scorecard.errorLoadingResults'))
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Card className="border-dashed">
        <CardContent className="py-6 flex items-center justify-center">
          <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none text-lia-text-tertiary" />
          <span className="ml-2 text-sm text-lia-text-tertiary">{t('scorecard.loadingWSI')}</span>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="border-dashed border-status-error/30 dark:border-status-error/30">
        <CardContent className="py-6 flex items-center justify-center">
          <AlertCircle className="w-5 h-5 text-status-error" />
          <span className="ml-2 text-sm text-status-error">{error}</span>
        </CardContent>
      </Card>
    )
  }

  if (!results || results.total_screenings === 0) {
    return (
      <Card className="border-dashed">
        <CardContent className="py-6 text-center">
          <Brain className="w-8 h-8 text-wedo-cyan mx-auto mb-2" />
          <p className="text-sm text-lia-text-tertiary">
            {t('scorecard.noScreening')}
          </p>
        </CardContent>
      </Card>
    )
  }

  const latestResult = results.results[0]
  const scoreDisplay = getScoreDisplay(latestResult.overall_wsi)
  const classificationBadge = getClassificationBadge(latestResult.classification)

  if (compact && !expanded) {
    return (
      <Card 
        className="cursor-pointer hover:bg-lia-bg-tertiary/50 transition-colors motion-reduce:transition-none"
        onClick={() => setExpanded(true)}
      >
        <CardContent className="py-3 px-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${scoreDisplay.bgColor}`}>
                <span className={`text-lg font-semibold ${scoreDisplay.color}`}>
                  {latestResult.overall_wsi.toFixed(1)}
                </span>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm">{t('scorecard.scoreWSI')}</span>
                  <Chip variant="neutral" muted className={`${classificationBadge.bgColor} ${classificationBadge.color} text-xs`}>
                    {latestResult.classification}
                  </Chip>
                </div>
                <p className="text-xs text-lia-text-tertiary">
                  {latestResult.screening_type === 'voice' ? t('scorecard.voiceScreening') : t('scorecard.textScreening')}
                </p>
              </div>
            </div>
            <ChevronDown className="w-4 h-4 text-lia-text-tertiary" />
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Brain className="w-4 h-4 text-wedo-cyan" />
            {t('scorecard.scoreWSI')}
            {candidateName && (
              <span className="text-lia-text-tertiary font-normal">• {candidateName}</span>
            )}
          </CardTitle>
          {compact && (
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => setExpanded(false)}
              className="h-6 w-6 p-0"
            >
              <ChevronUp className="w-4 h-4" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-4">
          <div className={`w-20 h-20 rounded-full flex flex-col items-center justify-center ${scoreDisplay.bgColor}`}>
            <span className={`text-2xl font-semibold ${scoreDisplay.color}`}>
              {latestResult.overall_wsi.toFixed(1)}
            </span>
            <span className="text-xs text-lia-text-tertiary">{t('scorecard.of5')}</span>
          </div>

          <div className="flex-1 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-lia-text-tertiary flex items-center gap-1">
                <Target className="w-3 h-3" />
                {t('scorecard.technical')}
              </span>
              <span className="font-medium">{latestResult.technical_wsi.toFixed(1)}</span>
            </div>
            <Progress 
              value={wsiPercent(latestResult.technical_wsi)} 
              className="h-1.5"
            />

            <div className="flex items-center justify-between mt-2">
              <span className="text-sm text-lia-text-tertiary flex items-center gap-1">
                <MessageSquare className="w-3 h-3" />
                {t('scorecard.behavioral')}
              </span>
              <span className="font-medium">{latestResult.behavioral_wsi.toFixed(1)}</span>
            </div>
            <Progress 
              value={wsiPercent(latestResult.behavioral_wsi)} 
              className="h-1.5"
            />
          </div>
        </div>

        <div className="flex items-center justify-between pt-2 border-t">
          <Chip variant="neutral" muted className={`${classificationBadge.bgColor} ${classificationBadge.color}`}>
            <Award className="w-3 h-3 mr-1" />
            {getClassificationConfig(latestResult.classification).label}
          </Chip>

          <div className="flex items-center gap-2 text-xs text-lia-text-tertiary">
            {latestResult.screening_type === 'voice' ? (
              <Chip density="relaxed" variant="neutral" >
                {t('scorecard.voice')}
              </Chip>
            ) : (
              <Chip density="relaxed" variant="neutral" >
                {t('scorecard.text')}
              </Chip>
            )}
            {latestResult.percentile && (
              <span className="flex items-center gap-1">
                <TrendingUp className="w-3 h-3" />
                Top {100 - latestResult.percentile}%
              </span>
            )}
          </div>
        </div>

        {showHistory && results.total_screenings > 1 && (
          <div className="pt-2 border-t">
            <p className="text-xs text-lia-text-tertiary mb-2">
              {t('scorecard.history', { count: results.total_screenings })}
            </p>
            <div className="space-y-2">
              {results.results.slice(1, 4).map((result, idx) => (
                <div 
                  key={result.result_id}
                  className="flex items-center justify-between text-sm p-2 bg-lia-bg-tertiary/50 rounded-md cursor-pointer hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none"
                  onClick={() => onViewDetails?.(result.result_id)}
                >
                  <div className="flex items-center gap-2">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${getScoreDisplay(result.overall_wsi).bgColor} ${getScoreDisplay(result.overall_wsi).color}`}>
                      {result.overall_wsi.toFixed(1)}
                    </div>
                    <span className="text-xs text-lia-text-tertiary">
                      {new Date(result.created_at).toLocaleDateString(locale)}
                    </span>
                  </div>
                  <Chip density="relaxed" variant="neutral" >
                    {result.classification}
                  </Chip>
                </div>
              ))}
            </div>
          </div>
        )}

        {onViewDetails && (
          <Button 
            variant="outline" 
            size="sm" 
            className="w-full text-xs gap-1"
            onClick={() => onViewDetails(latestResult.result_id)}
          >
            <FileText className="w-3 h-3" />
            {t('scorecard.viewFullReport')}
          </Button>
        )}
      </CardContent>
    </Card>
  )
}

export function WSIScoreBadge({ score, classification }: { score: number; classification: string }) {
  const t = useTranslations('screening.wsi')
  const display = getWsiVisualState(score)
  const badge = getWsiVisualStateForClassification(classification)
  const i18nKey = wsiClassificationI18nKey(classification)
  const labelKey = `classification.${i18nKey}` as never
  const label = t.has(labelKey) ? t(labelKey) : classification

  return (
    <div className="inline-flex items-center gap-1.5">
      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${display.bg} ${display.text}`}>
        {score.toFixed(1)}
      </div>
      <Chip variant="neutral" muted className={`${badge.bg} ${badge.text} text-xs`}>
        {label}
      </Chip>
    </div>
  )
}

export function WSIMiniScore({ score }: { score: number }) {
  const t = useTranslations('screening.wsi')
  const v = getWsiVisualState(score)
  const i18nKey = wsiClassificationI18nKey(v.classification)
  const labelKey = `classification.${i18nKey}` as never
  const label = t.has(labelKey) ? t(labelKey) : v.classification

  return (
    <div
      className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold ${v.bg} ${v.text}`}
      title={`WSI: ${score.toFixed(1)}/${WSI_DISPLAY_SCALE.toFixed(1)} - ${label}`}
    >
      {score.toFixed(1)}
    </div>
  )
}
