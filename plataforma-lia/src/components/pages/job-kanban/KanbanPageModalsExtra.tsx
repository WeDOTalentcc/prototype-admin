"use client"

import React from "react"
import dynamic from "next/dynamic"
import { Copy } from "lucide-react"
import { LoadingModal } from "@/components/ui/loading"
import { toast } from "sonner"
import { useTranslations } from "next-intl"
import type { KanbanPageCoreState } from "./hooks/useKanbanPageCore"
import { useCompanyId } from "@/hooks/company/useCompanyId"

const GeneralScoreModal = dynamic(() => import("@/components/modals/general-score-modal").then(m => ({ default: m.GeneralScoreModal })), { ssr: false, loading: () => <LoadingModal /> })
const TechnicalTestModal = dynamic(() => import("@/components/modals/technical-test-modal").then(m => ({ default: m.TechnicalTestModal })), { ssr: false, loading: () => <LoadingModal /> })
const EnglishTestModal = dynamic(() => import("@/components/modals/english-test-modal").then(m => ({ default: m.EnglishTestModal })), { ssr: false, loading: () => <LoadingModal /> })
const CandidateCompareModal = dynamic(() => import("@/components/modals/candidate-compare-modal").then(m => ({ default: m.CandidateCompareModal })), { ssr: false, loading: () => <LoadingModal /> })
const UniversalTransitionModal = dynamic(() => import("@/components/kanban").then(m => ({ default: m.UniversalTransitionModal })), { ssr: false, loading: () => <LoadingModal /> })
const DataRequestModal = dynamic(() => import("@/components/modals/data-request-modal").then(m => ({ default: m.DataRequestModal })), { ssr: false, loading: () => <LoadingModal /> })
const CloseVacancyModal = dynamic(() => import("@/components/modals/close-vacancy-modal").then(m => ({ default: m.CloseVacancyModal })), { ssr: false, loading: () => <LoadingModal /> })
import type { CloseVacancyPayload } from "@/components/modals/close-vacancy-modal"
const JobStatusModal = dynamic(() => import("@/components/modals/job-status-modal").then(m => ({ default: m.JobStatusModal })), { ssr: false, loading: () => <LoadingModal /> })
const ShareSearchModal = dynamic(() => import("@/components/modals/share-search-modal").then(m => ({ default: m.ShareSearchModal })), { ssr: false, loading: () => <LoadingModal /> })
const BulkActionModal = dynamic(() => import("@/components/modals/bulk-action-modal").then(m => ({ default: m.BulkActionModal })), { ssr: false, loading: () => <LoadingModal /> })
const OfferReviewModal = dynamic(() => import("@/components/offer-review-modal/OfferReviewModal").then(m => ({ default: m.OfferReviewModal })), { ssr: false })

export function KanbanPageModalsExtra(state: KanbanPageCoreState) {
  const t = useTranslations('kanban')
  const { companyId: resolvedCompanyId } = useCompanyId()
  const {
    showGeneralScoreModal, setShowGeneralScoreModal,
    showTechnicalTestModal, setShowTechnicalTestModal,
    showEnglishTestModal, setShowEnglishTestModal,
    scoreModalCandidate,
    showCompareModal, setShowCompareModal, compareCandidates, setCompareCandidates,
    _jobIdForSL, _companyIdForSL,
    selectedForCompare, setSelectedForCompare, allTableCandidates,
    universalModalState, closeTransition, setTransitionInitialPrompt, setTransitionAllowStageSelection, setTransitionInterviewAlert,
    handleUniversalTransitionConfirm, handleOpenSpecializedModal, dynamicStages,
    transitionInitialPrompt, transitionAllowStageSelection, transitionInterviewAlert,
    showDataRequestModal, setShowDataRequestModal, dataRequestModalCandidate, setDataRequestModalCandidate, handleDataRequestSubmit,
    showBulkActionModal, setShowBulkActionModal, bulkActionType, handleBulkActionExecute,
    selectedCandidates, candidatesData, currentJob, user,
    showJobStatusModal, setShowJobStatusModal, jobStatusModalMode, setJobEditForm,
    showCloseVacancyModal, setShowCloseVacancyModal,
    showPublishSuccess, setShowPublishSuccess, publicLink,
    showShareGestorModal, setShowShareGestorModal,
    allCandidateIds, setSelectedCandidates,
  } = state
  return (
    <>
      <GeneralScoreModal
        isOpen={showGeneralScoreModal}
        onClose={() => setShowGeneralScoreModal(false)}
        candidate={scoreModalCandidate ?? {}}
      />
      <TechnicalTestModal
        isOpen={showTechnicalTestModal}
        onClose={() => setShowTechnicalTestModal(false)}
        candidate={scoreModalCandidate ?? {}}
      />
      <EnglishTestModal
        isOpen={showEnglishTestModal}
        onClose={() => setShowEnglishTestModal(false)}
        candidate={scoreModalCandidate ?? {}}
      />

      <CandidateCompareModal
        open={showCompareModal}
        onClose={() => setShowCompareModal(false)}
        candidates={compareCandidates as unknown as React.ComponentProps<typeof CandidateCompareModal>['candidates']}
        jobId={_jobIdForSL ?? undefined}
        companyId={_companyIdForSL ?? undefined}
      />

      {selectedForCompare.size >= 2 && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2">
          <button
            className="flex items-center gap-2 bg-lia-btn-primary-bg text-lia-btn-primary-text px-4 py-2 rounded-xl text-sm font-medium hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none shadow-lia-md"
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
            <span>{t('compareCountBtn', { count: selectedForCompare.size })}</span>
          </button>
          <button
            className="bg-lia-bg-primary border border-lia-border-subtle text-lia-text-secondary px-3 py-2 rounded-xl text-sm hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none shadow-lia-md"
            onClick={() => setSelectedForCompare(new Set())}
            aria-label={t('clearComparisonAria')}
          >
            ✕
          </button>
        </div>
      )}

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
        companyId={resolvedCompanyId || undefined}
        jobTitle={currentJob?.title as string | undefined}
        initialPrompt={transitionInitialPrompt}
        availableStages={dynamicStages.map(s => ({ id: s.id, displayName: s.displayName, actionBehavior: s.actionBehavior }))}
        allowStageSelection={transitionAllowStageSelection}
        interviewAlert={transitionInterviewAlert ?? undefined}
      />

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
            }))}
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
          })) as any}
          jobTitle={currentJob?.title as string | undefined}
          onExecute={handleBulkActionExecute}
        />
      )}

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
                name: (c.name as string | undefined) || t('candidateFallback'),
                email: c.email as string | undefined,
                phone: c.phone as string | undefined,
                stage: stageId,
                jobId: String(currentJob.backendId || currentJob.jobId || currentJob.id),
              }))
            )}
          mode={jobStatusModalMode}
          onStatusChange={(_jobIds, newStatus) => {
            setJobEditForm((prev: Record<string, unknown>) => ({ ...prev, status: newStatus }))
            toast.success(newStatus === 'Paralisada' ? t('jobPausedSuccess') : t('jobReactivatedSuccess'))
            setShowJobStatusModal(false)
          }}
        />
      )}

      {showCloseVacancyModal && (() => {
        const hiredList: Record<string, unknown>[] = candidatesData.hired || []
        const hiredCandidate = hiredList[0]
          ? { id: String(hiredList[0].id), name: (hiredList[0].name as string | undefined) || t('candidateFallback'), email: hiredList[0].email as string | undefined, phone: hiredList[0].phone as string | undefined }
          : { id: '', name: '—', email: undefined as string | undefined, phone: undefined as string | undefined }
        const otherCandidates = Object.entries(candidatesData)
          .filter(([stageId]) => stageId !== 'hired')
          .flatMap(([stageId, cands]: [string, Record<string, unknown>[]]) =>
            (cands as Record<string, unknown>[]).map((c: Record<string, unknown>) => ({
              id: String(c.id),
              name: (c.name as string | undefined) || t('candidateFallback'),
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
            onConfirm={async (data: CloseVacancyPayload) => {
              const vacancyId = String(currentJob.backendId || currentJob.jobId || currentJob.id)
              try {
                const response = await fetch(`/api/backend-proxy/job-vacancies/${vacancyId}/close`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({
                    hired_candidate_id: data.hired_candidate_id || data.hired_candidate_ids?.[0] || null,
                    close_reason: data.close_reason || 'filled',
                    hired_notification: data.hired_notification,
                    other_notifications: data.other_notifications,
                  })
                })

                if (!response.ok) {
                  const errorData = await response.json().catch(() => ({}))
                  toast.error('Erro ao fechar vaga', {
                    description: (errorData as Record<string, string>).detail || (errorData as Record<string, string>).error || 'Não foi possível fechar a vaga. Tente novamente.'
                  })
                  return
                }

                setJobEditForm((prev: Record<string, unknown>) => ({ ...prev, status: 'Encerrada' }))
                toast.success(t('jobClosedSuccess'))
                setShowCloseVacancyModal(false)
              } catch {
                toast.error('Erro de conexão', { description: 'Não foi possível conectar ao servidor.' })
              }
            }}
          />
        )
      })()}

      {showPublishSuccess && publicLink && (
        <div className="fixed inset-0 bg-lia-overlay z-50 flex items-center justify-center" onClick={() => setShowPublishSuccess(false)}>
          <div className="bg-lia-bg-secondary rounded-xl shadow-lia-lg w-full max-w-sm mx-4 animate-in fade-in zoom-in-95 duration-200" onClick={e => e.stopPropagation()}>
            <div className="px-6 py-4">
              <h3 className="text-base font-semibold text-lia-text-primary">
                {t('jobPublishedTitle')}
              </h3>
            </div>
            <div className="px-6 py-4 space-y-4">
              <p className="text-sm text-lia-text-secondary">
                {t('jobPublishedDesc')}
              </p>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  readOnly
                  value={publicLink}
                  className="flex-1 px-3 py-2 text-xs text-lia-text-secondary bg-lia-bg-secondary border border-lia-border-subtle rounded-md select-all"
                  onClick={e => (e.target as HTMLInputElement).select()}
                />
                <button
                  onClick={() => {
                    try {
                      navigator.clipboard.writeText(publicLink)
                      toast.success(t('linkCopied'), { description: t('linkCopiedDesc') })
                    } catch {
                      toast.error(t('copyFailed'), { description: t('copyFailedDesc') })
                    }
                  }}
                  className="p-2 rounded-md bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none flex-shrink-0"
                  title={t('copyLink')}
                >
                  <Copy className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div className="px-6 py-4 bg-lia-bg-secondary border-t border-lia-border-subtle flex justify-end">
              <button
                onClick={() => setShowPublishSuccess(false)}
                className="px-4 py-2 text-sm font-medium rounded-xl bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none"
              >
                {t('closePanel')}
              </button>
            </div>
          </div>
        </div>
      )}

      <ShareSearchModal
        open={showShareGestorModal}
        onClose={() => {
          setShowShareGestorModal(false)
        }}
        shareType="list"
        title={t('candidatesShareTitle', { title: (currentJob?.title ?? t('jobFallback')) as string })}
        candidateIds={selectedCandidates.size > 0 ? Array.from(selectedCandidates) : allCandidateIds}
        candidateCount={selectedCandidates.size > 0 ? selectedCandidates.size : allCandidateIds.length}
        onSuccess={() => {
          setSelectedCandidates(new Set())
        }}
      />
      {/* PR-B: OfferReviewModal — controlado pelo useOfferDraftStore, sem props */}
      <OfferReviewModal />
    </>
  )
}
