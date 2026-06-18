"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import React from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { cn } from "@/lib/utils"
import {
  Loader2,
  Check,
  X,
  ArrowRight,
  Send,
  CheckCircle2,
  ChevronRight,
} from "lucide-react"
import { useJobUnpublish } from "./useJobUnpublish"
import { OptionsStep, CommunicationStep } from "./UnpublishSteps"
import { ConfirmationStep, CompleteStep } from "./UnpublishFinalSteps"

export interface JobUnpublishModalProps {
  isOpen: boolean
  onClose: () => void
  jobs: Array<{
    id: string
    code?: string
    title: string
    status: string
    is_published?: boolean
    published_channels?: string[]
  }>
  candidates?: Array<{
    id: string
    name: string
    email?: string
    phone?: string
    stage: string
    jobId: string
  }>
  onUnpublish: (data: UnpublishData) => Promise<void>
  onComplete?: () => void
  onNavigateToJobWithCommunication?: (jobId: string, params: {
    template: string
    candidateIds: string[]
    channel: 'email' | 'whatsapp' | 'both'
  }) => void
}

export interface UnpublishData {
  jobIds: string[]
  freezeJob: boolean
  freezeReason?: string
  freezeStartDate?: string
  unfreezeDate?: string
  notifyApplicants: boolean
  notificationChannel?: 'email' | 'whatsapp' | 'both'
  notificationMessage?: string
  notificationSubject?: string
  candidateIds?: string[]
  cancelScheduledInterviews: boolean
  cancelScheduledScreenings: boolean
  sendRecruiterSummary: boolean
}

export function JobUnpublishModal(props: JobUnpublishModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('job-unpublish', props.isOpen)

  const hook = useJobUnpublish(props)

  const {
    currentStep, setCurrentStep,
    isSubmitting,
    freezeJob, freezeReason,
    notifyApplicants, notificationChannel,
    notificationMessage,
    selectedCandidateIds,
    acknowledgedWarning,
    hasProposalBlock,
    handleProceed, handleCommunicationProceed,
    handleSubmit, handleClose,
    jobs,
  } = hook

  const getStepIndicator = () => {
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

  const getFooterButtons = () => {
    switch (currentStep) {
      case 'options':
        return (
          <>
            <Button variant="outline" onClick={handleClose} disabled={isSubmitting}
              className="h-9 px-4 text-xs font-medium border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary">
              Cancelar
            </Button>
            <Button onClick={handleProceed}
              disabled={isSubmitting || hasProposalBlock || (freezeJob && !freezeReason)}
              className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text">
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
            <Button variant="outline" onClick={() => setCurrentStep('options')} disabled={isSubmitting}
              className="h-9 px-4 text-xs font-medium border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary">
              Voltar
            </Button>
            <Button onClick={handleCommunicationProceed}
              disabled={isSubmitting || selectedCandidateIds.size === 0 || !notificationMessage}
              className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text">
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
            <Button variant="outline" onClick={() => setCurrentStep('communication')} disabled={isSubmitting}
              className="h-9 px-4 text-xs font-medium border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary">
              Voltar
            </Button>
            <Button onClick={handleSubmit} disabled={isSubmitting || !acknowledgedWarning}
              className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text">
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
          <Button onClick={handleClose}
            className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text">
            <Check className="w-3.5 h-3.5 mr-1.5" />
            Concluir
          </Button>
        )
    }
  }

  return (
    <Dialog open={props.isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className="max-w-lg bg-lia-bg-primary border border-lia-border-subtle">
        <DialogHeader className="pb-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-lia-bg-tertiary flex items-center justify-center">
              {currentStep === 'complete' ? (
                <CheckCircle2 className="w-4 h-4 text-status-success" />
              ) : (
                <X className="w-4 h-4 text-lia-text-secondary" />
              )}
            </div>
            <div>
              <DialogTitle className="text-sm font-semibold text-lia-text-primary">
                {currentStep === 'complete' ? 'Processo Finalizado' : 'Despublicar Vagas'}
              </DialogTitle>
              <p className="text-xs text-lia-text-secondary mt-0.5" aria-live="polite" aria-atomic="true">
                {jobs.length} vaga{jobs.length > 1 ? 's' : ''} selecionada{jobs.length > 1 ? 's' : ''}
              </p>
            </div>
          </div>
        </DialogHeader>

        <div className="py-4">
          {getStepIndicator()}

          {currentStep === 'options' && <OptionsStep hook={hook} />}
          {currentStep === 'communication' && <CommunicationStep hook={hook} />}
          {currentStep === 'confirmation' && <ConfirmationStep hook={hook} />}
          {currentStep === 'complete' && <CompleteStep hook={hook} />}
        </div>

        <DialogFooter className="border-t border-lia-border-subtle pt-3 gap-2">
          {getFooterButtons()}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
