"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { X, ArrowRight, List, Share2, Fingerprint, FileText, Mail, Star, XCircle, Tag } from "lucide-react"
import { Button } from "@/components/ui/button"
import { BulkActionsBar, type BulkActionType } from "@/components/ui/bulk-actions-bar"
import { PipelineStagesCarousel } from "@/components/ui/pipeline-stages-carousel"
import { JobEditTab } from "@/components/jobs/JobEditTab"
// Onda 3 F4 (2026-05-28) — aba Agentes da Vaga.
import { JobAgentsTab } from "@/components/jobs/JobAgentsTab"
import { VacancyAnalyticsTab } from "@/components/vacancy-preview/VacancyAnalyticsTab"
import { KanbanToolbar } from "@/components/pages/job-kanban/KanbanToolbar"
import { KanbanTableView } from "@/components/pages/job-kanban/KanbanTableView"
import { KanbanBoardSection } from "@/components/pages/job-kanban/KanbanBoardSection"
import { getLiaAlerts } from "@/components/pages/job-kanban/utils/kanbanHelpers"
import type { KanbanPageCoreState } from "@/components/pages/job-kanban/hooks/useKanbanPageCore"
import { DataRequestDetailsModal } from "@/components/ui/data-request-details-modal"

interface KanbanPageContentProps {
  state: KanbanPageCoreState
}

export function KanbanPageContent({ state }: KanbanPageContentProps) {
  const t = useTranslations('kanban')
  const {
    viewMode, activeTab, currentJob, jobEditForm, setJobEditForm,
    handleSaveJobSection, savingJobSection, companyDefaults,
    isCreationMode, handlePublishJob, isPublishing, publicLink,
    setJobLocalOverrides, proactiveInsights, dismissInsight,
    searchQuery, setSearchQuery,
    showKanbanFiltersPanel, setShowKanbanFiltersPanel,
    showTableFiltersPanel, setShowTableFiltersPanel,
    showColumnConfig, setShowColumnConfig,
    kanbanScoreMin, kanbanStatusFilter, kanbanWorkModelFilter, kanbanOriginFilter,
    selectedCandidates, setSelectedCandidates,
    allTableCandidates, candidatesData,
    viewMode: _vm,
    tableStageFilter, setTableStageFilter, clearStageFilters,
    toggleStageFilter, pipelineStages, getStageCount,
    handleBulkAction, tableColumns, setTableColumns,
    tableSortColumn, tableSortDirection, setTableSortColumn, setTableSortDirection,
    currentPage, setCurrentPage, getPaginatedCandidates,
    dynamicStages, saturationData,
    handleTableColumnResize, handleOpenPreview, handleInteractiveStatusChange,
    handleTableTransitionRequest, handleTransitionRequired,
    calculateNotaLiaGeral, viewedCandidateIds,
    handleOpenTriagem, handleOpenAnalysis,
    setSelectedCandidateForModal, setActiveModal, setShowBigFiveModal,
    setScoreModalCandidate, getDataRequestForCandidate,
    handleDataRequestResend, handleDataRequestViewDetails,
    handleApproveFromScreening, handleRejectFromScreening,
    handleApproveCandidate, handleRejectCandidate,
    openDecisionFlowModal, setTransitionInitialPrompt,
    setTransitionAllowStageSelection, setTransitionInterviewAlert,
    openTransition, isPreviewOpen, previewCandidate, isPreviewMaximized,
    handleClosePreview, handleTogglePreviewMaximize,
    handleNavigateCandidate, handleCandidatePageOpen,
    handleScheduleInterview, handleAddToVacancy,
    handleToggleFavorite, handleSendWSIInvite,
    handleSendEmail, handleSendWhatsApp, handleSendTriagem,
    handleSendAgendamento, handleSendFeedback,
    favoriteCandidates, jobData,
    dataRequestDetailsId, showDataRequestDetailsModal, setShowDataRequestDetailsModal,
  } = state

  if (activeTab === 'agents') {
    return (
      <JobAgentsTab
        jobId={String(currentJob?.id || jobData?.id || '')}
        jobTitle={(currentJob?.title || jobData?.title) as string | undefined}
      />
    )
  }

  if (activeTab === 'indicators') {
    return (
      <div className="flex-1 overflow-y-auto bg-lia-bg-primary dark:bg-lia-bg-primary">
        <div className="px-4 py-4 pb-12">
          <VacancyAnalyticsTab jobId={String(currentJob?.id || jobData?.id || '')} />
        </div>
      </div>
    )
  }

  if (activeTab === 'edit') {
    return (
      <div className="flex-1 overflow-y-auto bg-lia-bg-primary dark:bg-lia-bg-primary">
        <div className="px-4 py-4 pb-12">
          <JobEditTab
            jobEditForm={jobEditForm}
            setJobEditForm={setJobEditForm}
            onSaveSection={handleSaveJobSection}
            savingSection={savingJobSection}
            companyDefaults={companyDefaults}
            job={currentJob}
            onJobUpdate={(updatedJob) => {
              setJobEditForm((prev: Record<string, unknown>) => ({ ...prev, ...updatedJob }))
              setJobLocalOverrides((prev) => ({ ...prev, ...updatedJob }))
            }}
            onFormUpdate={(updates) => {
              setJobEditForm((prev: Record<string, unknown>) => ({ ...prev, ...updates }))
            }}
            isCreationMode={isCreationMode}
            onPublish={handlePublishJob}
            isPublishing={isPublishing}
            publicLink={publicLink}
          />
        </div>
      </div>
    )
  }

  return (
    <>
    <div data-testid="kanban-page-content" className="flex-1 overflow-hidden bg-lia-bg-primary dark:bg-lia-bg-primary flex flex-col min-w-0">
      {viewMode === "table" && (
        <div className="flex-shrink-0 bg-lia-bg-primary dark:bg-lia-bg-primary px-4 py-2">
          <div className="w-full">
            <div className="flex items-center gap-2">
              {tableStageFilter.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearStageFilters}
                  className="h-6 text-micro gap-1 flex-shrink-0 px-2 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
                >
                  <X className="w-3 h-3" />
                  {t('clear')}
                </Button>
              )}
              <PipelineStagesCarousel
                stages={pipelineStages.map(stage => ({
                  id: stage.id,
                  name: stage.id,
                  displayName: stage.name,
                  count: getStageCount(stage.name),
                }))}
                selectedStages={tableStageFilter}
                onStageClick={(stageId) => {
                  const stage = pipelineStages.find(s => s.id === stageId)
                  if (stage) toggleStageFilter(stage.name)
                }}
                className="flex-1"
              />
            </div>
          </div>
        </div>
      )}

      {selectedCandidates.size > 0 && (
        <div className="flex-shrink-0 px-4 py-2">
          <BulkActionsBar
            selectedCount={selectedCandidates.size}
            totalCount={allTableCandidates.length}
            showSelectAll={true}
            isAllSelected={selectedCandidates.size === allTableCandidates.length && allTableCandidates.length > 0}
            onSelectAll={() => {
              if (selectedCandidates.size === allTableCandidates.length) {
                setSelectedCandidates(new Set())
              } else {
                setSelectedCandidates(new Set(allTableCandidates.map(c => c.id as string)))
              }
            }}
            onDeselectAll={() => setSelectedCandidates(new Set())}
            actions={[
              {
                id: 'move_stage',
                label: t('moveStage'),
                icon: <ArrowRight className="w-3.5 h-3.5 text-lia-text-secondary" />,
                onClick: () => handleBulkAction('move_stage' as BulkActionType | string),
              },
              {
                id: 'add_to_list',
                label: t('list'),
                icon: <List className="w-3.5 h-3.5 text-lia-text-secondary" />,
                onClick: () => handleBulkAction('add_to_list' as BulkActionType | string),
              },
              {
                id: 'share_search',
                label: t('shareLabel'),
                icon: <Share2 className="w-3.5 h-3.5 text-lia-text-secondary" />,
                onClick: () => handleBulkAction('share_search' as BulkActionType | string),
              },
              {
                id: 'wsi_screening',
                label: t('wsiScreeningBulk'),
                icon: <Fingerprint className="w-3.5 h-3.5 text-lia-text-secondary" />,
                onClick: () => handleBulkAction('wsi_screening' as BulkActionType | string),
              },
              {
                id: 'request_data',
                label: t('requestData'),
                icon: <FileText className="w-3.5 h-3.5 text-lia-text-secondary" />,
                onClick: () => handleBulkAction('request_data' as BulkActionType | string),
              },
              {
                id: 'send_message',
                label: t('messageAction'),
                icon: <Mail className="w-3.5 h-3.5 text-lia-text-secondary" />,
                onClick: () => handleBulkAction('send_message' as BulkActionType | string),
              },
              {
                id: 'favorites',
                label: t('favorites'),
                icon: <Star className="w-3.5 h-3.5 text-status-warning" />,
                onClick: () => handleBulkAction('favorites' as BulkActionType | string),
              },
              {
                id: 'reject',
                label: t('rejectBulk'),
                icon: <XCircle className="w-3.5 h-3.5" />,
                onClick: () => handleBulkAction('reject' as BulkActionType | string),
                variant: 'destructive' as const,
              },
              {
                id: 'add_tags',
                label: 'Adicionar Tags',
                icon: <Tag className="w-3.5 h-3.5 text-lia-text-secondary" />,
                onClick: () => handleBulkAction('add_tags' as BulkActionType | string),
              },
              {
                id: 'remove_tags',
                label: 'Remover Tags',
                icon: <Tag className="w-3.5 h-3.5 text-status-error" />,
                onClick: () => handleBulkAction('remove_tags' as BulkActionType | string),
                variant: 'destructive' as const,
              },
            ]}
          />
        </div>
      )}

      <KanbanToolbar
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        viewMode={viewMode}
        setViewMode={state.setViewMode as any}
        showKanbanFiltersPanel={showKanbanFiltersPanel}
        setShowKanbanFiltersPanel={setShowKanbanFiltersPanel}
        showTableFiltersPanel={showTableFiltersPanel}
        setShowTableFiltersPanel={setShowTableFiltersPanel}
        showColumnConfig={showColumnConfig}
        setShowColumnConfig={setShowColumnConfig}
        tableColumns={tableColumns as any}
        selectedCandidates={selectedCandidates}
        setSelectedCandidates={setSelectedCandidates}
        allTableCandidates={allTableCandidates}
        candidatesData={candidatesData as Record<string, Array<Record<string, unknown>>>}
        tableStageFilter={tableStageFilter}
        kanbanScoreMin={kanbanScoreMin}
        kanbanStatusFilter={kanbanStatusFilter}
        kanbanWorkModelFilter={kanbanWorkModelFilter}
        kanbanOriginFilter={kanbanOriginFilter}
      />

      <div className="flex-1 flex gap-2 overflow-hidden bg-lia-bg-primary dark:bg-lia-bg-primary min-w-0">
        {viewMode === "kanban" && (
          <KanbanBoardSection state={state} />
        )}

        {viewMode === "table" && (
          <KanbanTableView
            showTableFiltersPanel={showTableFiltersPanel}
            onShowTableFiltersPanelChange={setShowTableFiltersPanel}
            dynamicStages={dynamicStages}
            tableStageFilter={tableStageFilter}
            onTableStageFilterChange={setTableStageFilter}
            tableSortColumn={tableSortColumn}
            tableSortDirection={tableSortDirection}
            onSortChange={(config) => {
              setTableSortColumn(config.field)
              setTableSortDirection(config.direction)
            }}
            currentPage={currentPage}
            onCurrentPageChange={setCurrentPage}
            getPaginatedCandidates={getPaginatedCandidates as unknown as Parameters<typeof KanbanTableView>[0]["getPaginatedCandidates"]}
            showColumnConfig={showColumnConfig}
            onShowColumnConfigChange={setShowColumnConfig}
            tableColumns={tableColumns}
            onTableColumnsChange={setTableColumns}
            selectedCandidates={selectedCandidates}
            onSelectionChange={setSelectedCandidates}
            jobVacancyId={jobData?.id?.toString()}
            saturationData={saturationData}
            onColumnResize={handleTableColumnResize}
            onCandidateClick={handleOpenPreview as unknown as Parameters<typeof KanbanTableView>[0]["onCandidateClick"]}
            onStatusChange={handleInteractiveStatusChange as unknown as Parameters<typeof KanbanTableView>[0]["onStatusChange"]}
            onTransitionRequest={handleTableTransitionRequest as unknown as Parameters<typeof KanbanTableView>[0]["onTransitionRequest"]}
            onTransitionRequired={handleTransitionRequired as unknown as Parameters<typeof KanbanTableView>[0]["onTransitionRequired"]}
            calculateNotaLiaGeral={calculateNotaLiaGeral}
            getLiaAlerts={getLiaAlerts}
            viewedCandidateIds={viewedCandidateIds}
            onOpenTriagem={handleOpenTriagem}
            onOpenAnalysis={handleOpenAnalysis as unknown as Parameters<typeof KanbanTableView>[0]["onOpenAnalysis"]}
            onSetSelectedCandidateForModal={setSelectedCandidateForModal}
            onSetActiveModal={setActiveModal as unknown as Parameters<typeof KanbanTableView>[0]["onSetActiveModal"]}
            onSetShowBigFiveModal={setShowBigFiveModal}
            onSetScoreModalCandidate={setScoreModalCandidate}
            getDataRequestForCandidate={getDataRequestForCandidate as unknown as Parameters<typeof KanbanTableView>[0]["getDataRequestForCandidate"]}
            onDataRequestResend={handleDataRequestResend}
            onDataRequestViewDetails={handleDataRequestViewDetails}
            onApproveFromScreening={handleApproveFromScreening as unknown as Parameters<typeof KanbanTableView>[0]["onApproveFromScreening"]}
            onRejectFromScreening={handleRejectFromScreening as unknown as Parameters<typeof KanbanTableView>[0]["onRejectFromScreening"]}
            onApproveCandidate={handleApproveCandidate as unknown as Parameters<typeof KanbanTableView>[0]["onApproveCandidate"]}
            onRejectCandidate={handleRejectCandidate as unknown as Parameters<typeof KanbanTableView>[0]["onRejectCandidate"]}
            openDecisionFlowModal={openDecisionFlowModal as unknown as Parameters<typeof KanbanTableView>[0]["openDecisionFlowModal"]}
            onSetTransitionInitialPrompt={setTransitionInitialPrompt}
            onSetTransitionAllowStageSelection={setTransitionAllowStageSelection}
            onSetTransitionInterviewAlert={setTransitionInterviewAlert}
            openTransition={openTransition as unknown as Parameters<typeof KanbanTableView>[0]["openTransition"]}
            isPreviewOpen={isPreviewOpen}
            previewCandidate={previewCandidate as unknown as Parameters<typeof KanbanTableView>[0]["previewCandidate"]}
            isPreviewMaximized={isPreviewMaximized}
            onClosePreview={handleClosePreview}
            onTogglePreviewMaximize={handleTogglePreviewMaximize}
            onNavigateCandidate={handleNavigateCandidate}
            onCandidatePageOpen={handleCandidatePageOpen}
            onScheduleInterview={handleScheduleInterview}
            onAddToVacancy={handleAddToVacancy}
            onToggleFavorite={handleToggleFavorite as unknown as Parameters<typeof KanbanTableView>[0]["onToggleFavorite"]}
            favoriteCandidates={favoriteCandidates}
            onSendWSIInvite={handleSendWSIInvite}
            onSendEmail={handleSendEmail}
            onSendWhatsApp={handleSendWhatsApp}
            onSendTriagem={handleSendTriagem as unknown as Parameters<typeof KanbanTableView>[0]["onSendTriagem"]}
            onSendAgendamento={handleSendAgendamento as unknown as Parameters<typeof KanbanTableView>[0]["onSendAgendamento"]}
            onSendFeedback={handleSendFeedback as unknown as Parameters<typeof KanbanTableView>[0]["onSendFeedback"]}
            candidatesData={candidatesData as unknown as Parameters<typeof KanbanTableView>[0]["candidatesData"]}
          />
        )}
      </div>
    </div>
    <DataRequestDetailsModal
      requestId={dataRequestDetailsId}
      open={showDataRequestDetailsModal}
      onClose={() => setShowDataRequestDetailsModal(false)}
    />
  </>
  )
}
