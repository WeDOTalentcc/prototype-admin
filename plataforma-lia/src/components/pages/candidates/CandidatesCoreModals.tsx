"use client"

import { LoadingModal } from "@/components/ui/loading"
import dynamic from "next/dynamic"
import { toast } from "sonner"
import { useTranslations } from "next-intl"
import { liaApi } from "@/services/lia-api"
import { formatJobLocation } from "@/lib/jobs/location"
import type { CandidatesPageModalsProps } from "./CandidatesPageModals.types"

const CandidateComparison = dynamic(() => import("@/components/candidate-comparison").then(m => ({ default: m.CandidateComparison })), { ssr: false, loading: () => <LoadingModal /> })
const CandidatePage = dynamic(() => import("@/components/candidate-page").then(m => ({ default: m.CandidatePage })), { ssr: false, loading: () => <LoadingModal /> })
const NewCandidateUnifiedModal = dynamic(() => import("@/components/modals/new-candidate-unified-modal").then(m => ({ default: m.NewCandidateUnifiedModal })), { ssr: false, loading: () => <LoadingModal /> })
const BatchApprovalModal = dynamic(() => import("@/components/batch-approval-modal").then(m => ({ default: m.BatchApprovalModal })), { ssr: false, loading: () => <LoadingModal /> })
const WSITextScreeningModal = dynamic(() => import("@/components/wsi").then(m => ({ default: m.WSITextScreeningModal })), { ssr: false, loading: () => <LoadingModal /> })
const WSIVoiceScreeningStatus = dynamic(() => import("@/components/wsi").then(m => ({ default: m.WSIVoiceScreeningStatus })), { ssr: false, loading: () => <LoadingModal /> })
const WSITriagemInviteModal = dynamic(() => import("@/components/wsi/wsi-triagem-invite-modal").then(m => ({ default: m.WSITriagemInviteModal })), { ssr: false, loading: () => <LoadingModal /> })
const RubricEvaluationModal = dynamic(() => import("@/components/rubric-evaluation-modal").then(m => ({ default: m.RubricEvaluationModal })), { ssr: false, loading: () => <LoadingModal /> })
const RevealCreditsModal = dynamic(() => import("@/components/reveal-credits-modal").then(m => ({ default: m.RevealCreditsModal })), { ssr: false, loading: () => <LoadingModal /> })
const CVPreview = dynamic(() => import("@/components/cv").then(m => ({ default: m.CVPreview })), { ssr: false, loading: () => <LoadingModal /> })

type CandidatesCoreModalsProps = Pick<CandidatesPageModalsProps,
  | 'showComparisonModal'
  | 'setShowComparisonModal'
  | 'selectedCandidatesForBatch'
  | 'sortedCandidates'
  | 'candidates'
  | 'handleNavigateToFullProfile'
  | 'handleScheduleInterview'
  | 'handleContactCandidate'
  | 'showCandidatePage'
  | 'selectedCandidate'
  | 'handleCloseCandidatePage'
  | 'showAddCandidateModal'
  | 'setShowAddCandidateModal'
  | 'preSelectedListForModal'
  | 'setPreSelectedListForModal'
  | 'handleAddCandidate'
  | 'setCandidateListsForModal'
  | 'bulkJobVacancies'
  | 'candidateListsForModal'
  | 'handleCandidatePageOpen'
  | 'showBatchApproval'
  | 'setShowBatchApproval'
  | 'convertCandidatesForBatch'
  | 'handleBatchApprovalComplete'
  | 'wsiCandidateForScreening'
  | 'setWsiCandidateForScreening'
  | 'showWSITextModal'
  | 'setShowWSITextModal'
  | 'showWSIVoiceModal'
  | 'setShowWSIVoiceModal'
  | 'handleWSIScreeningComplete'
  | 'showWSIInviteModal'
  | 'setShowWSIInviteModal'
  | 'wsiInviteCandidate'
  | 'setWsiInviteCandidate'
  | 'showRubricModal'
  | 'setShowRubricModal'
  | 'rubricCandidate'
  | 'setRubricCandidate'
  | 'rubricEvaluationData'
  | 'setRubricEvaluationData'
  | 'showRevealModal'
  | 'setShowRevealModal'
  | 'revealCandidate'
  | 'setRevealCandidate'
  | 'handleRevealContact'
  | 'revealType'
  | 'showCVPreviewModal'
  | 'setShowCVPreviewModal'
  | 'parsedCVData'
  | 'setParsedCVData'
  | 'handleCVConfirmed'
>

export function CandidatesCoreModals(props: CandidatesCoreModalsProps) {
  const t = useTranslations('candidates.modals')
  const {
    showComparisonModal,
    setShowComparisonModal,
    selectedCandidatesForBatch,
    sortedCandidates,
    candidates,
    handleNavigateToFullProfile,
    handleScheduleInterview,
    handleContactCandidate,
    showCandidatePage,
    selectedCandidate,
    handleCloseCandidatePage,
    showAddCandidateModal,
    setShowAddCandidateModal,
    preSelectedListForModal,
    setPreSelectedListForModal,
    handleAddCandidate,
    setCandidateListsForModal,
    bulkJobVacancies,
    candidateListsForModal,
    handleCandidatePageOpen,
    showBatchApproval,
    setShowBatchApproval,
    convertCandidatesForBatch,
    handleBatchApprovalComplete,
    wsiCandidateForScreening,
    setWsiCandidateForScreening,
    showWSITextModal,
    setShowWSITextModal,
    showWSIVoiceModal,
    setShowWSIVoiceModal,
    handleWSIScreeningComplete,
    showWSIInviteModal,
    setShowWSIInviteModal,
    wsiInviteCandidate,
    setWsiInviteCandidate,
    showRubricModal,
    setShowRubricModal,
    rubricCandidate,
    setRubricCandidate,
    rubricEvaluationData,
    setRubricEvaluationData,
    showRevealModal,
    setShowRevealModal,
    revealCandidate,
    setRevealCandidate,
    handleRevealContact,
    revealType,
    showCVPreviewModal,
    setShowCVPreviewModal,
    parsedCVData,
    setParsedCVData,
    handleCVConfirmed,
  } = props

  return (
    <>
      {showComparisonModal && selectedCandidatesForBatch.size >= 2 && (
        <CandidateComparison
          isOpen={showComparisonModal}
          onClose={() => setShowComparisonModal(false)}
          candidates={sortedCandidates
            .filter(c => selectedCandidatesForBatch.has(c.id))
            .map(c => ({
              id: c.id,
              name: c.name,
              role: c.position,
              email: c.email,
              phone: c.phone,
              location: c.location,
              avatar: c.avatar || '',
              score: c.score,
              status: c.status || '',
              matchPercentage: c.liaAnalysis?.score ?? c.score,
              riskLevel: 'low' as const,
              culturalFit: 85,
              technicalMatch: 90,
              experience: String(c.experience),
              seniority: c.seniority_level || 'Pleno',
              availability: 'Imediata',
              expectedSalary: c.salary?.expected ? String(c.salary.expected) : '',
              skills: c.skills,
              lastActivity: new Date().toISOString(),
              source: 'internal'
            }))}
          onSelectCandidate={(candidateId) => {
            const candidate = candidates.find(c => c.id === candidateId)
            if (candidate) handleNavigateToFullProfile(candidate)
          }}
          onScheduleInterview={(candidateId) => {
            const candidate = candidates.find(c => c.id === candidateId)
            if (candidate) handleScheduleInterview(candidate)
          }}
          onContactCandidate={(candidateId) => {
            const candidate = candidates.find(c => c.id === candidateId)
            if (candidate) handleContactCandidate(candidate)
          }}
        />
      )}

      {showCandidatePage && selectedCandidate && (
        <CandidatePage
          candidate={selectedCandidate as unknown as Record<string, unknown>}
          isOpen={showCandidatePage}
          onClose={handleCloseCandidatePage}
          onBackToKanban={() => {}}
        />
      )}

      <NewCandidateUnifiedModal
        key={`modal-${preSelectedListForModal?.id || 'default'}`}
        isOpen={showAddCandidateModal}
        onClose={() => {
          setShowAddCandidateModal(false)
          setPreSelectedListForModal(null)
        }}
        onCandidateAdded={(candidate) => {
          handleAddCandidate(candidate)
          if (preSelectedListForModal) {
            liaApi.getCandidateLists({ limit: 50 }).then(response => {
              if (response.items) {
                setCandidateListsForModal(response.items.map(list => ({
                  id: list.id,
                  name: list.name,
                  color: list.color
                })))
              }
            }).catch((err) => { console.error('[CandidatesCoreModals] candidate lists fetch failed', err) })
          }
        }}
        jobVacancies={bulkJobVacancies.map(j => ({ id: j.id, title: j.title, department: j.department, location: formatJobLocation(j.location) }))}
        candidateLists={candidateListsForModal}
        preSelectedListId={preSelectedListForModal?.id}
        preSelectedListName={preSelectedListForModal?.name}
        onGoToSearch={() => {
          setShowAddCandidateModal(false)
          setPreSelectedListForModal(null)
        }}
        onOpenFullProfile={(candidateId) => {
          const candidate = candidates.find(c => c.id === candidateId)
          if (candidate) {
            handleCandidatePageOpen(candidate)
          }
        }}
      />

      {showBatchApproval && (
        <BatchApprovalModal
          candidates={convertCandidatesForBatch(candidates.filter(c => selectedCandidatesForBatch.has(c.id))) as any}
          isOpen={showBatchApproval}
          onClose={() => setShowBatchApproval(false)}
          onApprovalComplete={handleBatchApprovalComplete}
        />
      )}

      {wsiCandidateForScreening && (
        <WSITextScreeningModal
          isOpen={showWSITextModal}
          onClose={() => {
            setShowWSITextModal(false)
            setWsiCandidateForScreening(null)
          }}
          candidate={{
            id: wsiCandidateForScreening.id,
            name: wsiCandidateForScreening.name,
            avatar: wsiCandidateForScreening.avatar,
            position: wsiCandidateForScreening.position
          }}
          jobVacancy={{
            id: 'default-vacancy',
            title: wsiCandidateForScreening.position || t('defaultJobTitle')
          }}
          onComplete={handleWSIScreeningComplete}
        />
      )}

      {wsiCandidateForScreening && (
        <WSIVoiceScreeningStatus
          isOpen={showWSIVoiceModal}
          onClose={() => {
            setShowWSIVoiceModal(false)
            setWsiCandidateForScreening(null)
          }}
          candidate={{
            id: wsiCandidateForScreening.id,
            name: wsiCandidateForScreening.name,
            phone: wsiCandidateForScreening.phone
          }}
          jobVacancy={{
            id: 'default-vacancy',
            title: wsiCandidateForScreening.position || t('defaultJobTitle')
          }}
          onComplete={handleWSIScreeningComplete}
          autoStart={true}
        />
      )}

      <WSITriagemInviteModal
        isOpen={showWSIInviteModal}
        onClose={() => {
          setShowWSIInviteModal(false)
          setWsiInviteCandidate(null)
        }}
        candidate={wsiInviteCandidate ? {
          id: wsiInviteCandidate.id,
          name: wsiInviteCandidate.name,
          role: wsiInviteCandidate.position,
          email: wsiInviteCandidate.email,
          phone: wsiInviteCandidate.phone,
          location: wsiInviteCandidate.location,
          avatar: wsiInviteCandidate.avatar
        } : null}
        jobTitle={wsiInviteCandidate?.position || t('job')}
        onSend={async (data) => {
          try {
            if (data.channel === 'email' && wsiInviteCandidate?.email) {
              const sendData = data as { subject?: string; message?: string; channel: string }
              await liaApi.sendEmail('wsi-triagem-invite', {
                recipient_email: wsiInviteCandidate.email,
                recipient_name: wsiInviteCandidate.name,
                candidate_id: wsiInviteCandidate.id,
                subject_override: sendData.subject || t('screeningInviteSubject', { position: wsiInviteCandidate.position || t('job') }),
                body_override: sendData.message,
                variables: {
                  candidate_name: wsiInviteCandidate.name,
                  job_title: wsiInviteCandidate.position || t('job')
                }
              })
            }
            setShowWSIInviteModal(false)
            setWsiInviteCandidate(null)
          } catch (error) {
            setShowWSIInviteModal(false)
            setWsiInviteCandidate(null)
          }
        }}
      />

      <RubricEvaluationModal
        isOpen={showRubricModal}
        onClose={() => {
          setShowRubricModal(false)
          setRubricCandidate(null)
          setRubricEvaluationData(null)
        }}
        evaluation={rubricEvaluationData}
        candidateId={rubricCandidate?.id || ''}
        candidateName={rubricCandidate?.name}
        jobId=""
        onApprove={async () => {
          toast.success(t('candidateApproved'), { description: t('approvedSuccess', { name: rubricCandidate?.name || '' }) })
          setShowRubricModal(false)
          setRubricCandidate(null)
          setRubricEvaluationData(null)
        }}
        onReject={async () => {
          toast.success(t('candidateRejected'), { description: t('rejectedDescription', { name: rubricCandidate?.name || '' }) })
          setShowRubricModal(false)
          setRubricCandidate(null)
          setRubricEvaluationData(null)
        }}
      />

      {revealCandidate && (
        <RevealCreditsModal
          isOpen={showRevealModal}
          onClose={() => {
            setShowRevealModal(false)
            setRevealCandidate(null)
          }}
          onConfirm={handleRevealContact as () => Promise<void>}
          revealType={revealType}
          candidateName={revealCandidate.name}
          creditsRequired={revealType === 'email' ? 2 : 14}
        />
      )}

      {parsedCVData && (
        <CVPreview
          isOpen={showCVPreviewModal}
          onClose={() => {
            setShowCVPreviewModal(false)
            setParsedCVData(null)
          }}
          parsedData={parsedCVData}
          onConfirm={handleCVConfirmed}
          jobVacancies={bulkJobVacancies.map(j => ({ id: j.id, title: j.title }))}
        />
      )}
    </>
  )
}
