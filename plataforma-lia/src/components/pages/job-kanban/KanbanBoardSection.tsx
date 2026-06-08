"use client"

import React from "react"
import dynamic from "next/dynamic"
import { useTranslations } from "next-intl"
import { LoadingModal } from "@/components/ui/loading"
import { Plus, Users } from "lucide-react"
import { EmptyState } from "@/components/ui/empty-state"
import { KanbanFiltersPanel } from "@/components/pages/job-kanban/KanbanFiltersPanel"
import { KanbanColumnRenderer } from "@/components/pages/job-kanban/KanbanColumnRenderer"
import { AddColumnPopover } from "@/components/pages/job-kanban/AddColumnPopover"
import { JobFairnessBlockBanner } from "@/components/jobs/JobFairnessBlockBanner"
import type { KanbanPageCoreState } from "@/components/pages/job-kanban/hooks/useKanbanPageCore"
import { useOfferReviewFlow } from "@/hooks/offers/useOfferReviewFlow"

const CandidatePreview = dynamic(() => import("@/components/candidate-preview").then(m => ({ default: m.CandidatePreview })), { ssr: false, loading: () => <LoadingModal /> })

interface KanbanBoardSectionProps {
  state: KanbanPageCoreState
}

export function KanbanBoardSection({ state }: KanbanBoardSectionProps) {
  const t = useTranslations('kanban')
  const { openOfferReview } = useOfferReviewFlow()
  const {
    dynamicStages, setDynamicStages, candidatesData, setCandidatesData,
    isLoadingCandidates, hasMounted, searchQuery,
    selectedCandidates, setSelectedCandidates,
    selectedForCompare, setSelectedForCompare,
    viewedCandidateIds, favoriteCandidates,
    shortListedCandidateIds, aiSuggestions,
    kanbanScoreMin, kanbanStatusFilter, kanbanWorkModelFilter, kanbanOriginFilter,
    currentJob, _jobIdForSL, getColumnStyle, getStageCategory,
    calculateNotaLiaGeral, getDataRequestForCandidate,
    setTransitionInitialPrompt, setTransitionInterviewAlert,
    setTransitionAllowStageSelection, setDecisionFlowCandidate,
    setDecisionFlowType, setShowDecisionFlowModal,
    handleDragStart, handleDragEnd, handleDragOver, handleDrop, handleDragLeave,
    draggedCandidate, dragOverColumn,
    handleOpenPreview, handleSendEmail, handleSendWhatsApp,
    handleScheduleInterview, handleToggleFavorite, handleToggleShortList,
    handleOpenAnalysis, handleOpenScoreModal, openDecisionFlowModal,
    handleSendWSIInvite, handleSendFeedback,
    handleApproveFromScreening, handleRejectFromScreening,
    handleInlineRename, handleInlineToggleActive, handleInlineRemove,
    handleInlineMoveLeft, handleInlineMoveRight, handleInlineUpdateSLA,
    handleDataRequestResend, handleDataRequestViewDetails,
    approveSuggestion, rejectSuggestion, openTransition,
    router, showAddColumnPopover, setShowAddColumnPopover,
    isAddingColumn, setIsAddingColumn,
    showKanbanFiltersPanel, setShowKanbanFiltersPanel,
    isPreviewOpen, setIsPreviewOpen, previewCandidate,
    isPreviewMaximized, handleClosePreview, handleTogglePreviewMaximize,
    handleNavigateCandidate, handleCandidatePageOpen,
    handleAddToVacancy, handleOpenTriagem,
    handleSendTriagem, handleSendAgendamento,
    setShowAddToVacancyModal, jobData,
  } = state

  const renderKanbanColumn = (stageId: string, candidates: Record<string, unknown>[], colorClass: string, bgClass: string) => (
    <KanbanColumnRenderer
      stageId={stageId}
      candidates={candidates as unknown as Parameters<typeof KanbanColumnRenderer>[0]["candidates"]}
      colorClass={colorClass}
      bgClass={bgClass}
      dynamicStages={dynamicStages}
      searchQuery={searchQuery}
      draggedCandidate={draggedCandidate as unknown as Parameters<typeof KanbanColumnRenderer>[0]["draggedCandidate"]}
      dragOverColumn={dragOverColumn}
      selectedCandidates={selectedCandidates}
      selectedForCompare={selectedForCompare}
      viewedCandidateIds={viewedCandidateIds}
      favoriteCandidates={favoriteCandidates}
      shortListedCandidateIds={shortListedCandidateIds}
      aiSuggestions={aiSuggestions as unknown as Parameters<typeof KanbanColumnRenderer>[0]["aiSuggestions"]}
      kanbanScoreMin={kanbanScoreMin}
      kanbanStatusFilter={kanbanStatusFilter}
      kanbanWorkModelFilter={kanbanWorkModelFilter}
      kanbanOriginFilter={kanbanOriginFilter}
      currentJob={currentJob}
      _jobIdForSL={_jobIdForSL}
      getColumnStyle={getColumnStyle}
      getStageCategory={getStageCategory}
      calculateNotaLiaGeral={calculateNotaLiaGeral}
      getDataRequestForCandidate={getDataRequestForCandidate as unknown as Parameters<typeof KanbanColumnRenderer>[0]["getDataRequestForCandidate"]}
      setSelectedCandidates={setSelectedCandidates}
      setSelectedForCompare={setSelectedForCompare}
      setCandidatesData={setCandidatesData as unknown as Parameters<typeof KanbanColumnRenderer>[0]["setCandidatesData"]}
      setTransitionInitialPrompt={setTransitionInitialPrompt}
      setTransitionInterviewAlert={setTransitionInterviewAlert}
      setTransitionAllowStageSelection={setTransitionAllowStageSelection}
      setDecisionFlowCandidate={setDecisionFlowCandidate}
      setDecisionFlowType={setDecisionFlowType}
      setShowDecisionFlowModal={setShowDecisionFlowModal}
      onDragStart={handleDragStart as unknown as Parameters<typeof KanbanColumnRenderer>[0]["onDragStart"]}
      onDragEnd={handleDragEnd}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onDragLeave={handleDragLeave}
      onOpenPreview={handleOpenPreview}
      onSendEmail={handleSendEmail}
      onSendWhatsApp={handleSendWhatsApp}
      onScheduleInterview={handleScheduleInterview}
      onToggleFavorite={handleToggleFavorite}
      onToggleShortList={handleToggleShortList}
      onOpenAnalysis={handleOpenAnalysis as unknown as Parameters<typeof KanbanColumnRenderer>[0]["onOpenAnalysis"]}
      onOpenScoreModal={handleOpenScoreModal}
      onOpenDecisionFlowModal={openDecisionFlowModal as unknown as Parameters<typeof KanbanColumnRenderer>[0]["onOpenDecisionFlowModal"]}
      onSendWSIInvite={handleSendWSIInvite}
      onSendFeedback={handleSendFeedback}
      onApproveFromScreening={handleApproveFromScreening as unknown as Parameters<typeof KanbanColumnRenderer>[0]["onApproveFromScreening"]}
      onRejectFromScreening={handleRejectFromScreening as unknown as Parameters<typeof KanbanColumnRenderer>[0]["onRejectFromScreening"]}
      onManageProposal={(candidate) => {
        const c = candidate as { id: string | number; [key: string]: unknown }
        openOfferReview({ candidateId: String((c as { candidateId?: string; id: string | number }).candidateId ?? c.id), jobId: String((currentJob as { backendId?: string })?.backendId ?? currentJob?.id ?? "") })
      }}
      onInlineRename={handleInlineRename}
      onInlineToggleActive={handleInlineToggleActive}
      onInlineRemove={handleInlineRemove}
      onInlineMoveLeft={handleInlineMoveLeft}
      onInlineMoveRight={handleInlineMoveRight}
      onInlineUpdateSLA={handleInlineUpdateSLA}
      onOpenSettings={() => router.push('/configuracoes')}
      onDataRequestResend={handleDataRequestResend}
      onDataRequestViewDetails={handleDataRequestViewDetails}
      approveSuggestion={approveSuggestion}
      rejectSuggestion={rejectSuggestion}
      openTransition={openTransition as unknown as Parameters<typeof KanbanColumnRenderer>[0]["openTransition"]}
    />
  )

  return (
    <>
      <KanbanFiltersPanel
        open={showKanbanFiltersPanel}
        onClose={() => setShowKanbanFiltersPanel(false)}
        scoreMin={kanbanScoreMin}
        onScoreMinChange={state.setKanbanScoreMin}
        statusFilter={kanbanStatusFilter}
        onStatusFilterChange={state.setKanbanStatusFilter}
        originFilter={kanbanOriginFilter}
        onOriginFilterChange={state.setKanbanOriginFilter}
        workModelFilter={kanbanWorkModelFilter}
        onWorkModelFilterChange={state.setKanbanWorkModelFilter}
      />

      <div className="flex-1 overflow-x-auto overflow-y-hidden" suppressHydrationWarning>
        <div className="p-4 h-full" suppressHydrationWarning>
          {(currentJob as { id?: string })?.id ? (
            <JobFairnessBlockBanner jobId={((currentJob as { backendId?: string; id?: string })?.backendId || (currentJob as { id?: string })?.id) as string} />
          ) : null}
          {(!hasMounted || isLoadingCandidates) ? (
            <div className="flex gap-3 h-full min-w-max" suppressHydrationWarning>
              {dynamicStages.map((stage) => (
                <div key={stage.id} className="flex flex-col flex-1 bg-lia-bg-primary rounded-xl min-w-[250px] max-w-[320px] border border-lia-border-subtle h-[calc(100vh-16rem)]" suppressHydrationWarning>
                  <div className="flex-shrink-0 p-2.5 pb-1.5">
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full animate-pulse motion-reduce:animate-none" style={{backgroundColor: stage.color}}></div>
                      <h3 className="font-medium text-xs text-lia-text-disabled">{stage.displayName}</h3>
                      <span className="text-micro text-lia-text-disabled bg-lia-bg-tertiary px-1.5 py-0.5 rounded-full animate-pulse motion-reduce:animate-none">...</span>
                    </div>
                  </div>
                  <div className="flex-1 flex items-center justify-center">
                    <div className="animate-pulse motion-reduce:animate-none text-lia-text-disabled text-xs" suppressHydrationWarning>{t('loadingEllipsis')}</div>
                  </div>
                </div>
              ))}
            </div>
          ) : (() => {
            const totalCandidates = Object.values(candidatesData).reduce(
              (sum, arr) => sum + (arr?.length || 0), 0
            )
            if (totalCandidates === 0) {
              return (
                <EmptyState
                  icon={<Users />}
                  title={t('emptyTitle')}
                  description={t('emptyDescription')}
                  action={{
                    label: t('searchCandidates'),
                    onClick: () => setShowAddToVacancyModal(true),
                  }}
                  className="h-64"
                />
              )
            }
            return (
            <div
              className="flex gap-3 h-full min-w-max"
              key={`kanban-${dynamicStages.map(s => candidatesData[s.id]?.length || 0).join('-')}`}
              suppressHydrationWarning
            >
              {dynamicStages.map(stage => (
                <React.Fragment key={stage.id}>
                  {renderKanbanColumn(stage.id, candidatesData[stage.id] || [], '', '')}
                </React.Fragment>
              ))}
              <div className="flex-shrink-0 w-[280px]">
                <div 
                  className="h-full min-h-chart-sm rounded-xl border-2 border-dashed border-lia-border-default hover:border-lia-border-medium flex flex-col items-center justify-center gap-3 cursor-pointer transition-colors motion-reduce:transition-none hover:bg-lia-bg-secondary/50 group"
                  onClick={() => setShowAddColumnPopover(true)}
                >
                  <div className="w-10 h-10 rounded-full bg-lia-bg-tertiary group-hover:bg-lia-interactive-active flex items-center justify-center transition-colors motion-reduce:transition-none">
                    <Plus className="w-5 h-5 text-lia-text-disabled group-hover:text-lia-text-secondary" />
                  </div>
                  <span className="text-xs text-lia-text-disabled group-hover:text-lia-text-secondary font-medium transition-colors motion-reduce:transition-none">
                    {t('addColumn')}
                  </span>
                </div>
              </div>
              <AddColumnPopover
                isOpen={showAddColumnPopover}
                onClose={() => setShowAddColumnPopover(false)}
                dynamicStages={dynamicStages as unknown as Parameters<typeof AddColumnPopover>[0]["dynamicStages"]}
                isAddingColumn={isAddingColumn}
                onSetIsAddingColumn={setIsAddingColumn}
                onAddStage={(stage) => {
                  setDynamicStages(prev => {
                    const finalStages = prev.filter(s => s.isFinal || s.isHired || s.isRejection)
                    const activeStages = prev.filter(s => !s.isFinal && !s.isHired && !s.isRejection)
                    return [...activeStages, stage as unknown as typeof prev[0], ...finalStages]
                  })
                  setCandidatesData(prev => ({ ...prev, [stage.id]: [] }))
                }}
              />
            </div>
          )
          })()}
        </div>
      </div>

      {isPreviewOpen && previewCandidate && (
        <div className={`flex-shrink-0 transition-colors motion-reduce:transition-none duration-300 ${isPreviewMaximized ? 'w-[600px]' : 'w-panel-lg'}`}>
          <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle h-[calc(100vh-6rem)] overflow-hidden">
          <CandidatePreview
            candidate={previewCandidate}
            isOpen={isPreviewOpen}
            onClose={handleClosePreview}
            isMaximized={isPreviewMaximized}
            onToggleMaximize={handleTogglePreviewMaximize}
            candidates={(() => {
              const data = candidatesData as Record<string, Record<string, unknown>[]>
              const currentColumn = Object.keys(data).find(col => 
                data[col].some((c: Record<string, unknown>) => c.id === previewCandidate?.id)
              )
              return currentColumn ? data[currentColumn] : []
            })()}
            currentIndex={(() => {
              const data = candidatesData as Record<string, Record<string, unknown>[]>
              const currentColumn = Object.keys(data).find(col => 
                data[col].some((c: Record<string, unknown>) => c.id === previewCandidate?.id)
              )
              return currentColumn ? data[currentColumn].findIndex((c: Record<string, unknown>) => c.id === previewCandidate?.id) : 0
            })()}
            onNavigateCandidate={handleNavigateCandidate}
            onOpenFullPage={handleCandidatePageOpen}
            onScheduleInterview={handleScheduleInterview}
            onAddToVacancy={handleAddToVacancy}
            onToggleFavorite={handleToggleFavorite}
            onWSIScreening={handleSendWSIInvite}
            onOpenTriagemDetails={handleOpenTriagem}
            isFavorite={previewCandidate ? favoriteCandidates.has(previewCandidate.id as string) : false}
            onSendEmail={(candidate) => handleSendEmail(candidate)}
            onSendWhatsApp={(candidate) => handleSendWhatsApp(candidate)}
            onSendTriagem={(candidate) => handleSendTriagem(candidate)}
            onSendAgendamento={(candidate) => handleSendAgendamento(candidate)}
            onSendFeedback={(candidate) => handleSendFeedback(candidate)}
            jobId={((jobData.backendId || jobData.id) as string | number | undefined)?.toString()}
          />
          </div>
        </div>
      )}
    </>
  )
}
