"use client"

import { useState } from "react"
import type { CommunicationResult } from "@/components/modals/unified-communication-types"
import type { CommunicationType } from "@/components/modals/unified-communication-modal"
import dynamic from "next/dynamic"
import type { CandidatesPageModalsProps } from "./CandidatesPageModals.types"
import { BulkResultReport } from "@/components/bulk"
import type { BulkItemResult } from "@/lib/bulk"

const ContactModal = dynamic(() => import("@/components/quick-actions-modals").then(m => ({ default: m.ContactModal })), { ssr: false, loading: () => null })
const ScheduleModal = dynamic(() => import("@/components/quick-actions-modals").then(m => ({ default: m.ScheduleModal })), { ssr: false, loading: () => null })
const UnifiedCommunicationModal = dynamic(() => import("@/components/modals/unified-communication-modal").then(m => ({ default: m.UnifiedCommunicationModal })), { ssr: false, loading: () => null })
const ScheduleMessageModal = dynamic(() => import("@/components/communication").then(m => ({ default: m.ScheduleMessageModal })), { ssr: false, loading: () => null })
const SendEmailModal = dynamic(() => import("@/components/email-templates").then(m => ({ default: m.SendEmailModal })), { ssr: false, loading: () => null })

type CandidatesContactModalsProps = Pick<CandidatesPageModalsProps,
  | 'selectedCandidateForAction'
  | 'contactModalCandidate'
  | 'showContactModal'
  | 'contactModalAction'
  | 'setShowContactModal'
  | 'setSelectedCandidateForAction'
  | 'setContactModalCandidate'
  | 'setContactModalAction'
  | 'handleSendMessage'
  | 'showScheduleModal'
  | 'setShowScheduleModal'
  | 'handleScheduleComplete'
  | 'unifiedModalOpen'
  | 'unifiedModalCandidate'
  | 'unifiedModalSelectedCandidates'
  | 'unifiedModalType'
  | 'lastSearchQuery'
  | 'handleUnifiedModalClose'
  | 'handleUnifiedModalSend'
  | 'showSendEmailModal'
  | 'setShowSendEmailModal'
  | 'emailCandidateSelected'
  | 'setEmailCandidateSelected'
  | 'showScheduleMessageModal'
  | 'setShowScheduleMessageModal'
  | 'scheduleMessageCandidate'
  | 'setScheduleMessageCandidate'
>

const TYPE_LABELS: Record<string, string> = {
  email: 'Email',
  whatsapp: 'WhatsApp',
  triagem: 'Triagem',
  agendamento: 'Agendamento',
  feedback: 'Feedback',
}

export function CandidatesContactModals(props: CandidatesContactModalsProps) {
  const {
    selectedCandidateForAction,
    contactModalCandidate,
    showContactModal,
    contactModalAction,
    setShowContactModal,
    setSelectedCandidateForAction,
    setContactModalCandidate,
    setContactModalAction,
    handleSendMessage,
    showScheduleModal,
    setShowScheduleModal,
    handleScheduleComplete,
    unifiedModalOpen,
    unifiedModalCandidate,
    unifiedModalSelectedCandidates,
    unifiedModalType,
    lastSearchQuery,
    handleUnifiedModalClose,
    handleUnifiedModalSend,
    showSendEmailModal,
    setShowSendEmailModal,
    emailCandidateSelected,
    setEmailCandidateSelected,
    showScheduleMessageModal,
    setShowScheduleMessageModal,
    scheduleMessageCandidate,
    setScheduleMessageCandidate,
  } = props

  const [bulkReport, setBulkReport] = useState<{
    isOpen: boolean
    results: BulkItemResult[]
    actionLabel: string
  }>({ isOpen: false, results: [], actionLabel: '' })

  // Intercepts onSend: forwards to the original handler, then opens BulkResultReport
  // if the payload carries bulkResults (bulk mode injected by useUnifiedCommunication T5).
  const handleSend = (data: CommunicationResult) => {
    handleUnifiedModalSend?.(data)
    const withBulk = data as CommunicationResult & { bulkResults?: BulkItemResult[] }
    if (Array.isArray(withBulk.bulkResults) && withBulk.bulkResults.length > 0) {
      setBulkReport({
        isOpen: true,
        results: withBulk.bulkResults,
        actionLabel: TYPE_LABELS[data.type] ?? 'Envio',
      })
    }
  }

  return (
    <>
      {(selectedCandidateForAction || contactModalCandidate) && (
        <ContactModal
          isOpen={showContactModal}
          onClose={() => {
            setShowContactModal(false)
            setSelectedCandidateForAction(null)
            setContactModalCandidate(null)
            setContactModalAction('general')
          }}
          candidate={(() => {
            const c = contactModalCandidate || selectedCandidateForAction
            if (!c) return null
            return {
              id: c.id,
              name: c.name,
              role: c.position || c.role || '',
              email: c.email,
              phone: c.phone,
              location: c.location,
              avatar: c.avatar,
              score: c.score || 0,
              status: c.status || 'Novo',
              matchPercentage: c.liaAnalysis?.score ?? c.score ?? 0,
              riskLevel: 'low' as const,
              culturalFit: 85,
              technicalMatch: 90,
              experience: String(c.experience || ''),
              seniority: c.seniority_level || 'Pleno',
              availability: 'Imediata',
              expectedSalary: c.salary?.expected ? String(c.salary.expected) : '',
              preferredLocation: c.location,
              linkedin: c.linkedin,
              skills: c.skills || [],
              lastActivity: new Date().toISOString(),
              source: 'internal'
            }
          })()}
          onSend={handleSendMessage}
          initialAction={contactModalAction}
        />
      )}

      {selectedCandidateForAction && (
        <ScheduleModal
          isOpen={showScheduleModal}
          onClose={() => {
            setShowScheduleModal(false)
            setSelectedCandidateForAction(null)
          }}
          candidate={(() => {
            const sca = selectedCandidateForAction
            return ({
            id: sca.id,
            name: sca.name,
            role: sca.position,
            email: sca.email,
            phone: sca.phone,
            location: sca.location,
            avatar: sca.avatar || '',
            score: sca.score,
            status: sca.status || '',
            matchPercentage: sca.liaAnalysis?.score ?? sca.score,
            riskLevel: 'low' as const,
            culturalFit: 85,
            technicalMatch: 90,
            experience: String(sca.experience),
            seniority: sca.seniority_level || 'Pleno',
            availability: 'Imediata',
            expectedSalary: sca.salary?.expected ? String(sca.salary.expected) : '',
            preferredLocation: sca.location,
            linkedin: sca.linkedin,
            skills: sca.skills,
            lastActivity: new Date().toISOString(),
            source: 'internal'
          })
          })()}
          onSchedule={handleScheduleComplete}
        />
      )}

      <UnifiedCommunicationModal
        isOpen={unifiedModalOpen}
        onClose={handleUnifiedModalClose}
        candidate={unifiedModalCandidate ? (() => {
          const umc = unifiedModalCandidate
          return {
            id: umc.id,
            name: umc.name,
            role: umc.position || umc.current_title || '',
            email: umc.email,
            phone: umc.phone,
            location: umc.location,
            avatar: umc.avatar,
            score: umc.score,
            matchPercentage: umc.liaAnalysis?.score ?? umc.score,
            skills: umc.skills
          }
        })() : null}
        type={unifiedModalType}
        selectedCandidates={unifiedModalSelectedCandidates}
        jobTitle={lastSearchQuery || undefined}
        onSend={handleSend}
        companyId="demo"
      />

      <SendEmailModal
        isOpen={showSendEmailModal}
        onClose={() => {
          setShowSendEmailModal(false)
          setEmailCandidateSelected(null)
        }}
        candidate={emailCandidateSelected ? ({
          id: emailCandidateSelected.id,
          name: emailCandidateSelected.name,
          email: emailCandidateSelected.email,
          phone: emailCandidateSelected.phone,
          current_title: emailCandidateSelected.position,
          technical_skills: emailCandidateSelected.skills,
          source: 'internal',
          is_active: true,
          is_remote: emailCandidateSelected.workModel === 'remoto',
          willing_to_relocate: false,
          tags: emailCandidateSelected.tags || [],
          status: emailCandidateSelected.status || '',
          lia_insights: {},
          soft_skills: [],
          languages: {},
          certifications: []
        }) : null}
        onSuccess={() => {
          setShowSendEmailModal(false)
          setEmailCandidateSelected(null)
        }}
      />


      {/* GAP-07-007 - Schedule Message Modal */}
      <ScheduleMessageModal
        open={showScheduleMessageModal}
        onClose={() => {
          setShowScheduleMessageModal(false)
          setScheduleMessageCandidate(null)
        }}
        candidateId={scheduleMessageCandidate?.id ?? ""}
        candidateName={scheduleMessageCandidate?.name ?? ""}
      />

      <BulkResultReport
        isOpen={bulkReport.isOpen}
        onClose={() => setBulkReport(s => ({ ...s, isOpen: false }))}
        results={bulkReport.results}
        actionLabel={bulkReport.actionLabel}
      />
    </>
  )
}
