"use client"

import { X, Code, Clock, Trophy, Users, CheckCircle, Loader2, AlertCircle, TrendingUp, TrendingDown, Minus } from "lucide-react"
import { getPercentageScoreVar } from "@/lib/score-utils"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { useTranslations } from "next-intl"
import { useLocale } from "next-intl"

interface TestCategory {
  name: string
  score: number
  avgScore: number
}

interface TestData {
  status?: TestStatus
  score?: number
  duration?: number
  maxDuration?: number
  completedAt?: string
  categories?: TestCategory[]
  averageScore?: number
}

interface TechnicalTestModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: Record<string, unknown>
}

type TestStatus = 'pending' | 'in_progress' | 'completed'

const STATUS_CONFIG = {
  pending: {
    labelKey: 'statusPending' as const,
    icon: AlertCircle,
    color: 'var(--lia-text-tertiary)',
    bgColor: 'var(--lia-bg-tertiary)',
    borderColor: 'var(--lia-border-default)'
  },
  in_progress: {
    labelKey: 'statusInProgress' as const,
    icon: Loader2,
    color: 'var(--status-warning)',
    bgColor: 'var(--status-warning-bg)',
    borderColor: 'var(--status-warning-border)'
  },
  completed: {
    labelKey: 'statusCompleted' as const,
    icon: CheckCircle,
    color: 'var(--status-success)',
    bgColor: 'var(--status-success-bg)',
    borderColor: 'var(--status-success-bg-15)'
  }
}

export function TechnicalTestModal({ isOpen, onClose, candidate }: TechnicalTestModalProps) {
  const t = useTranslations('candidates.technicalTestModal')
  const locale = useLocale()
  if (!isOpen) return null

  const testData: TestData = (candidate?.technicalTest as TestData) ?? {
    status: 'completed',
    score: 78,
    duration: 72,
    maxDuration: 90,
    completedAt: '2024-01-15',
    categories: [
      { name: 'Design System', score: 95, avgScore: 72 },
      { name: 'Prototipagem', score: 90, avgScore: 68 },
      { name: 'User Research', score: 85, avgScore: 75 },
      { name: 'Ferramentas', score: 88, avgScore: 70 },
      { name: 'Metodologias Ágeis', score: 82, avgScore: 65 },
    ],
    averageScore: 72
  }

  const status: TestStatus = testData.status ?? 'pending'
  const statusConfig = STATUS_CONFIG[status]
  const StatusIcon = statusConfig.icon

  const getScoreColor = getPercentageScoreVar

  const getComparisonIcon = (candidateScore: number, avgScore: number) => {
    const diff = candidateScore - avgScore
    if (diff > 5) return <TrendingUp className="w-3 h-3 text-status-success"  />
    if (diff < -5) return <TrendingDown className="w-3 h-3 text-status-error"  />
    return <Minus className="w-3 h-3 text-lia-text-muted" />
  }

  const getComparisonLabel = (candidateScore: number, avgScore: number) => {
    const diff = candidateScore - avgScore
    if (diff > 0) return t('aboveAverage', { diff })
    if (diff < 0) return t('belowAverage', { diff })
    return t('atAverage')
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-lia-overlay"
      onClick={(e) => e.target === e.currentTarget && onClose()}
      data-testid="technical-test-modal"
    >
      <div
        className="w-full max-w-lg max-h-[85vh] overflow-hidden flex flex-col border border-lia-border-subtle bg-lia-bg-secondary rounded-xl"
      >
        <div 
          className="flex items-center justify-between px-4 py-3 border-b border-b-lia-border-subtle"
        >
          <div className="flex items-center gap-2">
            <div
              className="w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0 bg-wedo-cyan/12"
            >
              <Code className="w-4 h-4 text-lia-text-secondary" />
            </div>
            <div>
              <h2 
                className="text-base-ui font-semibold text-lia-text-primary"
               
              >
                {t('title')}
              </h2>
              <p 
                className="text-xs text-lia-text-secondary"
               
               aria-live="polite" aria-atomic="true">
                {String(candidate?.name ?? t('defaultCandidate'))}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="h-7 w-7 p-0 flex items-center justify-center transition-colors motion-reduce:transition-none hover:bg-lia-interactive-hover rounded-full text-lia-text-tertiary"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4 bg-[var(--lia-bg-secondary)]">
          <div 
            className="flex items-center justify-between p-3 rounded-md mb-4"
            style={{backgroundColor: statusConfig.bgColor, border: `1px solid ${statusConfig.borderColor}`}}
          >
            <div className="flex items-center gap-2" role="status" aria-live="polite" aria-label="Carregando...">
              <StatusIcon 
                className={`w-4 h-4 ${status === 'in_progress' ? 'animate-spin motion-reduce:animate-none' : ''}`} 
                style={{color: statusConfig.color}} 
              />
              <span 
                className="text-xs font-medium"
                style={{color: statusConfig.color}}
              >
                {t(statusConfig.labelKey)}
              </span>
            </div>
            {testData.completedAt && status === 'completed' && (
              <span 
                className="text-micro text-lia-text-secondary"
              >
                {t('completedAt', { date: new Date(testData.completedAt).toLocaleDateString(locale) })}
              </span>
            )}
          </div>

          {status === 'completed' && (
            <>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="p-3 rounded-xl border border-lia-border-subtle">
                  <div className="flex items-center gap-2 mb-1">
                    <Trophy className="w-3.5 h-3.5 text-lia-text-secondary" />
                    <span className="text-micro text-lia-text-secondary">
                      {t('overallScore')}
                    </span>
                  </div>
                  <span 
                    className="text-2xl font-semibold"
                    style={{color: getScoreColor(testData.score ?? 0)}}
                  >
                    {testData.score}
                  </span>
                  <span className="text-sm ml-1 text-lia-text-disabled">
                    / 100
                  </span>
                </div>

                <div className="p-3 rounded-xl border border-lia-border-subtle">
                  <div className="flex items-center gap-2 mb-1">
                    <Clock className="w-3.5 h-3.5 text-lia-text-secondary" />
                    <span className="text-micro text-lia-text-secondary">
                      {t('completionTime')}
                    </span>
                  </div>
                  <span className="text-2xl font-semibold text-lia-text-primary">
                    {testData.duration}
                  </span>
                  <span className="text-sm ml-1 text-lia-text-disabled">
                    / {testData.maxDuration} min
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2 p-3 rounded-xl mb-4 bg-wedo-cyan/[.08] border border-wedo-cyan/20">
                <Users className="w-4 h-4 text-lia-text-secondary" />
                <span 
                  className="text-xs text-lia-text-secondary"
                  aria-live="polite" aria-atomic="true">
                  {t('comparison')}
                </span>
                <span 
                  className={`text-xs font-semibold ml-auto ${(testData.score ?? 0) >= (testData.averageScore ?? 0) ? 'text-status-success' : 'text-status-error'}`}
                >
                  {getComparisonLabel(testData.score ?? 0, testData.averageScore ?? 0)}
                </span>
              </div>

              <div className="mb-4">
                <p className="text-xs font-semibold mb-3 text-lia-text-primary">
                  {t('categoryBreakdown')}
                </p>

                <div className="space-y-2.5">
                  {testData.categories?.map((category: TestCategory, index: number) => (
                    <div 
                      key={index}
                      className="p-3 rounded-xl border border-lia-border-subtle"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-medium text-lia-text-primary">
                          {category.name}
                        </span>

                        <div className="flex items-center gap-2">
                          {getComparisonIcon(category.score, category.avgScore)}
                          <span 
                            className="text-xs font-bold"
                            style={{color: getScoreColor(category.score)}}
                          >
                            {category.score}
                          </span>
                        </div>
                      </div>
                      <div className="relative">
                        <Progress 
                          value={category.score} 
                          className="h-1.5 bg-lia-interactive-active"
                        />
                        <div 
                          className="absolute top-0 h-1.5 rounded-full opacity-30 bg-lia-border-medium" style={{width: `${category.avgScore}%`}}
                        />
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <span 
                          className="text-micro text-lia-text-secondary"
                          aria-live="polite" aria-atomic="true">
                          {t('candidateAvg', { score: category.avgScore })}
                        </span>
                        <span 
                          className={`text-micro ${category.score >= category.avgScore ? 'text-status-success' : 'text-status-error'}`}
                        >
                          {category.score >= category.avgScore ? '+' : ''}{((category.score ?? 0) - (category.avgScore ?? 0))}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {status === 'pending' && (
            <div 
              className="flex flex-col items-center justify-center py-8 text-lia-text-disabled"
            >
              <AlertCircle className="w-12 h-12 mb-3" />
              <p 
                className="text-xs font-medium mb-1 text-lia-text-tertiary"
               
              >
                {t('notStarted')}
              </p>
              <p 
                className="text-micro text-center text-lia-text-muted"
                aria-live="polite" aria-atomic="true">
                {t('notStartedDesc')}
              </p>
            </div>
          )}

          {status === 'in_progress' && (
            <div 
              className="flex flex-col items-center justify-center py-8 text-status-warning"
              
            >
              <Loader2 className="w-12 h-12 mb-3 animate-spin motion-reduce:animate-none" />
              <p 
                className="text-xs font-medium mb-1 text-lia-text-tertiary"
               
              >
                {t('inProgress')}
              </p>
              <p 
                className="text-micro text-center text-lia-text-muted"
               
               aria-live="polite" aria-atomic="true">
                {t('inProgressDesc')}
              </p>
            </div>
          )}
        </div>

        <div 
          className="px-4 py-3 flex justify-end border-t border-t-lia-border-subtle"
        >
          <Button
            onClick={onClose}
            size="sm"
            className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
           
          >
            {t('close')}
          </Button>
        </div>
      </div>
    </div>
  )
}
