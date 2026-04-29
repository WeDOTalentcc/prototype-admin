'use client'

import React from 'react'
import { Brain } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { Button } from '@/components/ui/button'

interface LiaAnalysisCardProps {
  isEditing: boolean
  website?: string
  isLiaAnalyzing: boolean
  liaAnalysisProgress: number
  liaAnalysisStep: string | null
  handleLiaAnalysis: () => void
}

export function LiaAnalysisCard({
  isEditing,
  website,
  isLiaAnalyzing,
  liaAnalysisProgress,
  liaAnalysisStep,
  handleLiaAnalysis,
}: LiaAnalysisCardProps) {
  const t = useTranslations('settings.minhaEmpresa.liaAnalysis')
  return (
    <div className="rounded-xl border border-lia-border-default dark:border-lia-border-default bg-gradient-to-r from-lia-bg-secondary dark:from-lia-bg-primary to-transparent p-5">
      <div className="flex items-start gap-4">
        <div
          className="w-12 h-12 rounded-md flex items-center justify-center flex-shrink-0 bg-lia-btn-primary-bg"
        >
          <Brain className="w-6 h-6 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-lia-text-primary mb-1">
            {t('title')}
          </h4>
          <p className="text-xs text-lia-text-secondary mb-3 leading-relaxed">
            {t('description')}
          </p>

          {isLiaAnalyzing ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-lia-text-primary">
                  {liaAnalysisStep || t('starting')}
                </span>
                <span className="font-bold tabular-nums text-lia-text-primary">
                  {Math.round(liaAnalysisProgress)}%
                </span>
              </div>
              <div className="w-full bg-lia-interactive-active rounded-full h-2 overflow-hidden">
                <div
                  className="h-2 rounded-full transition-[width,height] duration-500 bg-lia-btn-primary-bg" style={{width: `${liaAnalysisProgress}%`}}
                />
              </div>
            </div>
          ) : (
            <Button
              onClick={handleLiaAnalysis}
              disabled={!isEditing || !website}
              className="gap-2 text-white hover:opacity-90 transition-opacity motion-reduce:transition-none text-xs bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active"
            >
              <Brain className="w-4 h-4 text-wedo-cyan" />
              {t('analyzeButton')}
            </Button>
          )}

          {!isLiaAnalyzing && (!isEditing || !website) && (
            <p className="text-micro text-status-warning mt-2">
              {!isEditing
                ? t('enableEditingHint')
                : t('enableWebsiteHint')
              }
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
