"use client"

import React, { useState } from "react"
import { useModalA11y } from "@/hooks/ui/use-modal-a11y"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Phone, Video, MessageSquare, X, Brain, RefreshCw, Building, Users, Info, Download, Calendar
} from "lucide-react"
import { liaApi } from "@/services/lia-api"
import { textStyles, cardStyles } from "@/lib/design-tokens"

interface LiaRecommendationAttentionPoints {
  strengths: string[]
  concerns: string[]
  risksToMitigate?: string[]
}

interface LiaRecommendations {
  recommendedType: string
  recommendedDuration: string
  recommendedPlatform: string
  suggestedTimes: Array<{ time: string; reason?: string }>
  attentionPoints: LiaRecommendationAttentionPoints
  interviewFocus: Record<string, { weight?: number; approach?: string }>
  [key: string]: unknown
}

interface Candidate {
  id: string; name: string; role: string; email: string; phone: string
  location: string; avatar?: string; score: number; status: string
  matchPercentage: number; riskLevel: string; culturalFit: number
  technicalMatch: number; experience: string; seniority: string
  availability: string; expectedSalary: string; preferredLocation: string
  linkedin?: string; portfolio?: string; skills: string[]
  lastActivity: string; source: string
  level?: string; position?: string
}

interface ScheduleModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: Candidate | null
  onSchedule: (type: string, datetime: string, details: Record<string, unknown>) => void
}

export function ScheduleModal({ isOpen, onClose, candidate, onSchedule }: ScheduleModalProps) {
  const [scheduleType, setScheduleType] = useState<'phone' | 'video' | 'presential'>('video')
  const [date, setDate] = useState('')
  const [time, setTime] = useState('')
  const [duration, setDuration] = useState('60')
  const [interviewer, setInterviewer] = useState('')
  const [notes, setNotes] = useState('')
  const [location, setLocation] = useState('')
  const [platform, setPlatform] = useState('zoom')

  // LIA states
  const [showLiaInsights, setShowLiaInsights] = useState(false)
  const [liaRecommendations, setLiaRecommendations] = useState<LiaRecommendations | null>(null)
  const [isLiaAnalyzing, setIsLiaAnalyzing] = useState(false)
  const [liaFocus, setLiaFocus] = useState<'technical' | 'behavioral' | 'cultural' | 'comprehensive'>('comprehensive')

  const [isScheduling, setIsScheduling] = useState(false)
  const [createdInterviewId, setCreatedInterviewId] = useState<string | null>(null)
  const dialogRef = useModalA11y(isOpen, onClose)
  if (!isOpen || !candidate) return null

  const interviewTypes = [
    {
      id: 'phone',
      name: 'Telefônica',
      icon: Phone,
      description: 'Conversa por telefone',
      color: 'bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle'
    },
    {
      id: 'video',
      name: 'Videoconferência',
      icon: Video,
      description: 'Reunião online por vídeo',
      color: 'bg-status-success/10 text-status-success border-status-success/30'
    },
    {
      id: 'presential',
      name: 'Presencial',
      icon: Building,
      description: 'Encontro no escritório',
      color: 'bg-wedo-purple/10 text-wedo-purple-text border-wedo-purple/30'
    }
  ]

  const platforms = [
    { id: 'zoom', name: 'Zoom', icon: Video },
    { id: 'teams', name: 'Teams', icon: Users },
    { id: 'meet', name: 'Google Meet', icon: Video },
    { id: 'whatsapp', name: 'WhatsApp', icon: MessageSquare }
  ]

  const interviewers = [
    'Ana Silva - Recrutadora Sênior',
    'Carlos Mendes - Tech Lead',
    'Marina Costa - Gerente de Produto',
    'Roberto Santos - RH'
  ]

  const generateLiaRecommendations = async () => {
    setIsLiaAnalyzing(true)
    setShowLiaInsights(true)

    // Simular análise da LIA
    await new Promise(resolve => setTimeout(resolve, 2000))

    const recommendations = analyzeCandidateForInterview(candidate, liaFocus)
    setLiaRecommendations(recommendations)
    setIsLiaAnalyzing(false)
  }

  const analyzeCandidateForInterview = (candidate: Candidate, focus: string) => {
    const seniorityLevel = candidate.seniority || candidate.level || 'Pleno'
    const skills = candidate.skills || []
    const experience = candidate.experience || ''
    const role = candidate.role || candidate.position || ''
    const score = candidate.matchPercentage || candidate.score || 85

    return {
      // Recomendações gerais
      recommendedType: seniorityLevel.toLowerCase().includes('senior') || seniorityLevel.toLowerCase().includes('sênior') ? 'video' : 'video',
      recommendedDuration: seniorityLevel.toLowerCase().includes('senior') ? '90' : seniorityLevel.toLowerCase().includes('junior') || seniorityLevel.toLowerCase().includes('júnior') ? '45' : '60',
      recommendedPlatform: score >= 90 ? 'zoom' : 'teams',

      // Horários sugeridos
      suggestedTimes: [
        { time: '10:00', reason: 'Horário ideal para entrevistas técnicas - candidato mais alerta' },
        { time: '14:00', reason: 'Pós-almoço, momento relaxado para avaliação comportamental' },
        { time: '16:00', reason: 'Final da tarde - bom para candidatos que trabalham' }
      ],

      // Foco da entrevista baseado no perfil
      interviewFocus: {
        technical: {
          weight: score >= 85 ? 40 : 60,
          topics: skills.slice(0, 3),
          approach: score >= 85 ? 'Validação de expertise avançada' : 'Avaliação de conhecimentos fundamentais'
        },
        behavioral: {
          weight: 30,
          topics: ['Trabalho em equipe', 'Resolução de problemas', 'Comunicação'],
          approach: seniorityLevel.toLowerCase().includes('senior') ? 'Foco em liderança e mentoria' : 'Foco em adaptabilidade e aprendizado'
        },
        cultural: {
          weight: 20,
          topics: ['Alinhamento com valores', 'Motivação', 'Objetivos de carreira'],
          approach: 'Avaliar fit com cultura organizacional'
        },
        company: {
          weight: 10,
          topics: ['Interesse na empresa', 'Conhecimento do mercado', 'Expectativas'],
          approach: 'Validar interesse genuíno na posição'
        }
      },

      // Perguntas sugeridas
      suggestedQuestions: {
        opening: [
          `Conte-me sobre sua experiência mais relevante como ${role}`,
          `O que te motivou a se candidatar para esta posição?`,
          `Como você descreveria seu estilo de trabalho?`
        ],
        technical: skills.slice(0, 3).map((skill: string) => `Descreva um projeto desafiador onde você utilizou ${skill}`),
        behavioral: [
          'Conte sobre uma situação onde você teve que resolver um conflito na equipe',
          'Descreva um momento onde você teve que aprender algo completamente novo rapidamente',
          'Como você lida com feedback negativo?'
        ],
        closing: [
          'Quais são suas expectativas para os próximos passos?',
          'Tem alguma dúvida sobre a empresa ou a posição?',
          'O que você espera encontrar nesta oportunidade?'
        ]
      },

      // Pontos de atenção
      attentionPoints: {
        strengths: [
          `Score alto de ${score}% indica forte compatibilidade`,
          `Experiência em ${skills[0]} alinhada com necessidades da vaga`,
          `Localização favorável: ${candidate.location}`
        ],
        concerns: score < 80 ? [
          'Score abaixo de 80% - investigar gaps específicos',
          'Verificar motivação real para mudança'
        ] : [
          'Candidato strong - verificar expectativas salariais',
          'Confirmar disponibilidade e interesse real'
        ],
        redFlags: [
          'Verificar estabilidade profissional',
          'Confirmar disponibilidade para início',
          'Validar expectativas de crescimento'
        ]
      },

      // Preparação do entrevistador
      preparation: {
        beforeInterview: [
          `Revisar currículo focando em experiência com ${skills.slice(0, 2).join(' e ')}`,
          'Preparar cenários práticos relacionados à vaga',
          'Definir critérios de avaliação específicos'
        ],
        duringInterview: [
          'Manter ambiente acolhedor mas profissional',
          'Fazer anotações sobre pontos técnicos e comportamentais',
          'Dar espaço para o candidato fazer perguntas'
        ],
        afterInterview: [
          'Preencher avaliação imediatamente',
          'Documentar impressões comportamentais',
          'Definir próximos passos com timeline'
        ]
      },

      // Configurações recomendadas
      settings: {
        sendReminder: true,
        reminderTime: '24h',
        includeCompanyInfo: true,
        includeInterviewerInfo: true,
        provideMaterials: score < 85
      }
    }
  }

  const applyLiaRecommendation = (type: string) => {
    if (!liaRecommendations) return

    switch (type) {
      case 'duration':
        setDuration(liaRecommendations.recommendedDuration)
        break
      case 'platform':
        setPlatform(liaRecommendations.recommendedPlatform)
        break
      case 'type':
        setScheduleType(liaRecommendations.recommendedType as 'video' | 'phone' | 'presential')
        break
      case 'notes': {
        const focusAreas = Object.entries(liaRecommendations.interviewFocus)
          .sort(([,a], [,b]) => ((b as { weight?: number }).weight ?? 0) - ((a as { weight?: number }).weight ?? 0))
          .slice(0, 2)
          .map(([key, value]) => `${key}: ${(value as { approach?: string }).approach ?? ''}`)
          .join('\n')
        const attentionPoints = (liaRecommendations as Record<string, unknown>).attentionPoints as Record<string, unknown> | undefined
        const strengths = (attentionPoints?.strengths as string[]) || []
        setNotes(`Foco da entrevista (sugerido por IA):\n\n${focusAreas}\n\nPontos de atenção:\n${strengths[0] || ''}`)
        break
      }
    }
  }


  const handleSchedule = async () => {
    setIsScheduling(true)

    try {
      const startTime = new Date(`${date}T${time}`)
      
      const interviewModeMap: Record<string, string> = {
        'phone': 'phone',
        'video': 'video', 
        'presential': 'in_person'
      }

      const response = await liaApi.createInterview({
        candidate_id: candidate.id,
        candidate_name: candidate.name,
        candidate_email: candidate.email,
        interviewer_name: interviewer.split(' - ')[0] || interviewer,
        interviewer_email: `${interviewer.split(' - ')[0]?.toLowerCase().replace(/\s+/g, '.')}@empresa.com`,
        start_time: startTime.toISOString(),
        duration_minutes: parseInt(duration),
        interview_type: 'screening',
        interview_mode: interviewModeMap[scheduleType] || 'video',
        job_title: candidate.role,
        location: scheduleType === 'presential' ? location : platform,
        notes: notes || (liaRecommendations ? `Recomendações de IA aplicadas: ${liaFocus}` : undefined)
      })

      setCreatedInterviewId(response.id)

      const scheduleData = {
        type: scheduleType,
        date,
        time,
        duration: parseInt(duration),
        interviewer,
        notes,
        location: scheduleType === 'presential' ? location : platform,
        candidateId: candidate.id,
        candidateName: candidate.name,
        candidateEmail: candidate.email,
        candidatePhone: candidate.phone,
        liaRecommendations: liaRecommendations || null,
        interviewId: response.id
      }

      onSchedule(scheduleType, `${date}T${time}`, scheduleData)

      const confirmMsg = `✅ Entrevista agendada com sucesso!\n\n` +
        `📅 Data: ${new Date(startTime).toLocaleDateString('pt-BR')} às ${time}\n` +
        `👤 Candidato: ${candidate.name}\n` +
        `🎥 Tipo: ${scheduleType === 'video' ? 'Videoconferência' : scheduleType === 'phone' ? 'Telefone' : 'Presencial'}\n` +
        `⏱️ Duração: ${duration} minutos\n\n` +
        `Status: Funcional - Aguardando Configuração Calendar\n` +
        `Os dados foram salvos no banco. Para sincronizar com calendário, configure Microsoft Graph ou Google Calendar.`

      alert(confirmMsg)
      onClose()
    } catch (error) {
      alert(`❌ Erro ao agendar entrevista: ${error instanceof Error ? error.message : 'Erro desconhecido'}`)
    } finally {
      setIsScheduling(false)
    }
  }

  const handleDownloadIcs = async () => {
    if (!createdInterviewId) return

    try {
      const blob = await liaApi.downloadInterviewIcs(createdInterviewId)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `entrevista_${candidate.name.replace(/\s+/g, '_')}.ics`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      alert('Erro ao baixar arquivo de calendário')
    }
  }

  return (
    <div className="fixed inset-0 bg-lia-overlay/70 backdrop-blur-[1px] z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="schedule-modal-title" className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle rounded-md w-full max-w-3xl max-h-[90vh] overflow-y-auto`} onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-5 dark:border-lia-border-subtle">
          <div className="flex items-center gap-3">
            <Avatar className="h-12 w-12">
              <AvatarImage src={candidate.avatar} />
              <AvatarFallback>{candidate.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
            </Avatar>
            <div>
              <h3 id="schedule-modal-title" className={`${textStyles.title}`}>
                Agendar Entrevista - {candidate.name}
              </h3>
              <p className={textStyles.bodySmall}>
                {candidate.role} • {candidate.location}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-xl text-lia-text-secondary hover:text-lia-text-secondary dark:hover:text-lia-text-tertiary hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan" aria-label="Fechar agendamento" data-dismiss="true">
            <X className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>

        <div className="p-5 space-y-6">
          {/* LIA Assistant */}
          <div className={`${cardStyles.flat} dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle p-4`}>
            <div className="flex items-center justify-between mb-3">
              <h4 className={`${textStyles.label} flex items-center gap-2`}>
                <Brain className="w-4 h-4 text-wedo-cyan" />
                IA - Recomendações Inteligentes
              </h4>
              <div className="flex items-center gap-2">
                <select
                  value={liaFocus}
                  onChange={(e) => setLiaFocus(e.target.value as 'comprehensive' | 'technical' | 'behavioral' | 'cultural')}
                  className="text-micro border border-lia-border-subtle rounded-md px-2 py-1 bg-lia-bg-primary focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20"
                >
                  <option value="comprehensive">Análise Completa</option>
                  <option value="technical">Foco Técnico</option>
                  <option value="behavioral">Foco Comportamental</option>
                  <option value="cultural">Foco Cultural</option>
                </select>
                <button
                  onClick={generateLiaRecommendations}
                  disabled={isLiaAnalyzing}
                  className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-xl border border-lia-border-subtle text-lia-text-primary hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none disabled:opacity-50"
                >
                  {isLiaAnalyzing ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                      Analisando...
                    </>
                  ) : (
                    <>
                      <Brain className="w-4 h-4 text-wedo-cyan" />
                      Analisar com IA
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* LIA Recommendations */}
            {showLiaInsights && (
              <div className="mt-4">
                {isLiaAnalyzing ? (
                  <div className="flex items-center justify-center py-6">
                    <div className="text-center">
                      <RefreshCw className="w-8 h-8 animate-spin motion-reduce:animate-none text-lia-text-secondary mx-auto mb-2" />
                      <p className="text-xs text-lia-text-secondary">LIA analisando perfil para recomendações...</p>
                    </div>
                  </div>
                ) : liaRecommendations && (
                  <div className="space-y-4">
                    {/* Quick Recommendations */}
                    <div className="grid grid-cols-3 gap-3">
                      <div className="text-center p-3 bg-lia-bg-primary rounded-xl border border-lia-border-subtle">
                        <div className="text-lg font-semibold text-lia-text-primary">{String((liaRecommendations as Record<string, unknown>).recommendedDuration ?? '')}min</div>
                        <div className="text-micro text-lia-text-secondary">Duração sugerida</div>
                        <button
                          onClick={() => applyLiaRecommendation('duration')}
                          className="text-micro mt-1 h-6 px-2 text-lia-text-primary hover:bg-lia-bg-secondary rounded-full transition-[width,height]"
                        >
                          Aplicar
                        </button>
                      </div>
                      <div className="text-center p-3 bg-lia-bg-primary rounded-xl border border-lia-border-subtle">
                        <div className="text-lg font-semibold text-lia-text-primary capitalize">{String((liaRecommendations as Record<string, unknown>).recommendedType ?? '')}</div>
                        <div className="text-micro text-lia-text-secondary">Tipo recomendado</div>
                        <button
                          onClick={() => applyLiaRecommendation('type')}
                          className="text-micro mt-1 h-6 px-2 text-lia-text-primary hover:bg-lia-bg-secondary rounded-full transition-[width,height]"
                        >
                          Aplicar
                        </button>
                      </div>
                      <div className="text-center p-3 bg-lia-bg-primary rounded-xl border border-lia-border-subtle">
                        <div className="text-lg font-semibold text-lia-text-primary capitalize">{String((liaRecommendations as Record<string, unknown>).recommendedPlatform ?? '')}</div>
                        <div className="text-micro text-lia-text-secondary">Plataforma sugerida</div>
                        <button
                          onClick={() => applyLiaRecommendation('platform')}
                          className="text-micro mt-1 h-6 px-2 text-lia-text-primary hover:bg-lia-bg-secondary rounded-full transition-[width,height]"
                        >
                          Aplicar
                        </button>
                      </div>
                    </div>

                    {/* Suggested Times */}
                    <div>
                      <h5 className="text-xs font-medium text-lia-text-primary mb-2">Horários Recomendados:</h5>
                      <div className="space-y-2">
                        {liaRecommendations.suggestedTimes.map((timeRec, idx: number) => (
                          <div key={idx} className="flex items-center justify-between p-2 bg-lia-bg-primary rounded-xl border border-lia-border-subtle">
                            <div>
                              <span className="font-medium text-lia-text-primary text-xs">{timeRec.time}</span>
                              <span className="text-micro text-lia-text-secondary ml-2">{timeRec.reason}</span>
                            </div>
                            <button
                              onClick={() => setTime(timeRec.time)}
                              className="text-micro h-6 px-2 text-lia-text-primary hover:bg-lia-bg-secondary rounded-full transition-[width,height]"
                            >
                              Usar
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Interview Focus */}
                    <div>
                      <h5 className="text-xs font-medium text-lia-text-primary mb-2">Foco da Entrevista:</h5>
                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(liaRecommendations.interviewFocus)
                          .sort(([,a], [,b]) => ((b as { weight?: number }).weight ?? 0) - ((a as { weight?: number }).weight ?? 0))
                          .slice(0, 4)
                          .map(([key, value]: [string, unknown]) => {
                            const v = value as { weight?: number; approach?: string }
                            return (
                          <div key={key} className="p-2 bg-lia-bg-primary rounded-xl border border-lia-border-subtle">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-micro font-medium text-lia-text-primary capitalize">{key}</span>
                              <span className="text-micro text-lia-text-secondary">{v.weight}%</span>
                            </div>
                            <p className="text-micro text-lia-text-secondary">{v.approach}</p>
                          </div>
                            )
                          })}
                      </div>
                      <button
                        onClick={() => applyLiaRecommendation('notes')}
                        className="text-micro mt-2 px-2 py-1 text-lia-text-primary hover:bg-lia-bg-secondary rounded-full transition-[width,height]"
                      >
                        Aplicar foco nas observações
                      </button>
                    </div>

                    {/* Key Insights */}
                    <div className="border-t border-lia-border-subtle pt-3">
                      <h5 className="text-xs font-medium text-lia-text-primary mb-2">Insights Principais:</h5>
                      <div className="grid grid-cols-1 gap-2">
                        <div>
                          <span className="text-micro font-medium text-lia-text-primary">Pontos Fortes:</span>
                          <ul className="text-micro text-lia-text-secondary ml-2">
                            {liaRecommendations.attentionPoints.strengths.slice(0, 2).map((strength: string, idx: number) => (
                              <li key={idx}>• {strength}</li>
                            ))}
                          </ul>
                        </div>
                        {liaRecommendations.attentionPoints.concerns.length > 0 && (
                          <div>
                            <span className="text-micro font-medium text-status-warning">Pontos de Atenção:</span>
                            <ul className="text-micro text-status-warning ml-2">
                              {liaRecommendations.attentionPoints.concerns.slice(0, 2).map((concern: string, idx: number) => (
                                <li key={idx}>• {concern}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Tipo de Entrevista */}
          <div>
            <h4 className="text-xs font-medium text-lia-text-primary mb-3">
              Tipo de Entrevista
            </h4>
            <div className="grid grid-cols-3 gap-3">
              {interviewTypes.map((type) => (
                <button
                  key={type.id}
                  onClick={() => setScheduleType(type.id as 'phone' | 'video' | 'presential')}
                  className={`p-4 border rounded-md text-left transition-colors motion-reduce:transition-none ${
 scheduleType === type.id
                      ? 'border-lia-border-default bg-lia-bg-tertiary'
                      : 'border-lia-border-subtle hover:bg-lia-bg-secondary hover:border-lia-border-subtle'
                  }`}
                >
                  <type.icon className={`w-5 h-5 mb-2 ${scheduleType === type.id ? 'text-lia-text-primary' : 'lia-text-secondary'}`} />
                  <div className="text-xs font-medium text-lia-text-primary">{type.name}</div>
                  <div className="text-micro text-lia-text-secondary">{type.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Data e Hora */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-lia-text-primary mb-1.5">
                Data
              </label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                min={new Date().toISOString().split('T')[0]}
                className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-xl focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-lia-text-primary mb-1.5">
                Horário
              </label>
              <input
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-xl focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-lia-text-primary mb-1.5">
                Duração (min)
              </label>
              <select
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-xl focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg"
              >
                <option value="30">30 minutos</option>
                <option value="45">45 minutos</option>
                <option value="60">1 hora</option>
                <option value="90">1h 30min</option>
                <option value="120">2 horas</option>
              </select>
            </div>
          </div>

          {/* Local/Plataforma */}
          {scheduleType === 'video' && (
            <div>
              <label className="block text-xs font-medium text-lia-text-primary mb-1.5">
                Plataforma
              </label>
              <div className="grid grid-cols-4 gap-2">
                {platforms.map((plat) => (
                  <button
                    key={plat.id}
                    onClick={() => setPlatform(plat.id)}
                    className={`p-3 border rounded-md text-center transition-colors motion-reduce:transition-none ${
 platform === plat.id
                        ? 'border-lia-border-default bg-lia-bg-tertiary'
                        : 'border-lia-border-subtle hover:bg-lia-bg-secondary hover:border-lia-border-subtle'
                    }`}
                  >
                    <plat.icon className={`w-5 h-5 mx-auto mb-1 ${platform === plat.id ? 'text-lia-text-primary' : 'lia-text-secondary'}`} />
                    <div className="text-micro text-lia-text-primary">{plat.name}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {scheduleType === 'presential' && (
            <div>
              <label className="block text-xs font-medium text-lia-text-primary mb-1.5">
                Local da Entrevista
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-md placeholder:lia-text-secondary focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg dark:bg-lia-bg-secondary dark:border-lia-border-default"
                placeholder="Endereço completo ou sala"
              />
            </div>
          )}

          {/* Entrevistador */}
          <div>
            <label className="block text-xs font-medium text-lia-text-primary mb-1.5">
              Entrevistador Responsável
            </label>
            <select
              value={interviewer}
              onChange={(e) => setInterviewer(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-xl focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg"
            >
              <option value="">Selecione o entrevistador</option>
              {interviewers.map((person) => (
                <option key={person} value={person}>{person}</option>
              ))}
            </select>
          </div>

          {/* Observações */}
          <div>
            <label className="block text-xs font-medium text-lia-text-primary mb-1.5">
              Observações para a Entrevista
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-md placeholder:lia-text-secondary focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg dark:bg-lia-bg-secondary dark:border-lia-border-default"
              placeholder="Pontos específicos a abordar, preparações necessárias..."
            />
          </div>

          {/* Status Info */}
          <div className="bg-status-warning/10 border border-status-warning/30 rounded-xl p-3">
            <div className="flex items-center gap-2 text-status-warning">
              <Info className="w-4 h-4" />
              <span className="text-xs font-medium">Funcional - Aguardando Configuração Calendar</span>
            </div>
            <p className="text-micro text-status-warning mt-1">
              Entrevistas são salvas no banco de dados. Para sincronização automática com calendários, configure Microsoft Graph ou Google Calendar.
            </p>
          </div>

          {/* Ações */}
          <div className="flex justify-end gap-3 pt-5 border-t border-lia-border-subtle">
            <button
              onClick={onClose}
              className="px-3 py-1.5 text-xs font-medium rounded-xl border border-lia-border-subtle bg-lia-bg-primary text-lia-text-primary hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
            >
              Cancelar
            </button>
            {createdInterviewId && (
              <button
                onClick={handleDownloadIcs}
                className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-xl border border-lia-border-subtle bg-lia-bg-primary text-lia-text-primary hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
              >
                <Download className="w-4 h-4" />
                Baixar .ICS
              </button>
            )}
            <button
              onClick={handleSchedule}
              disabled={!date || !time || !interviewer || isScheduling}
              className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-md bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text transition-colors motion-reduce:transition-none disabled:opacity-50"
            >
              {isScheduling ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                  Agendando...
                </>
              ) : (
                <>
                  <Calendar className="w-4 h-4" />
                  Agendar Entrevista
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

