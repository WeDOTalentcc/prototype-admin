"use client"

import React from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import { InputStep } from "@/components/modals/new-candidate/InputStep"
import { DuplicateFoundStep } from "./DuplicateFoundStep"
import { ProcessingStep, SuccessStep } from "./ProcessingAndSuccessSteps"
import { useNewCandidateUnifiedModal } from "./useNewCandidateUnifiedModal"
import type { NewCandidateUnifiedModalProps } from "./new-candidate-unified-types"

export type { NewCandidateUnifiedModalProps } from "./new-candidate-unified-types"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'

export function NewCandidateUnifiedModal({
  isOpen,
  onClose,
  onCandidateAdded,
  onOpenFullProfile,
}: NewCandidateUnifiedModalProps) {
  // P0-2 (2026-06-18): notify LIA which modal is open
  useLiaModalTracking('new-candidate', isOpen)
  const modal = useNewCandidateUnifiedModal({
    isOpen,
    onClose,
    onCandidateAdded,
    onOpenFullProfile,
  })

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md p-0 gap-0 overflow-hidden bg-lia-bg-primary border-lia-border-subtle" data-testid="new-candidate-unified-modal">
        <DialogHeader className="p-4 pb-0">
          <DialogTitle className="text-base font-semibold text-lia-text-primary font-sans">
            Novo Candidato
          </DialogTitle>
          <DialogDescription className="text-xs text-lia-text-tertiary font-sans">
            Cadastre um candidato usando CV, LinkedIn ou manualmente
          </DialogDescription>
        </DialogHeader>

        <div className="p-4">
          {modal.currentStep === 'input' && (
            <InputStep
              activeTab={modal.activeTab}
              setActiveTab={modal.setActiveTab}
              setError={modal.setError}
              selectedFile={modal.selectedFile}
              setSelectedFile={modal.setSelectedFile}
              cvText={modal.cvText}
              setCvText={modal.setCvText}
              isDragging={modal.isDragging}
              handleDragEnter={modal.handleDragEnter}
              handleDragLeave={modal.handleDragLeave}
              handleDragOver={modal.handleDragOver}
              handleDrop={modal.handleDrop}
              handleFileSelect={modal.handleFileSelect}
              isProcessing={modal.isProcessing}
              canSubmitCV={modal.canSubmitCV}
              handleSubmitCV={modal.handleSubmitCV}
              linkedinUrl={modal.linkedinUrl}
              setLinkedinUrl={modal.setLinkedinUrl}
              canSubmitLinkedin={modal.canSubmitLinkedin}
              handleSubmitLinkedin={modal.handleSubmitLinkedin}
              manualData={modal.manualData}
              setManualData={modal.setManualData}
              canSubmitManual={modal.canSubmitManual}
              handleSubmitManual={modal.handleSubmitManual}
              error={modal.error}
              fieldErrors={modal.fieldErrors}
              setFieldErrors={modal.setFieldErrors}
            />
          )}
          {modal.currentStep === 'duplicate-found' && (
            <DuplicateFoundStep
              duplicateResult={modal.duplicateResult}
              isProcessing={modal.isProcessing}
              onOpenExisting={modal.handleOpenExistingCandidate}
              onCreateAnyway={modal.handleCreateAnyway}
              onBack={() => {
                modal.setCurrentStep('input')
                modal.setDuplicateResult(null)
              }}
            />
          )}
          {modal.currentStep === 'processing' && (
            <ProcessingStep
              isEnriching={modal.isEnriching}
              activeTab={modal.activeTab}
              uploadProgress={modal.uploadProgress}
            />
          )}
          {modal.currentStep === 'success' && <SuccessStep />}
        </div>
      </DialogContent>
    </Dialog>
  )
}
