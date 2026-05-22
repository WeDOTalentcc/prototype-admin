"use client"

import { useTranslations } from "next-intl"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { textStyles } from"@/lib/design-tokens"
import {
  Award,
  BarChart3,
  Brain,
  Calendar,
  Clock,
  Download,
  Gauge,
  History,
  Target,
  Timer,
  TrendingUp,
  Trophy,
  UserCheck,
  Users,
  X,
  XCircle,
} from"lucide-react"

interface TestHistoryModalProps {
  open: boolean
  onClose: () => void
  testName: string | null
}

export function TestHistoryModal({ open, onClose, testName }: TestHistoryModalProps) {
  const t = useTranslations('kanban')
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-lia-overlay backdrop-blur-sm">
      <div className="bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl w-full max-w-5xl max-h-[90vh] overflow-hidden animate-fadeIn">
        <div className="bg-lia-btn-primary-bg dark:bg-lia-bg-secondary p-5 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-lia-bg-primary/20 rounded-xl">
                <History className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">{t('testHistory.title')}</h2>
                <p className="text-lia-text-disabled text-sm">{testName || 'UX Design - Fundamentos'}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-lia-bg-primary/20 rounded-xl transition-colors motion-reduce:transition-none"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="p-6 dark:border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-secondary">
          <div className="bg-wedo-purple rounded-xl p-4 mb-4 text-white">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-lia-bg-primary/20 rounded-xl">
                  <Trophy className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-sm opacity-90">{t('testHistory.historicalAvgScore')}</p>
                  <div className="flex items-baseline gap-3">
                    <p className="text-base-ui font-semibold">7.4</p>
                    <span className="text-lg opacity-80">/10</span>
                    <div className="flex items-center gap-2 ml-3">
                      <Chip variant="neutral" muted className="bg-lia-bg-primary/20 text-white border-white/30">
                        <TrendingUp className="w-3 h-3 mr-1" />
                        {t('testHistory.vsPreviousMonth', { diff: '+0.3' })}
                      </Chip>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-lia-bg-primary/10 rounded-xl p-3">
                <p className="text-xs opacity-80 mb-2">{t('testHistory.evolution6Months')}</p>
                <div className="flex items-end gap-1 h-10">
                  {[6.8, 7.0, 7.1, 7.2, 7.1, 7.4].map((value, i) => (
                    <div
                      key={i}
                      className="flex-1 bg-lia-bg-primary/30 rounded-t hover:bg-lia-bg-primary/40 transition-colors motion-reduce:transition-none relative group"
                      style={{height: `${((value - 6) / 2) * 100}%`}}
                    >
                      <span className="absolute -top-5 left-1/2 -translate-x-1/2 text-xs opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none">
                        {value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-5 gap-4">
            <div className="bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="w-4 h-4 text-lia-text-primary" />
                <span className="text-xs text-lia-text-primary">{t('testHistory.totalApplications')}</span>
              </div>
              <p className="text-sm font-semibold text-lia-text-primary">2,547</p>
              <p className="text-xs text-lia-text-primary mt-1">{t('testHistory.upThisMonth', { percent: 12 })}</p>
            </div>

            <div className="bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <Target className="w-4 h-4 text-lia-text-primary" />
                <span className="text-xs text-lia-text-primary">{t('testHistory.successRate')}</span>
              </div>
              <p className="text-sm font-semibold text-lia-text-primary">78%</p>
              <p className="text-xs text-lia-text-primary mt-1">{t('testHistory.scoreAbove', { score: '7.0' })}</p>
            </div>

            <div className="bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <UserCheck className="w-4 h-4 text-lia-text-primary" />
                <span className="text-xs text-lia-text-primary">{t('testHistory.completionRate')}</span>
              </div>
              <p className="text-sm font-semibold text-lia-text-primary">92%</p>
              <p className="text-xs text-lia-text-primary mt-1">{t('testHistory.candidatesComplete')}</p>
            </div>

            <div className="bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <Timer className="w-4 h-4 text-lia-text-primary" />
                <span className="text-xs text-lia-text-primary">{t('testHistory.averageTime')}</span>
              </div>
              <p className="text-sm font-semibold text-lia-text-primary">13min</p>
              <p className="text-xs text-lia-text-primary mt-1">{t('testHistory.ofExpected', { time: '15min' })}</p>
            </div>

            <div className="bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <Gauge className="w-4 h-4 text-status-error" />
                <span className="text-xs text-lia-text-primary">{t('testHistory.perceivedDifficulty')}</span>
              </div>
              <p className="text-sm font-semibold text-lia-text-primary">6.8/10</p>
              <p className="text-xs text-lia-text-primary mt-1">{t('testHistory.mediumHigh')}</p>
            </div>
          </div>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-380px)]">
          <h3 className="text-sm font-semibold text-lia-text-primary mb-4">
            {t('testHistory.jobsUsedThisTest')}
          </h3>

          <div className="space-y-3">
            <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl p-4 border border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h4 className="font-medium text-lia-text-primary">UX Designer Sênior</h4>
                    <Chip density="relaxed" variant="neutral" muted className="dark:bg-lia-bg-tertiary">{t('testHistory.statusFinished')}</Chip>
                    <span className="text-xs text-lia-text-primary">Sodexo • São Paulo</span>
                  </div>
                  <div className="flex items-center gap-6 text-xs text-lia-text-secondary">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      Mar 2024
                    </span>
                    <span className="flex items-center gap-1">
                      <Users className="w-3 h-3" />
                      {t('testHistory.candidatesCount', { count: 45 })}
                    </span>
                    <span className="flex items-center gap-1">
                      <Target className="w-3 h-3" />
                      {t('testHistory.approvalRate', { percent: 82 })}
                    </span>
                    <span className="flex items-center gap-1">
                      <Trophy className="w-3 h-3 text-lia-text-primary" />
                      {t('testHistory.hired', { count: 3 })}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-lia-text-primary">{t('testHistory.success')}</p>
                  <p className="text-xs text-lia-text-primary">ROI: 320%</p>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                <div className="flex items-center justify-between mb-1">
                  <span className={textStyles.description}>{t('testHistory.scoreDistribution')}</span>
                  <div className="flex items-center gap-2">
                    <Chip density="relaxed" variant="neutral" muted className="bg-lia-interactive-active text-lia-text-primary dark:bg-lia-bg-elevated px-1.5">
                      <Trophy className="w-2.5 h-2.5 mr-0.5" />
                      {t('testHistory.avgScore', { score: '7.8/10' })}
                    </Chip>
                  </div>
                </div>
                <div className="flex items-end gap-0.5 h-6">
                  {[2, 3, 5, 8, 12, 10, 5].map((height, i) => (
                    <div
                      key={i}
                      className="flex-1 bg-lia-border-medium dark:bg-lia-bg-elevated rounded-t opacity-80"
                      style={{height: `${(height / 12) * 100}%`}}
                    />
                  ))}
                </div>
              </div>
            </div>

            <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl p-4 border border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h4 className="font-medium text-lia-text-primary">Product Designer</h4>
                    <Chip density="relaxed" variant="neutral" muted className="bg-lia-interactive-active text-lia-text-primary dark:bg-lia-bg-elevated">{t('testHistory.statusInProgress')}</Chip>
                    <span className="text-xs text-lia-text-primary">Nubank • Remoto</span>
                  </div>
                  <div className="flex items-center gap-6 text-xs text-lia-text-secondary">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      Nov 2024
                    </span>
                    <span className="flex items-center gap-1">
                      <Users className="w-3 h-3" />
                      {t('testHistory.candidatesCount', { count: 28 })}
                    </span>
                    <span className="flex items-center gap-1">
                      <Target className="w-3 h-3" />
                      {t('testHistory.approvalRate', { percent: 75 })}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3 text-lia-text-primary" />
                      {t('testHistory.inInterviews')}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-lia-text-primary">{t('testHistory.statusActive')}</p>
                  <p className="text-xs text-lia-text-primary">{t('testHistory.finalists', { count: 5 })}</p>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                <div className="flex items-center justify-between mb-1">
                  <span className={textStyles.description}>{t('testHistory.scoreDistribution')}</span>
                  <div className="flex items-center gap-2">
                    <Chip density="relaxed" variant="neutral" muted className="bg-lia-interactive-active text-lia-text-primary dark:bg-lia-bg-elevated px-1.5">
                      <Trophy className="w-2.5 h-2.5 mr-0.5" />
                      {t('testHistory.avgScore', { score: '7.2/10' })}
                    </Chip>
                  </div>
                </div>
                <div className="flex items-end gap-0.5 h-6">
                  {[3, 4, 6, 7, 8, 4, 2].map((height, i) => (
                    <div
                      key={i}
                      className="flex-1 bg-lia-border-medium dark:bg-lia-bg-elevated rounded-t opacity-80"
                      style={{height: `${(height / 8) * 100}%`}}
                    />
                  ))}
                </div>
              </div>
            </div>

            <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl p-4 border border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h4 className="font-medium text-lia-text-primary">UI/UX Designer</h4>
                    <Chip density="relaxed" variant="neutral" muted className="bg-lia-bg-tertiary text-lia-text-primary">{t('testHistory.statusCancelled')}</Chip>
                    <span className="text-xs text-lia-text-primary">iFood • Campinas</span>
                  </div>
                  <div className="flex items-center gap-6 text-xs text-lia-text-secondary">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      Set 2024
                    </span>
                    <span className="flex items-center gap-1">
                      <Users className="w-3 h-3" />
                      {t('testHistory.candidatesCount', { count: 18 })}
                    </span>
                    <span className="flex items-center gap-1">
                      <Target className="w-3 h-3" />
                      {t('testHistory.approvalRate', { percent: 65 })}
                    </span>
                    <span className="flex items-center gap-1">
                      <XCircle className="w-3 h-3 text-lia-text-secondary" />
                      {t('testHistory.jobCancelled')}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-lia-text-secondary">{t('testHistory.statusClosed')}</p>
                  <p className="text-xs text-lia-text-primary">{t('testHistory.noHire')}</p>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                <div className="flex items-center justify-between mb-1">
                  <span className={textStyles.description}>{t('testHistory.scoreDistribution')}</span>
                  <div className="flex items-center gap-2">
                    <Chip density="relaxed" variant="neutral" muted className="bg-lia-interactive-active text-lia-text-primary dark:bg-lia-bg-elevated px-1.5">
                      <Trophy className="w-2.5 h-2.5 mr-0.5" />
                      {t('testHistory.avgScore', { score: '6.5/10' })}
                    </Chip>
                  </div>
                </div>
                <div className="flex items-end gap-0.5 h-6">
                  {[4, 5, 6, 5, 3, 2, 1].map((height, i) => (
                    <div
                      key={i}
                      className="flex-1 bg-lia-border-medium rounded-t opacity-60"
                      style={{height: `${(height / 6) * 100}%`}}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 bg-lia-bg-tertiary dark:bg-lia-bg-secondary/20 rounded-xl p-4 border border-lia-border-default dark:border-lia-border-subtle">
            <div className="flex items-start gap-3">
              <Brain className="w-5 h-5 text-wedo-cyan mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-lia-text-primary mb-2">
                  {t('testHistory.liaInsights')}
                </h4>
                <ul className="space-y-1 text-xs text-lia-text-primary">
                  <li>• {t('testHistory.insight1')}</li>
                  <li>• {t('testHistory.insight2')}</li>
                  <li>• {t('testHistory.insight3')}</li>
                  <li>• {t('testHistory.insight4')}</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle p-4 bg-lia-bg-secondary dark:bg-lia-bg-secondary">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 text-xs text-lia-text-primary">
              <span className="flex items-center gap-1">
                <TrendingUp className="w-3 h-3" />
                {t('testHistory.aboveAveragePerformance')}
              </span>
              <span className="flex items-center gap-1">
                <Award className="w-3 h-3" />
                {t('testHistory.top10Tests')}
              </span>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={onClose}>
                {t('testHistory.close')}
              </Button>
              <Button className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:hover:bg-lia-interactive-active">
                <Download className="w-4 h-4 mr-2" />
                {t('testHistory.exportReport')}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
