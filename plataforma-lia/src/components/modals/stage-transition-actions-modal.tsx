"use client"

import React, { useState, useEffect, useCallback } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Mail,
  MessageSquare,
  Calendar,
  ArrowRight,
  Send,
  X,
  Check,
  Eye,
  Loader2,
  ClipboardList,
  ChevronRight,
  AlertCircle,
  Brain,
  Edit3,
  RefreshCw,
} from "lucide-react"
import { toast } from "sonner"
import { textStyles, cardStyles, badgeStyles } from "@/lib/design-tokens"
import { RECRUITMENT_STAGES, type RecruitmentStage } from "@/lib/recruitment-stages"
import { cn } from "@/lib/utils"
import { useCommunicationTemplates, type CommunicationTemplate, type TemplateSituation } from "@/hooks/use-communication-templates"

export type TransitionActionType = 'email' | 'whatsapp' | 'triagem_wsi' | 'agendar_entrevista' | 'apenas_mover'

interface Candidate {
  id: string
  name: string
  email?: string
  phone?: string
  avatar?: string
  current_title?: string
  current_company?: string
}

interface JobVacancy {
  id: string
  title: string
  department?: string
  location?: string
}

interface TransitionAction {
  id: TransitionActionType
  name: string
  description: string
  icon: React.ReactNode
  color: 'cyan' | 'blue' | 'green' | 'amber' | 'red' | 'gray'
  recommended?: boolean
  templateCategory?: 'interview' | 'rejection' | 'offer' | 'followup' | 'screening'
}

interface WsiData {
  overall_wsi: number
  technical_wsi: number
  behavioral_wsi: number
  classification: string
}

interface StageTransitionActionsModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: Candidate | null
  job: JobVacancy | null
  currentStage: string
  newStage: string
  wsiData?: WsiData
  onConfirm: (action: TransitionActionType, data?: {
    channel?: 'email' | 'whatsapp' | 'both'
    templateId?: string
    subject?: string
    message?: string
    metadata?: any
  }) => Promise<void>
}

const COLOR_CLASSES = {
  cyan: {
    bg: 'bg-gray-50 dark:bg-gray-800',
    border: 'border-gray-200 dark:border-gray-700',
    text: 'text-gray-700 dark:text-gray-300',
    icon: 'text-gray-600 dark:text-gray-400',
    selectedBg: 'bg-gray-100 dark:bg-gray-800',
    selectedBorder: 'border-gray-900 dark:border-gray-50',
  },
  blue: {
    bg: 'bg-gray-50 dark:bg-gray-800',
    border: 'border-gray-200 dark:border-gray-700',
    text: 'text-gray-700 dark:text-gray-300',
    icon: 'text-gray-600 dark:text-gray-400',
    selectedBg: 'bg-gray-50 dark:bg-gray-700',
    selectedBorder: 'border-gray-900 dark:border-gray-300',
  },
  green: {
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    text: 'text-emerald-700',
    icon: 'text-emerald-600',
    selectedBg: 'bg-emerald-100',
    selectedBorder: 'border-emerald-400',
  },
  amber: {
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    text: 'text-amber-700',
    icon: 'text-amber-600',
    selectedBg: 'bg-amber-100',
    selectedBorder: 'border-amber-400',
  },
  red: {
    bg: 'bg-red-50',
    border: 'border-red-200',
    text: 'text-red-700',
    icon: 'text-red-600',
    selectedBg: 'bg-red-100',
    selectedBorder: 'border-red-400',
  },
  gray: {
    bg: 'bg-gray-50',
    border: 'border-gray-200',
    text: 'text-gray-800',
    icon: 'text-gray-600',
    selectedBg: 'bg-gray-50',
    selectedBorder: 'border-gray-900',
  },
}

function getStageDisplayName(stageName: string): string {
  const stage = RECRUITMENT_STAGES.find(s => s.name === stageName)
  return stage?.displayName || stageName
}

function mapTemplateCategoryToSituations(templateCategory: string): TemplateSituation[] {
  switch (templateCategory) {
    case 'rejection':
      return ['feedback_construtivo', 'vaga_fechada']
    case 'interview':
      return ['agendamento']
    case 'screening':
      return ['triagem']
    case 'offer':
      return ['proposta', 'proposta_aceita']
    case 'followup':
      return ['contato_inicial', 'follow_up']
    default:
      return ['contato_inicial', 'follow_up']
  }
}

function getSuggestedActions(currentStage: string, newStage: string): TransitionAction[] {
  const baseActions: TransitionAction[] = []

  const newStageData = RECRUITMENT_STAGES.find(s => s.name === newStage)

  if (newStageData?.isRejection) {
    baseActions.push({
      id: 'email',
      name: 'Enviar feedback por email',
      description: 'Comunicar resultado negativo de forma profissional',
      icon: <Mail className="h-4 w-4" />,
      color: 'red',
      recommended: true,
      templateCategory: 'rejection',
    })
    baseActions.push({
      id: 'whatsapp',
      name: 'Enviar feedback por WhatsApp',
      description: 'Comunicação rápida via WhatsApp',
      icon: <MessageSquare className="h-4 w-4" />,
      color: 'red',
      templateCategory: 'rejection',
    })
  } else if (newStage === 'screening' || currentStage === 'sourcing') {
    baseActions.push({
      id: 'triagem_wsi',
      name: 'Convidar para Triagem WSI',
      description: 'Enviar convite para triagem com a LIA',
      icon: <ClipboardList className="h-4 w-4" />,
      color: 'cyan',
      recommended: true,
      templateCategory: 'screening',
    })
    baseActions.push({
      id: 'email',
      name: 'Enviar email de contato',
      description: 'Primeiro contato por email',
      icon: <Mail className="h-4 w-4" />,
      color: 'blue',
      templateCategory: 'followup',
    })
  } else if (newStage === 'long_list' || newStage === 'short_list') {
    baseActions.push({
      id: 'email',
      name: 'Enviar email de aprovação',
      description: 'Comunicar avanço no processo seletivo',
      icon: <Mail className="h-4 w-4" />,
      color: 'blue',
      recommended: true,
      templateCategory: 'followup',
    })
    baseActions.push({
      id: 'whatsapp',
      name: 'Enviar WhatsApp de aprovação',
      description: 'Comunicação rápida de aprovação',
      icon: <MessageSquare className="h-4 w-4" />,
      color: 'blue',
      templateCategory: 'followup',
    })
  } else if (newStage.includes('interview')) {
    baseActions.push({
      id: 'agendar_entrevista',
      name: 'Agendar entrevista',
      description: 'Enviar convite para agendamento de entrevista',
      icon: <Calendar className="h-4 w-4" />,
      color: 'blue',
      recommended: true,
      templateCategory: 'interview',
    })
    baseActions.push({
      id: 'email',
      name: 'Enviar convite por email',
      description: 'Enviar email com detalhes da entrevista',
      icon: <Mail className="h-4 w-4" />,
      color: 'blue',
      templateCategory: 'interview',
    })
  } else if (newStage === 'offer') {
    baseActions.push({
      id: 'email',
      name: 'Enviar proposta por email',
      description: 'Enviar proposta formal de contratação',
      icon: <Mail className="h-4 w-4" />,
      color: 'green',
      recommended: true,
      templateCategory: 'offer',
    })
  } else if (newStage === 'hired') {
    baseActions.push({
      id: 'email',
      name: 'Enviar boas-vindas',
      description: 'Email de boas-vindas e próximos passos',
      icon: <Mail className="h-4 w-4" />,
      color: 'green',
      recommended: true,
      templateCategory: 'offer',
    })
  } else {
    baseActions.push({
      id: 'email',
      name: 'Enviar email',
      description: 'Comunicar atualização do processo',
      icon: <Mail className="h-4 w-4" />,
      color: 'blue',
      templateCategory: 'followup',
    })
    baseActions.push({
      id: 'whatsapp',
      name: 'Enviar WhatsApp',
      description: 'Comunicação rápida via WhatsApp',
      icon: <MessageSquare className="h-4 w-4" />,
      color: 'blue',
      templateCategory: 'followup',
    })
  }

  baseActions.push({
    id: 'apenas_mover',
    name: 'Apenas mover',
    description: 'Mover sem enviar comunicação',
    icon: <ArrowRight className="h-4 w-4" />,
    color: 'gray',
  })

  return baseActions
}

function generateDefaultMessage(
  action: TransitionAction,
  candidate: Candidate | null,
  job: JobVacancy | null,
  newStage: string,
  wsiData?: WsiData
): { subject: string; message: string } {
  const candidateName = candidate?.name || 'Candidato'
  const jobTitle = job?.title || 'a vaga'
  const firstName = candidateName.split(' ')[0]

  if (action.templateCategory === 'rejection') {
    const wsiParagraph = wsiData
      ? `\n\nSua avaliação indicou uma compatibilidade de ${wsiData.overall_wsi}% com os requisitos da posição.`
      : ''
    return {
      subject: `Retorno sobre sua candidatura - ${jobTitle}`,
      message: `Olá ${firstName},\n\nAgradecemos seu interesse e participação em nosso processo seletivo para ${jobTitle}.\n\nApós análise cuidadosa, decidimos seguir com outros candidatos cujos perfis estão mais alinhados com as necessidades atuais da posição.${wsiParagraph}\n\nMantemos seu currículo em nosso banco de talentos para futuras oportunidades.\n\nDesejamos sucesso em sua carreira!\n\nAtenciosamente,\nEquipe de Recrutamento`,
    }
  }

  if (action.templateCategory === 'interview') {
    const wsiParagraph = wsiData
      ? `\n\nSua avaliação na triagem foi muito positiva (${wsiData.classification}), o que reforça nosso interesse em conhecê-lo(a) melhor.`
      : ''
    return {
      subject: `Convite para entrevista - ${jobTitle}`,
      message: `Olá ${firstName},\n\nParabéns por avançar em nosso processo seletivo para ${jobTitle}! 🎉\n\nGostaríamos de convidá-lo(a) para a próxima etapa: uma entrevista.${wsiParagraph}\n\nPor favor, clique no link abaixo para escolher o melhor horário:\n[Link para agendamento]\n\nCaso tenha alguma dúvida, estamos à disposição.\n\nAtenciosamente,\nEquipe de Recrutamento`,
    }
  }

  if (action.templateCategory === 'offer') {
    return {
      subject: `Proposta de contratação - ${jobTitle}`,
      message: `Olá ${firstName},\n\nÉ com grande satisfação que comunicamos que você foi selecionado(a) para a posição de ${jobTitle}!\n\nAnexo a esta mensagem você encontrará nossa proposta formal de contratação.\n\nAguardamos seu retorno em até 5 dias úteis.\n\nEstamos muito animados com a possibilidade de tê-lo(a) em nossa equipe!\n\nAtenciosamente,\nEquipe de Recrutamento`,
    }
  }

  if (action.templateCategory === 'screening') {
    return {
      subject: `Próximo passo: Avaliação - ${jobTitle}`,
      message: `Olá ${firstName},\n\nEstamos avançando em nosso processo seletivo para ${jobTitle} e gostaríamos de convidá-lo(a) para uma triagem rápida com a nossa assistente LIA.\n\n📋 Sobre a triagem:\n• Duração estimada: 15-20 minutos\n• Formato: Conversa por chat ou WhatsApp\n• Objetivo: Conhecer melhor sua forma de pensar e resolver problemas\n\nClique no link abaixo para iniciar:\n[Link para triagem]\n\nQualquer dúvida, estamos à disposição!\n\nAtenciosamente,\nEquipe de Recrutamento`,
    }
  }

  const wsiFollowupParagraph = wsiData
    ? `\n\nSua avaliação na triagem foi muito positiva (${wsiData.classification}), o que reforça nosso interesse em conhecê-lo(a) melhor.`
    : ''
  return {
    subject: `Atualização do processo seletivo - ${jobTitle}`,
    message: `Olá ${firstName},\n\nGostaríamos de informar que você avançou para a próxima etapa do processo seletivo para ${jobTitle}!${wsiFollowupParagraph}\n\nEm breve entraremos em contato com mais detalhes sobre os próximos passos.\n\nQualquer dúvida, estamos à disposição.\n\nAtenciosamente,\nEquipe de Recrutamento`,
  }
}

function getWsiClassificationColor(classification: string): { bg: string; text: string } {
  const lower = classification.toLowerCase()
  if (lower === 'excelente' || lower === 'alto') {
    return { bg: 'bg-emerald-100', text: 'text-emerald-700' }
  }
  if (lower === 'medio' || lower === 'médio') {
    return { bg: 'bg-amber-100', text: 'text-amber-700' }
  }
  return { bg: 'bg-red-100', text: 'text-red-700' }
}

export function StageTransitionActionsModal({
  isOpen,
  onClose,
  candidate,
  job,
  currentStage,
  newStage,
  wsiData,
  onConfirm,
}: StageTransitionActionsModalProps) {
  const [selectedAction, setSelectedAction] = useState<TransitionActionType | null>(null)
  const [channel, setChannel] = useState<'email' | 'whatsapp' | 'both'>('email')
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('')
  const [subject, setSubject] = useState('')
  const [message, setMessage] = useState('')
  const [originalMessage, setOriginalMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [isMessageEdited, setIsMessageEdited] = useState(false)
  const [showPulse, setShowPulse] = useState(false)

  const suggestedActions = getSuggestedActions(currentStage, newStage)

  const { templates: allTemplates, loading: isLoadingTemplates } = useCommunicationTemplates()

  const getFilteredTemplates = useCallback((templateCategory?: string): CommunicationTemplate[] => {
    if (!templateCategory) return []
    
    const situations = mapTemplateCategoryToSituations(templateCategory)
    
    const filterChannel = channel === 'both' ? 'email' : channel
    return allTemplates.filter(t => {
      const matchesChannel = t.channel === filterChannel
      const matchesSituation = situations.includes(t.situation as TemplateSituation)
      return matchesChannel && matchesSituation && t.isActive
    })
  }, [allTemplates, channel])

  const selectedActionData = suggestedActions.find(a => a.id === selectedAction)
  const filteredTemplates = getFilteredTemplates(selectedActionData?.templateCategory)

  useEffect(() => {
    if (isOpen) {
      const recommended = suggestedActions.find(a => a.recommended)
      setSelectedAction(recommended?.id || 'apenas_mover')
      setChannel('email')
      setSelectedTemplateId('')
      setSubject('')
      setMessage('')
      setOriginalMessage('')
      setIsMessageEdited(false)
      setShowPulse(false)
    }
  }, [isOpen, currentStage, newStage])

  const regenerateMessage = useCallback(async () => {
    if (!selectedAction || selectedAction === 'apenas_mover') return
    
    setIsRegenerating(true)
    
    const action = suggestedActions.find(a => a.id === selectedAction)
    
    try {
      const response = await fetch('/api/backend-proxy/stage-automation/generate-message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_context: {
            id: candidate?.id,
            name: candidate?.name,
            email: candidate?.email,
            phone: candidate?.phone,
            current_title: candidate?.current_title,
          },
          job_context: {
            id: job?.id,
            title: job?.title,
            department: job?.department,
          },
          to_stage: newStage,
          substatus: 'profile_not_aligned',
          message_type: action?.templateCategory || 'feedback_construtivo',
          channel: channel === 'both' ? 'email' : channel
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.subject) setSubject(data.subject)
        if (data.body) {
          setMessage(data.body)
          setOriginalMessage(data.body)
          setIsMessageEdited(false)
        }
      } else {
        if (action) {
          const defaultContent = generateDefaultMessage(action, candidate, job, newStage, wsiData)
          setSubject(defaultContent.subject)
          setMessage(defaultContent.message)
          setOriginalMessage(defaultContent.message)
          setIsMessageEdited(false)
        }
      }
    } catch (err) {
      console.error('Error generating message:', err)
      if (action) {
        const defaultContent = generateDefaultMessage(action, candidate, job, newStage, wsiData)
        setSubject(defaultContent.subject)
        setMessage(defaultContent.message)
        setOriginalMessage(defaultContent.message)
        setIsMessageEdited(false)
      }
    }
    
    setIsRegenerating(false)
    setShowPulse(true)
    setTimeout(() => setShowPulse(false), 1000)
  }, [selectedAction, suggestedActions, candidate, job, newStage, channel, wsiData])

  useEffect(() => {
    if (isOpen && selectedAction && selectedAction !== 'apenas_mover') {
      regenerateMessage()
    }
  }, [isOpen, selectedAction, channel])

  const handleTemplateSelect = (template: CommunicationTemplate) => {
    setSelectedTemplateId(template.id)
    setSubject(template.subject)
    setMessage(template.body)
    setOriginalMessage(template.body)
    setIsMessageEdited(false)
  }

  const handleMessageChange = (value: string) => {
    setMessage(value)
    setIsMessageEdited(value !== originalMessage)
  }

  const handleConfirm = async () => {
    if (!selectedAction) return

    setIsLoading(true)
    try {
      await onConfirm(selectedAction, {
        channel: selectedAction === 'email' || selectedAction === 'whatsapp' ? channel : undefined,
        templateId: selectedTemplateId || undefined,
        subject: subject || undefined,
        message: message || undefined,
      })

      if (selectedAction === 'apenas_mover') {
        toast.success('Candidato movido com sucesso', {
          description: `${candidate?.name} foi movido para ${getStageDisplayName(newStage)}`,
        })
      } else if ((selectedAction === 'email' || selectedAction === 'whatsapp') && channel === 'both') {
        toast.success('Mensagem enviada por email e WhatsApp', {
          description: `Comunicação enviada para ${candidate?.email} e ${candidate?.phone}`,
        })
      } else if (selectedAction === 'email') {
        toast.success('Email enviado com sucesso', {
          description: `Mensagem enviada para ${candidate?.email}`,
        })
      } else if (selectedAction === 'whatsapp') {
        toast.success('WhatsApp enviado com sucesso', {
          description: `Mensagem enviada para ${candidate?.phone}`,
        })
      } else if (selectedAction === 'triagem_wsi') {
        toast.success('Convite de triagem enviado', {
          description: `${candidate?.name} receberá o convite para triagem WSI`,
        })
      } else if (selectedAction === 'agendar_entrevista') {
        toast.success('Convite de entrevista enviado', {
          description: `${candidate?.name} receberá o convite para agendar`,
        })
      }

      onClose()
    } catch (error) {
      console.error('Error confirming action:', error)
      toast.error('Erro ao executar ação', {
        description: 'Tente novamente ou contate o suporte',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const needsMessageComposition = selectedAction && selectedAction !== 'apenas_mover'
  const newStageData = RECRUITMENT_STAGES.find(s => s.name === newStage)
  const headerColor = newStageData?.isRejection ? 'red' : 'gray'

  if (!isOpen || !candidate) return null

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col p-0">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gray-50/50">
          <div className="flex items-center gap-3">
            <div className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center",
              headerColor === 'red' ? 'bg-red-100' : 'bg-gray-100'
            )}>
              <ArrowRight className={cn(
                "w-4 h-4",
                headerColor === 'red' ? 'text-red-600' : 'text-gray-600'
              )} />
            </div>
            <div>
              <h3 className={cn(textStyles.title, "font-['Open_Sans',sans-serif]")}>
                Mover Candidato
              </h3>
              <p className={textStyles.description}>
                Escolha uma ação de comunicação para acompanhar a mudança de estágio
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-md text-gray-600 hover:text-gray-800 hover:bg-gray-100 transition-all">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Main Content - 2 Column Layout */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left Panel - Form */}
          <div className="w-1/2 border-r border-gray-100 overflow-y-auto">
            <div className="p-5 space-y-5">
              {/* Candidate Info */}
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-md border border-gray-100">
                <div className="flex items-center gap-3">
                  <Avatar className="h-10 w-10">
                    <AvatarImage src={candidate.avatar} />
                    <AvatarFallback className="bg-gray-100 text-gray-600 text-xs">
                      {candidate.name?.charAt(0) || '?'}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <p className={textStyles.subtitle}>{candidate.name}</p>
                    <p className={textStyles.caption}>
                      {candidate.current_title}
                      {candidate.current_company && ` @ ${candidate.current_company}`}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge className={badgeStyles.default}>
                    {getStageDisplayName(currentStage)}
                  </Badge>
                  <ChevronRight className="h-4 w-4 text-gray-400" />
                  <Badge className={cn(
                    "text-white",
                    headerColor === 'red' ? 'bg-red-500' : 'bg-gray-900'
                  )}>
                    {getStageDisplayName(newStage)}
                  </Badge>
                </div>
              </div>

              {wsiData && (
                <div className="flex items-center gap-2 mt-2">
                  <Badge className={cn(
                    "text-xs px-2 py-0.5 font-medium",
                    getWsiClassificationColor(wsiData.classification).bg,
                    getWsiClassificationColor(wsiData.classification).text
                  )}>
                    WSI: {wsiData.overall_wsi}% ({wsiData.classification})
                  </Badge>
                </div>
              )}

              {job && (
                <div className="flex items-center gap-2 text-gray-600">
                  <span className={textStyles.caption}>Vaga:</span>
                  <span className={textStyles.label}>{job.title}</span>
                  {job.department && (
                    <span className={textStyles.caption}>• {job.department}</span>
                  )}
                </div>
              )}

              {/* Action Selection - Card Style */}
              <div className="space-y-3">
                <p className={cn(textStyles.label, "mb-2")}>Selecione uma ação:</p>
                <div className="grid gap-2">
                  {suggestedActions.map((action) => {
                    const colors = COLOR_CLASSES[action.color]
                    const isSelected = selectedAction === action.id

                    return (
                      <button
                        key={action.id}
                        onClick={() => setSelectedAction(action.id)}
                        className={cn(
                          "flex items-center gap-3 p-3 rounded-md border transition-all text-left",
                          isSelected
                            ? cn(colors.selectedBg, colors.selectedBorder, "ring-1", action.color === 'cyan' ? "ring-gray-900/20" : action.color === 'red' ? "ring-red-300" : action.color === 'green' ? "ring-emerald-300" : "ring-gray-300")
                            : cn(colors.bg, colors.border, "hover:border-gray-300")
                        )}
                      >
                        <div className={cn(
                          "flex items-center justify-center w-8 h-8 rounded-full",
                          isSelected ? colors.selectedBg : colors.bg
                        )}>
                          <span className={colors.icon}>{action.icon}</span>
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className={cn(textStyles.subtitle, colors.text)}>
                              {action.name}
                            </span>
                            {action.recommended && (
                              <Badge className="bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-50 text-micro px-1.5 py-0">
                                <Brain className="h-3 w-3 mr-0.5 text-wedo-cyan" />
                                Recomendado
                              </Badge>
                            )}
                          </div>
                          <p className={textStyles.caption}>{action.description}</p>
                        </div>
                        {isSelected && (
                          <Check className={cn("h-5 w-5", colors.icon)} />
                        )}
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* Channel Selection - Big Cards */}
              {needsMessageComposition && selectedAction !== 'triagem_wsi' && selectedAction !== 'agendar_entrevista' && (
                <div className="space-y-2">
                  <p className={textStyles.label}>Canal de Envio</p>
                  <div className="grid grid-cols-3 gap-2">
                    <button
                      onClick={() => setChannel('email')}
                      className={cn(
                        "flex items-center gap-2 p-3 rounded-md border transition-all",
                        channel === 'email'
                          ? 'border-gray-900 bg-gray-50 text-gray-900'
                          : 'border-gray-200 hover:border-gray-300 text-gray-800'
                      )}
                    >
                      <Mail className="w-4 h-4" />
                      <div className="text-left">
                        <div className="text-xs font-medium">Email</div>
                        <div className="text-micro opacity-70 truncate max-w-[120px]">{candidate.email || 'Não informado'}</div>
                      </div>
                    </button>
                    <button
                      onClick={() => setChannel('whatsapp')}
                      className={cn(
                        "flex items-center gap-2 p-3 rounded-md border transition-all",
                        channel === 'whatsapp'
                          ? 'border-green-500 bg-green-50 text-green-600'
                          : 'border-gray-200 hover:border-gray-300 text-gray-800'
                      )}
                    >
                      <MessageSquare className="w-4 h-4" />
                      <div className="text-left">
                        <div className="text-xs font-medium">WhatsApp</div>
                        <div className="text-micro opacity-70">{candidate.phone || 'Não informado'}</div>
                      </div>
                    </button>
                    <button
                      onClick={() => setChannel('both')}
                      className={cn(
                        "flex items-center gap-2 p-3 rounded-md border transition-all",
                        channel === 'both'
                          ? 'border-gray-900 bg-gray-50 text-gray-900'
                          : 'border-gray-200 hover:border-gray-300 text-gray-800'
                      )}
                    >
                      <div className="flex items-center -space-x-1">
                        <Mail className="w-3.5 h-3.5" />
                        <MessageSquare className="w-3.5 h-3.5" />
                      </div>
                      <div className="text-left">
                        <div className="text-xs font-medium">Ambos</div>
                        <div className="text-micro opacity-70">Email + WA</div>
                      </div>
                    </button>
                  </div>
                </div>
              )}

              {/* Template Selection */}
              {needsMessageComposition && filteredTemplates.length > 0 && (
                <div className="space-y-2">
                  <p className={textStyles.label}>Template (opcional)</p>
                  <Select
                    value={selectedTemplateId}
                    onValueChange={(value) => {
                      const template = filteredTemplates.find(t => t.id === value)
                      if (template) handleTemplateSelect(template)
                    }}
                  >
                    <SelectTrigger className="text-xs">
                      <SelectValue placeholder="Selecionar template..." />
                    </SelectTrigger>
                    <SelectContent className="z-[9999]">
                      {filteredTemplates.map(t => (
                        <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {/* Contact Info Alert */}
              {needsMessageComposition && (
                <div className="flex items-center gap-2 p-2 bg-amber-50 rounded-md border border-amber-100">
                  <AlertCircle className="h-4 w-4 text-amber-600 shrink-0" />
                  <p className="text-xs text-amber-700">
                    {channel === 'both' && candidate.email && candidate.phone
                      ? `Email para: ${candidate.email} + WhatsApp para: ${candidate.phone}`
                      : channel === 'both'
                      ? 'Verifique se o candidato possui email e telefone cadastrados'
                      : channel === 'email' && candidate.email
                      ? `Email será enviado para: ${candidate.email}`
                      : channel === 'whatsapp' && candidate.phone
                      ? `WhatsApp será enviado para: ${candidate.phone}`
                      : 'Verifique se o candidato possui email/telefone cadastrado'}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Right Panel - Preview */}
          <div className="w-1/2 bg-gray-50/50 overflow-y-auto">
            <div className="p-5 space-y-4">
              {needsMessageComposition ? (
                <>
                  {/* LIA Info Card */}
                  <div className="flex items-start gap-2 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-md border border-gray-300 dark:border-gray-600">
                    <Brain className="w-4 h-4 text-wedo-cyan mt-0.5 shrink-0" />
                    <div>
                      <p className="text-xs text-gray-900 dark:text-gray-50 font-medium">
                        LIA personalizou esta mensagem considerando:
                      </p>
                      <p className="text-micro text-gray-600 mt-0.5">
                        nome, cargo, vaga e contexto do candidato
                      </p>
                      {isMessageEdited && (
                        <p className="text-micro text-gray-600 mt-1 flex items-center gap-1">
                          <Edit3 className="w-3 h-3" />
                          (mensagem editada por você)
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <p className={cn(textStyles.label, "flex items-center gap-2")}>
                      {channel === 'both' ? (
                        <span className="flex items-center -space-x-1">
                          <Mail className="h-4 w-4 text-gray-500" />
                          <MessageSquare className="h-4 w-4 text-green-500" />
                        </span>
                      ) : channel === 'email' ? <Mail className="h-4 w-4 text-gray-500" /> : <MessageSquare className="h-4 w-4 text-green-500" />}
                      Preview da Mensagem
                    </p>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={regenerateMessage}
                      disabled={isRegenerating}
                      className="h-7 text-xs"
                    >
                      <RefreshCw className={cn("h-3 w-3 mr-1", isRegenerating && "animate-spin")} />
                      Regenerar
                    </Button>
                  </div>

                  {isLoadingTemplates ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
                    </div>
                  ) : (
                    <div className="relative">
                      {/* Regenerating Overlay */}
                      {isRegenerating && (
                        <div className="absolute inset-0 bg-white/80 rounded-md flex items-center justify-center z-10">
                          <div className="flex items-center gap-2">
                            <Loader2 className="h-4 w-4 animate-spin text-gray-600" />
                            <span className="text-xs text-gray-600 font-medium">LIA regenerando mensagem...</span>
                          </div>
                        </div>
                      )}

                      <div className={cn(
                        "space-y-3 transition-all",
                        showPulse && "animate-pulse"
                      )}>
                        {(channel === 'email' || channel === 'both' || selectedAction === 'triagem_wsi' || selectedAction === 'agendar_entrevista') && (
                          <div>
                            <label className={textStyles.caption}>Assunto</label>
                            <Input
                              value={subject}
                              onChange={(e) => setSubject(e.target.value)}
                              placeholder="Assunto do email"
                              className="text-xs mt-1"
                            />
                          </div>
                        )}
                        <div>
                          <label className={textStyles.caption}>Mensagem</label>
                          <Textarea
                            value={message}
                            onChange={(e) => handleMessageChange(e.target.value)}
                            placeholder="Escreva sua mensagem..."
                            className="min-h-[250px] text-xs resize-y mt-1"
                          />
                        </div>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mb-3">
                    <ArrowRight className="w-6 h-6 text-gray-400" />
                  </div>
                  <p className={textStyles.subtitle}>Apenas mover candidato</p>
                  <p className={cn(textStyles.caption, "mt-1 max-w-[250px]")}>
                    O candidato será movido para a nova etapa sem envio de comunicação
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100 bg-white">
          <Button 
            variant="outline" 
            onClick={onClose} 
            disabled={isLoading}
            className="h-9 px-4 text-xs font-medium border border-gray-300 text-gray-700 hover:bg-gray-50"
          >
            Cancelar
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={!selectedAction || isLoading}
            className={cn(
              "gap-2 h-9 px-4 text-xs font-medium",
              selectedActionData?.color === 'red'
                ? "bg-red-500 hover:bg-red-600 text-white"
                : "bg-gray-900 text-white hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
            )}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Processando...
              </>
            ) : (
              <>
                {selectedAction === 'apenas_mover' ? (
                  <>
                    <ArrowRight className="w-3.5 h-3.5" />
                    Mover
                  </>
                ) : (
                  <>
                    <Send className="w-3.5 h-3.5" />
                    Confirmar e Enviar
                  </>
                )}
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default StageTransitionActionsModal
