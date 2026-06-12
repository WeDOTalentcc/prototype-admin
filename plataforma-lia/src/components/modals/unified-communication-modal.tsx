"use client"

import React from "react"
import { createPortal } from "react-dom"
import { Button } from "@/components/ui/button"
import {
  Mail, MessageSquare, Send, X, RefreshCw
} from "lucide-react"
import { textStyles, cardStyles } from '@/lib/design-tokens'
import { MessageComposer } from '@/components/communication'
import { useUnifiedCommunication } from "./useUnifiedCommunication"
import { MessagePreviewPanel } from "./unified-communication-preview"
import { ChannelSelector, InterviewSettingsSection, VacancyLinkingSection } from "./unified-communication-form-sections"

export type { CommunicationType, CommunicationChannel } from "./unified-communication-types"
export type { UnifiedCommunicationModalProps } from "./unified-communication-types"

import type { UnifiedCommunicationModalProps } from "./unified-communication-types"

export function UnifiedCommunicationModal({
  isOpen,
  onClose,
  candidate: propCandidate,
  type,
  jobTitle,
  onSend,
  companyId,
  selectedCandidates = [],
  situation: explicitSituation,
  aiFeedbackContext
}: UnifiedCommunicationModalProps) {
  const {
    isBulkMode,
    candidate,
    channel,
    setChannel,
    subject,
    setSubject,
    message,
    setMessage,
    isSending,
    interviewSettings,
    setInterviewSettings,
    linkToVacancy,
    setLinkToVacancy,
    selectedVacancyId,
    setSelectedVacancyId,
    selectedStage,
    setSelectedStage,
    vacancies,
    isLoadingVacancies,
    linkOnCompletionOnly,
    setLinkOnCompletionOnly,
    roleOrJob,
    getSituationForType,
    getModalInfo,
    handleTemplateSelect,
    handleSend,
    dialogRef
  } = useUnifiedCommunication({
    isOpen,
    onClose,
    propCandidate,
    type,
    jobTitle,
    onSend,
    companyId,
    selectedCandidates,
    explicitSituation,
    aiFeedbackContext
  })

  if (!isOpen || (!candidate && selectedCandidates.length === 0)) return null

  const safeCandidate = candidate!
  const modalInfo = getModalInfo()

  const modalContent = (
    <div className="fixed inset-0 bg-lia-overlay backdrop-blur-[1px] z-modal flex items-center justify-center p-4" onClick={(e) => { if (e.target === e.currentTarget) onClose() }}>
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="comm-modal-title"
        className={`${cardStyles.default} rounded-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col`}
      >
        <div className="flex items-center justify-between px-6 pt-5 pb-4 bg-lia-bg-secondary/50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-lia-bg-tertiary rounded-full flex items-center justify-center">
              <modalInfo.icon className="w-4 h-4 text-lia-text-secondary" aria-hidden="true" />
            </div>
            <div>
              <h3 id="comm-modal-title" className={textStyles.title}>
                {modalInfo.title}
              </h3>
              <p className={textStyles.description}>
                {safeCandidate.name} • {safeCandidate.role || 'a vaga'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-lia-text-secondary hover:text-lia-text-primary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan"
            aria-label="Fechar modal de comunicação"
            data-dismiss="true"
          >
            <X className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>

        <div className="flex-1 flex overflow-hidden">
          <div className="w-1/2 border-r border-lia-border-subtle overflow-y-auto">
            <div className="p-5 space-y-5">
              <ChannelSelector
                channel={channel}
                setChannel={setChannel}
                candidate={safeCandidate}
              />

              {type === 'agendamento' && (
                <InterviewSettingsSection
                  interviewSettings={interviewSettings}
                  setInterviewSettings={setInterviewSettings}
                />
              )}

              <MessageComposer
                channel={channel === 'both' ? 'email' : channel}
                situation={getSituationForType(type)}
                initialSubject={subject}
                initialMessage={message}
                onSubjectChange={setSubject}
                onMessageChange={setMessage}
                onTemplateSelect={handleTemplateSelect}
                showTemplateSelector={true}
                showLiaAdjust={true}
                showVariableSelector={true}
                candidateContext={{
                  name: safeCandidate.name,
                  role: safeCandidate.role,
                  location: safeCandidate.location,
                  skills: safeCandidate.skills
                }}
                jobContext={{
                  title: jobTitle || roleOrJob
                }}
              />

              <VacancyLinkingSection
                type={type}
                linkToVacancy={linkToVacancy}
                setLinkToVacancy={setLinkToVacancy}
                selectedVacancyId={selectedVacancyId}
                setSelectedVacancyId={setSelectedVacancyId}
                selectedStage={selectedStage}
                setSelectedStage={setSelectedStage}
                vacancies={vacancies}
                isLoadingVacancies={isLoadingVacancies}
                linkOnCompletionOnly={linkOnCompletionOnly}
                setLinkOnCompletionOnly={setLinkOnCompletionOnly}
                isBulkMode={isBulkMode}
                selectedCandidatesCount={selectedCandidates.length}
              />
            </div>
          </div>

          <MessagePreviewPanel
            channel={channel}
            type={type}
            subject={subject}
            message={message}
            candidate={safeCandidate}
          />
        </div>

        <div className="px-6 py-4 bg-lia-bg-secondary rounded-b-xl flex items-center justify-between">
          <div className={textStyles.caption}>
            {channel === 'email' && (
              <span className="flex items-center gap-1">
                <Mail className="w-3 h-3" />
                Email será enviado via sistema
              </span>
            )}
            {channel === 'whatsapp' && (
              <span className="flex items-center gap-1">
                <MessageSquare className="w-3 h-3" />
                WhatsApp será enviado via sistema
              </span>
            )}
            {channel === 'both' && (
              <span className="flex items-center gap-1">
                <Mail className="w-3 h-3" />
                <MessageSquare className="w-3 h-3" />
                Email e WhatsApp serão enviados via sistema
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onClose}
              className="h-9 px-4 text-xs font-medium bg-lia-bg-primary border border-lia-border-default hover:bg-lia-interactive-hover text-lia-text-secondary dark:hover:bg-lia-btn-primary-bg"
            >
              Cancelar
            </Button>
            <Button
              size="sm"
              onClick={handleSend}
              disabled={isSending || !message.trim() || ((channel === 'email' || channel === 'both') && !subject.trim())}
              className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active gap-2"
            >
              {isSending ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
                  Enviando...
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  {channel === 'email' ? 'Enviar Email' : channel === 'whatsapp' ? 'Enviar WhatsApp' : 'Enviar Ambos'}
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )

  if (typeof document === 'undefined') return null

  return createPortal(modalContent, document.body)
}

export default UnifiedCommunicationModal
