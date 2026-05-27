"use client"
import NextImage from "next/image"

import React, { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  Check,
  X,
  Brain,
  Calendar,
  MessageSquare,
  Mail,
  Phone,
  Info,
  Loader2,
  ChevronRight,
  AlertCircle,
  Send,
  Edit3,
  CheckCircle,
} from "lucide-react"
import { textStyles } from '@/lib/design-tokens'

type FlowType = 'approve_to_triage' | 'approve_to_interview' | 'reject_pre_triage' | 'reject_post_triage' | 'request_urgency' | 'reschedule_interview' | 'confirm_hire'

interface CandidateDecisionFlowModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: {
    id: string
    name: string
    role?: string
    currentCompany?: string
    avatar?: string
    email?: string
    phone?: string
    hasWhatsApp?: boolean
    stage?: string
  }
  flowType: FlowType
  onConfirm: (action: string, feedbackMessage?: string, channel?: string) => void
  onOpenFeedbackModal?: (candidate: Record<string, unknown>) => void
}

interface StepperProps {
  steps: { id: string; label: string; status: 'completed' | 'current' | 'upcoming' }[]
  currentStep: number
}

const Stepper: React.FC<StepperProps> = ({ steps }) => {
  return (
    <div className="flex items-center justify-between w-full mb-5">
      {steps.map((step, index) => (
        <React.Fragment key={step.id}>
          <div className="flex flex-col items-center">
            <div
              className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium transition-[width,height] ${
 step.status === 'completed'
                  ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text'
                  : step.status === 'current'
                  ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text ring-2 ring-lia-btn-primary-bg/20'
                  : 'bg-lia-interactive-active text-lia-text-tertiary dark:bg-lia-bg-elevated'
              }`}
             
            >
              {step.status === 'completed' ? (
                <Check className="w-3 h-3" />
              ) : (
                index + 1
              )}
            </div>
            <span
              className={`mt-1.5 text-micro text-center max-w-[70px] ${
 step.status === 'current'
                  ? 'text-lia-text-primary font-medium'
                  : step.status === 'completed'
                  ? 'text-lia-text-secondary'
                  : 'lia-text-secondary'
              }`}
             
            >
              {step.label}
            </span>
          </div>
          {index < steps.length - 1 && (
            <div
              className={`flex-1 h-0.5 mx-1.5 ${
 steps[index + 1].status === 'completed' || steps[index + 1].status === 'current'
                  ? 'bg-lia-btn-primary-bg'
                  : 'bg-lia-interactive-active dark:bg-lia-bg-elevated'
              }`}
            />
          )}
        </React.Fragment>
      ))}
    </div>
  )
}

const LIARulesInfo: React.FC<{ type: 'triage' | 'interview' }> = ({ type }) => {
  const isInterview = type === 'interview'
  
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <button className="inline-flex items-center gap-1 text-xs text-lia-text-secondary hover:text-lia-text-primary transition-colors motion-reduce:transition-none">
            <Info className="w-3 h-3" />
            <span>Como funciona?</span>
          </button>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-xs p-3">
          <div className="space-y-2">
            <p className="font-medium text-xs text-lia-text-primary">
              {isInterview ? 'Processo de Agendamento IA:' : 'Processo de Triagem IA:'}
            </p>
            <ul className="space-y-1 text-xs text-lia-text-secondary">
              {isInterview ? (
                <>
                  <li className="flex items-start gap-1.5">
                    <span className="text-lia-text-disabled">•</span>
                    LIA envia mensagem por WhatsApp e Email com link e horários disponíveis em sua agenda
                  </li>
                  <li className="flex items-start gap-1.5">
                    <span className="text-lia-text-disabled">•</span>
                    Se não responder, nova tentativa a cada 12h
                  </li>
                  <li className="flex items-start gap-1.5">
                    <span className="text-lia-text-disabled">•</span>
                    Após 3 tentativas sem resposta, você será avisado
                  </li>
                </>
              ) : (
                <>
                  <li className="flex items-start gap-1.5">
                    <span className="text-lia-text-disabled">•</span>
                    LIA envia convite via WhatsApp e Email
                  </li>
                  <li className="flex items-start gap-1.5">
                    <span className="text-lia-text-disabled">•</span>
                    Se não responder, nova tentativa a cada 24h
                  </li>
                  <li className="flex items-start gap-1.5">
                    <span className="text-lia-text-disabled">•</span>
                    Após 3 tentativas sem resposta, você será avisado
                  </li>
                  <li className="flex items-start gap-1.5">
                    <span className="text-lia-text-disabled">•</span>
                    Candidato tem 24h para completar a triagem
                  </li>
                </>
              )}
            </ul>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

export const CandidateDecisionFlowModal: React.FC<CandidateDecisionFlowModalProps> = ({
  isOpen,
  onClose,
  candidate,
  flowType,
  onConfirm,
  onOpenFeedbackModal,
}) => {
  const [isLoading, setIsLoading] = useState(false)
  const [showFeedbackEditor, setShowFeedbackEditor] = useState(false)
  const [feedbackChannel, setFeedbackChannel] = useState<'whatsapp' | 'email'>('whatsapp')
  const [feedbackMessage, setFeedbackMessage] = useState('')
  const [isEditingMessage, setIsEditingMessage] = useState(false)

  const getDefaultFeedbackMessage = () => {
    return `Olá ${candidate.name.split(' ')[0]},

Agradecemos seu interesse na vaga e o tempo dedicado ao nosso processo seletivo.

Após análise cuidadosa, decidimos seguir com outros candidatos cujos perfis estão mais alinhados às necessidades atuais da posição.

Manteremos seu currículo em nosso banco de talentos e, caso surjam oportunidades compatíveis com seu perfil, entraremos em contato.

Desejamos sucesso em sua jornada profissional!

Atenciosamente,
Equipe de Recrutamento`
  }

  React.useEffect(() => {
    if (flowType === 'reject_post_triage' && !feedbackMessage) {
      setFeedbackMessage(getDefaultFeedbackMessage())
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [flowType, candidate.name])

  const getFlowConfig = () => {
    switch (flowType) {
      case 'approve_to_triage':
        return {
          title: 'Aprovar para Triagem',
          icon: <Brain className="w-5 h-5 text-wedo-cyan" />,
          steps: [
            { id: 'approve', label: 'Aprovação', status: 'current' as const },
            { id: 'triage', label: 'Triagem IA', status: 'upcoming' as const },
            { id: 'interview', label: 'Entrevista', status: 'upcoming' as const },
            { id: 'schedule', label: 'Agendamento', status: 'upcoming' as const },
          ],
          confirmLabel: 'Iniciar Triagem',
          confirmColor: 'bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active',
        }
      case 'approve_to_interview':
        return {
          title: 'Aprovar para Entrevista',
          icon: <Calendar className="w-5 h-5 text-lia-text-secondary" />,
          steps: [
            { id: 'approve', label: 'Aprovação', status: 'completed' as const },
            { id: 'triage', label: 'Triagem IA', status: 'completed' as const },
            { id: 'interview', label: 'Entrevista', status: 'current' as const },
            { id: 'schedule', label: 'Agendamento', status: 'upcoming' as const },
          ],
          confirmLabel: 'Agendar Entrevista',
          confirmColor: 'bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active',
        }
      case 'reject_pre_triage':
        return {
          title: 'Reprovar Candidato',
          icon: <X className="w-5 h-5 text-wedo-coral" />,
          steps: [],
          confirmLabel: 'Confirmar Reprovação',
          confirmColor: 'bg-wedo-coral hover:bg-status-error',
        }
      case 'reject_post_triage':
        return {
          title: 'Reprovar Candidato',
          icon: <X className="w-5 h-5 text-wedo-coral" />,
          steps: [],
          confirmLabel: 'Enviar Feedback',
          confirmColor: 'bg-wedo-coral hover:bg-status-error',
          showFeedbackActions: true,
        }
      case 'request_urgency':
        return {
          title: 'Solicitar Urgência',
          icon: <AlertCircle className="w-5 h-5 text-status-warning" />,
          steps: [],
          confirmLabel: 'Enviar Solicitação Urgente',
          confirmColor: 'bg-status-warning hover:bg-status-warning',
          description: 'A LIA enviará uma nova mensagem de agendamento com prioridade alta para o candidato, solicitando retorno imediato.',
        }
      case 'reschedule_interview':
        return {
          title: 'Alterar Horário',
          icon: <Calendar className="w-5 h-5 text-lia-text-secondary" />,
          steps: [],
          confirmLabel: 'Buscar Novos Horários',
          confirmColor: 'bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active',
          description: 'A LIA vai buscar novos horários disponíveis na sua agenda e enviar as opções para o candidato escolher.',
        }
      case 'confirm_hire':
        return {
          title: 'Confirmar Contratação',
          icon: <CheckCircle className="w-5 h-5 text-lia-text-secondary" />,
          steps: [
            { id: 'approve', label: 'Aprovação', status: 'completed' as const },
            { id: 'triage', label: 'Triagem', status: 'completed' as const },
            { id: 'interview', label: 'Entrevista', status: 'completed' as const },
            { id: 'hire', label: 'Contratação', status: 'current' as const },
          ],
          confirmLabel: 'Confirmar Contratação',
          confirmColor: 'bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active',
        }
    }
  }

  const config = getFlowConfig()

  const handleConfirm = async () => {
    setIsLoading(true)
    
    setTimeout(() => {
      if (flowType === 'reject_post_triage' && showFeedbackEditor) {
        onConfirm('reject_with_feedback', feedbackMessage, feedbackChannel)
      } else {
        onConfirm(flowType)
      }
      setIsLoading(false)
      onClose()
    }, 800)
  }

  const contactChannels: string[] = []
  if (candidate.hasWhatsApp || candidate.phone) contactChannels.push('WhatsApp')
  if (candidate.email) contactChannels.push('Email')

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[480px] p-0 overflow-hidden">
        <DialogHeader className="px-5 pt-5 pb-3 dark:border-lia-border-subtle">
          <DialogTitle className="flex items-center gap-2 text-sm font-semibold">
            {config.icon}
            {config.title}
          </DialogTitle>
        </DialogHeader>

        <div className="px-5 py-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="relative w-10 h-10 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary flex items-center justify-center overflow-hidden">
              {candidate.avatar ? (
                <NextImage src={candidate.avatar} alt={candidate.name} fill className="object-cover" />
              ) : (
                <span className="text-sm font-semibold text-lia-text-secondary">
                  {candidate.name.charAt(0)}
                </span>
              )}
            </div>
            <div>
              <p className="text-base-ui font-medium text-lia-text-primary">{candidate.name}</p>
              <p className="text-xs text-lia-text-tertiary">
                {candidate.role} {candidate.currentCompany && `• ${candidate.currentCompany}`}
              </p>
            </div>
          </div>

          {config.steps.length > 0 && (
            <Stepper steps={config.steps} currentStep={config.steps.findIndex(s => s.status === 'current')} />
          )}

          {(flowType === 'approve_to_triage' || flowType === 'approve_to_interview') && (
            <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-xl p-3 mb-4">
              <div className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary flex items-center justify-center flex-shrink-0">
                  <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                </div>
                <div className="flex-1">
                  <p className="text-base-ui font-medium text-lia-text-primary mb-0.5">
                    {flowType === 'approve_to_triage' ? 'LIA vai iniciar a triagem' : 'LIA vai agendar a entrevista'}
                  </p>
                  <p className="text-xs text-lia-text-tertiary mb-1.5" aria-live="polite" aria-atomic="true">
                    {flowType === 'approve_to_triage' 
                      ? `Contato via ${contactChannels.join(' e ') || 'WhatsApp e Email'}`
                      : 'Candidato receberá link para escolher horário'
                    }
                  </p>
                  <LIARulesInfo type={flowType === 'approve_to_interview' ? 'interview' : 'triage'} />
                </div>
              </div>
            </div>
          )}

          {flowType === 'confirm_hire' && (
            <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-xl p-3 mb-4">
              <div className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary flex items-center justify-center flex-shrink-0">
                  <CheckCircle className="w-3.5 h-3.5 text-lia-text-secondary" />
                </div>
                <div className="flex-1">
                  <p className="text-base-ui font-medium text-lia-text-primary mb-0.5">
                    LIA vai enviar boas-vindas
                  </p>
                  <p className="text-xs text-lia-text-tertiary mb-1.5">
                    {`Contato via ${contactChannels.join(' e ') || 'Email'} com próximos passos de onboarding`}
                  </p>
                </div>
              </div>
            </div>
          )}

          {flowType === 'reject_pre_triage' && (
            <div className="bg-wedo-orange/10 dark:bg-wedo-orange/10/20 rounded-md p-3 mb-4">
              <div className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-full bg-wedo-coral/10 flex items-center justify-center flex-shrink-0">
                  <AlertCircle className="w-3.5 h-3.5 text-wedo-coral" />
                </div>
                <div className="flex-1">
                  <p className="text-base-ui font-medium text-lia-text-primary mb-0.5" aria-live="polite" aria-atomic="true">
                    Candidato será reprovado
                  </p>
                  <p className="text-xs text-lia-text-tertiary">
                    Como ainda não iniciou a triagem, não é necessário enviar feedback.
                  </p>
                </div>
              </div>
            </div>
          )}

          {flowType === 'reject_post_triage' && (
            <div className="bg-wedo-orange/10 dark:bg-wedo-orange/10/20 rounded-md p-3 mb-4">
              <div className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-full bg-wedo-coral/10 flex items-center justify-center flex-shrink-0">
                  <MessageSquare className="w-3.5 h-3.5 text-wedo-coral" />
                </div>
                <div className="flex-1">
                  <p className="text-base-ui font-medium text-lia-text-primary mb-0.5" aria-live="polite" aria-atomic="true">
                    Candidato participou da triagem
                  </p>
                  <p className="text-xs text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
                    Recomendamos enviar feedback para manter boa experiência do candidato.
                  </p>
                </div>
              </div>
            </div>
          )}

          {flowType === 'request_urgency' && (
            <div className="bg-status-warning/10 dark:bg-status-warning/20 rounded-md p-3 mb-4">
              <div className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-full bg-status-warning/10 flex items-center justify-center flex-shrink-0">
                  <AlertCircle className="w-3.5 h-3.5 text-status-warning" />
                </div>
                <div className="flex-1">
                  <p className="text-base-ui font-medium text-lia-text-primary mb-0.5">
                    Solicitação de Urgência
                  </p>
                  <p className="text-xs text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
                    A LIA enviará uma nova mensagem de agendamento com prioridade alta para o candidato, solicitando retorno imediato.
                  </p>
                </div>
              </div>
            </div>
          )}

          {flowType === 'reschedule_interview' && (
            <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-xl p-3 mb-4">
              <div className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-elevated flex items-center justify-center flex-shrink-0">
                  <Calendar className="w-3.5 h-3.5 text-lia-text-secondary" />
                </div>
                <div className="flex-1">
                  <p className="text-base-ui font-medium text-lia-text-primary mb-0.5">
                    Alterar Horário da Entrevista
                  </p>
                  <p className="text-xs text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
                    A LIA vai buscar novos horários disponíveis na sua agenda e enviar as opções para o candidato escolher.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="px-6 py-3 bg-lia-bg-secondary dark:bg-lia-bg-primary border-t border-lia-border-subtle dark:border-lia-border-subtle flex justify-end gap-2">
          <Button 
            variant="outline" 
            onClick={onClose} 
            disabled={isLoading}
            className="text-xs h-8 border border-lia-border-default text-lia-text-secondary hover:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-btn-primary-hover"
           
          >
            Cancelar
          </Button>
          
          {(config as Record<string, unknown>).showFeedbackActions ? (
            <>
              <Button
                variant="ghost"
                onClick={() => {
                  onConfirm('reject_no_feedback')
                  onClose()
                }}
                disabled={isLoading}
                className="text-xs h-8 text-lia-text-secondary"
               
              >
                Apenas reprovar
              </Button>
              <Button
                onClick={() => {
                  if (onOpenFeedbackModal) {
                    onOpenFeedbackModal(candidate)
                    onClose()
                  }
                }}
                disabled={isLoading}
                className="bg-wedo-coral hover:bg-status-error text-white text-xs h-8"
               
              >
                <Send className="w-3.5 h-3.5 mr-1" />
                Enviar Feedback
              </Button>
            </>
          ) : (
            <Button
              onClick={handleConfirm}
              disabled={isLoading}
              className={`${config.confirmColor} text-white text-xs h-8`}
             
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin motion-reduce:animate-none" />
                  Processando...
                </>
              ) : (
                <>
                  {flowType.startsWith('reject') ? (
                    <X className="w-3.5 h-3.5 mr-1" />
                  ) : (
                    <Check className="w-3.5 h-3.5 mr-1" />
                  )}
                  {config.confirmLabel}
                </>
              )}
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default CandidateDecisionFlowModal
