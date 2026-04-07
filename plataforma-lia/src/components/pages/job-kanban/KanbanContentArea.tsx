"use client"

import React from "react"
import dynamic from "next/dynamic"
import { LoadingModal } from "@/components/ui/loading"
import {
  ArrowRight, FileText, Mail, Star, XCircle, X,
  ChevronRight, Brain, Users, Share2, Fingerprint, List,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { BulkActionsBar, type BulkActionType } from "@/components/ui/bulk-actions-bar"
import { PipelineStagesCarousel } from "@/components/ui/pipeline-stages-carousel"
import { KanbanToolbar } from "@/components/pages/job-kanban/KanbanToolbar"
import { LiaChatShell } from "@/components/lia-float/LiaChatShell"
import { KanbanTableView } from "@/components/pages/job-kanban/KanbanTableView"
import { KanbanBoardSection } from "@/components/pages/job-kanban/KanbanBoardSection"
import { calculateNotaLiaGeral, getLiaAlerts } from "@/components/pages/job-kanban/utils/kanbanHelpers"
import type { KanbanPageCoreState } from "@/components/pages/job-kanban/hooks/useKanbanPageCore"

const ExpandedChatModal = dynamic(() => import("@/components/expanded-chat-modal").then(m => ({ default: m.ExpandedChatModal })), { ssr: false, loading: () => <LoadingModal /> })

interface KanbanContentAreaProps {
  state: KanbanPageCoreState
}

export function KanbanContentArea({ state }: KanbanContentAreaProps) {
  const {
    viewMode, setViewMode,
    showSuperChat, setShowSuperChat,
    showExpandedLIA, setShowExpandedLIA,
    userCollapsedLIA, setUserCollapsedLIA,
    showKanbanFiltersPanel, setShowKanbanFiltersPanel,
    showTableFiltersPanel, setShowTableFiltersPanel,
    showColumnConfig, setShowColumnConfig,
    kanbanScoreMin, kanbanStatusFilter,
    kanbanWorkModelFilter, kanbanOriginFilter,
    searchQuery, setSearchQuery,
    selectedCandidates, setSelectedCandidates,
    allTableCandidates, candidatesData,
    tableStageFilter, setTableStageFilter,
    tableSortColumn, setTableSortColumn,
    tableSortDirection, setTableSortDirection,
    currentPage, setCurrentPage,
    tableColumns, setTableColumns,
    handleTableColumnResize, getPaginatedCandidates,
    saturationData, handleBulkAction,
    pipelineStages, clearStageFilters, toggleStageFilter, getStageCount,
    jobData, liaMessages, setLiaMessages,
    liaPromptValue, setLiaPromptValue,
    isLiaLoading, liaExpandedWidth, setLiaExpandedWidth,
    showLiaSuggestionsPanel, setShowLiaSuggestionsPanel,
    isResizingLIA, setIsResizingLIA, chatScrollRef,
    handleAICommand, handleLiaUiAction, openSuperChat, returnToExpandedPrompt,
    setSelectedCandidate, setShowCandidatePage,
    handleOrchestratedMessage, computedSuggestions,
    handleInteractiveStatusChange,
    handleTableTransitionRequest, handleTransitionRequired,
    setSelectedCandidateForModal, setActiveModal,
    setShowBigFiveModal, setScoreModalCandidate,
    getDataRequestForCandidate,
    setTransitionInitialPrompt, setTransitionAllowStageSelection, setTransitionInterviewAlert,
    openTransition,
    handleOpenPreview, handleClosePreview, handleTogglePreviewMaximize,
    handleNavigateCandidate, handleCandidatePageOpen,
    handleToggleFavorite,
    handleSendEmail, handleSendWhatsApp, handleSendTriagem,
    handleSendAgendamento, handleSendFeedback,
    handleScheduleInterview, handleAddToVacancy, handleSendWSIInvite,
    handleOpenTriagem, handleOpenAnalysis,
    handleApproveFromScreening, handleRejectFromScreening,
    handleApproveCandidate, handleRejectCandidate,
    openDecisionFlowModal, viewedCandidateIds,
    isPreviewOpen, previewCandidate, isPreviewMaximized,
    favoriteCandidates,
    handleDataRequestResend, handleDataRequestViewDetails,
  } = state

  return (
    <div data-testid="kanban-content-area" className="flex-1 overflow-hidden bg-lia-bg-primary dark:bg-lia-bg-primary flex flex-col min-w-0">
      {viewMode === "table" && (
        <div className="flex-shrink-0 bg-lia-bg-primary dark:bg-lia-bg-primary px-4 py-2">
          <div className="w-full">
            <div className="flex items-center gap-2">
              {tableStageFilter.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearStageFilters}
                  className="h-6 text-micro gap-1 flex-shrink-0 px-2"
                >
                  <X className="w-3 h-3" />
                  Limpar
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
                label: 'Mover Etapa',
                icon: <ArrowRight className="w-3.5 h-3.5 text-lia-text-secondary" />,
                onClick: () => handleBulkAction('move_stage' as BulkActionType | string),
              },
              {
                id: 'add_to_list',
                label: 'Lista',
                icon: <List className="w-3.5 h-3.5 text-lia-text-secondary" />,
                onClick: () => handleBulkAction('add_to_list' as BulkActionType | string),
              },
              {
                id: 'share_search',
                label: 'Compartilhar',
                icon: <Share2 className="w-3.5 h-3.5 text-lia-text-secondary" />,
                onClick: () => handleBulkAction('share_search' as BulkActionType | string),
              },
              {
                id: 'wsi_screening',
                label: 'Triagem WSI',
                icon: <Fingerprint className="w-3.5 h-3.5 text-lia-text-secondary" />,
                onClick: () => handleBulkAction('wsi_screening' as BulkActionType | string),
              },
              {
                id: 'request_data',
                label: 'Solicitar Dados',
                icon: <FileText className="w-3.5 h-3.5 text-lia-text-secondary" />,
                onClick: () => handleBulkAction('request_data' as BulkActionType | string),
              },
              {
                id: 'send_message',
                label: 'Mensagem',
                icon: <Mail className="w-3.5 h-3.5 text-lia-text-secondary" />,
                onClick: () => handleBulkAction('send_message' as BulkActionType | string),
              },
              {
                id: 'favorites',
                label: 'Favoritos',
                icon: <Star className="w-3.5 h-3.5 text-status-warning" />,
                onClick: () => handleBulkAction('favorites' as BulkActionType | string),
              },
              {
                id: 'reject',
                label: 'Reprovar',
                icon: <XCircle className="w-3.5 h-3.5" />,
                onClick: () => handleBulkAction('reject' as BulkActionType | string),
                variant: 'destructive' as const,
              },
            ]}
          />
        </div>
      )}

      <KanbanToolbar
        showExpandedLIA={showExpandedLIA}
        setShowExpandedLIA={setShowExpandedLIA}
        liaPromptValue={liaPromptValue}
        setLiaPromptValue={setLiaPromptValue}
        handleAICommand={handleAICommand}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        viewMode={viewMode}
        setViewMode={setViewMode as any}
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
        {showSuperChat && (
          <>
          <div 
            className="flex-1 transition-colors motion-reduce:transition-none duration-300 pl-4 py-4 pr-0 min-w-0 max-w-[calc(100%-48px)]"
          >
            <div className="h-full flex flex-col">
              <ExpandedChatModal
                isOpen={true}
                onClose={() => {
                  setShowSuperChat(false)
                  setUserCollapsedLIA(true)
                }}
                initialMessage={liaPromptValue}
                initialMessages={liaMessages.map(msg => ({
                  id: msg.id,
                  role: msg.type === 'user' ? 'user' : 'assistant',
                  content: msg.content,
                  timestamp: new Date(msg.timestamp)
                }))}
                contextTitle="Análise de Candidatos"
                inline={true}
                mode="general"
                onReturnToLateral={returnToExpandedPrompt}
                hideModeButtons={true}
                onOrchestratedMessage={handleOrchestratedMessage}
              />
            </div>
          </div>

          <div className="flex-shrink-0 w-12 transition-colors motion-reduce:transition-none duration-300 py-4 pr-2">
            <div className="h-[calc(100vh-12rem)] flex flex-col items-center bg-lia-bg-primary border border-lia-border-subtle rounded-md py-3 gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowSuperChat(false)}
                className="h-8 w-8 p-0 rounded-md hover:bg-lia-bg-tertiary"
                title="Expandir visualização"
              >
                <ChevronRight className="w-4 h-4 text-lia-text-tertiary" />
              </Button>
              
              <div className="w-6 h-px bg-lia-interactive-active my-1" />
              
              <div className="flex flex-col items-center gap-1 py-2 cursor-pointer hover:bg-lia-bg-secondary rounded-md px-2 transition-colors motion-reduce:transition-none">
                <div className="w-6 h-6 rounded-full bg-wedo-orange flex items-center justify-center">
                  <span className="text-white text-micro font-bold">H</span>
                </div>
              </div>
              
              <div className="flex flex-col items-center gap-1 py-2 cursor-pointer hover:bg-lia-bg-secondary rounded-md px-2 transition-colors motion-reduce:transition-none">
                <div className="w-6 h-6 rounded-full bg-status-warning flex items-center justify-center">
                  <Brain className="w-3.5 h-3.5 text-white" />
                </div>
              </div>
              
              <div className="flex-1" />
              
              <div 
                className="flex flex-col items-center gap-1 py-3 cursor-pointer hover:bg-lia-bg-secondary rounded-md px-1 transition-colors motion-reduce:transition-none border-r-2 border-lia-btn-primary-bg dark:border-lia-border-medium"
                onClick={() => setShowSuperChat(false)}
              >
                <Users className="w-4 h-4 text-lia-text-secondary" />
                <span 
                  className="text-micro font-medium text-lia-text-secondary tracking-wide [writing-mode:vertical-rl] [text-orientation:mixed]"
                 aria-live="polite" aria-atomic="true">
                  Candidatos ({Object.values(candidatesData).flat().length})
                </span>
              </div>
            </div>
          </div>
        </>
        )}

        {showExpandedLIA && !showSuperChat && (
          <div className="flex-shrink-0 pl-4 py-4 pr-0" style={{ width: `${liaExpandedWidth}px` }}>
            <LiaChatShell
              mode="inline-left"
              contextChips={[
                { id: "rankear", label: "Rankear", prompt: "Rankear candidatos desta vaga", icon: <Star className="w-2.5 h-2.5" /> },
                { id: "comparar", label: "Comparar", prompt: "Comparar os melhores candidatos", icon: <Users className="w-2.5 h-2.5" /> },
                { id: "triagem", label: "Triagem", prompt: "Iniciar triagem dos candidatos pendentes", icon: <Brain className="w-2.5 h-2.5" /> },
              ]}
              onClose={() => { setShowExpandedLIA(false); setUserCollapsedLIA(true) }}
              width="100%"
              className="h-full"
            />
          </div>
        )}

        {viewMode === "kanban" && !showSuperChat && (
          <KanbanBoardSection state={state} />
        )}

        {viewMode === "table" && !showSuperChat && (
          <KanbanTableView
            showSuperChat={showSuperChat}
            showTableFiltersPanel={showTableFiltersPanel}
            onShowTableFiltersPanelChange={setShowTableFiltersPanel}
            dynamicStages={state.dynamicStages}
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
  )
}
