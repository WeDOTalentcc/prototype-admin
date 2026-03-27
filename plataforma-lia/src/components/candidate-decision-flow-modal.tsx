"use client"

import React, { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
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
  onOpenFeedbackModal?: (candidate: any) => void
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
              className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium transition-all ${
                step.status === 'completed'
                  ? 'bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900'
                  : step.status === 'current'
                  ? 'bg-gray-900 text-white ring-2 ring-gray-900/20 dark:bg-gray-100 dark:text-gray-900'
                  : 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
              }`}
              style={{ fontFamily: "'Open Sans', sans-serif" }}
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
                  ? 'text-gray-900 font-medium dark:text-gray-100'
                  : step.status === 'completed'
                  ? 'text-gray-600 dark:text-gray-400'
                  : 'text-gray-400'
              }`}
              style={{ fontFamily: "'Open Sans', sans-serif" }}
            >
              {step.label}
            </span>
          </div>
          {index < steps.length - 1 && (
            <div
              className={`flex-1 h-0.5 mx-1.5 ${
                steps[index + 1].status === 'completed' || steps[index + 1].status === 'current'
                  ? 'bg-gray-900 dark:bg-gray-100'
                  : 'bg-gray-200 dark:bg-gray-700'
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
          <button className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-gray-900 dark:hover:text-gray-100 transition-colors" style={{ fontFamily: "'Open Sans', sans-serif" }}>
            <Info className="w-3 h-3" />
            <span>Como funciona?</span>
          </button>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-xs p-3">
          <div className="space-y-2">
            <p className="font-medium text-xs text-gray-950 dark:text-gray-50" style={{ fontFamily: "'Open Sans', sans-serif" }}>
              {isInterview ? 'Processo de Agendamento LIA:' : 'Processo de Triagem LIA:'}
            </p>
            <ul className="space-y-1 text-xs text-gray-600 dark:text-gray-300" style={{ fontFamily: "'Open Sans', sans-serif" }}>
              {isInterview ? (
                <>
                  <li className="flex items-start gap-1.5">
                    <span className="text-gray-400 dark:text-gray-500">•</span>
                    LIA envia mensagem por WhatsApp e Email com link e horários disponíveis em sua agenda
                  </li>
                  <li className="flex items-start gap-1.5">
                    <span className="text-gray-400 dark:text-gray-500">•</span>
                    Se não responder, nova tentativa a cada 12h
                  </li>
                  <li className="flex items-start gap-1.5">
                    <span className="text-gray-400 dark:text-gray-500">•</span>
                    Após 3 tentativas sem resposta, você será avisado
                  </li>
                </>
              ) : (
                <>
                  <li className="flex items-start gap-1.5">
                    <span className="text-gray-400 dark:text-gray-500">•</span>
                    LIA envia convite via WhatsApp e Email
                  </li>
                  <li className="flex items-start gap-1.5">
                    <span className="text-gray-400 dark:text-gray-500">•</span>
                    Se não responder, nova tentativa a cada 24h
                  </li>
                  <li className="flex items-start gap-1.5">
                    <span className="text-gray-400 dark:text-gray-500">•</span>
                    Após 3 tentativas sem resposta, você será avisado
                  </li>
                  <li className="flex items-start gap-1.5">
                    <span className="text-gray-400 dark:text-gray-500">•</span>
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
  }, [flowType, candidate.name])

  const getFlowConfig = () => {
    switch (flowType) {
      case 'approve_to_triage':
        return {
          title: 'Aprovar para Triagem',
          icon: <Brain className="w-5 h-5 text-wedo-cyan" />,
          steps: [
            { id: 'approve', label: 'Aprovação', status: 'current' as const },
            { id: 'triage', label: 'Triagem LIA', status: 'upcoming' as const },
            { id: 'interview', label: 'Entrevista', status: 'upcoming' as const },
            { id: 'schedule', label: 'Agendamento', status: 'upcoming' as const },
          ],
          confirmLabel: 'Iniciar Triagem',
          confirmColor: 'bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200',
        }
      case 'approve_to_interview':
        return {
          title: 'Aprovar para Entrevista',
          icon: <Calendar className="w-5 h-5 text-gray-700 dark:text-gray-300" />,
          steps: [
            { id: 'approve', label: 'Aprovação', status: 'completed' as const },
            { id: 'triage', label: 'Triagem LIA', status: 'completed' as const },
            { id: 'interview', label: 'Entrevista', status: 'current' as const },
            { id: 'schedule', label: 'Agendamento', status: 'upcoming' as const },
          ],
          confirmLabel: 'Agendar Entrevista',
          confirmColor: 'bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200',
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
          icon: <AlertCircle className="w-5 h-5 text-amber-500" />,
          steps: [],
          confirmLabel: 'Enviar Solicitação Urgente',
          confirmColor: 'bg-amber-500 hover:bg-amber-600',
          description: 'A LIA enviará uma nova mensagem de agendamento com prioridade alta para o candidato, solicitando retorno imediato.',
        }
      case 'reschedule_interview':
        return {
          title: 'Alterar Horário',
          icon: <Calendar className="w-5 h-5 text-gray-700 dark:text-gray-300" />,
          steps: [],
          confirmLabel: 'Buscar Novos Horários',
          confirmColor: 'bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200',
          description: 'A LIA vai buscar novos horários disponíveis na sua agenda e enviar as opções para o candidato escolher.',
        }
      case 'confirm_hire':
        return {
          title: 'Confirmar Contratação',
          icon: <CheckCircle className="w-5 h-5 text-gray-700 dark:text-gray-300" />,
          steps: [
            { id: 'approve', label: 'Aprovação', status: 'completed' as const },
            { id: 'triage', label: 'Triagem', status: 'completed' as const },
            { id: 'interview', label: 'Entrevista', status: 'completed' as const },
            { id: 'hire', label: 'Contratação', status: 'current' as const },
          ],
          confirmLabel: 'Confirmar Contratação',
          confirmColor: 'bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200',
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

  const contactChannels = []
  if (candidate.hasWhatsApp || candidate.phone) contactChannels.push('WhatsApp')
  if (candidate.email) contactChannels.push('Email')

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[480px] p-0 overflow-hidden">
        <DialogHeader className="px-5 pt-5 pb-3 border-b border-gray-200 dark:border-gray-700">
          <DialogTitle className="flex items-center gap-2 text-sm font-semibold" style={{ fontFamily: "'Open Sans', sans-serif" }}>
            {config.icon}
            {config.title}
          </DialogTitle>
        </DialogHeader>

        <div className="px-5 py-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center overflow-hidden">
              {candidate.avatar ? (
                <img src={candidate.avatar} alt={candidate.name} className="w-full h-full object-cover" />
              ) : (
                <span className="text-sm font-semibold text-gray-600 dark:text-gray-300" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                  {candidate.name.charAt(0)}
                </span>
              )}
            </div>
            <div>
              <p className="text-base-ui font-medium text-gray-950 dark:text-gray-50" style={{ fontFamily: "'Open Sans', sans-serif" }}>{candidate.name}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                {candidate.role} {candidate.currentCompany && `• ${candidate.currentCompany}`}
              </p>
            </div>
          </div>

          {config.steps.length > 0 && (
            <Stepper steps={config.steps} currentStep={config.steps.findIndex(s => s.status === 'current')} />
          )}

          {(flowType === 'approve_to_triage' || flowType === 'approve_to_interview') && (
            <div className="bg-gray-50 dark:bg-gray-800/50 rounded-md p-3 mb-4">
              <div className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center flex-shrink-0">
                  <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                </div>
                <div className="flex-1">
                  <p className="text-base-ui font-medium text-gray-950 dark:text-gray-50 mb-0.5" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                    {flowType === 'approve_to_triage' ? 'LIA vai iniciar a triagem' : 'LIA vai agendar a entrevista'}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-1.5" style={{ fontFamily: "'Open Sans', sans-serif" }}>
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
            <div className="bg-gray-50 dark:bg-gray-800/50 rounded-md p-3 mb-4">
              <div className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center flex-shrink-0">
                  <CheckCircle className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                </div>
                <div className="flex-1">
                  <p className="text-base-ui font-medium text-gray-950 dark:text-gray-50 mb-0.5" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                    LIA vai enviar boas-vindas
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-1.5" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                    {`Contato via ${contactChannels.join(' e ') || 'Email'} com próximos passos de onboarding`}
                  </p>
                </div>
              </div>
            </div>
          )}

          {flowType === 'reject_pre_triage' && (
            <div className="bg-orange-50 dark:bg-orange-900/20 rounded-md p-3 mb-4">
              <div className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-full bg-wedo-coral/10 flex items-center justify-center flex-shrink-0">
                  <AlertCircle className="w-3.5 h-3.5 text-wedo-coral" />
                </div>
                <div className="flex-1">
                  <p className="text-base-ui font-medium text-gray-950 dark:text-gray-50 mb-0.5" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                    Candidato será reprovado
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                    Como ainda não iniciou a triagem, não é necessário enviar feedback.
                  </p>
                </div>
              </div>
            </div>
          )}

          {flowType === 'reject_post_triage' && (
            <div className="bg-orange-50 dark:bg-orange-900/20 rounded-md p-3 mb-4">
              <div className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-full bg-wedo-coral/10 flex items-center justify-center flex-shrink-0">
                  <MessageSquare className="w-3.5 h-3.5 text-wedo-coral" />
                </div>
                <div className="flex-1">
                  <p className="text-base-ui font-medium text-gray-950 dark:text-gray-50 mb-0.5" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                    Candidato participou da triagem
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                    Recomendamos enviar feedback para manter boa experiência do candidato.
                  </p>
                </div>
              </div>
            </div>
          )}

          {flowType === 'request_urgency' && (
            <div className="bg-amber-50 dark:bg-amber-900/20 rounded-md p-3 mb-4">
              <div className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-full bg-amber-500/10 flex items-center justify-center flex-shrink-0">
                  <AlertCircle className="w-3.5 h-3.5 text-amber-500" />
                </div>
                <div className="flex-1">
                  <p className="text-base-ui font-medium text-gray-950 dark:text-gray-50 mb-0.5" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                    Solicitação de Urgência
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                    A LIA enviará uma nova mensagem de agendamento com prioridade alta para o candidato, solicitando retorno imediato.
                  </p>
                </div>
              </div>
            </div>
          )}

          {flowType === 'reschedule_interview' && (
            <div className="bg-gray-50 dark:bg-gray-800/50 rounded-md p-3 mb-4">
              <div className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center flex-shrink-0">
                  <Calendar className="w-3.5 h-3.5 text-gray-700 dark:text-gray-300" />
                </div>
                <div className="flex-1">
                  <p className="text-base-ui font-medium text-gray-950 dark:text-gray-50 mb-0.5" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                    Alterar Horário da Entrevista
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                    A LIA vai buscar novos horários disponíveis na sua agenda e enviar as opções para o candidato escolher.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="px-6 py-3 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-2">
          <Button 
            variant="outline" 
            onClick={onClose} 
            disabled={isLoading}
            className="text-xs h-8 border border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
            style={{ fontFamily: "'Open Sans', sans-serif" }}
          >
            Cancelar
          </Button>
          
          {(config as any).showFeedbackActions ? (
            <>
              <Button
                variant="ghost"
                onClick={() => {
                  onConfirm('reject_no_feedback')
                  onClose()
                }}
                disabled={isLoading}
                className="text-xs h-8 text-gray-600"
                style={{ fontFamily: "'Open Sans', sans-serif" }}
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
                style={{ fontFamily: "'Open Sans', sans-serif" }}
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
              style={{ fontFamily: "'Open Sans', sans-serif" }}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
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
