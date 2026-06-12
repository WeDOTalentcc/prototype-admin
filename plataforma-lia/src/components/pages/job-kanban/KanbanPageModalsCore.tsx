"use client"

import React, { useState } from "react"
import dynamic from "next/dynamic"
import { useTranslations } from "next-intl"
import type { KanbanPageCoreState } from "./hooks/useKanbanPageCore"
import { BulkResultReport } from "@/components/bulk"
import type { BulkItemResult } from "@/lib/bulk"
import type { CommunicationResult } from "@/components/modals/unified-communication-types"
import type { EligibilityResultItem } from "@/components/wsi/eligibility-results-section"

const CandidatePage = dynamic(() => import("@/components/candidate-page").then(m => ({ default: m.CandidatePage })), { ssr: false, loading: () => null })
const TriagemDetailsModal = dynamic(() => import("@/components/triagem-details-modal").then(m => ({ default: m.TriagemDetailsModal })), { ssr: false, loading: () => null })
const TestLibraryModal = dynamic(() => import("@/components/pages/job-kanban/TestLibraryModal").then(m => ({ default: m.TestLibraryModal })), { ssr: false, loading: () => null })
const TestHistoryModal = dynamic(() => import("@/components/pages/job-kanban/TestHistoryModal").then(m => ({ default: m.TestHistoryModal })), { ssr: false, loading: () => null })
const LIAQuestionsPanel = dynamic(() => import("@/components/pages/job-kanban/LIAQuestionsPanel").then(m => ({ default: m.LIAQuestionsPanel })), { ssr: false, loading: () => null })
const TestPreviewModal = dynamic(() => import("@/components/pages/job-kanban/TestPreviewModal").then(m => ({ default: m.TestPreviewModal })), { ssr: false, loading: () => null })
const LIASuggestionsPanel = dynamic(() => import("@/components/pages/job-kanban/LIASuggestionsPanel").then(m => ({ default: m.LIASuggestionsPanel })), { ssr: false, loading: () => null })
const JobReportModal = dynamic(() => import("@/components/job-report-modal").then(m => ({ default: m.JobReportModal })), { ssr: false, loading: () => null })
const SendEmailModal = dynamic(() => import("@/components/email-templates/send-email-modal").then(m => ({ default: m.SendEmailModal })), { ssr: false, loading: () => null })
const UnifiedCommunicationModal = dynamic(() => import("@/components/modals/unified-communication-modal").then(m => ({ default: m.UnifiedCommunicationModal })), { ssr: false, loading: () => null })
const AddToListModal = dynamic(() => import("@/components/modals/add-to-list-modal").then(m => ({ default: m.AddToListModal })), { ssr: false, loading: () => null })
const WSITextScreeningModal = dynamic(() => import("@/components/wsi/wsi-text-screening-modal").then(m => ({ default: m.WSITextScreeningModal })), { ssr: false, loading: () => null })
const WSITriagemInviteModal = dynamic(() => import("@/components/wsi/wsi-triagem-invite-modal").then(m => ({ default: m.WSITriagemInviteModal })), { ssr: false, loading: () => null })
const AddCandidatesToVacancyModal = dynamic(() => import("@/components/modals/add-candidates-to-vacancy-modal").then(m => ({ default: m.AddCandidatesToVacancyModal })), { ssr: false, loading: () => null })
const RubricEvaluationModal = dynamic(() => import("@/components/rubric-evaluation-modal").then(m => ({ default: m.RubricEvaluationModal })), { ssr: false, loading: () => null })
const BigFiveModal = dynamic(() => import("@/components/big-five-modal").then(m => ({ default: m.BigFiveModal })), { ssr: false, loading: () => null })
const CandidateDecisionFlowModal = dynamic(() => import("@/components/candidate-decision-flow-modal").then(m => ({ default: m.CandidateDecisionFlowModal })), { ssr: false, loading: () => null })

function extractEligibilityResults(
  candidate: Record<string, unknown>,
  job: Record<string, unknown>,
): EligibilityResultItem[] | undefined {
  const raw = candidate?.eligibility_results
  if (Array.isArray(raw) && raw.length > 0) {
    return (raw as Record<string, unknown>[]).map((r, i) => ({
      id: String(r.id ?? r.question_id ?? i),
      question: String(r.question ?? r.question_text ?? ""),
      answer: r.answer != null ? String(r.answer) : undefined,
      passed: Boolean(r.passed ?? r.met ?? true),
      is_eliminatory: r.is_eliminatory !== false,
      reconsideration: r.reconsideration != null ? String(r.reconsideration) : undefined,
    }))
  }

  const jobQuestions = job?.eligibility_questions
  if (Array.isArray(jobQuestions) && jobQuestions.length > 0) {
    const candidateAnswers = (candidate?.eligibility_answers ?? candidate?.answers) as
      | Record<string, unknown>
      | undefined
    return (jobQuestions as Record<string, unknown>[]).map((q, i) => {
      const qId = String(q.id ?? i)
      const answer = candidateAnswers?.[qId] != null ? String(candidateAnswers[qId]) : undefined
      return {
        id: qId,
        question: String(q.question ?? q.question_text ?? ""),
        answer,
        passed: answer !== undefined
          ? Boolean(candidateAnswers?.[`${qId}_passed`] ?? true)
          : true,
        is_eliminatory: q.is_eliminatory !== false,
      }
    })
  }

  return undefined
}

export function KanbanPageModalsCore(state: KanbanPageCoreState) {
  const t = useTranslations('kanban')
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
    handleUniversalTransitionConfirm,
  } = state
  const [bulkReport, setBulkReport] = useState<{ isOpen: boolean; results: BulkItemResult[]; actionLabel: string }>({ isOpen: false, results: [], actionLabel: "" })

  const COMM_TYPE_LABELS: Record<string, string> = { email: "Email", whatsapp: "WhatsApp", triagem: "Triagem", agendamento: "Agendamento", feedback: "Feedback" }

  const handleSend = (data: CommunicationResult) => {
    const withBulk = data as CommunicationResult & { bulkResults?: BulkItemResult[] }
    if (Array.isArray(withBulk.bulkResults) && withBulk.bulkResults.length > 0) {
      setBulkReport({ isOpen: true, results: withBulk.bulkResults, actionLabel: COMM_TYPE_LABELS[data.type] ?? "Envio" })
    }
    // FE-2c: fluxo unico de reprovacao — move o candidato AO ENVIAR o feedback
    // (just_move = move + reviewer/audit, sem re-disparar). Se o recrutador fecha
    // sem enviar, nada move.
    const aiCtx = unifiedModalCandidate?._aiFeedbackContext as
      | { vacancyCandidateId: string; toStage: string; subStatus?: string | null; moveOnSend?: boolean }
      | undefined
    if (aiCtx?.moveOnSend && aiCtx.vacancyCandidateId) {
      void handleUniversalTransitionConfirm({
        candidateIds: [aiCtx.vacancyCandidateId],
        toStage: aiCtx.toStage,
        subStatus: aiCtx.subStatus ?? undefined,
        action: 'just_move',
        actionBehavior: 'conclusion_rejected',
      } as Parameters<typeof handleUniversalTransitionConfirm>[0])
    }
  }

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
          jobId={((currentJob?.backendId || currentJob?.id) as string | number | undefined)?.toString()}
          jobTitle={currentJob?.title as string | undefined}
          companyId={
            (currentJob?.company_id as string | undefined) ??
            (currentJob?.companyId as string | undefined)
          }
          eligibilityResults={extractEligibilityResults(
            triagemCandidate as Record<string, unknown>,
            currentJob as Record<string, unknown>,
          )}
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
        testName={selectedTestForHistory}
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
            email: (emailCandidate.email as string | undefined) || `${((emailCandidate.name as string) || t('candidateFallback'))?.toLowerCase().replace(/\s+/g, '.')}@email.com`,
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
                  name: (candidate?.name as string | undefined) || t('candidateFallback'),
                  email: candidate?.email as string | undefined,
                  phone: candidate?.phone as string | undefined,
                  avatar: candidate?.avatar as string | undefined
                }
              })
            : []
        }
        onSend={handleSend}
        aiFeedbackContext={(unifiedModalCandidate?._aiFeedbackContext as { vacancyCandidateId: string; toStage: string; subStatus?: string | null } | undefined) ?? null}
      />

      <AddToListModal
        isOpen={showAddToListModal}
        onClose={() => setShowAddToListModal(false)}
        candidateIds={Array.from(selectedCandidates)}
        onSuccess={() => {
          setShowAddToListModal(false)
          setSelectedCandidates(new Set())
          toast.success(t('candidatesAddedToListSuccess'), { description: t('candidatesAddedToListDesc') })
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
          jobVacancyId={((jobData.backendId || jobData.id) as string | number | undefined)?.toString()}
          jobTitle={jobData.title as any}
          eligibilityResults={extractEligibilityResults(wsiCandidate as Record<string, unknown>, jobData)}
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
        jobId={((currentJob.backendId || currentJob.id) as string | number | undefined)?.toString()}
        companyId={
          (currentJob?.company_id as string | undefined) ??
          (currentJob?.companyId as string | undefined)
        }
        screeningQuestions={
          currentJob.screening_questions && (currentJob.screening_questions as unknown[]).length > 0
            ? (currentJob.screening_questions as Record<string, unknown>[]).map((q: Record<string, unknown>, idx: number) => ({
                id: (q.id as string | undefined) || `q-${idx}`,
                question: ((q.question || q.text) as string | undefined) || '',
                category: ((q.category || q.type) as string | undefined) || t('categoryTriagem'),
                bloomLevel: (q.bloom_level || q.bloomLevel) as string | undefined
              }))
            : [
                ...perguntasEliminatorias.map((q, idx) => ({
                  id: `elim-${idx}`,
                  question: q,
                  category: t('categoryEliminatoria')
                })),
                ...perguntasInformativas.map((q, idx) => ({
                  id: `info-${idx}`,
                  question: q,
                  category: t('categoryInformativa')
                })),
                ...perguntasTecnicasAvaliacao.map((q, idx) => ({
                  id: `tech-${idx}`,
                  question: q,
                  category: t('categoryTecnicaAvaliacao')
                }))
              ]
        }
        screeningChannels={(() => {
          const sc = currentJob.screening_config as Record<string, unknown> | undefined
          if (!sc || typeof sc !== 'object') return undefined
          const channelsCfg = sc.screening_channels as import('@/hooks/recruitment/useScreeningConfig').ScreeningChannelConfig | undefined
          if (!channelsCfg) return undefined
          return {
            ...channelsCfg,
            channels: sc.channels as import('@/hooks/recruitment/useScreeningConfig').ScreeningConfig['channels'],
            channels_master_enabled: sc.channels_master_enabled as boolean | undefined,
          }
        })()}
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
          toast.success(t('candidateAddedTitle'), { description: t('candidateAddedToJobDesc') })
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

      <BulkResultReport
        isOpen={bulkReport.isOpen}
        onClose={() => setBulkReport(prev => ({ ...prev, isOpen: false }))}
        results={bulkReport.results}
        actionLabel={bulkReport.actionLabel}
      />
    </>
  )
}
