"use client"

import { useTranslations } from "next-intl"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import {
  AlertCircle,
  CheckCircle,
  Clock,
  ListChecks,
  Send,
  Target,
  X,
} from"lucide-react"

interface TestPreviewModalProps {
  open: boolean
  onClose: () => void
}

export function TestPreviewModal({ open, onClose }: TestPreviewModalProps) {
  const t = useTranslations('kanban')
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-lia-overlay backdrop-blur-sm">
      <div className="bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl w-full max-w-4xl max-h-[90vh] overflow-hidden animate-fadeIn">
        <div className="bg-wedo-purple p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-semibold mb-2">{t('testPreview.title')}</h2>
              <p className="text-wedo-purple-text text-sm">{t('testPreview.jobInfo')}</p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-lia-bg-primary/20 rounded-xl transition-colors motion-reduce:transition-none"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="overflow-y-auto max-h-[calc(90vh-120px)]">
          <div className="p-6 dark:border-lia-border-subtle">
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-lia-text-primary" />
                <div>
                  <p className="text-xs text-lia-text-primary">{t('testPreview.totalTime')}</p>
                  <p className="text-sm font-semibold text-lia-text-primary">{t('testPreview.totalTimeValue')}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <ListChecks className="w-4 h-4 text-lia-text-primary" />
                <div>
                  <p className="text-xs text-lia-text-primary">{t('testPreview.totalQuestions')}</p>
                  <p className="text-sm font-semibold text-lia-text-primary">{t('testPreview.totalQuestionsValue')}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-lia-text-primary" />
                <div>
                  <p className="text-xs text-lia-text-primary">{t('testPreview.minimumScore')}</p>
                  <p className="text-sm font-semibold text-lia-text-primary">70%</p>
                </div>
              </div>
            </div>

            <div className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary/20 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-lia-text-primary mb-2 flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                {t('testPreview.importantInstructions')}
              </h3>
              <ul className="text-sm text-lia-text-primary space-y-1">
                <li>• {t('testPreview.instructionRead')}</li>
                <li>• {t('testPreview.instructionTimeLimit')}</li>
                <li>• {t('testPreview.instructionNavigate')}</li>
                <li>• {t('testPreview.instructionAutoSubmit')}</li>
                <li>• {t('testPreview.instructionConnection')}</li>
              </ul>
            </div>
          </div>

          <div className="p-6 space-y-6">
            <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl p-5">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start gap-3">
                  <div className="bg-lia-interactive-active dark:bg-lia-bg-elevated text-lia-text-primary rounded-full w-8 h-8 flex items-center justify-center font-semibold text-sm">
                    1
                  </div>
                  <div className="flex-1">
                    <p className="text-lia-text-primary font-medium">
                      {t('testPreview.question1')}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <div className="flex items-center gap-1 text-xs text-lia-text-primary">
                        <Clock className="w-3 h-3" />
                        <span className="font-medium">{t('testPreview.timeLimitLabel', { time: '3:00' })}</span>
                      </div>
                      <div className="flex-1 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-1.5 max-w-sidebar-content">
                        <div className="bg-lia-bg-inverse dark:bg-lia-text-secondary h-1.5 rounded-full animate-pulse motion-reduce:animate-none"></div>
                      </div>
                    </div>
                  </div>
                </div>
                <Chip variant="neutral" muted className="bg-lia-interactive-active dark:bg-lia-bg-elevated text-lia-text-secondary">{t('testPreview.points', { count: 10 })}</Chip>
              </div>
              <div className="ml-11 space-y-2">
                {[
                  t('testPreview.option1_1'),
                  t('testPreview.option1_2'),
                  t('testPreview.option1_3'),
                  t('testPreview.option1_4')
                ].map((option, idx) => (
                  <label key={idx} className="flex items-center gap-3 p-3 bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-medium dark:hover:border-lia-border-medium cursor-pointer transition-colors motion-reduce:transition-none group">
                    <input
                      type="radio"
                      name="candidate-q1"
                      className="w-4 h-4 text-lia-text-primary border-lia-border-default focus:ring-lia-border-medium"
                    />
                    <span className="text-sm text-lia-text-primary group-hover:text-lia-text-primary dark:group-hover:text-lia-text-inverse">
                      {option}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl p-5">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start gap-3">
                  <div className="bg-lia-interactive-active dark:bg-lia-bg-elevated text-lia-text-primary rounded-full w-8 h-8 flex items-center justify-center font-semibold text-sm">
                    2
                  </div>
                  <div className="flex-1">
                    <p className="text-lia-text-primary font-medium">
                      {t('testPreview.question2')}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <div className="flex items-center gap-1 text-xs text-lia-text-primary">
                        <CheckCircle className="w-3 h-3" />
                        <span className="font-medium">{t('testPreview.answeredIn', { time: '0:45' })}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <Chip variant="neutral" muted className="bg-lia-interactive-active dark:bg-lia-bg-elevated text-lia-text-secondary">{t('testPreview.points', { count: 10 })}</Chip>
              </div>
              <div className="ml-11 space-y-2">
                {[
                  t('testPreview.option2_1'),
                  t('testPreview.option2_2'),
                  t('testPreview.option2_3'),
                  t('testPreview.option2_4')
                ].map((option, idx) => (
                  <label key={idx} className="flex items-center gap-3 p-3 bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-medium dark:hover:border-lia-border-medium cursor-pointer transition-colors motion-reduce:transition-none group">
                    <input
                      type="radio"
                      name="candidate-q2"
                      className="w-4 h-4 text-lia-text-primary border-lia-border-default focus:ring-lia-border-medium"
                    />
                    <span className="text-sm text-lia-text-primary group-hover:text-lia-text-primary dark:group-hover:text-lia-text-inverse">
                      {option}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl p-5">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start gap-3">
                  <div className="bg-lia-interactive-active dark:bg-lia-bg-elevated text-lia-text-primary rounded-full w-8 h-8 flex items-center justify-center font-semibold text-sm">
                    3
                  </div>
                  <div className="flex-1">
                    <p className="text-lia-text-primary font-medium">
                      {t('testPreview.question3')}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <div className="flex items-center gap-1 text-xs text-lia-text-primary">
                        <CheckCircle className="w-3 h-3" />
                        <span className="font-medium">{t('testPreview.answeredIn', { time: '1:23' })}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <Chip variant="neutral" muted className="bg-lia-interactive-active dark:bg-lia-bg-elevated text-lia-text-secondary">{t('testPreview.points', { count: 10 })}</Chip>
              </div>
              <div className="ml-11 space-y-2">
                {[
                  t('testPreview.option3_1'),
                  t('testPreview.option3_2'),
                  t('testPreview.option3_3'),
                  t('testPreview.option3_4')
                ].map((option, idx) => (
                  <label key={idx} className="flex items-center gap-3 p-3 bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-medium dark:hover:border-lia-border-medium cursor-pointer transition-colors motion-reduce:transition-none group">
                    <input
                      type="radio"
                      name="candidate-q3"
                      className="w-4 h-4 text-lia-text-primary border-lia-border-default focus:ring-lia-border-medium"
                    />
                    <span className="text-sm text-lia-text-primary group-hover:text-lia-text-primary dark:group-hover:text-lia-text-inverse">
                      {option}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="flex items-center gap-2">
                <span className="text-sm text-lia-text-primary">{t('testPreview.progressLabel')}</span>
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map(num => (
                    <div
                      key={num}
                      className={`w-8 h-1 rounded-full ${
                        num <= 3 ? 'bg-lia-btn-primary-bg' : 'bg-lia-border-default dark:bg-lia-bg-elevated'
                      }`}
                    />
                  ))}
                </div>
              </div>
              <span className="text-sm text-lia-text-primary">{t('testPreview.questionsAnswered', { answered: 3, total: 5 })}</span>
            </div>
          </div>
        </div>

        <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle p-4 bg-lia-bg-secondary dark:bg-lia-bg-secondary">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3 bg-lia-bg-tertiary dark:bg-lia-bg-secondary/20 px-3 py-1.5 rounded-xl">
                <Clock className="w-4 h-4 text-lia-text-primary" />
                <div>
                  <span className="text-xs text-lia-text-secondary">{t('testPreview.totalTimeLabel')}</span>
                  <span className="text-sm font-bold text-lia-text-primary ml-1">11:32</span>
                  <span className="text-xs text-lia-text-primary mx-2">|</span>
                  <span className="text-xs text-lia-text-secondary">{t('testPreview.currentQuestionLabel')}</span>
                  <span className="text-sm font-bold text-lia-text-primary ml-1">2:15</span>
                </div>
              </div>
              <div className="text-sm text-lia-text-primary">
                <CheckCircle className="w-3 h-3 inline text-lia-text-primary mr-1" />
                {t('testPreview.autoSave')}
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={onClose}
              >
                {t('testPreview.closePreview')}
              </Button>
              <Button className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover dark:bg-lia-bg-secondary dark:hover:bg-lia-interactive-active text-white">
                <Send className="w-4 h-4 mr-2" />
                {t('testPreview.sendTest')}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
