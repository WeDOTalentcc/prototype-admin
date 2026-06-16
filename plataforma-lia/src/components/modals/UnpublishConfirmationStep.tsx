"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"
import {
  Loader2,
  Check,
  X,
  CalendarOff,
  AlertCircle,
  CheckCircle2,
  ChevronRight,
  ArrowRight,
  Send,
  Mail,
} from "lucide-react"

type FlowStep = 'options' | 'communication' | 'confirmation' | 'complete'

export interface UnpublishStepIndicatorProps {
  notifyApplicants: boolean
  currentStep: FlowStep
}

export function UnpublishStepIndicator({ notifyApplicants, currentStep }: UnpublishStepIndicatorProps) {
  if (!notifyApplicants) return null

  const steps = [
    { id: 'unpublish', label: 'Despublicar', done: currentStep !== 'options' },
    { id: 'message', label: 'Enviar mensagem', done: currentStep === 'confirmation' || currentStep === 'complete' },
    { id: 'done', label: 'Processo finalizado', done: currentStep === 'complete' },
  ]

  return (
    <div className="flex items-center justify-center gap-1 mb-4 pb-3">
      {steps.map((step, index) => (
        <React.Fragment key={step.id}>
          <div className="flex items-center gap-1.5">
            <div className={cn(
              "w-5 h-5 rounded-full flex items-center justify-center text-micro font-medium",
              step.done
                ? "bg-lia-btn-primary-bg text-lia-btn-primary-text"
                : currentStep === 'options' && index === 0
                  ? "bg-lia-bg-tertiary text-lia-text-primary border border-lia-btn-primary-bg"
                  : currentStep === 'communication' && index === 1
                    ? "bg-lia-bg-tertiary text-lia-text-primary border border-lia-btn-primary-bg"
                    : currentStep === 'confirmation' && index === 1
                      ? "bg-lia-bg-tertiary text-lia-text-primary border border-lia-btn-primary-bg"
                      : "bg-lia-bg-tertiary text-lia-text-tertiary"
            )}>
              {step.done ? <Check className="w-3 h-3" /> : index + 1}
            </div>
            <span className={cn(
              "text-xs font-medium",
              step.done ? "text-lia-text-primary" : "text-lia-text-secondary"
            )}>
              {step.label}
            </span>
          </div>
          {index < steps.length - 1 && (
            <ChevronRight className="w-3.5 h-3.5 text-lia-text-muted mx-1" />
          )}
        </React.Fragment>
      ))}
    </div>
  )
}

export interface ConfirmationStepProps {
  selectedCandidateIds: Set<string>
  notificationChannel: string
  acknowledgedWarning: boolean
  setAcknowledgedWarning: (v: boolean) => void
}

export function ConfirmationStep({ selectedCandidateIds, notificationChannel, acknowledgedWarning, setAcknowledgedWarning }: ConfirmationStepProps) {
  return (
    <div className="space-y-4">
      <div className="p-4 bg-status-warning/10 border border-status-warning/30 rounded-xl">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-status-warning flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="text-xs font-semibold text-status-warning">Confirmação de ações</h4>
            <p className="text-xs text-status-warning mt-1">
              Ao confirmar, as seguintes ações serão executadas:
            </p>
            <ul className="mt-2 space-y-1.5">
              <li className="text-xs text-status-warning flex items-center gap-2">
                <Check className="w-3.5 h-3.5 text-status-warning" />
                A vaga será despublicada dos job boards
              </li>
              <li className="text-xs text-status-warning flex items-center gap-2">
                <Check className="w-3.5 h-3.5 text-status-warning" />
                Status alterado para "Paralisada"
              </li>
              <li className="text-xs text-status-warning flex items-center gap-2">
                <Check className="w-3.5 h-3.5 text-status-warning" />
                {selectedCandidateIds.size} candidato(s) serão notificados via {notificationChannel === 'both' ? 'email e WhatsApp' : notificationChannel}
              </li>
              <li className="text-xs text-status-warning flex items-center gap-2">
                <CalendarOff className="w-3.5 h-3.5 text-status-warning" />
                Entrevistas e triagens agendadas serão canceladas
              </li>
              <li className="text-xs text-status-warning flex items-center gap-2">
                <Mail className="w-3.5 h-3.5 text-status-warning" />
                Você receberá um email com o resumo de todas as ações
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div className="flex items-start gap-2 p-3 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle">
        <Checkbox
          id="acknowledgeWarning"
          checked={acknowledgedWarning}
          onCheckedChange={(checked) => setAcknowledgedWarning(!!checked)}
          className="mt-0.5 data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg"
        />
        <Label htmlFor="acknowledgeWarning" className="text-xs text-lia-text-secondary cursor-pointer">
          Li e estou ciente de que todas as ações acima serão executadas e não podem ser desfeitas.
        </Label>
      </div>
    </div>
  )
}

export interface CompleteStepProps {
  selectedCandidateIds: Set<string>
}

export function CompleteStep({ selectedCandidateIds }: CompleteStepProps) {
  return (
    <div className="py-6 text-center">
      <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-status-success/15 flex items-center justify-center">
        <CheckCircle2 className="w-8 h-8 text-status-success" />
      </div>
      <h3 className="text-sm font-semibold text-lia-text-primary mb-2">Processo finalizado!</h3>
      <p className="text-xs text-lia-text-secondary mb-4" aria-live="polite" aria-atomic="true">
        A vaga foi despublicada e congelada com sucesso.
      </p>
      <div className="bg-lia-bg-secondary rounded-xl p-3 border border-lia-border-subtle text-left space-y-2">
        <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
          <Check className="w-3.5 h-3.5 text-status-success" />
          <span aria-live="polite" aria-atomic="true">Vaga despublicada dos job boards</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
          <Check className="w-3.5 h-3.5 text-status-success" />
          <span>Status alterado para "Paralisada"</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
          <Check className="w-3.5 h-3.5 text-status-success" />
          <span aria-live="polite" aria-atomic="true">{selectedCandidateIds.size} candidatos notificados</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
          <Check className="w-3.5 h-3.5 text-status-success" />
          <span>Agendamentos cancelados</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
          <Mail className="w-3.5 h-3.5 text-lia-text-secondary" />
          <span>Resumo enviado para seu email</span>
        </div>
      </div>
    </div>
  )
}

export interface UnpublishFooterButtonsProps {
  currentStep: FlowStep
  isSubmitting: boolean
  hasProposalBlock: boolean
  freezeJob: boolean
  freezeReason: string
  notifyApplicants: boolean
  selectedCandidateIds: Set<string>
  notificationMessage: string
  acknowledgedWarning: boolean
  handleClose: () => void
  handleProceed: () => void
  handleCommunicationProceed: () => void
  handleSubmit: () => void
  setCurrentStep: (step: FlowStep) => void
}

export function UnpublishFooterButtons({
  currentStep,
  isSubmitting,
  hasProposalBlock,
  freezeJob,
  freezeReason,
  notifyApplicants,
  selectedCandidateIds,
  notificationMessage,
  acknowledgedWarning,
  handleClose,
  handleProceed,
  handleCommunicationProceed,
  handleSubmit,
  setCurrentStep,
}: UnpublishFooterButtonsProps) {
  switch (currentStep) {
    case 'options':
      return (
        <>
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={isSubmitting}
            className="h-9 px-4 text-xs font-medium border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary"
          >
            Cancelar
          </Button>
          <Button
            onClick={handleProceed}
            disabled={isSubmitting || hasProposalBlock || (freezeJob && !freezeReason)}
            className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
          >
            {isSubmitting ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none mr-1.5" />
            ) : notifyApplicants ? (
              <ArrowRight className="w-3.5 h-3.5 mr-1.5" />
            ) : (
              <X className="w-3.5 h-3.5 mr-1.5" />
            )}
            {notifyApplicants ? 'Continuar' : 'Despublicar'}
          </Button>
        </>
      )

    case 'communication':
      return (
        <>
          <Button
            variant="outline"
            onClick={() => setCurrentStep('options')}
            disabled={isSubmitting}
            className="h-9 px-4 text-xs font-medium border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary"
          >
            Voltar
          </Button>
          <Button
            onClick={handleCommunicationProceed}
            disabled={isSubmitting || selectedCandidateIds.size === 0 || !notificationMessage}
            className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
          >
            {isSubmitting ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none mr-1.5" />
            ) : freezeJob ? (
              <ArrowRight className="w-3.5 h-3.5 mr-1.5" />
            ) : (
              <Send className="w-3.5 h-3.5 mr-1.5" />
            )}
            {freezeJob ? 'Revisar e Confirmar' : 'Enviar e Despublicar'}
          </Button>
        </>
      )

    case 'confirmation':
      return (
        <>
          <Button
            variant="outline"
            onClick={() => setCurrentStep('communication')}
            disabled={isSubmitting}
            className="h-9 px-4 text-xs font-medium border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary"
          >
            Voltar
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || !acknowledgedWarning}
            className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
          >
            {isSubmitting ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none mr-1.5" />
            ) : (
              <Check className="w-3.5 h-3.5 mr-1.5" />
            )}
            Confirmar e Executar
          </Button>
        </>
      )

    case 'complete':
      return (
        <Button
          onClick={handleClose}
          className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
        >
          <Check className="w-3.5 h-3.5 mr-1.5" />
          Concluir
        </Button>
      )
  }
}
