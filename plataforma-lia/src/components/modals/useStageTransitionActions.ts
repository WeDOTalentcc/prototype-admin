"use client"

import { useState, useEffect, useCallback } from "react"
import { toast } from "sonner"
import { useCommunicationTemplates, type CommunicationTemplate, type TemplateSituation } from "@/hooks/chat/use-communication-templates"
import {
  type TransitionActionType,
  type Candidate,
  type JobVacancy,
  type WsiData,
  type TransitionAction,
  getSuggestedActions,
  generateDefaultMessage,
  getStageDisplayName,
  mapTemplateCategoryToSituations,
} from "./stage-transition-helpers"

interface UseStageTransitionActionsParams {
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
    metadata?: Record<string, unknown>
  }) => Promise<void>
}

export function useStageTransitionActions({
  isOpen, onClose, candidate, job, currentStage, newStage, wsiData, onConfirm
}: UseStageTransitionActionsParams) {
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
  }, [isOpen, currentStage, newStage, suggestedActions])

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
  }, [isOpen, selectedAction, channel, regenerateMessage])

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
      toast.error('Erro ao executar ação', {
        description: 'Tente novamente ou contate o suporte',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const needsMessageComposition = selectedAction && selectedAction !== 'apenas_mover'

  return {
    selectedAction, setSelectedAction,
    channel, setChannel,
    selectedTemplateId,
    subject, setSubject,
    message, handleMessageChange,
    isLoading, isRegenerating,
    isMessageEdited, showPulse,
    suggestedActions, selectedActionData,
    filteredTemplates, isLoadingTemplates,
    needsMessageComposition,
    regenerateMessage,
    handleTemplateSelect,
    handleConfirm,
  }
}
