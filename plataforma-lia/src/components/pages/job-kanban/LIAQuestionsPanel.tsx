"use client"

import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { BarChart3, Brain, RefreshCw, Target, Wand2, X } from"lucide-react"
import { useTranslations } from "next-intl"

interface LIAQuestionsPanelProps {
  open: boolean
  onClose: () => void
}

export function LIAQuestionsPanel({ open, onClose }: LIAQuestionsPanelProps) {
  const t = useTranslations('kanban')
  if (!open) return null

  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm"
        onClick={onClose}
      />

      <div className="fixed right-0 top-0 h-full z-50 w-[450px] bg-lia-bg-primary dark:bg-lia-bg-primary">
        <div className="bg-wedo-purple p-4 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-lia-bg-primary/20 rounded-xl">
                <Wand2 className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-lg font-semibold">{t('liaQuestionSuggestions')}</h2>
                <p className="text-lia-text-muted text-xs">{t('basedOnJobProfile')}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 hover:bg-lia-bg-primary/20 rounded-xl transition-colors motion-reduce:transition-none"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="p-4 overflow-y-auto h-[calc(100vh-80px)]">
          <div className="mb-3">
            <div className="flex items-center gap-2 mb-1">
              <Brain className="w-4 h-4 text-wedo-cyan" />
              <h3 className="text-sm font-semibold text-lia-text-primary">
                {t('recommendedUXQuestions')}
              </h3>
            </div>
            <p className="text-xs text-lia-text-secondary">
              {t('clickReplaceInstruction')}
            </p>
          </div>

          <div className="space-y-3">
            <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl p-4 border border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-medium dark:hover:border-lia-border-medium cursor-pointer transition-colors motion-reduce:transition-none group">
              <div className="flex items-start justify-between mb-2">
                <h4 className="text-sm font-medium text-lia-text-primary group-hover:text-lia-text-primary">
                  {t('questionUX1')}
                </h4>
                <div className="flex items-center gap-2">
                  <Chip density="relaxed" variant="neutral" muted className="bg-lia-interactive-active text-lia-text-primary dark:bg-lia-bg-elevated">{t('recommendedBadge')}</Chip>
                  <Chip density="relaxed" variant="neutral" muted className="bg-lia-bg-tertiary text-lia-text-primary">2 min</Chip>
                </div>
              </div>
              <div className="space-y-1 ml-2 text-xs text-lia-text-secondary">
                <p>{t('questionUX1optA')}</p>
                <p>{t('questionUX1optB')}</p>
                <p className="text-lia-text-primary font-bold">{t('questionUX1optC')}</p>
                <p>{t('questionUX1optD')}</p>
              </div>
              <div className="mt-3 flex items-center justify-between">
                <div className="flex items-center gap-4 text-xs text-lia-text-primary">
                  <span className="flex items-center gap-1">
                    <Target className="w-3 h-3" />
                    {t('evaluatesResearchMethods')}
                  </span>
                  <span className="flex items-center gap-1">
                    <BarChart3 className="w-3 h-3" />
                    {t('difficultyMedium')}
                  </span>
                </div>
                <Button
                  size="sm"
                  className="text-xs bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover text-white"
                  onClick={onClose}
                >
                  <RefreshCw className="w-3 h-3 mr-1" />
                  {t('replaceAction')}
                </Button>
              </div>
            </div>

            <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl p-4 border border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-medium dark:hover:border-lia-border-medium cursor-pointer transition-colors motion-reduce:transition-none group">
              <div className="flex items-start justify-between mb-2">
                <h4 className="text-sm font-medium text-lia-text-primary group-hover:text-lia-text-primary">
                  {t('questionUX2')}
                </h4>
                <div className="flex items-center gap-2">
                  <Chip density="relaxed" variant="neutral" muted className="dark:bg-lia-bg-tertiary">{t('highRelevanceBadge')}</Chip>
                  <Chip density="relaxed" variant="neutral" muted className="bg-lia-bg-tertiary text-lia-text-primary">3 min</Chip>
                </div>
              </div>
              <div className="space-y-1 ml-2 text-xs text-lia-text-secondary">
                <p className="text-lia-text-primary font-bold">{t('questionUX2optA')}</p>
                <p>{t('questionUX2optB')}</p>
                <p>{t('questionUX2optC')}</p>
                <p>{t('questionUX2optD')}</p>
              </div>
              <div className="mt-3 flex items-center justify-between">
                <div className="flex items-center gap-4 text-xs text-lia-text-primary">
                  <span className="flex items-center gap-1">
                    <Target className="w-3 h-3" />
                    {t('evaluatesPrioritization')}
                  </span>
                  <span className="flex items-center gap-1">
                    <BarChart3 className="w-3 h-3" />
                    {t('difficultyEasy')}
                  </span>
                </div>
                <Button
                  size="sm"
                  className="text-xs bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover text-white"
                  onClick={onClose}
                >
                  <RefreshCw className="w-3 h-3 mr-1" />
                  {t('replaceAction')}
                </Button>
              </div>
            </div>

            <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl p-4 border border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-medium dark:hover:border-lia-border-medium cursor-pointer transition-colors motion-reduce:transition-none group">
              <div className="flex items-start justify-between mb-2">
                <h4 className="text-sm font-medium text-lia-text-primary group-hover:text-lia-text-primary">
                  {t('questionUX3')}
                </h4>
                <div className="flex items-center gap-2">
                  <Chip density="relaxed" variant="neutral" muted className="bg-lia-interactive-active text-lia-text-primary dark:bg-lia-bg-elevated">{t('conceptualBadge')}</Chip>
                  <Chip density="relaxed" variant="neutral" muted className="bg-lia-bg-tertiary text-lia-text-primary">2 min</Chip>
                </div>
              </div>
              <div className="space-y-1 ml-2 text-xs text-lia-text-secondary">
                <p>{t('questionUX3optA')}</p>
                <p className="text-lia-text-primary font-bold">{t('questionUX3optB')}</p>
                <p>{t('questionUX3optC')}</p>
                <p>{t('questionUX3optD')}</p>
              </div>
              <div className="mt-3 flex items-center justify-between">
                <div className="flex items-center gap-4 text-xs text-lia-text-primary">
                  <span className="flex items-center gap-1">
                    <Target className="w-3 h-3" />
                    {t('evaluatesTechnicalKnowledge')}
                  </span>
                  <span className="flex items-center gap-1">
                    <BarChart3 className="w-3 h-3" />
                    {t('difficultyMedium')}
                  </span>
                </div>
                <Button
                  size="sm"
                  className="text-xs bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover text-white"
                  onClick={onClose}
                >
                  <RefreshCw className="w-3 h-3 mr-1" />
                  {t('replaceAction')}
                </Button>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-lia-border-subtle dark:border-lia-border-subtle">
              <Button variant="outline" className="w-full text-sm">
                <Brain className="w-4 h-4 mr-2 text-wedo-cyan" />
                {t('generateMore')}
              </Button>
            </div>
          </div>
        </div>

        <div className="absolute bottom-0 left-0 right-0 border-t border-lia-border-subtle dark:border-lia-border-subtle p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary">
          <div className="flex items-center justify-between">
            <p className="text-xs text-lia-text-primary">
              <Brain className="w-3 h-3 inline mr-1 text-wedo-cyan" />
              {t('basedOnTestsCount')}
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={onClose}
              className="text-xs"
            >
              {t('closePanel')}
            </Button>
          </div>
        </div>
      </div>
    </>
  )
}
