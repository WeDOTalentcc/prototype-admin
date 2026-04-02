"use client"

import React from "react"
import dynamic from "next/dynamic"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
const TriagemDetailsModal = dynamic(() => import("@/components/triagem-details-modal").then(m => ({ default: m.TriagemDetailsModal })), {
  ssr: false,
  loading: () => null,
})
const JobReportModal = dynamic(() => import("@/components/job-report-modal").then(m => ({ default: m.JobReportModal })), {
  ssr: false,
  loading: () => null,
})
import { SendEmailModal } from "@/components/email-templates/send-email-modal"
import { UnifiedCommunicationModal } from "@/components/modals/unified-communication-modal"
import { AddToListModal } from "@/components/modals/add-to-list-modal"
import { WSITextScreeningModal } from "@/components/wsi/wsi-text-screening-modal"
import { WSITriagemInviteModal } from "@/components/wsi/wsi-triagem-invite-modal"
import { AddCandidatesToVacancyModal } from "@/components/modals/add-candidates-to-vacancy-modal"
import { RubricEvaluationModal } from "@/components/rubric-evaluation-modal"
const BigFiveModal = dynamic(() => import("@/components/big-five-modal").then(m => ({ default: m.BigFiveModal })), { ssr: false })
import { GeneralScoreModal } from "@/components/modals/general-score-modal"
import { TechnicalTestModal } from "@/components/modals/technical-test-modal"
import { EnglishTestModal } from "@/components/modals/english-test-modal"
import { CandidateDecisionFlowModal } from "@/components/candidate-decision-flow-modal"
import { TestPreviewModal } from "@/components/pages/job-kanban/TestPreviewModal"
import { LIASuggestionsPanel } from "@/components/pages/job-kanban/LIASuggestionsPanel"
import { TestLibraryModal } from "@/components/pages/job-kanban/TestLibraryModal"
import { TestHistoryModal } from "@/components/pages/job-kanban/TestHistoryModal"
import { LIAQuestionsPanel } from "@/components/pages/job-kanban/LIAQuestionsPanel"
import { CandidateCompareModal } from "@/components/modals/candidate-compare-modal"
import { UniversalTransitionModal } from "@/components/kanban"
import { DataRequestModal } from "@/components/modals/data-request-modal"
import { CloseVacancyModal } from "@/components/modals/close-vacancy-modal"
import { JobStatusModal } from "@/components/modals/job-status-modal"
import { ShareSearchModal } from "@/components/modals/share-search-modal"
import { BulkActionModal } from "@/components/modals/bulk-action-modal"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  ArrowRight, X, Brain, CheckCircle, XCircle, Copy, BrainCircuit, FileText, Languages
} from "lucide-react"
import { formatScorePercent } from "@/lib/design-tokens"
import { calculateNotaLiaGeral, getLiaAlerts } from "@/components/pages/job-kanban/utils/kanbanHelpers"
import type { KanbanPageCoreState } from "./hooks/useKanbanPageCore"
import { toast } from "sonner"

const CandidatePage = dynamic(() => import("@/components/candidate-page").then(m => ({ default: m.CandidatePage })), { ssr: false })

export function KanbanPageModals(state: KanbanPageCoreState) {
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
    statusModalOpen, pendingMove, cancelMove, getStageDisplayName,
    getSuggestedSubStatus, selectedSubStatus, setSelectedSubStatus, getAvailableSubStatuses, getSubStatusColor, confirmMove,
    activeModal, setActiveModal,
    showGeneralScoreModal, setShowGeneralScoreModal,
    showTechnicalTestModal, setShowTechnicalTestModal,
    showEnglishTestModal, setShowEnglishTestModal,
    showCompareModal, setShowCompareModal, compareCandidates, setCompareCandidates,
    _jobIdForSL, _companyIdForSL,
    selectedForCompare, setSelectedForCompare, allTableCandidates, allCandidateIds,
    universalModalState, closeTransition, setTransitionInitialPrompt, setTransitionAllowStageSelection, setTransitionInterviewAlert,
    handleUniversalTransitionConfirm, handleOpenSpecializedModal, dynamicStages,
    transitionInitialPrompt, transitionAllowStageSelection, transitionInterviewAlert,
    showDataRequestModal, setShowDataRequestModal, dataRequestModalCandidate, setDataRequestModalCandidate, handleDataRequestSubmit,
    showBulkActionModal, setShowBulkActionModal, bulkActionType, handleBulkActionExecute,
    showJobStatusModal, setShowJobStatusModal, jobStatusModalMode, jobEditForm, setJobEditForm,
    showCloseVacancyModal, setShowCloseVacancyModal,
    showPublishSuccess, setShowPublishSuccess, publicLink,
    showShareGestorModal, setShowShareGestorModal,
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

      {/* Modal de Detalhes da Triagem */}
      {isTriagemOpen && triagemCandidate && (
        <TriagemDetailsModal
          candidate={triagemCandidate as unknown as never}
          isOpen={isTriagemOpen}
          onClose={handleCloseTriagem}
          onApprove={handleTriagemApprove as unknown as never}
          onReject={handleTriagemReject as unknown as never}
        />
      )}

      {/* Modal da Biblioteca de Testes */}
      <TestLibraryModal
        open={showTestLibrary}
        onClose={() => setShowTestLibrary(false)}
        onTestPreview={() => setShowTestPreview(true)}
        onTestHistoryOpen={(testName) => { (setSelectedTestForHistory as unknown as (v: string) => void)(testName); setShowTestHistory(true) }}
      />

      {/* Modal de Histórico do Teste */}
      <TestHistoryModal
        open={showTestHistory}
        onClose={() => setShowTestHistory(false)}
        testName={selectedTestForHistory as unknown as Parameters<typeof TestHistoryModal>[0]["testName"]}
      />

      {/* Painel Lateral de Sugestões da LIA */}
      <LIAQuestionsPanel open={showLiaSuggestions} onClose={() => setShowLiaSuggestions(false)} />

      {/* Modal de Preview do Teste para Candidato */}
      <TestPreviewModal open={showTestPreview} onClose={() => setShowTestPreview(false)} />

      {/* Painel Lateral de Sugestões da LIA para Triagem */}
      <LIASuggestionsPanel open={showTriagemSuggestions} onClose={() => setShowTriagemSuggestions(false)} selectedTriagemQuestion={selectedTriagemQuestion} />

      {/* Modal de Relatório */}
      {showReport && currentJob && (
        <JobReportModal
          job={currentJob}
          isOpen={showReport}
          onClose={handleCloseReport}
        />
      )}

      {/* Modal de Email */}
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
          } as unknown as Parameters<typeof SendEmailModal>[0]["candidate"]}
          onSuccess={() => {
            setShowEmailModal(false)
            setEmailCandidate(null)
          }}
        />
      )}

      {/* Unified Communication Modal */}
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
        } as unknown as Parameters<typeof UnifiedCommunicationModal>[0]["candidate"] : null}
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

      {/* Modal Adicionar à Lista */}
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

      {/* WSI Text Screening Modal */}
      {showWSIModal && wsiCandidate && (
        <WSITextScreeningModal
          isOpen={showWSIModal}
          onClose={() => {
            setShowWSIModal(false)
            setWsiCandidate(null)
          }}
          candidate={wsiCandidate as unknown as Parameters<typeof WSITextScreeningModal>[0]["candidate"]}
          jobVacancyId={jobData.id?.toString()}
          jobTitle={jobData.title}
        />
      )}

      {/* WSI Triagem Invite Modal */}
      <WSITriagemInviteModal
        isOpen={showWSIInviteModal}
        onClose={() => {
          setShowWSIInviteModal(false)
          setWsiInviteCandidate(null)
        }}
        candidate={wsiInviteCandidate as unknown as Parameters<typeof WSITriagemInviteModal>[0]["candidate"]}
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

      {/* Add to Vacancy Modal */}
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

      {/* Rubric Evaluation Modal */}
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

      {/* Big Five Modal */}
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

      {/* Modal de Seleção de Status (Movimentação no Kanban) */}
      {statusModalOpen && pendingMove && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div 
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={cancelMove}
          />
          <div 
            className="relative bg-lia-bg-primary rounded-md w-full max-w-md mx-4 overflow-hidden border border-lia-border-subtle"
           
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-lia-border-subtle bg-lia-bg-secondary">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-lia-bg-tertiary flex items-center justify-center">
                  <ArrowRight className="w-5 h-5 text-lia-text-secondary" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-lia-text-primary">
                    Confirmar Movimentação
                  </h2>
                  <p className="text-sm text-lia-text-secondary">
                    Selecione o status detalhado
                  </p>
                </div>
              </div>
              <button
                onClick={cancelMove}
                className="p-2 hover:bg-lia-interactive-hover rounded-md transition-colors motion-reduce:transition-none"
              >
                <X className="w-5 h-5 text-lia-text-tertiary" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 space-y-5">
              {/* Candidato Info */}
              <div className="flex items-center gap-3 p-3 bg-lia-bg-secondary rounded-md">
                <Avatar className="w-10 h-10">
                  <AvatarImage src={pendingMove.candidate.avatar as string | undefined} alt={pendingMove.candidate.name as string} />
                  <AvatarFallback>{(pendingMove.candidate.name as string | undefined)?.split(' ').map((n: string) => n[0]).join('') || 'C'}</AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-medium text-lia-text-primary">{pendingMove.candidate.name as string}</p>
                  <p className="text-sm text-lia-text-secondary">{((pendingMove.candidate.role as string | undefined) || (pendingMove.candidate.cargo as string | undefined) || 'Candidato')}</p>
                </div>
              </div>

              {/* Transição de Etapa */}
              <div className="flex items-center gap-3 justify-center">
                <div className="px-3 py-2 bg-lia-bg-tertiary rounded-md">
                  <span className="text-sm font-medium text-lia-text-secondary">
                    {getStageDisplayName(pendingMove.fromColumn)}
                  </span>
                </div>
                <ArrowRight className="w-5 h-5 text-lia-text-disabled" />
                <div className="px-3 py-2 bg-lia-btn-primary-bg rounded-md">
                  <span className="text-sm font-medium text-white">
                    {getStageDisplayName(pendingMove.toColumn)}
                  </span>
                </div>
              </div>

              {/* Status Sugerido pela LIA */}
              {getSuggestedSubStatus(pendingMove.toColumn) && (
                <div className="space-y-2">
                  <label className="text-sm font-medium text-lia-text-secondary flex items-center gap-2">
                    <Brain className="w-4 h-4 text-wedo-cyan" />
                    Status Sugerido pela LIA
                  </label>
                  <div 
                    className={`p-3 rounded-md border-2 cursor-pointer transition-colors motion-reduce:transition-none ${
                      selectedSubStatus === getSuggestedSubStatus(pendingMove.toColumn)
                        ? 'bg-lia-bg-tertiary border-lia-border-medium'
 : 'bg-lia-bg-secondary border-lia-border-subtle hover:border-lia-border-default'
                    }`}
                    onClick={() => setSelectedSubStatus(getSuggestedSubStatus(pendingMove.toColumn))}
                  >
                    <Badge 
                      className="text-sm px-3 py-1 font-medium border-0 text-lia-text-primary bg-lia-btn-primary-bg"
                    >
                      {getAvailableSubStatuses(pendingMove.toColumn).find(s => s.name === getSuggestedSubStatus(pendingMove.toColumn))?.displayName || getSuggestedSubStatus(pendingMove.toColumn)}
                    </Badge>
                  </div>
                </div>
              )}

              {/* Seleção Manual de Status */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-lia-text-secondary">
                  Selecionar outro status
                </label>
                <Select 
                  value={selectedSubStatus} 
                  onValueChange={setSelectedSubStatus}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Selecione um status" />
                  </SelectTrigger>
                  <SelectContent className="max-h-60">
                    {getAvailableSubStatuses(pendingMove.toColumn).map((status) => {
                      const colors = getSubStatusColor(status)
                      return (
                        <SelectItem 
                          key={status.name} 
                          value={status.name}
                          className="cursor-pointer"
                        >
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-sm font-medium ${colors.bg} ${colors.text}`}>
                            {status.displayName}
                          </span>
                        </SelectItem>
                      )
                    })}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-lia-border-subtle bg-lia-bg-secondary">
              <Button
                variant="outline"
                onClick={cancelMove}
                className="px-4"
              >
                Cancelar
              </Button>
              <Button
                onClick={confirmMove}
                disabled={!selectedSubStatus}
                className="px-4 text-white bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover"
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                Confirmar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Avaliação (Nota Geral, Triagem, Testes) */}
      {activeModal && selectedCandidateForModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div 
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => {
              setActiveModal(null)
              setSelectedCandidateForModal(null)
            }}
          />
          <div 
            className="relative bg-lia-bg-primary rounded-md w-full max-w-2xl mx-4 max-h-[85vh] overflow-hidden border border-lia-border-subtle"
           
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-lia-border-subtle bg-lia-bg-secondary">
              <div className="flex items-center gap-3">
                {activeModal === 'notaGeral' && <BrainCircuit className="w-5 h-5 text-lia-text-primary" />}
                {activeModal === 'triagem' && <BrainCircuit className="w-5 h-5 text-wedo-cyan" />}
                {activeModal === 'testeTecnico' && <FileText className="w-5 h-5 text-lia-text-secondary" />}
                {activeModal === 'testeIngles' && <Languages className="w-5 h-5 text-lia-text-secondary" />}
                <div>
                  <h2 className="text-lg font-semibold text-lia-text-primary">
                    {activeModal === 'notaGeral' && 'Nota Geral'}
                    {activeModal === 'triagem' && 'Nota Triagem'}
                    {activeModal === 'testeTecnico' && 'Teste Técnico'}
                    {activeModal === 'testeIngles' && 'Teste Inglês'}
                  </h2>
                  <p className="text-sm text-lia-text-secondary">{selectedCandidateForModal.name as string}</p>
                </div>
              </div>
              <button
                onClick={() => {
                  setActiveModal(null)
                  setSelectedCandidateForModal(null)
                }}
                className="p-2 hover:bg-lia-interactive-hover rounded-md transition-colors motion-reduce:transition-none"
              >
                <X className="w-5 h-5 text-lia-text-tertiary" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(85vh-140px)]">
              {/* Nota Geral */}
              {activeModal === 'notaGeral' && (
                <div className="space-y-6">
                  <div className="text-center py-8">
                    <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-lia-bg-tertiary mb-4">
                      <span className="text-4xl font-bold text-lia-text-primary">
                        {calculateNotaLiaGeral(selectedCandidateForModal as unknown as Parameters<typeof calculateNotaLiaGeral>[0])}
                      </span>
                    </div>
                    <p className="text-sm text-lia-text-secondary">Pontuação Geral do Candidato</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-lia-bg-secondary rounded-md">
                      <p className="text-xs text-lia-text-tertiary mb-1">Nota Triagem</p>
                      <p className="text-lg font-semibold text-lia-text-primary">
                        {formatScorePercent((selectedCandidateForModal.liaScore ?? selectedCandidateForModal.score) as number | null | undefined, 0)}
                      </p>
                    </div>
                    <div className="p-4 bg-lia-bg-secondary rounded-md">
                      <p className="text-xs text-lia-text-tertiary mb-1">Nota CV</p>
                      <p className="text-lg font-semibold text-lia-text-primary">
                        {formatScorePercent((selectedCandidateForModal.skillsMatch as number | undefined) || (selectedCandidateForModal.fitScore as number | undefined) || 0, 0)}
                      </p>
                    </div>
                    <div className="p-4 bg-lia-bg-secondary rounded-md">
                      <p className="text-xs text-lia-text-tertiary mb-1">Teste Técnico</p>
                      <p className="text-lg font-semibold text-lia-text-primary">
                        {(selectedCandidateForModal.technicalTestScore as number | null | undefined) !== null && selectedCandidateForModal.technicalTestScore !== undefined
                          ? formatScorePercent(selectedCandidateForModal.technicalTestScore as number, 0)
                          : '—'}
                      </p>
                    </div>
                    <div className="p-4 bg-lia-bg-secondary rounded-md">
                      <p className="text-xs text-lia-text-tertiary mb-1">Teste Inglês</p>
                      <p className="text-lg font-semibold text-lia-text-primary">
                        {(selectedCandidateForModal.englishTestScore as number | null | undefined) !== null && selectedCandidateForModal.englishTestScore !== undefined
                          ? formatScorePercent(selectedCandidateForModal.englishTestScore as number, 0)
                          : '—'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Triagem */}
              {activeModal === 'triagem' && (
                <div className="space-y-6">
                  <div className="text-center py-6">
                    <div 
                      className="inline-flex items-center justify-center w-20 h-20 rounded-full mb-4 bg-lia-bg-tertiary"
                    >
                      <span className="text-3xl font-bold text-lia-text-primary">
                        {formatScorePercent((selectedCandidateForModal.liaScore ?? selectedCandidateForModal.score) as number | null | undefined, 0)}
                      </span>
                    </div>
                    <p className="text-sm text-lia-text-secondary">Score de Triagem LIA</p>
                  </div>
                  <div className="p-4 bg-lia-bg-secondary rounded-md">
                    <h4 className="text-sm font-semibold text-lia-text-primary mb-3">Análise da LIA</h4>
                    <p className="text-sm text-lia-text-secondary leading-relaxed">
                      Candidato avaliado automaticamente pela LIA com base em critérios de experiência, 
                      competências e aderência ao perfil da vaga. A triagem considera fatores como 
                      histórico profissional, formação acadêmica e habilidades técnicas declaradas.
                    </p>
                  </div>
                </div>
              )}

              {/* Teste Técnico */}
              {activeModal === 'testeTecnico' && (
                <div className="space-y-6">
                  <div className="text-center py-6">
                    <div 
                      className="inline-flex items-center justify-center w-20 h-20 rounded-full mb-4"
                      style={{backgroundColor: (selectedCandidateForModal.technicalTestScore as number) >= 80 ? 'var(--status-success)' :
                                         (selectedCandidateForModal.technicalTestScore as number) >= 60 ? 'var(--status-warning)' :
                                         (selectedCandidateForModal.technicalTestScore as number) >= 40 ? 'var(--lia-border-medium)' :
                                         'var(--lia-border-medium)'}}
                    >
                      <span className="text-3xl font-bold text-lia-text-primary">
                        {formatScorePercent(selectedCandidateForModal.technicalTestScore as number | null | undefined, 0)}
                      </span>
                    </div>
                    <p className="text-sm text-lia-text-secondary">Resultado do Teste Técnico</p>
                  </div>
                  <div className="p-4 bg-lia-bg-secondary rounded-md">
                    <h4 className="text-sm font-semibold text-lia-text-primary mb-3">Detalhes do Teste</h4>
                    <p className="text-sm text-lia-text-secondary leading-relaxed">
                      Avaliação técnica realizada através de teste prático com foco nas competências 
                      técnicas requeridas para a posição. Inclui análise de código, resolução de 
                      problemas e conhecimento de ferramentas específicas.
                    </p>
                  </div>
                </div>
              )}

              {/* Teste Inglês */}
              {activeModal === 'testeIngles' && (
                <div className="space-y-6">
                  <div className="text-center py-6">
                    <div 
                      className="inline-flex items-center justify-center w-20 h-20 rounded-full mb-4"
                      style={{backgroundColor: (selectedCandidateForModal.englishTestScore as number) >= 80 ? 'var(--status-success)' :
                                         (selectedCandidateForModal.englishTestScore as number) >= 60 ? 'var(--lia-border-default)' :
                                         (selectedCandidateForModal.englishTestScore as number) >= 40 ? 'var(--lia-border-medium)' :
                                         'var(--lia-border-medium)'}}
                    >
                      <span className="text-3xl font-bold text-lia-text-primary">
                        {formatScorePercent(selectedCandidateForModal.englishTestScore as number | null | undefined, 0)}
                      </span>
                    </div>
                    <p className="text-sm text-lia-text-secondary">Resultado do Teste de Inglês</p>
                  </div>
                  <div className="p-4 bg-lia-bg-secondary rounded-md">
                    <h4 className="text-sm font-semibold text-lia-text-primary mb-3">Nível de Proficiência</h4>
                    <p className="text-sm text-lia-text-secondary leading-relaxed">
                      Avaliação de proficiência em inglês cobrindo compreensão escrita, 
                      expressão oral e vocabulário técnico relevante para a posição.
                    </p>
                  </div>
                </div>
              )}

            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-lia-border-subtle bg-lia-bg-secondary">
              <button
                onClick={() => {
                  setActiveModal(null)
                  setSelectedCandidateForModal(null)
                }}
                className="px-4 py-2 text-sm font-medium text-lia-text-primary bg-lia-bg-secondary border border-lia-border-default rounded-md hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modais de Scores */}
      <GeneralScoreModal
        isOpen={showGeneralScoreModal}
        onClose={() => setShowGeneralScoreModal(false)}
        candidate={scoreModalCandidate as unknown as Parameters<typeof GeneralScoreModal>[0]["candidate"]}
      />
      <TechnicalTestModal
        isOpen={showTechnicalTestModal}
        onClose={() => setShowTechnicalTestModal(false)}
        candidate={scoreModalCandidate as unknown as Parameters<typeof TechnicalTestModal>[0]["candidate"]}
      />
      <EnglishTestModal
        isOpen={showEnglishTestModal}
        onClose={() => setShowEnglishTestModal(false)}
        candidate={scoreModalCandidate as unknown as Parameters<typeof EnglishTestModal>[0]["candidate"]}
      />

      {/* D9 — Modal de Análise Comparativa */}
      <CandidateCompareModal
        open={showCompareModal}
        onClose={() => setShowCompareModal(false)}
        candidates={compareCandidates}
        jobId={_jobIdForSL}
        companyId={_companyIdForSL}
      />

      {/* D9-G1 — Botão flutuante de comparação (aparece quando 2+ candidatos selecionados) */}
      {selectedForCompare.size >= 2 && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2">
          <button
            className="flex items-center gap-2 bg-lia-btn-primary-bg text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none shadow-lia-md"
            onClick={() => {
              const selectedIds = Array.from(selectedForCompare)
              const resolvedCandidates = allTableCandidates
                .filter(c => selectedIds.includes(c.id as string))
.map(c => ({ id: c.id as string, name: (c.name as string) || '' }))
              setCompareCandidates(resolvedCandidates as unknown as Parameters<typeof setCompareCandidates>[0])
              setShowCompareModal(true)
              setSelectedForCompare(new Set())
            }}
          >
            <span>Comparar ({selectedForCompare.size})</span>
          </button>
          <button
            className="bg-lia-bg-primary border border-lia-border-subtle text-lia-text-secondary px-3 py-2 rounded-md text-sm hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none shadow-lia-md"
            onClick={() => setSelectedForCompare(new Set())}
            aria-label="Limpar seleção de comparação"
          >
            ✕
          </button>
        </div>
      )}

      {/* UniversalTransitionModal - Modal universal para transições de etapa */}
      <UniversalTransitionModal
        isOpen={universalModalState.isOpen}
        onClose={() => { closeTransition(); setTransitionInitialPrompt(undefined); setTransitionAllowStageSelection(false); setTransitionInterviewAlert(null); }}
        candidates={universalModalState.candidates}
        fromStage={universalModalState.fromStage}
        toStage={universalModalState.toStage}
        toStageDisplayName={universalModalState.toStageDisplayName}
        actionBehavior={universalModalState.actionBehavior}
        subStatusOptions={universalModalState.subStatusOptions}
        onConfirm={handleUniversalTransitionConfirm}
        onOpenSpecializedModal={handleOpenSpecializedModal}
        companyId={user?.company as string | undefined}
        jobTitle={currentJob?.title as string | undefined}
        initialPrompt={transitionInitialPrompt}
        availableStages={dynamicStages.map(s => ({ id: s.id, displayName: s.displayName, actionBehavior: s.actionBehavior }))}
        allowStageSelection={transitionAllowStageSelection}
        interviewAlert={transitionInterviewAlert ?? undefined}
      />

      {/* DataRequestModal - Modal para solicitar dados do candidato */}
      {showDataRequestModal && dataRequestModalCandidate && (
        <DataRequestModal
          isOpen={showDataRequestModal}
          onClose={() => {
            setShowDataRequestModal(false)
            setDataRequestModalCandidate(null)
          }}
          candidates={[{
            id: dataRequestModalCandidate.id as string,
            name: dataRequestModalCandidate.name as string,
            email: dataRequestModalCandidate.email as string | undefined,
            phone: dataRequestModalCandidate.phone as string | undefined,
            avatar: dataRequestModalCandidate.avatar as string | undefined
          }]}
          jobTitle={currentJob?.title as string | undefined}
          onSubmit={handleDataRequestSubmit}
        />
      )}

      {/* BulkActionModal - Modal para ações em lote */}
      {showBulkActionModal && (
        <BulkActionModal
          isOpen={showBulkActionModal}
          onClose={() => setShowBulkActionModal(false)}
          actionType={bulkActionType}
          candidates={allTableCandidates
            .filter(c => selectedCandidates.has(c.id as string))
            .map(c => ({
              id: c.id as string,
              name: (c.name as string | undefined) || '',
              email: c.email as string | undefined,
              avatar: (c.avatar as string | undefined) || (c.avatar_url as string | undefined),
              currentStage: c.stage as string | undefined
            })) as unknown as Parameters<typeof BulkActionModal>[0]["candidates"]}
          stages={dynamicStages.map(s => ({
            name: s.name,
            displayName: s.displayName,
            stageOrder: (s as unknown as Record<string, unknown>).order as number || 0,
            color: s.color,
            stageType: s.stageType,
            isInitial: s.isInitial,
            isFinal: s.isFinal,
            isHired: s.isHired,
            isRejection: s.isRejection,
            icon: (s as unknown as Record<string, unknown>).icon || '',
            stageCategory: (s as unknown as Record<string, unknown>).stageCategory || 'active',
            allowedTransitions: (s as unknown as Record<string, unknown>).allowedTransitions || []
          })) as unknown as Parameters<typeof BulkActionModal>[0]["stages"]}
          jobTitle={currentJob?.title as string | undefined}
          onExecute={handleBulkActionExecute}
        />
      )}

      {/* JobStatusModal — Pausar / Reativar Vaga (T5) */}
      {showJobStatusModal && (
        <JobStatusModal
          isOpen={showJobStatusModal}
          onClose={() => setShowJobStatusModal(false)}
          jobs={[{
            id: String(currentJob.backendId || currentJob.jobId || currentJob.id),
            title: (currentJob.title as string) || '',
            status: (currentJob.status as string) || '',
            candidates_count: Object.values(candidatesData).flat().length,
          }]}
          candidates={Object.entries(candidatesData)
            .filter(([stageId]) => !['hired', 'rejected', 'offer_declined'].includes(stageId))
            .flatMap(([stageId, cands]: [string, Record<string, unknown>[]]) =>
              (cands as Record<string, unknown>[]).map((c: Record<string, unknown>) => ({
                id: String(c.id),
                name: (c.name as string | undefined) || 'Candidato',
                email: c.email as string | undefined,
                phone: c.phone as string | undefined,
                stage: stageId,
                jobId: String(currentJob.backendId || currentJob.jobId || currentJob.id),
              }))
            )}
          mode={jobStatusModalMode}
          onStatusChange={(_jobIds, newStatus) => {
            setJobEditForm((prev: Record<string, unknown>) => ({ ...prev, status: newStatus }))
            toast.success(newStatus === 'Paralisada' ? 'Vaga pausada com sucesso' : 'Vaga reativada com sucesso')
            setShowJobStatusModal(false)
          }}
        />
      )}

      {/* CloseVacancyModal — Fechar Vaga com notificações (T4) */}
      {showCloseVacancyModal && (() => {
        const hiredList: Record<string, unknown>[] = candidatesData.hired || []
        const hiredCandidate = hiredList[0]
          ? { id: String(hiredList[0].id), name: (hiredList[0].name as string | undefined) || 'Candidato', email: hiredList[0].email as string | undefined, phone: hiredList[0].phone as string | undefined }
          : { id: '', name: '—', email: undefined as string | undefined, phone: undefined as string | undefined }
        const otherCandidates = Object.entries(candidatesData)
          .filter(([stageId]) => stageId !== 'hired')
          .flatMap(([stageId, cands]: [string, Record<string, unknown>[]]) =>
            (cands as Record<string, unknown>[]).map((c: Record<string, unknown>) => ({
              id: String(c.id),
              name: (c.name as string | undefined) || 'Candidato',
              email: c.email as string | undefined,
              phone: c.phone as string | undefined,
              stage: stageId,
            }))
          )
        return (
          <CloseVacancyModal
            isOpen={showCloseVacancyModal}
            onClose={() => setShowCloseVacancyModal(false)}
            vacancy={{
              id: String(currentJob.backendId || currentJob.jobId || currentJob.id),
              title: (currentJob.title as string) || '',
              department: currentJob.department as string | undefined,
            }}
            hiredCandidate={hiredCandidate}
            otherCandidates={otherCandidates}
            onConfirm={async () => {
              setJobEditForm((prev: Record<string, unknown>) => ({ ...prev, status: 'Encerrada' }))
              toast.success('Vaga encerrada com sucesso')
              setShowCloseVacancyModal(false)
            }}
          />
        )
      })()}

      {showPublishSuccess && publicLink && (
        <div className="fixed inset-0 bg-lia-overlay z-50 flex items-center justify-center" onClick={() => setShowPublishSuccess(false)}>
          <div className="bg-lia-bg-secondary rounded-md shadow-lia-lg w-full max-w-sm mx-4 animate-in fade-in zoom-in-95 duration-200" onClick={e => e.stopPropagation()}>
            <div className="px-6 py-4 border-b border-lia-border-subtle">
              <h3 className="text-base font-semibold text-lia-text-primary font-['Open_Sans',sans-serif]">
                Vaga Publicada!
              </h3>
            </div>
            <div className="px-6 py-4 space-y-4">
              <p className="text-sm text-lia-text-secondary font-['Open_Sans',sans-serif]">
                A vaga está ativa. Compartilhe o link abaixo com candidatos:
              </p>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  readOnly
                  value={publicLink}
                  className="flex-1 px-3 py-2 text-xs text-lia-text-secondary bg-lia-bg-secondary border border-lia-border-subtle rounded-md font-['Open_Sans',sans-serif] select-all"
                  onClick={e => (e.target as HTMLInputElement).select()}
                />
                <button
                  onClick={() => {
                    try {
                      navigator.clipboard.writeText(publicLink)
                      toast.success("Link copiado!", { description: "O link foi copiado para a área de transferência." })
                    } catch {
                      toast.error("Não foi possível copiar", { description: "Selecione o link manualmente e copie." })
                    }
                  }}
                  className="p-2 rounded-md bg-lia-btn-primary-bg text-white hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none flex-shrink-0"
                  title="Copiar link"
                >
                  <Copy className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div className="px-6 py-4 bg-lia-bg-secondary border-t border-lia-border-subtle flex justify-end">
              <button
                onClick={() => setShowPublishSuccess(false)}
                className="px-4 py-2 text-sm font-medium rounded-md bg-lia-btn-primary-bg text-white hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none font-['Open_Sans',sans-serif]"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Compartilhar com Gestor (H.3a) */}
      <ShareSearchModal
        open={showShareGestorModal}
        onClose={() => {
          setShowShareGestorModal(false)
        }}
        shareType="list"
        title={`Candidatos — ${currentJob?.title ?? "Vaga"}`}
        candidateIds={selectedCandidates.size > 0 ? Array.from(selectedCandidates) : allCandidateIds}
        candidateCount={selectedCandidates.size > 0 ? selectedCandidates.size : allCandidateIds.length}
        onSuccess={() => {
          setSelectedCandidates(new Set())
        }}
      />
    </>
  )
}
