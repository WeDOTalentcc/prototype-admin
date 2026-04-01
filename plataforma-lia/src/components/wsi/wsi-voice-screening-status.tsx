"use client"

import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import {
  Phone, PhoneCall, PhoneOff, Loader2, CheckCircle, AlertCircle,
  Clock, Brain, Mic, Volume2, X, RefreshCw
} from "lucide-react"
import { liaApi, VoiceScreeningStatusResponse, WSICompetency, StartVoiceScreeningRequest } from "@/services/lia-api"

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
}

type VoiceStatus = 'idle' | 'initiating' | 'calling' | 'in_progress' | 'processing' | 'completed' | 'failed'

const STATUS_CONFIG: Record<VoiceStatus, { 
  icon: React.ElementType
  label: string
  color: string
  bgColor: string
  animate?: boolean
}> = {
  idle: {
    icon: Phone,
    label: 'Pronto para iniciar',
    color: 'text-lia-text-primary dark:text-lia-text-primary',
    bgColor: 'bg-gray-100 dark:bg-lia-bg-secondary'
  },
  initiating: {
    icon: Loader2,
    label: 'Iniciando chamada...',
    color: 'text-lia-text-secondary dark:text-lia-text-tertiary',
    bgColor: 'bg-gray-100 dark:bg-lia-bg-secondary',
    animate: true
  },
  calling: {
    icon: PhoneCall,
    label: 'Chamando candidato...',
    color: 'text-status-warning',
    bgColor: 'bg-status-warning/10 dark:bg-status-warning/20',
    animate: true
  },
  in_progress: {
    icon: Mic,
    label: 'Triagem em andamento',
    color: 'text-status-success',
    bgColor: 'bg-status-success/10 dark:bg-status-success/20',
    animate: true
  },
  processing: {
    icon: Brain,
    label: 'Processando respostas...',
    color: 'text-wedo-purple',
    bgColor: 'bg-wedo-purple/10 dark:bg-wedo-purple/20',
    animate: true
  },
  completed: {
    icon: CheckCircle,
    label: 'Triagem concluída',
    color: 'text-status-success',
    bgColor: 'bg-status-success/15 dark:bg-status-success/30'
  },
  failed: {
    icon: AlertCircle,
    label: 'Erro na triagem',
    color: 'text-status-error',
    bgColor: 'bg-status-error/10 dark:bg-status-error/20'
  }
}


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
  autoStart = false
}: WSIVoiceScreeningStatusProps) {
  const [status, setStatus] = useState<VoiceStatus>('idle')
  const [sessionId, setSessionId] = useState<string | null>(initialSessionId || null)
  const [callId, setCallId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<WSIScreeningResult | null>(null)
  const [elapsedTime, setElapsedTime] = useState(0)
  const [questionsCount, setQuestionsCount] = useState(0)

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
            // @ts-ignore TODO: fix type — Argument of type 'CalculateWSIResponse' is not assignable to parameter of type '
            setResult(statusResponse.result)
            // @ts-ignore TODO: fix type — Argument of type 'CalculateWSIResponse' is not assignable to parameter of type '
            onComplete?.(statusResponse.result)
          }
          break
        case 'failed':
          setStatus('failed')
          setError('A chamada falhou ou foi encerrada')
          break
      }
    } catch (err) {
    }
  }, [sessionId, onComplete])

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
  }, [isOpen, autoStart])

  const startVoiceScreening = async () => {
    if (!candidate.phone) {
      setError('Candidato não possui telefone cadastrado')
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
      setError(err instanceof Error ? err.message : 'Erro ao iniciar chamada')
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
            <Phone className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-secondary" />
            Triagem por Voz WSI
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
                      <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                        <Clock className="w-4 h-4" />
                        <span>{formatTime(elapsedTime)}</span>
                      </div>
                      {questionsCount > 0 && (
                        <p className="text-xs text-muted-foreground">
                          {questionsCount} perguntas preparadas
                        </p>
                      )}
                    </div>
                  )}

                  {status === 'calling' && (
                    <p className="text-sm text-muted-foreground mt-2">
                      Ligando para {candidate.phone}...
                    </p>
                  )}

                  {status === 'processing' && (
                    <div className="mt-3 w-48">
                      <Progress value={75} className="h-1.5" />
                      <p className="text-xs text-muted-foreground mt-1">
                        Analisando respostas com IA
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
                      <div className={`text-3xl font-bold ${
 result.overall_wsi >= 4 ? 'text-status-success' :
                        result.overall_wsi >= 3 ? 'text-status-warning' :
                        'text-status-error'
                      }`}>
                        {result.overall_wsi.toFixed(1)}
                      </div>
                      <Badge className={`mt-1 ${
 result.classification === 'excelente' || result.classification === 'alto' 
                          ? 'bg-status-success/15 text-status-success' :
                        result.classification === 'medio' 
                          ? 'bg-status-warning/15 text-status-warning' :
                        'bg-status-error/15 text-status-error'
                      }`}>
                        {result.classification.charAt(0).toUpperCase() + result.classification.slice(1)}
                      </Badge>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-2 bg-white dark:bg-lia-bg-secondary rounded-md text-center">
                        <div className="text-lg font-semibold">{result.technical_wsi.toFixed(1)}</div>
                        <div className="text-xs text-muted-foreground">Técnico</div>
                      </div>
                      <div className="p-2 bg-white dark:bg-lia-bg-secondary rounded-md text-center">
                        <div className="text-lg font-semibold">{result.behavioral_wsi.toFixed(1)}</div>
                        <div className="text-xs text-muted-foreground">Comportamental</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="flex gap-2">
          {status === 'idle' && (
            <Button onClick={startVoiceScreening} className="flex-1 gap-2">
              <PhoneCall className="w-4 h-4" />
              Iniciar Chamada
            </Button>
          )}

          {status === 'failed' && (
            <Button onClick={startVoiceScreening} variant="outline" className="flex-1 gap-2">
              <RefreshCw className="w-4 h-4" />
              Tentar novamente
            </Button>
          )}

          {['initiating', 'calling', 'in_progress', 'processing'].includes(status) && (
            <Button variant="destructive" onClick={handleClose} className="flex-1 gap-2">
              <PhoneOff className="w-4 h-4" />
              Cancelar
            </Button>
          )}

          {status === 'completed' && (
            <Button onClick={handleClose} className="flex-1">
              Fechar
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
