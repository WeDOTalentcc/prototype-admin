"use client"

import { useTranslations } from "next-intl"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { textStyles } from"@/lib/design-tokens"
import {
  BarChart3,
  BookOpen,
  Brain,
  Building,
  CheckCircle,
  Code,
  Eye,
  Gauge,
  Globe,
  History,
  Library,
  Pencil,
  Plus,
  RefreshCw,
  Star,
  Target,
  Timer,
  TrendingUp,
  Trophy,
  UserCheck,
  Users,
  X,
} from"lucide-react"

interface TestLibraryModalProps {
  open: boolean
  onClose: () => void
  onTestPreview: () => void
  onTestHistoryOpen: (testName: string) => void
}

export function TestLibraryModal({ open, onClose, onTestPreview, onTestHistoryOpen }: TestLibraryModalProps) {
  const t = useTranslations('kanban')
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-lia-overlay backdrop-blur-sm">
      <div className="bg-lia-bg-primary rounded-xl w-full max-w-6xl max-h-[90vh] overflow-hidden animate-fadeIn">
        <div className="bg-wedo-purple p-5 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-lia-bg-primary/20 rounded-xl">
                <Library className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">{t('testLibrary.title')}</h2>
                <p className="text-lia-text-muted text-sm">{t('testLibrary.subtitle')}</p>
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

        <div className="flex h-[calc(90vh-100px)]">
          <div className="w-64 bg-lia-bg-secondary p-4 border-r border-lia-border-subtle overflow-y-auto">
            <h3 className="text-xs font-semibold text-lia-text-primary uppercase mb-3">{t('testLibrary.categories')}</h3>
            <div className="space-y-1">
              {[
                { icon: <Code className="w-4 h-4" />, label: t('testLibrary.catDevelopment'), count: 24, color: 'text-lia-text-primary' },
                { icon: <Pencil className="w-4 h-4" />, label: t('testLibrary.catDesignUX'), count: 18, color: 'text-lia-text-primary', active: true },
                { icon: <BarChart3 className="w-4 h-4" />, label: t('testLibrary.catDataAnalytics'), count: 15, color: 'text-lia-text-primary' },
                { icon: <Users className="w-4 h-4" />, label: t('testLibrary.catManagement'), count: 12, color: 'text-lia-text-primary' },
                { icon: <Target className="w-4 h-4" />, label: t('testLibrary.catMarketingSales'), count: 20, color: 'text-lia-text-primary' },
                { icon: <Building className="w-4 h-4" />, label: t('testLibrary.catAdministrative'), count: 10, color: 'text-lia-text-secondary' },
                { icon: <Globe className="w-4 h-4" />, label: t('testLibrary.catLanguages'), count: 8, color: 'text-lia-text-primary' },
                { icon: <Brain className="w-4 h-4 text-wedo-cyan-text" />, label: t('testLibrary.catSoftSkills'), count: 14, color: 'text-lia-text-primary' }
              ].map((category) => (
                <button
                  key={category.label}
                  className={`w-full flex items-center justify-between p-2.5 rounded-md transition-colors motion-reduce:transition-none ${
                    category.active
                      ? 'bg-lia-bg-primary border border-lia-border-default'
                      : 'hover:bg-lia-bg-primary hover:bg-lia-interactive-hover'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className={category.color}>{category.icon}</span>
                    <span className="text-sm font-medium text-lia-text-primary">{category.label}</span>
                  </div>
                  <Chip density="relaxed" variant="neutral" muted className="bg-lia-bg-tertiary text-lia-text-secondary">
                    {category.count}
                  </Chip>
                </button>
              ))}
            </div>

            <div className="mt-6 pt-6 border-t border-lia-border-subtle">
              <h3 className="text-xs font-semibold text-lia-text-primary uppercase mb-3">{t('testLibrary.filtersTitle')}</h3>
              <div className="space-y-3">
                <div>
                  <label className="text-xs text-lia-text-secondary">{t('testLibrary.level')}</label>
                  <select className="w-full mt-1 p-2 text-sm border border-lia-border-subtle rounded-xl bg-lia-bg-primary">
                    <option>{t('testLibrary.levelAll')}</option>
                    <option>{t('testLibrary.levelJunior')}</option>
                    <option>{t('testLibrary.levelMid')}</option>
                    <option>{t('testLibrary.levelSenior')}</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-lia-text-secondary">{t('testLibrary.duration')}</label>
                  <select className="w-full mt-1 p-2 text-sm border border-lia-border-subtle rounded-xl bg-lia-bg-primary">
                    <option>{t('testLibrary.durationAny')}</option>
                    <option>5-10 min</option>
                    <option>10-20 min</option>
                    <option>20-30 min</option>
                    <option>30+ min</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          <div className="flex-1 p-6 overflow-y-auto">
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-lia-text-primary mb-1">
                {t('testLibrary.designUXTests')}
              </h3>
              <p className="text-sm text-lia-text-secondary">
                {t('testLibrary.testsAvailableApproval', { count: 18, percent: 85 })}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-lia-bg-secondary rounded-xl border border-lia-border-subtle hover:border-lia-border-medium transition-colors motion-reduce:transition-none">
                <div className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="font-medium text-lia-text-primary mb-1">
                        {t('testLibrary.test1Name')}
                      </h4>
                      <p className="text-xs text-lia-text-secondary">
                        {t('testLibrary.test1Desc')}
                      </p>
                    </div>
                    <Chip density="relaxed" variant="neutral" muted >{t('testLibrary.badgePopular')}</Chip>
                  </div>

                  <div className="bg-lia-bg-secondary rounded-xl p-3 mb-3">
                    <div className="flex items-center justify-between mb-3 pb-3">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-wedo-purple/15 dark:bg-wedo-purple/30 rounded-md">
                          <Trophy className="w-5 h-5 text-lia-text-primary" />
                        </div>
                        <div>
                          <p className="text-xs text-lia-text-primary">{t('testLibrary.overallAvgScore')}</p>
                          <div className="flex items-baseline gap-2">
                            <p className="text-2xl font-semibold text-lia-text-primary">7.4</p>
                            <span className="text-xs text-lia-text-primary">/10</span>
                            <Chip density="relaxed" variant="neutral" muted >
                              <TrendingUp className="w-2.5 h-2.5 mr-0.5" />
                              +0.3
                            </Chip>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={textStyles.description}>{t('testLibrary.basedOn')}</p>
                        <p className="text-xs font-medium text-lia-text-primary">{t('testLibrary.testsCount', { count: '2.5k' })}</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="flex items-center gap-2">
                        <div className="p-1.5 bg-lia-interactive-active rounded-md">
                          <Target className="w-3.5 h-3.5 text-lia-text-primary" />
                        </div>
                        <div>
                          <p className={textStyles.description}>{t('testLibrary.successRateLabel')}</p>
                          <p className="text-sm font-bold text-lia-text-primary">78%</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="p-1.5 bg-lia-interactive-active rounded-md">
                          <Gauge className="w-3.5 h-3.5 text-lia-text-primary" />
                        </div>
                        <div>
                          <p className={textStyles.description}>{t('testLibrary.realDifficulty')}</p>
                          <p className="text-sm font-bold text-lia-text-primary">{t('testLibrary.mediumPlus')}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="p-1.5 bg-lia-interactive-active rounded-md">
                          <UserCheck className="w-3.5 h-3.5 text-lia-text-primary" />
                        </div>
                        <div>
                          <p className={textStyles.description}>{t('testLibrary.completionLabel')}</p>
                          <p className="text-sm font-bold text-lia-text-primary">92%</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="p-1.5 bg-lia-interactive-active rounded-md">
                          <Timer className="w-3.5 h-3.5 text-lia-text-primary" />
                        </div>
                        <div>
                          <p className={textStyles.description}>{t('testLibrary.avgTimeLabel')}</p>
                          <p className="text-sm font-bold text-lia-text-primary">13min</p>
                        </div>
                      </div>
                    </div>

                    <div className="mt-3 pt-3 border-t border-lia-border-subtle">
                      <p className={`${textStyles.description} mb-2`}>{t('testLibrary.scoreDistribution')}</p>
                      <div className="flex items-end gap-1 h-8">
                        <div className="flex-1 bg-status-error rounded-t" title="0-40%: 5%"></div>
                        <div className="flex-1 bg-lia-text-secondary rounded-t" title="40-60%: 15%"></div>
                        <div className="flex-1 bg-lia-text-secondary rounded-t" title="60-80%: 35%"></div>
                        <div className="flex-1 bg-lia-border-medium rounded-t" title="80-100%: 45%"></div>
                      </div>
                      <div className="flex justify-between mt-1">
                        <span className={textStyles.bodySmall}>0%</span>
                        <span className={textStyles.bodySmall}>100%</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2 mb-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary">{t('testLibrary.questionsLabel')}</span>
                      <span className="font-medium">{t('testLibrary.questionsCount', { count: 5 })}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary">{t('testLibrary.totalTimeLabel')}</span>
                      <span className="font-medium">{t('testLibrary.minutesValue', { count: 15 })}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary">{t('testLibrary.levelLabel')}</span>
                      <Chip density="relaxed" variant="neutral" muted className="bg-lia-interactive-active text-lia-text-primary">{t('testLibrary.levelMid')}</Chip>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-lia-border-subtle">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="flex -space-x-1">
                          <div className="w-5 h-5 rounded-full bg-lia-border-medium flex items-center justify-center">
                            <CheckCircle className="w-3 h-3 text-white" />
                          </div>
                        </div>
                        <span className={textStyles.description}>{t('testLibrary.usesCount', { count: '2.5k' })}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Star className="w-3 h-3 text-lia-text-secondary fill-lia-text-tertiary" />
                        <span className="text-xs font-medium">4.8</span>
                      </div>
                    </div>
                    <div className="flex gap-1.5">
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 text-xs"
                        onClick={onTestPreview}
                      >
                        <Eye className="w-3 h-3 mr-1" />
                        {t('testLibrary.view')}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 text-xs"
                        onClick={() => onTestHistoryOpen('UX Design - Fundamentos')}
                      >
                        <History className="w-3 h-3 mr-1" />
                        {t('testLibrary.history')}
                      </Button>
                      <Button
                        size="sm"
                        className="flex-1 text-xs bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
                        onClick={onClose}
                      >
                        <RefreshCw className="w-3 h-3 mr-1" />
                        {t('testLibrary.use')}
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-lia-bg-secondary rounded-xl border border-lia-border-subtle hover:border-lia-border-medium transition-colors motion-reduce:transition-none">
                <div className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="font-medium text-lia-text-primary mb-1">
                        {t('testLibrary.test2Name')}
                      </h4>
                      <p className="text-xs text-lia-text-secondary">
                        {t('testLibrary.test2Desc')}
                      </p>
                    </div>
                    <Chip density="relaxed" variant="neutral" muted className="bg-lia-interactive-active text-lia-text-primary">{t('testLibrary.badgeNew')}</Chip>
                  </div>

                  <div className="space-y-2 mb-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary">{t('testLibrary.questionsLabel')}</span>
                      <span className="font-medium">{t('testLibrary.questionsCount', { count: 7 })}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary">{t('testLibrary.totalTimeLabel')}</span>
                      <span className="font-medium">{t('testLibrary.minutesValue', { count: 20 })}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary">{t('testLibrary.levelLabel')}</span>
                      <Chip density="relaxed" variant="neutral" muted className="bg-lia-border-default text-lia-text-primary">{t('testLibrary.levelSenior')}</Chip>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-lia-border-subtle">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="flex -space-x-1">
                          <div className="w-5 h-5 rounded-full bg-lia-border-medium flex items-center justify-center">
                            <CheckCircle className="w-3 h-3 text-white" />
                          </div>
                        </div>
                        <span className={textStyles.description}>{t('testLibrary.usesCount', { count: '850' })}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Star className="w-3 h-3 text-lia-text-secondary fill-lia-text-tertiary" />
                        <span className="text-xs font-medium">4.9</span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 text-xs"
                        onClick={onTestPreview}
                      >
                        <Eye className="w-3 h-3 mr-1" />
                        {t('testLibrary.viewFull')}
                      </Button>
                      <Button
                        size="sm"
                        className="flex-1 text-xs bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
                        onClick={onClose}
                      >
                        <RefreshCw className="w-3 h-3 mr-1" />
                        {t('testLibrary.useThis')}
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-lia-bg-secondary rounded-xl border border-lia-border-subtle hover:border-lia-border-medium transition-colors motion-reduce:transition-none">
                <div className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="font-medium text-lia-text-primary mb-1">
                        {t('testLibrary.test3Name')}
                      </h4>
                      <p className="text-xs text-lia-text-secondary">
                        {t('testLibrary.test3Desc')}
                      </p>
                    </div>
                    <Chip density="relaxed" variant="neutral" muted className="bg-lia-interactive-active text-lia-text-primary">{t('testLibrary.badgeRecommended')}</Chip>
                  </div>

                  <div className="space-y-2 mb-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary">{t('testLibrary.questionsLabel')}</span>
                      <span className="font-medium">{t('testLibrary.questionsCount', { count: 6 })}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary">{t('testLibrary.totalTimeLabel')}</span>
                      <span className="font-medium">{t('testLibrary.minutesValue', { count: 18 })}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary">{t('testLibrary.levelLabel')}</span>
                      <Chip density="relaxed" variant="neutral" muted className="bg-lia-interactive-active text-lia-text-primary">{t('testLibrary.levelMid')}</Chip>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-lia-border-subtle">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="flex -space-x-1">
                          <div className="w-5 h-5 rounded-full bg-lia-border-medium flex items-center justify-center">
                            <CheckCircle className="w-3 h-3 text-white" />
                          </div>
                        </div>
                        <span className={textStyles.description}>{t('testLibrary.usesCount', { count: '1.2k' })}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Star className="w-3 h-3 text-lia-text-secondary fill-lia-text-tertiary" />
                        <span className="text-xs font-medium">4.7</span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 text-xs"
                        onClick={onTestPreview}
                      >
                        <Eye className="w-3 h-3 mr-1" />
                        {t('testLibrary.viewFull')}
                      </Button>
                      <Button
                        size="sm"
                        className="flex-1 text-xs bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
                        onClick={onClose}
                      >
                        <RefreshCw className="w-3 h-3 mr-1" />
                        {t('testLibrary.useThis')}
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-lia-bg-secondary rounded-xl border border-lia-border-subtle hover:border-lia-border-medium transition-colors motion-reduce:transition-none">
                <div className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="font-medium text-lia-text-primary mb-1">
                        {t('testLibrary.test4Name')}
                      </h4>
                      <p className="text-xs text-lia-text-secondary">
                        {t('testLibrary.test4Desc')}
                      </p>
                    </div>
                    <Chip density="relaxed" variant="neutral" muted className="bg-lia-bg-tertiary text-lia-text-primary">{t('testLibrary.badgeTechnical')}</Chip>
                  </div>

                  <div className="space-y-2 mb-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary">{t('testLibrary.questionsLabel')}</span>
                      <span className="font-medium">{t('testLibrary.questionsCount', { count: 4 })}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary">{t('testLibrary.totalTimeLabel')}</span>
                      <span className="font-medium">{t('testLibrary.minutesValue', { count: 12 })}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary">{t('testLibrary.levelLabel')}</span>
                      <Chip density="relaxed" variant="neutral" muted >{t('testLibrary.levelJunior')}</Chip>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-lia-border-subtle">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="flex -space-x-1">
                          <div className="w-5 h-5 rounded-full bg-lia-border-medium flex items-center justify-center">
                            <CheckCircle className="w-3 h-3 text-white" />
                          </div>
                        </div>
                        <span className={textStyles.description}>{t('testLibrary.usesCount', { count: '3.1k' })}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Star className="w-3 h-3 text-lia-text-secondary fill-lia-text-tertiary" />
                        <span className="text-xs font-medium">4.6</span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 text-xs"
                        onClick={onTestPreview}
                      >
                        <Eye className="w-3 h-3 mr-1" />
                        {t('testLibrary.viewFull')}
                      </Button>
                      <Button
                        size="sm"
                        className="flex-1 text-xs bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
                        onClick={onClose}
                      >
                        <RefreshCw className="w-3 h-3 mr-1" />
                        {t('testLibrary.useThis')}
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 text-center">
              <Button variant="outline">
                <Plus className="w-4 h-4 mr-2" />
                {t('testLibrary.loadMoreTests')}
              </Button>
            </div>
          </div>
        </div>

        <div className="border-t border-lia-border-subtle p-4 bg-lia-bg-secondary">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 text-xs text-lia-text-primary">
              <span className="flex items-center gap-1">
                <BookOpen className="w-3 h-3" />
                {t('testLibrary.testsAvailable', { count: 121 })}
              </span>
              <span className="flex items-center gap-1">
                <Users className="w-3 h-3" />
                {t('testLibrary.usedByCompanies', { count: '5.2k' })}
              </span>
              <span className="flex items-center gap-1">
                <TrendingUp className="w-3 h-3" />
                {t('testLibrary.successRateFooter', { percent: 87 })}
              </span>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={onClose}>
                {t('testLibrary.close')}
              </Button>
              <Button className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text">
                <Plus className="w-4 h-4 mr-2" />
                {t('testLibrary.createNewTest')}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
