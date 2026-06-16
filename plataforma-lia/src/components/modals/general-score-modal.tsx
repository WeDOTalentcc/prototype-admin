"use client"

import { X, Gauge, TrendingUp, FileText, Brain, Code, Globe } from "lucide-react"
import { getPercentageScoreVar, getPercentageScoreBgVar, getPercentageScoreLabel } from "@/lib/score-utils"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { useTranslations } from "next-intl"

interface GeneralScoreModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: Record<string, unknown>
}

const SCORE_COMPONENTS = [
  { id: 'cv_fit', weight: 25, icon: FileText },
  { id: 'triagem_lia', weight: 30, icon: Brain },
  { id: 'teste_tecnico', weight: 25, icon: Code },
  { id: 'teste_ingles', weight: 20, icon: Globe },
]

export function GeneralScoreModal({ isOpen, onClose, candidate }: GeneralScoreModalProps) {
  const t = useTranslations('candidates.scoreModal')
  if (!isOpen) return null

  const scores = {
    cv_fit: candidate?.cvFitScore ?? candidate?.fitScore ?? 85,
    triagem_lia: candidate?.triagemScore ?? candidate?.screeningScore ?? 92,
    teste_tecnico: candidate?.technicalScore ?? candidate?.testeTecnico ?? 78,
    teste_ingles: candidate?.englishScore ?? candidate?.testeIngles ?? 72,
  }

  const calculateWeightedScore = () => {
    let totalWeightedScore = 0
    let totalWeight = 0

    SCORE_COMPONENTS.forEach(component => {
      const score = scores[component.id as keyof typeof scores]
      if (score !== null && score !== undefined) {
        totalWeightedScore += Number(score) * (component.weight / 100)
        totalWeight += component.weight
      }
    })

    if (totalWeight === 0) return 0
    return Math.round((totalWeightedScore / totalWeight) * 100)
  }

  const finalScore = (candidate?.score ?? calculateWeightedScore()) as number

  const getScoreColor = getPercentageScoreVar

  const getScoreBgColor = getPercentageScoreBgVar

  const getScoreLabel = getPercentageScoreLabel

  return (
    <div
      data-testid="general-score-modal"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-lia-overlay"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        className="w-full max-w-2xl overflow-hidden flex flex-col bg-lia-bg-primary border border-lia-border-subtle rounded-xl"
      >
        <div 
          className="flex items-center justify-between px-4 py-3 bg-lia-bg-secondary rounded-t-xl"
        >
          <div className="flex items-center gap-2">
            <div
              className="w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0 bg-wedo-cyan/12"
            >
              <Gauge className="w-4 h-4 text-lia-text-secondary" />
            </div>
            <div>
              <h2 
                className="text-sm font-semibold text-lia-text-primary"
               
              >
                {t('title')}
              </h2>
              <p 
                className="text-xs text-lia-text-secondary"
               
              >
                {t('subtitle')}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="h-7 w-7 p-0 flex items-center justify-center transition-colors motion-reduce:transition-none hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-bg rounded-full text-lia-text-tertiary"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="px-4 py-4 bg-lia-bg-primary">
          <div 
            className="flex items-center justify-between p-4 rounded-xl mb-4 border border-lia-border-subtle"
          >
            <div>
              <p 
                className="text-micro uppercase tracking-wide mb-1 text-lia-text-secondary"
               
              >
                {t('finalScore')}
              </p>
              <div className="flex items-baseline gap-2">
                <span 
                  className="text-3xl font-semibold"
                  style={{color: getScoreColor(finalScore)}}
                >
                  {finalScore}
                </span>
                <span 
                  className="text-sm text-lia-text-tertiary"
                >
                  / 100
                </span>
              </div>
            </div>
            <div className="text-right">
              <span 
                className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full"
                style={{backgroundColor: getScoreBgColor(finalScore), color: getScoreColor(finalScore)}}
              >

                <TrendingUp className="w-3 h-3" />
                {getScoreLabel(finalScore)}
              </span>
            </div>
          </div>

          <div className="mb-3">
            <p 
              className="text-xs font-semibold mb-3 text-lia-text-primary"
             
            >
              {t('composition')}
            </p>

            <div className="space-y-3">
              {SCORE_COMPONENTS.map((component) => {
                const Icon = component.icon
                const score = scores[component.id as keyof typeof scores]
                const hasScore = score !== null && score !== undefined

                return (
                  <div 
                    key={component.id}
                    className="p-3 rounded-xl border border-lia-border-subtle"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Icon className="w-3.5 h-3.5 text-lia-text-secondary" />
                        <span 
                          className="text-xs font-medium text-lia-text-primary"
                         
                        >
                          {t(`components.${component.id}.label`)}
                        </span>
                        <span 
                          className="text-micro px-1.5 py-0.5 rounded-full text-lia-text-secondary bg-lia-interactive-active"
                        >
                          {t('weight', { weight: component.weight })}
                        </span>
                      </div>
                      <span 
                        className="text-xs font-bold"
                        style={{color: hasScore ? getScoreColor(Number(score)) : 'var(--lia-text-tertiary)'}}
                      >
                        {hasScore ? `${score}` : 'N/A'}
                      </span>
                    </div>
                    <Progress 
                      value={hasScore ? Number(score) : 0} 
                      className="h-1.5 bg-lia-interactive-active" style={{['--progress-color' as string]: hasScore ? getScoreColor(Number(score)) : 'var(--lia-border-subtle)'} as React.CSSProperties}
                    />
                    <p 
                      className="text-micro mt-1.5 text-lia-text-secondary"
                     
                    >
                      {t(`components.${component.id}.description`)}
                    </p>
                  </div>
                )
              })}
            </div>
          </div>

          <div
            className="p-3 rounded-xl bg-wedo-cyan/8 border border-wedo-cyan/20"
          >
            <p 
              className="text-micro font-medium mb-1 text-lia-text-secondary"
             
            >
              {t('formulaTitle')}
            </p>
            <p 
              className="text-micro text-lia-text-secondary"
             
            >
              {t('formulaBody')}
            </p>
          </div>
        </div>

        <div 
          className="px-4 py-3 flex justify-end bg-lia-bg-secondary border-t border-lia-border-subtle rounded-b-xl"
        >
          <Button
            onClick={onClose}
            size="sm"
            className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
          >
            {t('understood')}
          </Button>
        </div>
      </div>
    </div>
  )
}
