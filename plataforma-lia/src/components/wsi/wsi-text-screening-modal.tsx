"use client"

import { useState, useEffect, useRef } from"react"
import { Button } from"@/components/ui/button"
import { Card, CardContent } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Progress } from"@/components/ui/progress"
import { Textarea } from"@/components/ui/textarea"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from"@/components/ui/dialog"
import {
  Brain, Send, Loader2, CheckCircle, AlertCircle,
  ChevronRight, MessageSquare, Target, X,
  BarChart3, FileText, User, TrendingUp, Award
} from"lucide-react"
import { useTranslations } from "next-intl"
import { EligibilityResultsSection } from "./eligibility-results-section"
import type { EligibilityResultItem } from "./eligibility-results-section"

export type { EligibilityResultItem }

interface WSITextScreeningModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: {
    id: string
    name: string
    avatar?: string
    position?: string
  }
  jobVacancy?: {
    id: string
    title: string
    requirements?: string[]
    skills?: string[]
  }
  jobVacancyId?: string
  jobTitle?: string
  eligibilityResults?: EligibilityResultItem[]
  onComplete?: (result: Record<string, unknown>) => void
}

interface WSIQuestion {
  id: string
  text: string
  bloom_level: number
  bloom_level_name: string
  skill_targeted: string
  question_type: string
}

interface BigFiveIndicators {
  openness: number
  conscientiousness: number
  extraversion: number
  agreeableness: number
  stability: number
}

interface ArchetypeIndicator {
  archetype: string
  match_score: number
  description: string
}

interface WSIResult {
  result_id: string
  overall_score: number
  classification: string
  cognitive_level: {
    level: number
    name: string
    name_pt: string
    description: string
  }
  proficiency_level: {
    level: number
    name: string
    name_pt: string
    description: string
  }
  big_five_profile: BigFiveIndicators
  archetype_indicators: ArchetypeIndicator[]
  summary: string
  recommendations: string[]
  response_analyses: Record<string, unknown>[]
}

type ScreeningStep = 'loading' | 'questions' | 'processing' | 'completed' | 'error'

const BLOOM_COLORS: Record<number, string> = {
  1: 'bg-lia-bg-tertiary text-lia-text-primary',
  2: 'bg-lia-interactive-active text-lia-text-primary',
  3: '',
  4: '',
  5: '',
  6: ''
}

export function WSITextScreeningModal({
  isOpen,
  onClose,
  candidate,
  jobVacancy,
  jobVacancyId,
  jobTitle,
  eligibilityResults,
  onComplete
}: WSITextScreeningModalProps) {
  const t = useTranslations('screening.wsi')

  const BLOOM_NAMES: Record<number, string> = {
    1: t('textScreening.bloomNames.1'),
    2: t('textScreening.bloomNames.2'),
    3: t('textScreening.bloomNames.3'),
    4: t('textScreening.bloomNames.4'),
    5: t('textScreening.bloomNames.5'),
    6: t('textScreening.bloomNames.6')
  }

  const DREYFUS_NAMES: Record<number, string> = {
    1: t('textScreening.dreyfusNames.1'),
    2: t('textScreening.dreyfusNames.2'),
    3: t('textScreening.dreyfusNames.3'),
    4: t('textScreening.dreyfusNames.4'),
    5: t('textScreening.dreyfusNames.5')
  }

  const BIG_FIVE_LABELS: Record<string, { label: string; color?: string }> = {
    openness: { label: t('textScreening.bigFiveLabels.openness') },
    conscientiousness: { label: t('textScreening.bigFiveLabels.conscientiousness') },
    extraversion: { label: t('textScreening.bigFiveLabels.extraversion'), color: 'var(--status-success)' },
    agreeableness: { label: t('textScreening.bigFiveLabels.agreeableness'), color: 'var(--wedo-orange)' },
    stability: { label: t('textScreening.bigFiveLabels.stability'), color: 'var(--status-success)' }
  }

  const effectiveJobVacancy = jobVacancy || {
    id: jobVacancyId || '',
    title: jobTitle || t('textScreening.jobDefault'),
    requirements: [],
    skills: []
  }
  
  const [step, setStep] = useState<ScreeningStep>('loading')
  const [sessionId, setSessionId] = useState<string>('')
  const [questions, setQuestions] = useState<WSIQuestion[]>([])
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [currentAnswer, setCurrentAnswer] = useState('')
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<WSIResult | null>(null)
  const [fetchedEligibilityResults, setFetchedEligibilityResults] = useState<EligibilityResultItem[] | null>(null)
  const [eligibilityFetchLoading, setEligibilityFetchLoading] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isOpen && step === 'loading') {
      initializeScreening()
      fetchEligibilityFromBackend()
    }
  }, // eslint-disable-next-line react-hooks/exhaustive-deps
  [isOpen])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [currentQuestionIndex])

  const fetchEligibilityFromBackend = async () => {
    const candidateId = candidate.id
    const jobId = effectiveJobVacancy.id
    if (!candidateId || !jobId) return

    setEligibilityFetchLoading(true)
    try {
      const params = new URLSearchParams({ candidate_id: candidateId, job_id: jobId })
      const response = await fetch(`/api/backend-proxy/triagem/sessions?${params.toString()}`, {
        signal: AbortSignal.timeout(10000),
      })
      if (!response.ok) return

      const data = await response.json()
      const items: EligibilityResultItem[] = (data?.eligibility_results ?? [])
        .filter((r: Record<string, unknown>) => r && typeof r.question === 'string' && r.question)
        .map((r: Record<string, unknown>, i: number) => ({
          id: String(r.id ?? i),
          question: String(r.question),
          answer: r.answer != null ? String(r.answer) : undefined,
          passed: Boolean(r.passed),
          is_eliminatory: r.is_eliminatory !== false,
          reconsideration: r.reconsideration != null ? String(r.reconsideration) : undefined,
        }))

      if (items.length > 0) {
        setFetchedEligibilityResults(items)
      }
    } catch {
    } finally {
      setEligibilityFetchLoading(false)
    }
  }

  const initializeScreening = async () => {
    try {
      setError(null)

      const response = await fetch('/api/backend-proxy/api/v1/wsi/generate-questions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_vacancy_id: effectiveJobVacancy.id,
          job_title: effectiveJobVacancy.title,
          requirements: effectiveJobVacancy.requirements || [],
          skills: effectiveJobVacancy.skills || [],
          num_questions: 5
        })
      })

      if (!response.ok) {
        throw new Error('Failed to generate questions')
      }

      const data = await response.json()
      setSessionId(data.session_id)
      setQuestions(data.questions)
      setStep('questions')
    } catch (err) {
      setError(err instanceof Error ? err.message : t('textScreening.errorStarting'))
      setStep('error')
    }
  }

  const handleSubmitAnswer = async () => {
    if (!currentAnswer.trim() || isSubmitting) return

    setIsSubmitting(true)
    const currentQuestion = questions[currentQuestionIndex]

    try {
      setAnswers(prev => ({ ...prev, [currentQuestion.id]: currentAnswer }))
      setCurrentAnswer('')

      if (currentQuestionIndex < questions.length - 1) {
        setCurrentQuestionIndex(prev => prev + 1)
      } else {
        await completeScreening()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t('textScreening.errorSendingResponse'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const completeScreening = async () => {
    setStep('processing')
    try {
      const allAnswers = { ...answers, [questions[currentQuestionIndex].id]: currentAnswer }
      
      const responses = questions.map(q => ({
        question_id: q.id,
        response_text: allAnswers[q.id] || ''
      }))

      const response = await fetch('/api/backend-proxy/api/v1/wsi/complete-screening', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          candidate_id: candidate.id,
          job_vacancy_id: effectiveJobVacancy.id,
          responses
        })
      })

      if (!response.ok) {
        throw new Error('Failed to complete screening')
      }

      const wsiResult = await response.json()
      setResult(wsiResult)
      setStep('completed')
      onComplete?.(wsiResult)
    } catch (err) {
      setError(err instanceof Error ? err.message : t('textScreening.errorCalculatingScore'))
      setStep('error')
    }
  }

  const resolvedEligibilityResults = fetchedEligibilityResults ?? eligibilityResults

  const handleClose = () => {
    setStep('loading')
    setSessionId('')
    setQuestions([])
    setCurrentQuestionIndex(0)
    setCurrentAnswer('')
    setAnswers({})
    setError(null)
    setResult(null)
    setFetchedEligibilityResults(null)
    setEligibilityFetchLoading(false)
    onClose()
  }

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()
  }

  const progressPercentage = questions.length > 0 
    ? ((currentQuestionIndex + 1) / questions.length) * 100 
    : 0

  const renderBloomDreyfusMatrix = () => {
    if (!result) return null
    
    const bloomLevel = result.cognitive_level.level
    const dreyfusLevel = result.proficiency_level.level
    
    return (
      <div className="bg-lia-bg-primary rounded-xl p-4 border border-lia-border-subtle">
        <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-lia-text-secondary" />
          {t('textScreening.bloomDreyfusMatrix')}
        </h4>
        <div className="grid grid-cols-6 gap-1 text-micro">
          {[5, 4, 3, 2, 1].map(d => (
            <div key={`dreyfus-${d}`} className="contents">
              <div className="flex items-center justify-end pr-2 text-lia-text-secondary">
                D{d}
              </div>
              {[1, 2, 3, 4, 5].map(b => {
                const isActive = b <= bloomLevel && d <= dreyfusLevel
                const isCurrent = b === bloomLevel && d === dreyfusLevel
                return (
                  <div
                    key={`cell-${b}-${d}`}
                    className={`h-6 rounded-md transition-colors motion-reduce:transition-none ${
 isCurrent 
                        ? 'bg-lia-btn-primary-bg ring-2 ring-lia-border-default' 
                        : isActive 
                          ? 'bg-lia-border-medium' 
                          : 'bg-lia-bg-tertiary'
                    }`}
                  />
                )
              })}
            </div>
          ))}
          <div className="col-span-6 flex justify-end mt-1 gap-1 text-lia-text-secondary">
            <span className="w-[calc(100%/6)]"></span>
            {[1, 2, 3, 4, 5].map(b => (
              <span key={`bloom-${b}`} className="w-[calc(100%/6)] text-center">B{b}</span>
            ))}
          </div>
        </div>
        <div className="flex justify-between text-micro text-lia-text-secondary mt-2">
          <span>{t('textScreening.cognitive', { name: result.cognitive_level.name_pt })}</span>
          <span>{t('textScreening.proficiencyLabel', { name: result.proficiency_level.name_pt })}</span>
        </div>
      </div>
    )
  }

  const renderBigFiveIndicators = () => {
    if (!result?.big_five_profile) return null
    
    const traits = result.big_five_profile
    const traitEntries = Object.entries(traits).filter(([key]) => key in BIG_FIVE_LABELS)
    
    return (
      <div className="bg-lia-bg-primary rounded-xl p-4 border border-lia-border-subtle">
        <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
          <User className="w-4 h-4 text-lia-text-secondary" />
          {t('textScreening.bigFiveProfile')}
        </h4>
        <div className="space-y-2">
          {traitEntries.map(([key, value]) => {
            const trait = BIG_FIVE_LABELS[key]
            const displayValue = value
            return (
              <div key={key} className="flex items-center gap-2">
                <span className="text-xs w-28 text-lia-text-primary">{trait.label}</span>
                <div className="flex-1 h-2 bg-lia-bg-tertiary rounded-full overflow-hidden">
                  <div 
                    className="h-full rounded-full transition-[width,height] duration-500"
                    style={{width: `${displayValue}%`,
                      backgroundColor: trait.color}}
                  />
                </div>
                <span className="text-xs w-8 text-right text-lia-text-primary">{displayValue}%</span>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  const renderArchetypes = () => {
    if (!result?.archetype_indicators?.length) return null
    
    return (
      <div className="bg-lia-bg-primary rounded-xl p-4 border border-lia-border-subtle">
        <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
          <Award className="w-4 h-4 text-lia-text-secondary" />
          {t('textScreening.archetypesIdentified')}
        </h4>
        <div className="space-y-2">
          {result.archetype_indicators.slice(0, 3).map((arch, idx) => (
            <div key={idx} className="flex items-center justify-between p-2 bg-lia-bg-secondary rounded-xl">
              <div>
                <div className="text-sm font-medium">{arch.archetype}</div>
                <div className="text-xs text-lia-text-secondary">{arch.description}</div>
              </div>
              <Chip variant="neutral" muted className="bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle">
                {arch.match_score}%
              </Chip>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent 
        className="max-w-2xl max-h-[90vh] overflow-hidden flex flex-col bg-lia-bg-primary rounded-xl border border-lia-border-subtle"
       
      >
        <DialogHeader className="flex-shrink-0 p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-lia-btn-primary-bg rounded-full flex items-center justify-center">
                <FileText className="w-5 h-5 text-white" />
              </div>
              <div>
                <DialogTitle className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
                  {t('textScreening.title')}
                  <Chip variant="neutral" className="text-micro font-normal">
                    Bloom + Dreyfus + Big Five
                  </Chip>
                </DialogTitle>
                <DialogDescription className="text-xs text-lia-text-secondary mt-1">
                  {candidate.name} • {effectiveJobVacancy.title}
                </DialogDescription>
              </div>
            </div>
            {step === 'questions' && (
              <Chip variant="neutral" muted className="bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle">
                {t('textScreening.ofQuestions', { current: currentQuestionIndex + 1, total: questions.length })}
              </Chip>
            )}
            {step === 'completed' && eligibilityFetchLoading && (
              <div className="h-6 w-20 rounded-full bg-lia-bg-tertiary animate-pulse motion-reduce:animate-none" aria-hidden="true" />
            )}
            {step === 'completed' && !eligibilityFetchLoading && resolvedEligibilityResults && resolvedEligibilityResults.length > 0 && (
              resolvedEligibilityResults.every(r => r.passed) ? (
                <Chip variant="success" muted className="text-micro font-medium">
                  ✅ Elegível
                </Chip>
              ) : (
                <Chip variant="danger" muted className="text-micro font-medium">
                  ❌ Não elegível
                </Chip>
              )
            )}
          </div>
        </DialogHeader>

        {step === 'questions' && (
          <div className="px-1 flex-shrink-0">
            <Progress 
              value={progressPercentage} 
              className="h-1.5 [&>div]:bg-lia-btn-primary-bg" 
            />
          </div>
        )}

        <div className="flex-1 overflow-y-auto py-4 space-y-4" role="status" aria-live="polite" aria-label="Carregando...">
          {step === 'loading' && (
            <div className="flex flex-col items-center justify-center py-12 space-y-4" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-8 h-8 text-lia-text-secondary animate-spin motion-reduce:animate-none" />
              <p className="text-sm text-lia-text-primary">
                {t('textScreening.generatingQuestions')}
              </p>
            </div>
          )}

          {step === 'error' && (
            <div className="flex flex-col items-center justify-center py-12 space-y-4">
              <AlertCircle className="w-12 h-12 text-status-error" />
              <div className="text-center">
                <p className="font-medium text-status-error">{t('textScreening.screeningError')}</p>
                <p className="text-sm text-lia-text-primary mt-1">{error}</p>
              </div>
              <Button 
                onClick={initializeScreening} 
                className="border border-lia-border-subtle bg-lia-bg-primary text-lia-text-primary hover:bg-lia-interactive-hover"
              >
                {t('textScreening.tryAgain')}
              </Button>
            </div>
          )}

          {step === 'questions' && (
            <div className="space-y-4">
              {questions.slice(0, currentQuestionIndex + 1).map((question, idx) => (
                <div key={question.id} className="space-y-3">
                  <div className="flex gap-3">
                    <div className="w-8 h-8 bg-lia-bg-tertiary rounded-full flex items-center justify-center flex-shrink-0">
                      <Brain className="w-4 h-4 text-wedo-cyan" />
                    </div>
                    <div className="flex-1">
                      <Card className="bg-lia-bg-primary border-lia-border-subtle">
                        <CardContent className="p-3">
                          <div className="flex items-center gap-2 mb-2 flex-wrap">
                            <Chip variant="neutral" muted className={`text-micro ${BLOOM_COLORS[question.bloom_level]}`}>
                              {question.bloom_level_name} (B{question.bloom_level})
                            </Chip>
                            <Chip variant="neutral" className="text-micro">
                              {question.skill_targeted}
                            </Chip>
                          </div>
                          <p className="text-sm">{question.text}</p>
                        </CardContent>
                      </Card>
                    </div>
                  </div>

                  {answers[question.id] && (
                    <div className="flex gap-3 justify-end">
                      <div className="flex-1 max-w-[80%]">
                        <Card className="bg-lia-bg-tertiary border-lia-border-subtle">
                          <CardContent className="p-3">
                            <p className="text-sm">{answers[question.id]}</p>
                          </CardContent>
                        </Card>
                      </div>
                      <Avatar className="w-8 h-8 flex-shrink-0">
                        <AvatarImage src={candidate.avatar} />
                        <AvatarFallback className="text-xs bg-lia-interactive-active">
                          {getInitials(candidate.name)}
                        </AvatarFallback>
                      </Avatar>
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}

          {step === 'processing' && (
            <div className="flex flex-col items-center justify-center py-12 space-y-4" role="status" aria-live="polite" aria-label="Carregando...">
              <div className="relative" role="status" aria-live="polite" aria-label="Carregando...">
                <Loader2 className="w-12 h-12 text-lia-text-secondary animate-spin motion-reduce:animate-none" />
                <Brain className="w-5 h-5 text-status-warning absolute -top-1 -right-1 animate-pulse motion-reduce:animate-none" />
              </div>
              <div className="text-center">
                <p className="font-medium text-lia-text-primary">{t('textScreening.analyzingWithAI')}</p>
                <p className="text-sm text-lia-text-primary mt-1">
                  {t('textScreening.evaluatingLevels')}
                </p>
              </div>
            </div>
          )}

          {step === 'completed' && result && (
            <div className="space-y-4">
              {eligibilityFetchLoading && (
                <div
                  className="rounded-xl border border-lia-border-subtle bg-lia-bg-secondary p-4 flex items-center gap-3"
                  aria-busy="true"
                >
                  <div className="w-7 h-7 rounded-md bg-lia-bg-tertiary animate-pulse motion-reduce:animate-none flex-shrink-0" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3 w-40 rounded-full bg-lia-bg-tertiary animate-pulse motion-reduce:animate-none" />
                    <div className="h-2.5 w-56 rounded-full bg-lia-bg-tertiary animate-pulse motion-reduce:animate-none" />
                  </div>
                </div>
              )}
              {!eligibilityFetchLoading && resolvedEligibilityResults && resolvedEligibilityResults.length > 0 && (
                <EligibilityResultsSection results={resolvedEligibilityResults} />
              )}

              <div className="text-center py-4">
                <CheckCircle className="w-12 h-12 text-status-success mx-auto mb-3" />
                <h3 className="text-sm font-semibold text-lia-text-primary">{t('textScreening.screeningCompleted')}</h3>
              </div>

              <Card className="bg-lia-bg-primary border-lia-border-subtle">
                <CardContent className="p-4 space-y-4">
                  <div className="text-center">
                    <div className={`text-5xl font-bold ${
 result.overall_score >= 4 ? 'text-status-success' :
                      result.overall_score >= 3 ? 'text-status-warning' :
                      'text-status-error'
                    }`}>
                      {result.overall_score.toFixed(1)}
                    </div>
                    <Chip
                      variant={
                        result.classification === 'excelente' || result.classification === 'alto'
                          ? 'success'
                          : result.classification === 'medio'
                            ? 'warning'
                            : 'danger'
                      }
                      muted
                      className="mt-2"
                    >
                      {result.classification.charAt(0).toUpperCase() + result.classification.slice(1)}
                    </Chip>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="text-center p-3 bg-lia-bg-primary rounded-xl border border-lia-border-subtle">
                      <Target className="w-5 h-5 text-lia-text-secondary mx-auto mb-1" />
                      <div className="text-lg font-semibold text-lia-text-primary">{BLOOM_NAMES[result.cognitive_level.level]}</div>
                      <div className="text-xs text-lia-text-primary">{t('textScreening.cognitiveLevel', { level: result.cognitive_level.level })}</div>
                    </div>
                    <div className="text-center p-3 bg-lia-bg-primary rounded-xl border border-lia-border-subtle">
                      <TrendingUp className="w-5 h-5 text-lia-text-secondary mx-auto mb-1" />
                      <div className="text-lg font-semibold text-lia-text-primary">{DREYFUS_NAMES[result.proficiency_level.level]}</div>
                      <div className="text-xs text-lia-text-primary">{t('textScreening.proficiency', { level: result.proficiency_level.level })}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {renderBloomDreyfusMatrix()}
              {renderBigFiveIndicators()}
              {renderArchetypes()}

              {result.summary && (
                <Card className="bg-lia-bg-primary border border-lia-border-subtle">
                  <CardContent className="p-4">
                    <h4 className="text-sm font-medium mb-2 flex items-center gap-2 text-lia-text-primary">
                      <MessageSquare className="w-4 h-4 text-lia-text-secondary" />
                      {t('textScreening.evaluationSummary')}
                    </h4>
                    <p className="text-sm text-lia-text-primary">
                      {result.summary}
                    </p>
                  </CardContent>
                </Card>
              )}

              {result.recommendations?.length > 0 && (
                <Card className="bg-lia-bg-primary border border-lia-border-subtle">
                  <CardContent className="p-4">
                    <h4 className="text-sm font-medium mb-2 text-lia-text-primary">{t('textScreening.recommendations')}</h4>
                    <ul className="text-sm text-lia-text-primary space-y-1">
                      {result.recommendations.map((rec, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-lia-text-secondary">•</span>
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>

        {step === 'questions' && !answers[questions[currentQuestionIndex]?.id] && (
          <div className="flex-shrink-0 pt-4 border-t border-lia-border-subtle">
            <div className="flex gap-2">
              <Textarea
                value={currentAnswer}
                onChange={(e) => setCurrentAnswer(e.target.value)}
                placeholder={t('textScreening.candidateResponsePlaceholder')}
                className="min-h-20 resize-none border-lia-border-subtle focus:border-lia-border-medium focus:ring-lia-btn-primary-bg/20"
                disabled={isSubmitting}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && e.ctrlKey) {
                    handleSubmitAnswer()
                  }
                }}
              />
            </div>
            <div className="flex items-center justify-between mt-3">
              <span className="text-xs text-lia-text-secondary">
                {t('textScreening.ctrlEnterToSend')}
              </span>
              <Button 
                onClick={handleSubmitAnswer}
                disabled={!currentAnswer.trim() || isSubmitting}
                className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text gap-2"
              >
                {isSubmitting ? (
                  <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                ) : currentQuestionIndex === questions.length - 1 ? (
                  <>
                    {t('textScreening.finalizeAndAnalyze')}
                    <Brain className="w-4 h-4 text-wedo-cyan" />
                  </>
                ) : (
                  <>
                    {t('textScreening.next')}
                    <ChevronRight className="w-4 h-4" />
                  </>
                )}
              </Button>
            </div>
          </div>
        )}

        {step === 'completed' && (
          <div className="flex-shrink-0 pt-4 border-t border-lia-border-subtle">
            <Button 
              onClick={handleClose} 
              className="w-full h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
            >
              {t('textScreening.close')}
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
