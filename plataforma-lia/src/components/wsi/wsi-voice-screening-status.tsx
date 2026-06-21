"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import { useState, useEffect, useCallback } from"react"
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Progress } from"@/components/ui/progress"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from"@/components/ui/dialog"
import {
  Phone, PhoneCall, PhoneOff, Loader2, CheckCircle, AlertCircle,
  Clock, Brain, Mic, Volume2, X, RefreshCw
} from"lucide-react"
import { liaApi, VoiceScreeningStatusResponse, WSICompetency, StartVoiceScreeningRequest } from"@/services/lia-api"
import { useTranslations } from "next-intl"
import { WSI_VISUAL_3TIER } from '@/lib/wsi/visual'

interface WSIVoiceScreeningStatusProps {
  isOpen: boolean
  onClose: () => void
  candidate: {
    id: string
    name: string
    phone?: string
  }
  jobVacancy: {
    id: string
    title: string
    description?: string
    competencies?: WSICompetency[]
  }
  sessionId?: string
  onComplete?: (result: Record<string, unknown>) => void
  autoStart?: boolean
  voipSessionId?: string
}

type VoiceStatus = 'idle' | 'initiating' | 'calling' | 'in_progress' | 'processing' | 'completed' | 'failed'

interface WSIScreeningResult {
  overall_wsi: number
  technical_wsi: number
  behavioral_wsi: number
  classification: string
  [key: string]: unknown
}


export function WSIVoiceScreeningStatus({
  isOpen,
  onClose,
  candidate,
  jobVacancy,
  sessionId: initialSessionId,
  onComplete,
  autoStart = false,
  voipSessionId,
}: WSIVoiceScreeningStatusProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('wsi-voice-screening-status', isOpen)

  const t = useTranslations('screening.wsi')
  const isVoipMode = Boolean(voipSessionId)
  const [status, setStatus] = useState<VoiceStatus>(
    voipSessionId ? 'in_progress' : 'idle'
  )
  const [sessionId, setSessionId] = useState<string | null>(
    voipSessionId || initialSessionId || null
  )
  const [callId, setCallId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<WSIScreeningResult | null>(null)
  const [elapsedTime, setElapsedTime] = useState(0)
  const [questionsCount, setQuestionsCount] = useState(0)

  const STATUS_CONFIG: Record<VoiceStatus, { 
    icon: React.ElementType
    label: string
    color: string
    bgColor: string
    animate?: boolean
  }> = {
    idle: {
      icon: Phone,
      label: t('voiceScreening.statusIdle'),
      color: 'text-lia-text-primary',
      bgColor: 'bg-lia-bg-tertiary'
    },
    initiating: {
      icon: Loader2,
      label: t('voiceScreening.statusInitiating'),
      color: 'text-lia-text-secondary',
      bgColor: 'bg-lia-bg-tertiary',
      animate: true
    },
    calling: {
      icon: PhoneCall,
      label: t('voiceScreening.statusCalling'),
      color: 'text-status-warning',
      bgColor: 'bg-status-warning/10 dark:bg-status-warning/20',
      animate: true
    },
    in_progress: {
      icon: Mic,
      label: t('voiceScreening.statusInProgress'),
      color: 'text-status-success',
      bgColor: 'bg-status-success/10 dark:bg-status-success/20',
      animate: true
    },
    processing: {
      icon: Brain,
      label: t('voiceScreening.statusProcessing'),
      color: 'text-lia-text-secondary',
      bgColor: 'bg-wedo-purple/10 dark:bg-wedo-purple/20',
      animate: true
    },
    completed: {
      icon: CheckCircle,
      label: t('voiceScreening.statusCompleted'),
      color: 'text-status-success',
      bgColor: 'bg-status-success/15 dark:bg-status-success/30'
    },
    failed: {
      icon: AlertCircle,
      label: t('voiceScreening.statusFailed'),
      color: 'text-status-error',
      bgColor: 'bg-status-error/10 dark:bg-status-error/20'
    }
  }

  useEffect(() => {
    if (voipSessionId && voipSessionId !== sessionId) {
      setSessionId(voipSessionId)
      setStatus('in_progress')
      setError(null)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [voipSessionId])

  const pollStatus = useCallback(async () => {
    if (!sessionId) return

    try {
      const statusResponse = await liaApi.wsiGetVoiceScreeningStatus(sessionId)
      
      switch (statusResponse.status) {
        case 'pending':
          setStatus('calling')
          break
        case 'in_progress':
          setStatus('in_progress')
          break
        case 'processing':
          setStatus('processing')
          break
        case 'completed':
          setStatus('completed')
          if (statusResponse.result) {
            setResult(statusResponse.result as unknown as WSIScreeningResult)
            onComplete?.(statusResponse.result as unknown as Record<string, unknown>)
          }
          break
        case 'failed':
          setStatus('failed')
          setError(t('voiceScreening.callFailed'))
          break
      }
    } catch (err) {
    }
  }, [sessionId, onComplete, t])

  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null

    if (isOpen && sessionId && ['initiating', 'calling', 'in_progress', 'processing'].includes(status)) {
      intervalId = setInterval(pollStatus, 3000)
    }

    return () => {
      if (intervalId) clearInterval(intervalId)
    }
  }, [isOpen, sessionId, status, pollStatus])

  useEffect(() => {
    let timerId: NodeJS.Timeout | null = null

    if (status === 'in_progress') {
      timerId = setInterval(() => {
        setElapsedTime(prev => prev + 1)
      }, 1000)
    }

    return () => {
      if (timerId) clearInterval(timerId)
    }
  }, [status])

  useEffect(() => {
    if (isOpen && autoStart && status === 'idle') {
      startVoiceScreening()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, autoStart])

  const startVoiceScreening = async () => {
    if (isVoipMode) {
      return
    }

    if (!candidate.phone) {
      setError(t('voiceScreening.noPhoneRegistered'))
      setStatus('failed')
      return
    }

    setStatus('initiating')
    setError(null)

    try {
      const defaultCompetencies: WSICompetency[] = jobVacancy.competencies || [
        { name: 'Comunicação', type: 'behavioral', weight: 0.20 },
        { name: 'Resolução de Problemas', type: 'technical', weight: 0.25 },
        { name: 'Trabalho em Equipe', type: 'behavioral', weight: 0.15 },
        { name: 'Conhecimento Técnico', type: 'technical', weight: 0.25 },
        { name: 'Adaptabilidade', type: 'behavioral', weight: 0.15 },
      ]

      const request: StartVoiceScreeningRequest = {
        candidate_id: candidate.id,
        job_vacancy_id: jobVacancy.id,
        competencies: defaultCompetencies,
        candidate_phone: candidate.phone,
        candidate_name: candidate.name,
        job_title: jobVacancy.title,
        job_description: jobVacancy.description,
        mode: 'compact'
      }

      const response = await liaApi.wsiStartVoiceScreening(request)
      
      setSessionId(response.session_id)
      setCallId(response.call_id)
      setQuestionsCount(response.questions_generated)
      setStatus('calling')
    } catch (err) {
      setError(err instanceof Error ? err.message : t('voiceScreening.errorStartingCall'))
      setStatus('failed')
    }
  }

  const handleClose = () => {
    setStatus('idle')
    setSessionId(null)
    setCallId(null)
    setError(null)
    setResult(null)
    setElapsedTime(0)
    setQuestionsCount(0)
    onClose()
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const statusConfig = STATUS_CONFIG[status]
  const StatusIcon = statusConfig.icon

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {isVoipMode
              ? <Volume2 className="w-5 h-5 text-lia-text-secondary" />
              : <Phone className="w-5 h-5 text-lia-text-secondary" />
            }
            {t('voiceScreening.title')}
            {isVoipMode && (
              <span className="text-micro font-normal text-lia-text-tertiary bg-lia-bg-tertiary px-1.5 py-0.5 rounded">
                VoIP
              </span>
            )}
          </DialogTitle>
          <DialogDescription>
            {candidate.name} • {jobVacancy.title}
          </DialogDescription>
        </DialogHeader>

        <div className="py-6">
          <Card className={`${statusConfig.bgColor} border-none`}>
            <CardContent className="p-6">
              <div className="flex flex-col items-center text-center space-y-4">
                <div className={`w-16 h-16 rounded-full flex items-center justify-center ${statusConfig.bgColor} border-2 border-current ${statusConfig.color}`}>
                  <StatusIcon className={`w-8 h-8 ${statusConfig.color} ${statusConfig.animate ? 'animate-pulse motion-reduce:animate-none' : ''}`} />
                </div>

                <div>
                  <p className={`font-semibold ${statusConfig.color}`}>
                    {statusConfig.label}
                  </p>
                  
                  {status === 'in_progress' && (
                    <div className="mt-2 space-y-2">
                      <div className="flex items-center justify-center gap-2 text-sm text-lia-text-tertiary">
                        <Clock className="w-4 h-4" />
                        <span>{formatTime(elapsedTime)}</span>
                      </div>
                      {questionsCount > 0 && (
                        <p className="text-xs text-lia-text-tertiary">
                          {t('voiceScreening.questionsReady', { count: questionsCount })}
                        </p>
                      )}
                    </div>
                  )}

                  {status === 'calling' && !isVoipMode && (
                    <p className="text-sm text-lia-text-tertiary mt-2">
                      {t('voiceScreening.callingPhone', { phone: candidate.phone ?? '' })}
                    </p>
                  )}

                  {isVoipMode && status === 'in_progress' && (
                    <p className="text-sm text-lia-text-tertiary mt-2">
                      {t('voiceScreening.candidateConnectedVoIP')}
                    </p>
                  )}

                  {status === 'processing' && (
                    <div className="mt-3 w-48">
                      <Progress value={75} className="h-1.5" />
                      <p className="text-xs text-lia-text-tertiary mt-1">
                        {t('voiceScreening.analyzingWithAI')}
                      </p>
                    </div>
                  )}

                  {status === 'failed' && error && (
                    <p className="text-sm text-status-error mt-2">
                      {error}
                    </p>
                  )}
                </div>

                {result && status === 'completed' && (
                  <div className="w-full space-y-3 pt-2">
                    <div className="text-center">
                      <div className={`text-3xl font-semibold ${
 // Escala WSI 0-10 (Task #512). Cutoffs canônicos em `lib/wsi/visual.ts`.
                        result.overall_wsi >= WSI_VISUAL_3TIER.green ? 'text-status-success' :
                        result.overall_wsi >= WSI_VISUAL_3TIER.yellow ? 'text-status-warning' :
                        'text-status-error'
                      }`}>
                        {result.overall_wsi.toFixed(1)}
                      </div>
                      <Chip variant="neutral" muted className={`mt-1 ${
 result.classification === 'excelente' || result.classification === 'alto' 
                          ? '' :
                        result.classification === 'medio' 
                          ? '' :
                        ''
                      }`}>
                        {result.classification.charAt(0).toUpperCase() + result.classification.slice(1)}
                      </Chip>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-2 bg-lia-bg-primary rounded-xl text-center">
                        <div className="text-lg font-semibold">{result.technical_wsi.toFixed(1)}</div>
                        <div className="text-xs text-lia-text-tertiary">{t('voiceScreening.technical')}</div>
                      </div>
                      <div className="p-2 bg-lia-bg-primary rounded-xl text-center">
                        <div className="text-lg font-semibold">{result.behavioral_wsi.toFixed(1)}</div>
                        <div className="text-xs text-lia-text-tertiary">{t('voiceScreening.behavioral')}</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="flex gap-2">
          {status === 'idle' && !isVoipMode && (
            <Button onClick={startVoiceScreening} className="flex-1 gap-2 hover:bg-lia-interactive-hover transition-colors cursor-pointer">
              <PhoneCall className="w-4 h-4" />
              {t('voiceScreening.startCall')}
            </Button>
          )}

          {status === 'failed' && !isVoipMode && (
            <Button onClick={startVoiceScreening} variant="outline" className="flex-1 gap-2 hover:bg-lia-interactive-hover transition-colors cursor-pointer">
              <RefreshCw className="w-4 h-4" />
              {t('voiceScreening.tryAgain')}
            </Button>
          )}

          {['initiating', 'calling', 'in_progress', 'processing'].includes(status) && (
            <Button variant="destructive" onClick={handleClose} className="flex-1 gap-2 hover:bg-lia-interactive-hover transition-colors cursor-pointer">
              <PhoneOff className="w-4 h-4" />
              {t('voiceScreening.cancel')}
            </Button>
          )}

          {status === 'completed' && (
            <Button onClick={handleClose} className="flex-1 hover:bg-lia-interactive-hover transition-colors cursor-pointer">
              {t('voiceScreening.close')}
            </Button>
          )}

          {status !== 'completed' && status !== 'idle' && status !== 'failed' && (
            <Button variant="outline" onClick={handleClose}>
              <X className="w-4 h-4" />
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}