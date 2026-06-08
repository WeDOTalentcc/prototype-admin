"use client"

import { LoadingModal } from "@/components/ui/loading"
import type { CommunicationType } from "@/components/modals/unified-communication-modal"
import dynamic from "next/dynamic"
import type { CandidatesPageModalsProps } from "./CandidatesPageModals.types"

const ContactModal = dynamic(() => import("@/components/quick-actions-modals").then(m => ({ default: m.ContactModal })), { ssr: false, loading: () => <LoadingModal /> })
const ScheduleModal = dynamic(() => import("@/components/quick-actions-modals").then(m => ({ default: m.ScheduleModal })), { ssr: false, loading: () => <LoadingModal /> })
const UnifiedCommunicationModal = dynamic(() => import("@/components/modals/unified-communication-modal").then(m => ({ default: m.UnifiedCommunicationModal })), { ssr: false, loading: () => <LoadingModal /> })
const SendEmailModal = dynamic(() => import("@/components/email-templates").then(m => ({ default: m.SendEmailModal })), { ssr: false, loading: () => <LoadingModal /> })

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
>

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
  } = props

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
        onSend={handleUnifiedModalSend}
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
    </>
  )
}
