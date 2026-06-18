"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import React from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Pause, Play, XCircle, ChevronRight, Loader2 } from "lucide-react"
import { useJobStatusModal } from "./job-status/useJobStatusModal"
import { PauseOptionsStep } from "./job-status/PauseOptionsStep"
import { ActivateOptionsStep } from "./job-status/ActivateOptionsStep"
import { CancelOptionsStep } from "./job-status/CancelOptionsStep"
import { CommunicationStep } from "./job-status/CommunicationStep"
import { ConfirmationStep } from "./job-status/ConfirmationStep"
import { CompleteStep } from "./job-status/CompleteStep"
import { StepIndicator } from "./job-status/StepIndicator"

export type { PauseData, ActivateData, CancelData } from "./job-status/types"

interface JobStatusModalProps {
  isOpen: boolean
  onClose: () => void
  jobs: Array<{
    id: string
    code?: string
    title: string
    status: string
    candidates_count?: number
    screening_count?: number
    interviews_scheduled?: number
    tests_scheduled?: number
    paused_since?: string
    approved_count?: number
  }>
  candidates?: Array<{
    id: string
    name: string
    email?: string
    phone?: string
    stage: string
    jobId: string
  }>
  mode: 'pause' | 'activate' | 'cancel'
  onPause?: (data: import("./job-status/types").PauseData) => Promise<void | unknown>
  onActivate?: (data: import("./job-status/types").ActivateData) => Promise<void | unknown>
  onCancel?: (data: import("./job-status/types").CancelData) => Promise<void | unknown>
  onStatusChange?: (jobIds: string[], newStatus: string, options: {
    reason?: string
    notifyRecruiters?: boolean
    notifyCandidates?: boolean
    resumeScreening?: boolean
    republish?: boolean
    updateDeadlines?: boolean
  }) => void
  onNavigateToJobWithCommunication?: (jobId: string, params: {
    template: string
    candidateIds: string[]
    channel: 'email' | 'whatsapp' | 'both'
  }) => void
}

export function JobStatusModal({
  isOpen,
  onClose,
  jobs,
  candidates = [],
  mode,
  onPause,
  onActivate,
  onCancel,
  onStatusChange,
  onNavigateToJobWithCommunication
}: JobStatusModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('job-status', isOpen)

  const state = useJobStatusModal({
    isOpen,
    onClose,
    jobs,
    candidates,
    mode,
    onPause,
    onActivate,
    onCancel,
    onStatusChange,
    onNavigateToJobWithCommunication,
  })

  if (jobs.length === 0) return null

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && state.handleClose()}>
      <DialogContent className="max-w-2xl bg-lia-bg-primary border border-lia-border-subtle">
        <DialogHeader className="pb-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-lia-bg-tertiary">
              {state.isCancelMode ? (
                <XCircle className="w-4 h-4 text-status-error" />
              ) : state.isPauseMode ? (
                <Pause className="w-4 h-4 text-lia-text-secondary" />
              ) : (
                <Play className="w-4 h-4 text-lia-text-secondary" />
              )}
            </div>
            <div>
              <DialogTitle className="text-sm font-semibold text-lia-text-primary">
                {state.isCancelMode ? 'Cancelar Vagas' : state.isPauseMode ? 'Pausar Vagas' : 'Ativar Vagas'}
              </DialogTitle>
              <p className="text-xs text-lia-text-secondary mt-0.5" aria-live="polite" aria-atomic="true">
                {jobs.length} vaga{jobs.length > 1 ? 's' : ''} selecionada{jobs.length > 1 ? 's' : ''}
              </p>
            </div>
          </div>
        </DialogHeader>

        <div className="py-4">
          <StepIndicator
            currentStep={state.currentStep}
            isPauseMode={state.isPauseMode}
            notifyApplicants={state.notifyApplicants}
          />

          {state.currentStep === 'options' && (state.isCancelMode ? (
            <CancelOptionsStep
              jobs={jobs}
              cancelReason={state.cancelReason}
              customReason={state.customReason}
              notifyRecruiters={state.notifyRecruiters}
              recruiterChannel={state.recruiterChannel}
              notifyApplicants={state.notifyApplicants}
              onCancelReasonChange={state.setCancelReason}
              onCustomReasonChange={state.setCustomReason}
              onNotifyRecruitersChange={state.setNotifyRecruiters}
              onRecruiterChannelChange={state.setRecruiterChannel}
              onNotifyApplicantsChange={state.setNotifyApplicants}
            />
          ) : state.isPauseMode ? (
            <PauseOptionsStep
              jobs={jobs}
              candidatesInProposal={state.candidatesInProposal}
              hasProposalBlock={state.hasProposalBlock}
              totalScreenings={state.totalScreenings}
              totalInterviews={state.totalInterviews}
              totalTests={state.totalTests}
              pauseReason={state.pauseReason}
              customReason={state.customReason}
              cancelScreenings={state.cancelScreenings}
              cancelInterviews={state.cancelInterviews}
              cancelTests={state.cancelTests}
              notifyRecruiters={state.notifyRecruiters}
              recruiterChannel={state.recruiterChannel}
              notifyApplicants={state.notifyApplicants}
              onPauseReasonChange={state.setPauseReason}
              onCustomReasonChange={state.setCustomReason}
              onCancelScreeningsChange={state.setCancelScreenings}
              onCancelInterviewsChange={state.setCancelInterviews}
              onCancelTestsChange={state.setCancelTests}
              onNotifyRecruitersChange={state.setNotifyRecruiters}
              onRecruiterChannelChange={state.setRecruiterChannel}
              onNotifyApplicantsChange={state.setNotifyApplicants}
            />
          ) : (
            <ActivateOptionsStep
              jobs={jobs}
              resumeScreening={state.resumeScreening}
              republish={state.republish}
              updateDeadlines={state.updateDeadlines}
              notifyRecruiters={state.notifyRecruiters}
              notifyApplicants={state.notifyApplicants}
              onResumeScreeningChange={state.setResumeScreening}
              onRepublishChange={state.setRepublish}
              onUpdateDeadlinesChange={state.setUpdateDeadlines}
              onNotifyRecruitersChange={state.setNotifyRecruiters}
              onNotifyApplicantsChange={state.setNotifyApplicants}
            />
          ))}

          {state.currentStep === 'communication' && (
            <CommunicationStep
              jobCandidatesCount={state.jobCandidates.length}
              candidatesInProposalCount={state.candidatesInProposal.length}
              notificationChannel={state.notificationChannel}
              onNotificationChannelChange={state.setNotificationChannel}
              templatesLoading={state.templatesLoading}
              selectedTemplateId={state.selectedTemplateId}
              onTemplateChange={state.handleTemplateChange}
              availableTemplates={state.availableTemplates}
              notificationSubject={state.notificationSubject}
              onNotificationSubjectChange={state.setNotificationSubject}
              notificationMessage={state.notificationMessage}
              onNotificationMessageChange={state.setNotificationMessage}
            />
          )}

          {state.currentStep === 'confirmation' && (
            <ConfirmationStep
              jobsCount={jobs.length}
              cancelScreenings={state.cancelScreenings}
              totalScreenings={state.totalScreenings}
              cancelInterviews={state.cancelInterviews}
              totalInterviews={state.totalInterviews}
              cancelTests={state.cancelTests}
              totalTests={state.totalTests}
              notifyApplicants={state.notifyApplicants}
              selectedCandidateIdsSize={state.selectedCandidateIds.size}
              notificationChannel={state.notificationChannel}
              notifyRecruiters={state.notifyRecruiters}
              recruiterChannel={state.recruiterChannel}
              pauseReason={state.pauseReason}
              customReason={state.customReason}
            />
          )}

          {state.currentStep === 'complete' && (
            <CompleteStep successMessage={state.getSuccessMessage()} notificationReport={state.notificationReport} />
          )}
        </div>

        <DialogFooter className="pt-4 gap-2">
          {state.currentStep === 'complete' ? (
            <Button
              onClick={state.handleClose}
              className="h-9 px-4 text-xs font-medium text-white bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover"
            >
              Fechar
            </Button>
          ) : (
            <>
              {state.currentStep !== 'options' && (
                <Button
                  variant="outline"
                  onClick={() => state.setCurrentStep(state.currentStep === 'confirmation' ? (state.notifyApplicants ? 'communication' : 'options') : 'options')}
                  className="h-9 px-4 text-xs font-medium border border-lia-border-default text-lia-text-secondary hover:bg-lia-interactive-hover"
                >
                  Voltar
                </Button>
              )}
              <Button
                variant="outline"
                onClick={state.handleClose}
                className="h-9 px-4 text-xs font-medium border border-lia-border-default text-lia-text-secondary hover:bg-lia-interactive-hover"
              >
                Cancelar
              </Button>
              <Button
                onClick={state.currentStep === 'options' ? state.handleProceed : state.currentStep === 'communication' ? state.handleCommunicationProceed : state.handleSubmit}
                disabled={state.isSubmitting || (state.isPauseMode && state.hasProposalBlock) || (state.isCancelMode && !state.cancelReason)}
                className="h-9 px-4 text-xs font-medium text-white bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover disabled:opacity-50"
              >
                {state.isSubmitting ? (
                  <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                ) : state.currentStep === 'options' ? (
                  <>
                    {state.notifyApplicants ? 'Continuar' : 'Revisar'}
                    <ChevronRight className="w-3.5 h-3.5 ml-1" />
                  </>
                ) : state.currentStep === 'communication' ? (
                  <>
                    Revisar
                    <ChevronRight className="w-3.5 h-3.5 ml-1" />
                  </>
                ) : state.isCancelMode ? (
                  <>
                    <XCircle className="w-3.5 h-3.5 mr-1.5" />
                    Cancelar {jobs.length} Vaga{jobs.length > 1 ? 's' : ''}
                  </>
                ) : state.isPauseMode ? (
                  <>
                    <Pause className="w-3.5 h-3.5 mr-1.5" />
                    Pausar {jobs.length} Vaga{jobs.length > 1 ? 's' : ''}
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 mr-1.5" />
                    Ativar {jobs.length} Vaga{jobs.length > 1 ? 's' : ''}
                  </>
                )}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
