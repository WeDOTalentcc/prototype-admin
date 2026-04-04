"use client"

import React from "react"
import dynamic from "next/dynamic"
import { LoadingModal } from "@/components/ui/loading"
import type { KanbanPageCoreState } from "./hooks/useKanbanPageCore"

const CandidatePage = dynamic(() => import("@/components/candidate-page").then(m => ({ default: m.CandidatePage })), { ssr: false, loading: () => <LoadingModal /> })
const TriagemDetailsModal = dynamic(() => import("@/components/triagem-details-modal").then(m => ({ default: m.TriagemDetailsModal })), { ssr: false, loading: () => <LoadingModal /> })
const TestLibraryModal = dynamic(() => import("@/components/pages/job-kanban/TestLibraryModal").then(m => ({ default: m.TestLibraryModal })), { ssr: false, loading: () => <LoadingModal /> })
const TestHistoryModal = dynamic(() => import("@/components/pages/job-kanban/TestHistoryModal").then(m => ({ default: m.TestHistoryModal })), { ssr: false, loading: () => <LoadingModal /> })
const LIAQuestionsPanel = dynamic(() => import("@/components/pages/job-kanban/LIAQuestionsPanel").then(m => ({ default: m.LIAQuestionsPanel })), { ssr: false, loading: () => <LoadingModal /> })
const TestPreviewModal = dynamic(() => import("@/components/pages/job-kanban/TestPreviewModal").then(m => ({ default: m.TestPreviewModal })), { ssr: false, loading: () => <LoadingModal /> })
const LIASuggestionsPanel = dynamic(() => import("@/components/pages/job-kanban/LIASuggestionsPanel").then(m => ({ default: m.LIASuggestionsPanel })), { ssr: false, loading: () => <LoadingModal /> })
const JobReportModal = dynamic(() => import("@/components/job-report-modal").then(m => ({ default: m.JobReportModal })), { ssr: false, loading: () => <LoadingModal /> })
const SendEmailModal = dynamic(() => import("@/components/email-templates/send-email-modal").then(m => ({ default: m.SendEmailModal })), { ssr: false, loading: () => <LoadingModal /> })
const UnifiedCommunicationModal = dynamic(() => import("@/components/modals/unified-communication-modal").then(m => ({ default: m.UnifiedCommunicationModal })), { ssr: false, loading: () => <LoadingModal /> })
const AddToListModal = dynamic(() => import("@/components/modals/add-to-list-modal").then(m => ({ default: m.AddToListModal })), { ssr: false, loading: () => <LoadingModal /> })
const WSITextScreeningModal = dynamic(() => import("@/components/wsi/wsi-text-screening-modal").then(m => ({ default: m.WSITextScreeningModal })), { ssr: false, loading: () => <LoadingModal /> })
const WSITriagemInviteModal = dynamic(() => import("@/components/wsi/wsi-triagem-invite-modal").then(m => ({ default: m.WSITriagemInviteModal })), { ssr: false, loading: () => <LoadingModal /> })
const AddCandidatesToVacancyModal = dynamic(() => import("@/components/modals/add-candidates-to-vacancy-modal").then(m => ({ default: m.AddCandidatesToVacancyModal })), { ssr: false, loading: () => <LoadingModal /> })
const RubricEvaluationModal = dynamic(() => import("@/components/rubric-evaluation-modal").then(m => ({ default: m.RubricEvaluationModal })), { ssr: false, loading: () => <LoadingModal /> })
const BigFiveModal = dynamic(() => import("@/components/big-five-modal").then(m => ({ default: m.BigFiveModal })), { ssr: false, loading: () => <LoadingModal /> })
const CandidateDecisionFlowModal = dynamic(() => import("@/components/candidate-decision-flow-modal").then(m => ({ default: m.CandidateDecisionFlowModal })), { ssr: false, loading: () => <LoadingModal /> })

export function KanbanPageModalsCore(state: KanbanPageCoreState) {
  const {
    showCandidatePage, previewCandidate, handleCloseCandidatePage,
    isTriagemOpen, triagemCandidate, handleCloseTriagem, handleTriagemApprove, handleTriagemReject,
    showTestLibrary, setShowTestLibrary, showTestHistory, setShowTestHistory, selectedTestForHistory, setSelectedTestForHistory,
    showTestPreview, setShowTestPreview,
    showLiaSuggestions, setShowLiaSuggestions, showTriagemSuggestions, setShowTriagemSuggestions, selectedTriagemQuestion,
    showReport, currentJob, handleCloseReport,
    emailCandidate, showEmailModal, setShowEmailModal, setEmailCandidate,
    unifiedModalOpen, handleUnifiedModalClose, unifiedModalCandidate, unifiedModalType, unifiedModalSituation,
    candidatesData, selectedCandidates, setSelectedCandidates, toast,
    showAddToListModal, setShowAddToListModal,
    showWSIModal, setShowWSIModal, wsiCandidate, setWsiCandidate, jobData,
    showWSIInviteModal, setShowWSIInviteModal, wsiInviteCandidate, setWsiInviteCandidate,
    perguntasEliminatorias, perguntasInformativas, perguntasTecnicasAvaliacao,
    showAddToVacancyModal, setShowAddToVacancyModal, candidateForVacancy, setCandidateForVacancy, user,
    showRubricModal, handleRubricModalClose, rubricEvaluationData, rubricCandidate,
    handleApproveCandidate, handleRejectCandidate,
    showBigFiveModal, setShowBigFiveModal, selectedCandidateForModal, setSelectedCandidateForModal,
    scoreModalCandidate, setScoreModalCandidate,
    showDecisionFlowModal, setShowDecisionFlowModal, decisionFlowCandidate, setDecisionFlowCandidate,
    decisionFlowType, handleDecisionFlowConfirm,
    setUnifiedModalCandidate, setUnifiedModalType, setUnifiedModalSituation, setUnifiedModalOpen,
  } = state
  return (
    <>
      {showCandidatePage && previewCandidate && (
        <CandidatePage
          candidate={previewCandidate}
          isOpen={showCandidatePage}
          onClose={handleCloseCandidatePage}
          onBackToKanban={handleCloseCandidatePage}
        />
      )}

      {isTriagemOpen && triagemCandidate && (
        <TriagemDetailsModal
          candidate={triagemCandidate as unknown as never}
          isOpen={isTriagemOpen}
          onClose={handleCloseTriagem}
          onApprove={handleTriagemApprove as unknown as never}
          onReject={handleTriagemReject as unknown as never}
        />
      )}

      <TestLibraryModal
        open={showTestLibrary}
        onClose={() => setShowTestLibrary(false)}
        onTestPreview={() => setShowTestPreview(true)}
        onTestHistoryOpen={(testName) => { (setSelectedTestForHistory as unknown as (v: string) => void)(testName); setShowTestHistory(true) }}
      />

      <TestHistoryModal
        open={showTestHistory}
        onClose={() => setShowTestHistory(false)}
        testName={selectedTestForHistory as any}
      />

      <LIAQuestionsPanel open={showLiaSuggestions} onClose={() => setShowLiaSuggestions(false)} />

      <TestPreviewModal open={showTestPreview} onClose={() => setShowTestPreview(false)} />

      <LIASuggestionsPanel open={showTriagemSuggestions} onClose={() => setShowTriagemSuggestions(false)} selectedTriagemQuestion={selectedTriagemQuestion} />

      {showReport && currentJob && (
        <JobReportModal
          job={currentJob}
          isOpen={showReport}
          onClose={handleCloseReport}
        />
      )}

      {emailCandidate && showEmailModal && (
        <SendEmailModal
          isOpen={showEmailModal}
          onClose={() => {
            setShowEmailModal(false)
            setEmailCandidate(null)
          }}
          candidate={{
            id: String(emailCandidate.id),
            name: (emailCandidate.name as string) || '',
            email: (emailCandidate.email as string | undefined) || `${((emailCandidate.name as string) || 'candidato')?.toLowerCase().replace(/\s+/g, '.')}@email.com`,
            current_title: (emailCandidate.role as string | undefined) || (emailCandidate.current_title as string | undefined) || '',
            current_company: (emailCandidate.currentCompany as string | undefined) || (emailCandidate.current_company as string | undefined) || '',
            location_city: (emailCandidate.location as string | undefined)?.split(',')[0]?.trim() || (emailCandidate.location_city as string | undefined) || '',
            location_state: (emailCandidate.location as string | undefined)?.split(',')[1]?.trim() || (emailCandidate.location_state as string | undefined) || '',
          } as any}
          onSuccess={() => {
            setShowEmailModal(false)
            setEmailCandidate(null)
          }}
        />
      )}

      <UnifiedCommunicationModal
        isOpen={unifiedModalOpen}
        onClose={handleUnifiedModalClose}
        candidate={unifiedModalCandidate ? {
          id: unifiedModalCandidate.id as string,
          name: unifiedModalCandidate.name as string,
          role: (unifiedModalCandidate.role as string | undefined) || (unifiedModalCandidate.current_title as string | undefined) || '',
          email: unifiedModalCandidate.email as string | undefined,
          phone: unifiedModalCandidate.phone as string | undefined,
          location: unifiedModalCandidate.location as string | undefined,
          avatar: unifiedModalCandidate.avatar as string | undefined,
          score: (unifiedModalCandidate.score || unifiedModalCandidate.fitScore) as number | undefined,
          matchPercentage: (unifiedModalCandidate.score || unifiedModalCandidate.fitScore) as number | undefined,
          skills: unifiedModalCandidate.skills as unknown[]
        } as any : null}
        type={unifiedModalType}
        situation={unifiedModalSituation}
        companyId="demo"
        selectedCandidates={
          !unifiedModalCandidate && selectedCandidates.size > 0
            ? Array.from(selectedCandidates).map(id => {
                const allCandidates = [
                  ...(candidatesData.sourcing || []),
                  ...(candidatesData.screening || []),
                  ...(candidatesData.interview_hr || []),
                  ...(candidatesData.interview_technical || []),
                  ...(candidatesData.interview_manager || []),
                  ...(candidatesData.offer || []),
                  ...(candidatesData.hired || []),
                  ...(candidatesData.rejected || []),
                  ...(candidatesData.offer_declined || [])
                ]
                const candidate = allCandidates.find(c => c.id === id)
                return {
                  id,
                  name: (candidate?.name as string | undefined) || 'Candidato',
                  email: candidate?.email as string | undefined,
                  phone: candidate?.phone as string | undefined,
                  avatar: candidate?.avatar as string | undefined
                }
              })
            : []
        }
      />

      <AddToListModal
        isOpen={showAddToListModal}
        onClose={() => setShowAddToListModal(false)}
        candidateIds={Array.from(selectedCandidates)}
        onSuccess={() => {
          setShowAddToListModal(false)
          setSelectedCandidates(new Set())
          toast.success("Sucesso", { description: "Candidatos adicionados à lista com sucesso!" })
        }}
      />

      {showWSIModal && wsiCandidate && (
        <WSITextScreeningModal
          isOpen={showWSIModal}
          onClose={() => {
            setShowWSIModal(false)
            setWsiCandidate(null)
          }}
          candidate={wsiCandidate as any}
          jobVacancyId={jobData.id?.toString()}
          jobTitle={jobData.title as any}
        />
      )}

      <WSITriagemInviteModal
        isOpen={showWSIInviteModal}
        onClose={() => {
          setShowWSIInviteModal(false)
          setWsiInviteCandidate(null)
        }}
        candidate={wsiInviteCandidate as any}
        jobTitle={currentJob.title as string | undefined}
        jobId={(currentJob.id as string | number | undefined)?.toString()}
        screeningQuestions={
          currentJob.screening_questions && (currentJob.screening_questions as unknown[]).length > 0
            ? (currentJob.screening_questions as Record<string, unknown>[]).map((q: Record<string, unknown>, idx: number) => ({
                id: (q.id as string | undefined) || `q-${idx}`,
                question: ((q.question || q.text) as string | undefined) || '',
                category: ((q.category || q.type) as string | undefined) || 'Triagem',
                bloomLevel: (q.bloom_level || q.bloomLevel) as string | undefined
              }))
            : [
                ...perguntasEliminatorias.map((q, idx) => ({
                  id: `elim-${idx}`,
                  question: q,
                  category: 'Eliminatória'
                })),
                ...perguntasInformativas.map((q, idx) => ({
                  id: `info-${idx}`,
                  question: q,
                  category: 'Informativa'
                })),
                ...perguntasTecnicasAvaliacao.map((q, idx) => ({
                  id: `tech-${idx}`,
                  question: q,
                  category: 'Técnica/Avaliação'
                }))
              ]
        }
      />

      <AddCandidatesToVacancyModal
        isOpen={showAddToVacancyModal}
        onClose={() => {
          setShowAddToVacancyModal(false)
          setCandidateForVacancy(null)
        }}
        candidateIds={candidateForVacancy ? [candidateForVacancy.id as string] : []}
        candidateNames={candidateForVacancy ? [(candidateForVacancy.name as string) || ''] : []}
        currentRecruiterEmail={user?.email}
        onSuccess={() => {
          toast.success("Candidato adicionado", { description: "Candidato adicionado à vaga com sucesso" })
        }}
      />

      <RubricEvaluationModal
        isOpen={showRubricModal}
        onClose={handleRubricModalClose}
        evaluation={rubricEvaluationData}
        candidateId={(rubricCandidate?.id as string) || ''}
        candidateName={rubricCandidate?.name as string | undefined}
        jobId={jobData?.id?.toString() || ''}
        onApprove={async (candidateId: string, jobId: string) => {
          if (rubricCandidate) {
            await handleApproveCandidate(rubricCandidate as unknown as Parameters<typeof handleApproveCandidate>[0])
            handleRubricModalClose()
          }
        }}
        onReject={async (candidateId: string, jobId: string) => {
          if (rubricCandidate) {
            await handleRejectCandidate(rubricCandidate as unknown as Parameters<typeof handleRejectCandidate>[0])
            handleRubricModalClose()
          }
        }}
      />

      <BigFiveModal
        isOpen={showBigFiveModal}
        onClose={() => {
          setShowBigFiveModal(false)
          setSelectedCandidateForModal(null)
          setScoreModalCandidate(null)
        }}
        candidate={(selectedCandidateForModal || scoreModalCandidate) as unknown as never}
      />

      {decisionFlowCandidate && (
        <CandidateDecisionFlowModal
          isOpen={showDecisionFlowModal}
          onClose={() => {
            setShowDecisionFlowModal(false)
            setDecisionFlowCandidate(null)
          }}
          candidate={{
            id: decisionFlowCandidate.id as string,
            name: decisionFlowCandidate.name as string,
            role: (decisionFlowCandidate.role as string | undefined) || (decisionFlowCandidate.cargo as string | undefined),
            currentCompany: (decisionFlowCandidate.currentCompany as string | undefined) || (decisionFlowCandidate.empresa as string | undefined),
            avatar: decisionFlowCandidate.avatar as string | undefined,
            email: decisionFlowCandidate.email as string | undefined,
            phone: (decisionFlowCandidate.phone as string | undefined) || (decisionFlowCandidate.telefone as string | undefined),
            hasWhatsApp: decisionFlowCandidate.hasWhatsApp !== false,
            stage: (decisionFlowCandidate.stage as string | undefined) || (decisionFlowCandidate.etapa as string | undefined),
          }}
          flowType={decisionFlowType}
          onConfirm={handleDecisionFlowConfirm}
          onOpenFeedbackModal={(candidate) => {
            setUnifiedModalCandidate(decisionFlowCandidate)
            setUnifiedModalType('feedback')
            setUnifiedModalSituation('feedback_construtivo')
            setUnifiedModalOpen(true)
            handleRejectCandidate(decisionFlowCandidate as unknown as Parameters<typeof handleRejectCandidate>[0])
          }}
        />
      )}
    </>
  )
}
