"use client"

import { useState, useEffect } from 'react'
import { useInterpretContext, type ChatMessage } from '@/hooks/shared/use-interpret-context'
import { useTransitionContext, type CandidateContext, type JobContext } from '@/hooks/recruitment/use-transition-context'
import { RECRUITMENT_STAGES } from '@/lib/recruitment-stages'
import { isLiaAutoAllowed } from '../utils/action-matrix'
import { getSubStatusOptionsForBehavior } from '../hooks/use-universal-transition'
import type { KanbanCandidate } from '../types'
import { ACTION_BEHAVIOR_MODALS } from '../constants'
import React from 'react'
import {
  Brain,
  Calendar,
  ClipboardList,
  FileText,
  Gift,
  Mail,
  MessageSquare,
} from 'lucide-react'

export interface UniversalTransitionConfirmData {
  candidateIds: string[]
  toStage: string
  subStatus: string
  action: 'lia_auto' | 'manual' | 'just_move'
  prompt?: string
  channel?: 'email' | 'whatsapp'
  perCandidateSubStatus?: Record<string, string>
  extracted_preferences?: Record<string, string>
  actionBehavior?: string
}

export interface AvailableStage {
  id: string
  displayName: string
  actionBehavior?: string
}

export interface UniversalTransitionModalProps {
  isOpen: boolean
  onClose: () => void
  candidates: KanbanCandidate[]
  fromStage: string
  toStage: string
  toStageDisplayName: string
  actionBehavior: string
  subStatusOptions: Array<{ code: string; display_name: string }>
  onConfirm: (data: UniversalTransitionConfirmData) => Promise<void>
  onOpenSpecializedModal?: (modalType: string, context: Record<string, unknown>) => void
  companyId?: string
  jobTitle?: string
  initialPrompt?: string
  availableStages?: AvailableStage[]
  allowStageSelection?: boolean
  interviewAlert?: { name: string; date: string }
}

export const ACTION_BEHAVIOR_CONFIG: Record<string, { label: string; icon: React.ReactNode; description: string }> = {
  intake: {
    label: 'Orientação LIA',
    icon: <Brain className="w-3.5 h-3.5 text-wedo-cyan" />,
    description: 'LIA orienta o recrutador sobre o candidato recebido',
  },
  screening: {
    label: 'Convidar para Triagem WSI',
    icon: <ClipboardList className="w-3.5 h-3.5" />,
    description: 'LIA conduz triagem automatizada com o candidato',
  },
  scheduling: {
    label: 'Abrir Agendamento',
    icon: <Calendar className="w-3.5 h-3.5" />,
    description: 'LIA envia convite de agendamento ao candidato',
  },
  evaluation: {
    label: 'Enviar Teste',
    icon: <FileText className="w-3.5 h-3.5" />,
    description: 'LIA envia teste técnico ou avaliação',
  },
  verification: {
    label: 'Solicitar Documentos',
    icon: <FileText className="w-3.5 h-3.5" />,
    description: 'LIA solicita documentos necessários',
  },
  offer: {
    label: 'Enviar Proposta',
    icon: <Gift className="w-3.5 h-3.5" />,
    description: 'LIA prepara e envia proposta formal',
  },
  passive: {
    label: 'Orientação LIA',
    icon: <Brain className="w-3.5 h-3.5 text-wedo-cyan" />,
    description: 'LIA orienta sobre a movimentação do candidato',
  },
  standby: {
    label: 'Banco de Talentos',
    icon: <Brain className="w-3.5 h-3.5 text-wedo-cyan" />,
    description: 'LIA registra candidato no banco de talentos',
  },
  conclusion_hired: {
    label: 'Enviar Boas-vindas',
    icon: <Mail className="w-3.5 h-3.5" />,
    description: 'LIA envia mensagem de boas-vindas e próximos passos',
  },
  conclusion_rejected: {
    label: 'Enviar Feedback',
    icon: <MessageSquare className="w-3.5 h-3.5" />,
    description: 'LIA envia feedback construtivo ao candidato',
  },
  conclusion_declined: {
    label: 'Agradecimento',
    icon: <Mail className="w-3.5 h-3.5" />,
    description: 'LIA envia agradecimento e mantém porta aberta',
  },
}

export function useUniversalTransitionModal({
  isOpen,
  candidates,
  fromStage,
  toStage,
  toStageDisplayName,
  actionBehavior,
  subStatusOptions,
  onConfirm,
  onClose,
  onOpenSpecializedModal,
  companyId,
  jobTitle,
  initialPrompt,
}: UniversalTransitionModalProps) {
  const [subStatus, setSubStatus] = useState('')
  const [action, setAction] = useState<'lia_auto' | 'manual' | 'just_move'>('lia_auto')
  const [prompt, setPrompt] = useState('')
  const [channel, setChannel] = useState<'email' | 'whatsapp'>('email')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [perCandidateSubStatus, setPerCandidateSubStatus] = useState<Record<string, string>>({})
  const [manuallyEditedCandidates, setManuallyEditedCandidates] = useState<Set<string>>(new Set())
  const [showAllPerCandidate, setShowAllPerCandidate] = useState(false)
  const [policyWarnings, setPolicyWarnings] = useState<string[]>([])
  const [policyMetadata, setPolicyMetadata] = useState<Record<string, unknown>>({})
  const [selectedToStage, setSelectedToStage] = useState(toStage)
  const [selectedToStageDisplayName, setSelectedToStageDisplayName] = useState(toStageDisplayName)
  const [currentActionBehavior, setCurrentActionBehavior] = useState(actionBehavior)
  const [currentSubStatusOptions, setCurrentSubStatusOptions] = useState(subStatusOptions)
  const [showStageSelector, setShowStageSelector] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setSelectedToStage(toStage)
      setSelectedToStageDisplayName(toStageDisplayName)
      setCurrentActionBehavior(actionBehavior)
      setCurrentSubStatusOptions(subStatusOptions)
      setShowStageSelector(false)
    }
  }, [isOpen, toStage, toStageDisplayName, actionBehavior, subStatusOptions])

  const handleStageSelect = (stage: AvailableStage) => {
    setSelectedToStage(stage.id)
    setSelectedToStageDisplayName(stage.displayName)
    const newBehavior = stage.actionBehavior || 'passive'
    setCurrentActionBehavior(newBehavior)
    setCurrentSubStatusOptions(getSubStatusOptionsForBehavior(newBehavior, stage.id))
    setShowStageSelector(false)
    setSubStatus('')
  }

  const isSingle = candidates.length === 1
  const candidate = isSingle ? candidates[0] : null
  const fromStageInfo = RECRUITMENT_STAGES.find(s => s.name === fromStage)
  const fromStageDisplayName = fromStageInfo?.displayName || fromStage
  const behaviorConfig = ACTION_BEHAVIOR_CONFIG[currentActionBehavior]
  const isRejectedBatch = selectedToStage === 'rejected' && candidates.length > 1
  const showChatPanel = isLiaAutoAllowed(currentActionBehavior) && action !== 'just_move'
  const isRejectedStage = selectedToStage === 'rejected'

  const transitionCandidates: CandidateContext[] = isRejectedBatch
    ? candidates.map(c => ({
        id: c.id,
        name: c.name,
        email: c.email,
        phone: c.phone,
        avatar: c.avatar,
        current_title: c.role,
        current_company: c.currentCompany || c.company,
      }))
    : []

  const transitionJobContext: JobContext = {
    id: companyId || '',
    title: jobTitle || '',
  }

  const {
    predictedSubStatuses,
    predictionReasonings,
    isPredicting: isBulkPredicting,
  } = useTransitionContext({
    candidates: transitionCandidates,
    fromStage,
    toStage: selectedToStage,
    jobContext: transitionJobContext,
    companyId,
  })

  const { sendMessage, messages, result: interpretResult, isLoading: isInterpreting, reset: resetInterpret } = useInterpretContext()

  useEffect(() => {
    if (!isOpen || !companyId) return
    const isOfferStage = selectedToStage.toLowerCase().includes('proposta') ||
                         selectedToStage.toLowerCase().includes('offer') ||
                         selectedToStage.toLowerCase().includes('contrata')
    if (!isOfferStage) {
      setPolicyWarnings([])
      setPolicyMetadata({})
      return
    }
    const candidateId = candidates[0]?.id
    if (!candidateId) return

    fetch(`/api/backend-proxy/pipeline-policy?action=validate-transition&candidate_id=${candidateId}&target_stage=${selectedToStage}&company_id=${companyId}`)
      .then(res => res.json())
      .then(data => {
        setPolicyWarnings(data.warnings || [])
        setPolicyMetadata(data.metadata || {})
      })
      .catch((err) => { console.error('[useUniversalTransitionModal] pipeline-policy fetch failed', err) })
  }, [isOpen, companyId, selectedToStage, candidates])

  useEffect(() => {
    if (isOpen) {
      setSubStatus(currentSubStatusOptions.length > 0 ? currentSubStatusOptions[0].code : '')
      setAction('lia_auto')
      setPrompt(initialPrompt || '')
      setChannel('email')
      setPerCandidateSubStatus({})
      setManuallyEditedCandidates(new Set())
      setShowAllPerCandidate(false)
      resetInterpret()
      if (initialPrompt) {
        setTimeout(() => {
          sendMessage(initialPrompt, {
            candidate_id: candidates[0]?.id || '',
            candidate_name: candidates[0]?.name,
            job_title: jobTitle,
            from_stage: fromStage,
            to_stage: selectedToStage,
            action_behavior: currentActionBehavior,
            company_id: companyId,
          })
        }, 300)
      }
    }
  }, [isOpen, currentSubStatusOptions, resetInterpret, initialPrompt, candidates, companyId, currentActionBehavior, fromStage, jobTitle, selectedToStage, sendMessage])

  useEffect(() => {
    if (isRejectedBatch && Object.keys(predictedSubStatuses).length > 0) {
      setPerCandidateSubStatus(prev => {
        const updated = { ...prev }
        for (const [candidateId, predicted] of Object.entries(predictedSubStatuses)) {
          if (!manuallyEditedCandidates.has(candidateId)) {
            updated[candidateId] = predicted
          }
        }
        return updated
      })
    }
  }, [isRejectedBatch, predictedSubStatuses, manuallyEditedCandidates])

  useEffect(() => {
    if (!interpretResult) return
    if (interpretResult.suggested_sub_status && currentSubStatusOptions.some(o => o.code === interpretResult.suggested_sub_status)) {
      setSubStatus(interpretResult.suggested_sub_status)
    }
    if (interpretResult.suggested_action) {
      setAction(interpretResult.suggested_action)
    }
  }, [interpretResult, currentSubStatusOptions])

  const handleGlobalSubStatusChange = (value: string) => {
    setSubStatus(value)
    if (isRejectedBatch) {
      setPerCandidateSubStatus(prev => {
        const updated = { ...prev }
        for (const c of candidates) {
          if (!manuallyEditedCandidates.has(c.id)) {
            updated[c.id] = value
          }
        }
        return updated
      })
    }
  }

  const handlePerCandidateSubStatusChange = (candidateId: string, value: string) => {
    setPerCandidateSubStatus(prev => ({ ...prev, [candidateId]: value }))
    setManuallyEditedCandidates(prev => new Set(prev).add(candidateId))
  }

  const handleSendChatMessage = (userMessage: string) => {
    setPrompt(prev => prev ? `${prev}\n${userMessage}` : userMessage)
    sendMessage(userMessage, {
      candidate_id: candidate?.id || candidates[0]?.id || '',
      candidate_name: candidate?.name,
      job_title: jobTitle,
      from_stage: fromStage,
      to_stage: selectedToStage,
      action_behavior: currentActionBehavior,
      company_id: companyId,
    })
  }

  const handleConfirm = async () => {
    setIsSubmitting(true)
    try {
      await onConfirm({
        candidateIds: candidates.map(c => c.id),
        toStage: selectedToStage,
        subStatus,
        action,
        prompt: prompt.trim() || undefined,
        channel: action !== 'just_move' ? channel : undefined,
        perCandidateSubStatus: isRejectedBatch ? perCandidateSubStatus : undefined,
        extracted_preferences: (action === 'lia_auto' && interpretResult?.extracted_preferences) ? interpretResult.extracted_preferences : undefined,
        actionBehavior: currentActionBehavior,
      })
      onClose()
    } catch (err) {
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleOpenManualModal = () => {
    const modalType = ACTION_BEHAVIOR_MODALS[currentActionBehavior]
    if (modalType && onOpenSpecializedModal) {
      onOpenSpecializedModal(modalType, {
        candidates,
        fromStage,
        toStage: selectedToStage,
        subStatus,
        prompt,
        channel,
        companyId,
        jobTitle,
      })
    }
  }

  return {
    subStatus,
    action,
    setAction,
    isSubmitting,
    perCandidateSubStatus,
    manuallyEditedCandidates,
    showAllPerCandidate,
    setShowAllPerCandidate,
    policyWarnings,
    policyMetadata,
    selectedToStage,
    selectedToStageDisplayName,
    currentActionBehavior,
    currentSubStatusOptions,
    showStageSelector,
    setShowStageSelector,
    handleStageSelect,
    isSingle,
    candidate,
    fromStageDisplayName,
    behaviorConfig,
    isRejectedBatch,
    showChatPanel,
    isRejectedStage,
    isBulkPredicting,
    predictedSubStatuses,
    predictionReasonings,
    messages,
    isInterpreting,
    interpretResult,
    resetInterpret,
    handleGlobalSubStatusChange,
    handlePerCandidateSubStatusChange,
    handleSendChatMessage,
    handleConfirm,
    handleOpenManualModal,
    prompt,
    setPrompt,
  }
}
