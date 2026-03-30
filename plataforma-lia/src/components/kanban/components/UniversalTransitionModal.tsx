"use client"

import { useState, useEffect, useRef } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import {
  ArrowRight,
  Brain,
  Send,
  User,
  Mail,
  MessageSquare,
  Loader2,
  Calendar,
  CalendarClock,
  ClipboardList,
  FileText,
  Gift,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { textStyles, cardStyles } from '@/lib/design-tokens'
import { RECRUITMENT_STAGES } from '@/lib/recruitment-stages'
import type { KanbanCandidate } from '../types'
import { ACTION_BEHAVIOR_MODALS } from '../constants'
import { useInterpretContext, type ChatMessage } from '@/hooks/use-interpret-context'
import { useTransitionContext, type CandidateContext, type JobContext } from '@/hooks/use-transition-context'
import { isLiaAutoAllowed } from '../utils/action-matrix'
import { getSubStatusOptionsForBehavior } from '../hooks/use-universal-transition'
import { TransitionChatPanel } from './TransitionChatPanel'

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

interface AvailableStage {
  id: string
  displayName: string
  actionBehavior?: string
}

interface UniversalTransitionModalProps {
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

const ACTION_BEHAVIOR_CONFIG: Record<string, { label: string; icon: React.ReactNode; description: string }> = {
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



export function UniversalTransitionModal({
  isOpen,
  onClose,
  candidates,
  fromStage,
  toStage,
  toStageDisplayName,
  actionBehavior,
  subStatusOptions,
  onConfirm,
  onOpenSpecializedModal,
  companyId,
  jobTitle,
  initialPrompt,
  availableStages,
  allowStageSelection,
  interviewAlert,
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
      .catch(() => {})
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
  }, [isOpen, currentSubStatusOptions, resetInterpret, initialPrompt])

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

  const isRejectedStage = selectedToStage === 'rejected'

  const stageSelectable = allowStageSelection && availableStages && availableStages.length > 0
  const filteredAvailableStages = stageSelectable
    ? availableStages!.filter(s => s.id !== fromStage)
    : []

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        className={cn(
          "max-h-[85vh] overflow-hidden p-0 rounded-md",
          showChatPanel
            ? "max-w-4xl bg-white dark:bg-lia-bg-secondary"
            : "max-w-lg bg-white dark:bg-lia-bg-secondary"
        )}
      >
        <DialogHeader className="px-5 py-3 border-b border-lia-border-subtle dark:border-lia-border-subtle">
          <DialogTitle className={`flex items-center gap-2 ${textStyles.h3}`}>
            <ArrowRight className="w-4 h-4 lia-text-500 dark:text-lia-text-tertiary" />
            Mover para: {selectedToStageDisplayName}
          </DialogTitle>
        </DialogHeader>

        {policyWarnings.length > 0 && (
          <div className="mx-6 mt-3 p-3 bg-status-warning/10 border border-status-warning/30 rounded-md text-sm dark:bg-status-warning/20 dark:border-status-warning/30">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-status-warning mt-0.5 flex-shrink-0 dark:text-status-warning" />
              <div>
                <p className="font-medium text-status-warning dark:text-status-warning">Atenção — Política da empresa</p>
                {policyWarnings.map((w, i) => (
                  <p key={i} className="mt-1 text-status-warning dark:text-status-warning">{w}</p>
                ))}
                {policyMetadata.requires_manager_approval && (
                  <p className="mt-1 text-status-warning dark:text-status-warning">
                    Aprovação do gestor será necessária antes de prosseguir.
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {interviewAlert && (
          <div className="mx-4 mt-2 flex items-start gap-2 px-3 py-2 bg-status-warning/10 dark:bg-status-warning/20 border border-status-warning/30 dark:border-status-warning/30 rounded-lg">
            <CalendarClock className="w-3.5 h-3.5 text-status-warning dark:text-status-warning flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-micro font-semibold text-status-warning dark:text-status-warning">
                Entrevista agendada
              </p>
              <p className="text-micro text-status-warning dark:text-status-warning">
                {interviewAlert.name} — {interviewAlert.date}
              </p>
            </div>
          </div>
        )}

        <div className={cn(
          "overflow-y-auto",
          showChatPanel ? "flex flex-col md:flex-row" : ""
        )}>
          {/* LEFT PANEL: Transition details */}
          <div className={cn(
            "px-4 py-3 space-y-2.5 overflow-y-auto",
            showChatPanel
              ? "md:w-[36%] md:max-h-[calc(85vh-120px)]"
              : "w-full"
          )}>
            {/* Candidate info + stage transition */}
            <div className={`p-2.5 ${cardStyles.flat} space-y-2`}>
              {isSingle && candidate ? (
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 bg-gray-200 dark:bg-lia-bg-elevated rounded-full flex items-center justify-center flex-shrink-0">
                    {candidate.avatar ? (
                      <img src={candidate.avatar} alt="" className="w-8 h-8 rounded-full object-cover" />
                    ) : (
                      <User className="w-3.5 h-3.5 lia-text-500 dark:text-lia-text-tertiary" />
                    )}
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-medium lia-text-900 dark:lia-text-50 truncate leading-tight">
                      {candidate.name}
                    </p>
                    {(candidate.role || candidate.currentTitle || candidate.currentCompany) && (
                      <p className="text-micro lia-text-500 dark:text-lia-text-tertiary truncate leading-tight mt-0.5">
                        {candidate.role || candidate.currentTitle}{(candidate.role || candidate.currentTitle) && candidate.currentCompany ? ' • ' : ''}{candidate.currentCompany}
                      </p>
                    )}
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-gray-200 dark:bg-lia-bg-elevated rounded-full flex items-center justify-center flex-shrink-0">
                    <span className="text-micro font-semibold lia-text-600 dark:text-lia-text-secondary">{candidates.length}</span>
                  </div>
                  <p className="text-xs font-medium lia-text-900 dark:lia-text-50">
                    {candidates.length} candidatos selecionados
                  </p>
                </div>
              )}

              <div className="flex items-center justify-center gap-2">
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium lia-text-600 dark:text-lia-text-secondary border border-lia-border-default dark:border-lia-border-default bg-white dark:bg-lia-bg-elevated">
                  {fromStageDisplayName}
                </span>
                <ArrowRight className="w-3.5 h-3.5 lia-text-400 dark:lia-text-500 flex-shrink-0" />
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => stageSelectable && setShowStageSelector(!showStageSelector)}
                    className={cn(
                      "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-semibold border bg-white dark:bg-lia-bg-elevated",
                      stageSelectable
                        ? "lia-text-900 dark:lia-text-50 border-gray-900 dark:border-lia-border-default cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-600"
                        : "lia-text-900 dark:lia-text-50 border-gray-900 dark:border-lia-border-default cursor-default"
                    )}
                  >
                    {selectedToStageDisplayName}
                    {stageSelectable && <ChevronDown className="w-3 h-3" />}
                  </button>
                  {showStageSelector && stageSelectable && (
                    <div className="absolute top-full left-0 mt-1 z-50 bg-white dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md shadow-lia-md max-h-48 overflow-y-auto min-w-[160px]">
                      {filteredAvailableStages.map((stage) => (
                        <button
                          key={stage.id}
                          type="button"
                          onClick={() => handleStageSelect(stage)}
                          className={cn(
                            "w-full text-left px-3 py-1.5 text-xs hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors",
                            stage.id === selectedToStage
                              ? "bg-gray-100 dark:bg-lia-bg-elevated font-semibold lia-text-900 dark:lia-text-50"
                              : "lia-text-700 dark:text-lia-text-secondary"
                          )}
                        >
                          {stage.displayName}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Action mode + batch per-candidate */}
            <>
              {/* Batch rejection: per-candidate sub-status */}
                {isRejectedBatch && currentSubStatusOptions.length > 0 && (
                  <div className="space-y-2">
                    <button
                      type="button"
                      className="w-full flex items-center justify-between py-1.5 group"
                      onClick={() => setShowAllPerCandidate(prev => !prev)}
                    >
                      <span className="font-sans text-xs font-medium lia-text-700 dark:text-lia-text-primary flex items-center gap-1.5">
                        Motivo por candidato
                        {isBulkPredicting && (
                          <Loader2 className="w-3 h-3 animate-spin text-wedo-cyan" />
                        )}
                        {!isBulkPredicting && Object.keys(predictedSubStatuses).length > 0 && (
                          <span className="inline-flex items-center gap-0.5 text-micro font-normal text-wedo-cyan">
                            <Brain className="w-2.5 h-2.5 text-wedo-cyan" />
                            IA
                          </span>
                        )}
                      </span>
                      <span className="flex items-center gap-1 text-micro lia-text-500 dark:text-lia-text-tertiary group-hover:lia-text-700 dark:group-hover:lia-text-200 transition-colors">
                        {candidates.length} candidatos
                        {showAllPerCandidate ? (
                          <ChevronUp className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronDown className="w-3.5 h-3.5" />
                        )}
                      </span>
                    </button>
                    {showAllPerCandidate && (
                      <div className="max-h-[240px] overflow-y-auto space-y-1.5 pr-0.5">
                        {candidates.map((c) => {
                          const candidateSubStatus = perCandidateSubStatus[c.id] || subStatus
                          const isAiPredicted = !manuallyEditedCandidates.has(c.id) && !!predictedSubStatuses[c.id]
                          const reasoning = predictionReasonings[c.id]
                          const initials = c.name
                            ?.split(' ')
                            .slice(0, 2)
                            .map(n => n[0])
                            .join('')
                            .toUpperCase() || '?'

                          return (
                            <div
                              key={c.id}
                              className="p-2.5 bg-gray-50 rounded-md border border-lia-border-subtle dark:bg-lia-bg-secondary dark:border-lia-border-subtle"
                            >
                              <div className="flex items-center gap-2.5">
                                <div className="w-7 h-7 rounded-full bg-gray-200 dark:bg-lia-bg-elevated flex items-center justify-center flex-shrink-0">
                                  {c.avatar ? (
                                    <img src={c.avatar} alt="" className="w-7 h-7 rounded-full object-cover" />
                                  ) : (
                                    <span className="text-micro font-semibold lia-text-600 dark:text-lia-text-secondary">{initials}</span>
                                  )}
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="font-sans text-xs font-medium lia-text-700 dark:lia-text-50 truncate">
                                    {c.name}
                                  </p>
                                  {(c.role || c.currentCompany) && (
                                    <p className="font-sans text-xs lia-text-500 dark:text-lia-text-tertiary truncate">
                                      {c.role}{c.role && c.currentCompany ? ' @ ' : ''}{c.currentCompany}
                                    </p>
                                  )}
                                </div>
                                <div className="flex items-center gap-1.5 flex-shrink-0">
                                  {isAiPredicted && (
                                    <Brain className="w-3 h-3 text-wedo-cyan" />
                                  )}
                                  <Select
                                    value={candidateSubStatus}
                                    onValueChange={(value) => handlePerCandidateSubStatusChange(c.id, value)}
                                  >
                                    <SelectTrigger className="w-[180px] h-7 rounded-md text-xs">
                                      <SelectValue placeholder="Selecione..." />
                                    </SelectTrigger>
                                    <SelectContent>
                                      {currentSubStatusOptions.map((opt) => (
                                        <SelectItem key={opt.code} value={opt.code} className="text-xs">
                                          {opt.display_name}
                                        </SelectItem>
                                      ))}
                                    </SelectContent>
                                  </Select>
                                </div>
                              </div>
                              {reasoning && (
                                <p className="font-sans text-xs lia-text-500 dark:text-lia-text-tertiary mt-1.5 ml-[38px] flex items-center gap-1"> {/* [OPT-022] ml-[38px] px arbitrário — sem canônico Tailwind */}
                                  <Brain className="w-2.5 h-2.5 text-wedo-cyan flex-shrink-0" />
                                  {reasoning}
                                </p>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )}

                {/* Action mode */}
                {behaviorConfig && (
                  <div className="space-y-1">
                    <Label className="text-micro font-semibold lia-text-500 dark:text-lia-text-tertiary uppercase tracking-wider">
                      Ação
                    </Label>
                    <RadioGroup
                      value={action}
                      onValueChange={(v) => setAction(v as 'lia_auto' | 'manual' | 'just_move')}
                      className="space-y-1"
                    >
                      <div
                        className={cn(
                          "flex items-start gap-2 p-2 rounded-md border cursor-pointer transition-colors",
                          action === 'lia_auto'
                            ? "border-gray-900 bg-white dark:lia-border-400 dark:bg-lia-bg-secondary"
                            : "border-lia-border-subtle hover:border-lia-border-default dark:border-lia-border-subtle dark:hover:border-gray-600"
                        )}
                        onClick={() => setAction('lia_auto')}
                      >
                        <RadioGroupItem value="lia_auto" id="action-lia" className="mt-0.5" />
                        <div className="flex-1 min-w-0">
                          <label htmlFor="action-lia" className="flex items-center gap-1 cursor-pointer">
                            <Brain className="w-3 h-3 text-wedo-cyan" />
                            <span className="text-xs font-medium lia-text-900 dark:lia-text-50">LIA automático</span>
                            <span className="text-micro bg-gray-100 dark:bg-lia-bg-elevated lia-text-500 dark:text-lia-text-tertiary px-1 py-px rounded-full ml-auto">
                              Recomendado
                            </span>
                          </label>
                          <p className="text-micro lia-text-500 dark:text-lia-text-tertiary mt-0.5 leading-tight">
                            {behaviorConfig.description}
                          </p>
                        </div>
                      </div>

                      <div
                        className={cn(
                          "flex items-start gap-2 p-2 rounded-md border cursor-pointer transition-colors",
                          action === 'manual'
                            ? "border-gray-900 bg-white dark:lia-border-400 dark:bg-lia-bg-secondary"
                            : "border-lia-border-subtle hover:border-lia-border-default dark:border-lia-border-subtle dark:hover:border-gray-600"
                        )}
                        onClick={() => setAction('manual')}
                      >
                        <RadioGroupItem value="manual" id="action-manual" className="mt-0.5" />
                        <div className="flex-1">
                          <label htmlFor="action-manual" className="flex items-center gap-1 cursor-pointer">
                            <span className="text-xs font-medium lia-text-900 dark:lia-text-50">Manual</span>
                          </label>
                          {action === 'manual' && onOpenSpecializedModal && ACTION_BEHAVIOR_MODALS[currentActionBehavior] && (
                            <Button
                              variant="outline"
                              size="sm"
                              className="mt-1.5 h-6 text-micro gap-1 rounded-md"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleOpenManualModal()
                              }}
                            >
                              {behaviorConfig.icon}
                              {behaviorConfig.label}
                            </Button>
                          )}
                        </div>
                      </div>

                      <div
                        className={cn(
                          "flex items-center gap-2 p-2 rounded-md border cursor-pointer transition-colors",
                          action === 'just_move'
                            ? "border-gray-900 bg-white dark:lia-border-400 dark:bg-lia-bg-secondary"
                            : "border-lia-border-subtle hover:border-lia-border-default dark:border-lia-border-subtle dark:hover:border-gray-600"
                        )}
                        onClick={() => setAction('just_move')}
                      >
                        <RadioGroupItem value="just_move" id="action-move" />
                        <label htmlFor="action-move" className="text-xs font-medium lia-text-900 dark:lia-text-50 cursor-pointer">
                          Apenas mover
                        </label>
                      </div>
                    </RadioGroup>
                  </div>
                )}

                {/* Generic action mode (no behaviorConfig) */}
                {!behaviorConfig && (
                  <div className="space-y-1">
                    <Label className="text-micro font-semibold lia-text-500 dark:text-lia-text-tertiary uppercase tracking-wider">
                      Ação
                    </Label>
                    <RadioGroup
                      value={action}
                      onValueChange={(v) => setAction(v as 'lia_auto' | 'manual' | 'just_move')}
                      className="space-y-1"
                    >
                      <div
                        className={cn(
                          "flex items-center gap-2 p-2 rounded-md border cursor-pointer transition-colors",
                          action === 'lia_auto'
                            ? "border-gray-900 bg-white dark:lia-border-400 dark:bg-lia-bg-secondary"
                            : "border-lia-border-subtle hover:border-lia-border-default dark:border-lia-border-subtle dark:hover:border-gray-600"
                        )}
                        onClick={() => setAction('lia_auto')}
                      >
                        <RadioGroupItem value="lia_auto" id="action-lia-generic" />
                        <label htmlFor="action-lia-generic" className="flex items-center gap-1 cursor-pointer">
                          <Brain className="w-3 h-3 text-wedo-cyan" />
                          <span className="text-xs font-medium lia-text-900 dark:lia-text-50">LIA automático</span>
                        </label>
                      </div>
                      <div
                        className={cn(
                          "flex items-center gap-2 p-2 rounded-md border cursor-pointer transition-colors",
                          action === 'just_move'
                            ? "border-gray-900 bg-white dark:lia-border-400 dark:bg-lia-bg-secondary"
                            : "border-lia-border-subtle hover:border-lia-border-default dark:border-lia-border-subtle dark:hover:border-gray-600"
                        )}
                        onClick={() => setAction('just_move')}
                      >
                        <RadioGroupItem value="just_move" id="action-move-generic" />
                        <label htmlFor="action-move-generic" className="text-xs font-medium lia-text-900 dark:lia-text-50 cursor-pointer">
                          Apenas mover
                        </label>
                      </div>
                    </RadioGroup>
                  </div>
                )}
            </>
          </div>

          {/* RIGHT PANEL: Chat with LIA (follows lia-expanded-panel pattern) */}
          {showChatPanel && (
            <div className="md:w-[64%] border-t md:border-t-0 md:border-l border-lia-border-subtle dark:border-lia-border-subtle flex flex-col md:max-h-[calc(85vh-120px)] bg-white dark:bg-lia-bg-secondary">
              <TransitionChatPanel
                messages={messages}
                isLoading={isInterpreting}
                onSendMessage={handleSendChatMessage}
                onClearChat={() => { resetInterpret(); setPrompt(''); }}
                actionBehavior={currentActionBehavior}
                extractedPreferences={action === 'lia_auto' ? interpretResult?.extracted_preferences : null}
              />
            </div>
          )}
        </div>

        {/* SUB-STATUS ROW (separate band above footer buttons) */}
        {currentSubStatusOptions.length > 0 && (
          <div className="flex items-center justify-end gap-2 w-full px-5 py-2.5 bg-gray-50 dark:bg-lia-bg-primary border-t border-lia-border-subtle dark:border-lia-border-subtle">
            <span className="text-xs font-medium lia-text-600 dark:text-lia-text-secondary whitespace-nowrap">
              {isRejectedBatch ? 'Motivo padrão:' : isRejectedStage ? 'Motivo:' : 'Sub-status da etapa:'}
            </span>
            <Select value={subStatus} onValueChange={handleGlobalSubStatusChange}>
              <SelectTrigger className="w-[220px] h-8 rounded-md text-xs bg-white dark:bg-lia-bg-secondary">
                <SelectValue placeholder="Selecione..." />
              </SelectTrigger>
              <SelectContent className="z-modal" position="popper" sideOffset={4} side="top">
                {currentSubStatusOptions.map((opt) => (
                  <SelectItem key={opt.code} value={opt.code} className="text-xs">
                    {opt.display_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {interpretResult?.suggested_sub_status === subStatus && interpretResult?.ai_powered && (
              <span title="Sugerido pela IA">
                <Brain className="w-3 h-3 text-wedo-cyan flex-shrink-0" />
              </span>
            )}
          </div>
        )}

        {/* FOOTER: Action buttons */}
        <DialogFooter className="px-5 py-0 bg-gray-50 dark:bg-lia-bg-primary border-t border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-center justify-between w-full py-2.5 gap-3">
            <div className="flex items-center gap-2">
              {currentActionBehavior === 'conclusion_rejected' && onOpenSpecializedModal && (
                <Button
                  variant="outline"
                  size="sm"
                  className="h-9 px-3 text-xs font-medium rounded-md border-lia-border-default lia-text-600 hover:bg-gray-50 focus:ring-2 focus:ring-gray-900/20 focus:outline-none dark:border-lia-border-default dark:text-lia-text-tertiary"
                  onClick={() => onOpenSpecializedModal('rejection-feedback', { candidates, toStage: selectedToStage })}
                >
                  <MessageSquare className="w-3.5 h-3.5 mr-1.5" />
                  Feedback
                </Button>
              )}
            </div>

            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                onClick={onClose}
                disabled={isSubmitting}
                className="h-9 px-4 text-xs font-semibold rounded-md transition-colors duration-150 font-['Open_Sans'] bg-white lia-text-900 border border-lia-border-default hover:bg-gray-50 hover:border-gray-400 focus:ring-2 focus:ring-gray-900/20 focus:outline-none dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:border-lia-border-default dark:hover:bg-gray-700"
              >
                Cancelar
              </Button>

              <Button
                onClick={handleConfirm}
                disabled={isSubmitting || (isRejectedStage && !subStatus)}
                className="h-9 px-4 text-xs font-semibold rounded-md transition-colors duration-150 font-['Open_Sans'] bg-gray-900 text-white hover:bg-gray-800 active:bg-gray-700 focus:ring-2 focus:ring-gray-900/20 focus:outline-none dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" />
                    Processando...
                  </>
                ) : (
                  <>
                    {action === 'lia_auto' ? (
                      <>
                        <Brain className="w-3.5 h-3.5 mr-1.5 text-wedo-cyan" />
                        Confirmar com LIA
                      </>
                    ) : (
                      <>
                        <ArrowRight className="w-3.5 h-3.5 mr-1.5" />
                        Confirmar
                      </>
                    )}
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
