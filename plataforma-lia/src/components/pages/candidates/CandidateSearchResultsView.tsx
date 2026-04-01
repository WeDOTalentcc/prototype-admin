"use client"

import React, { useRef } from "react"
import { SearchResultsHeader } from "./SearchResultsHeader"
import { CrossTabFilterBanner } from "./CrossTabFilterBanner"
import { ViewingListBanner } from "./ViewingListBanner"
import { ColumnConfigSidebar } from "./ColumnConfigSidebar"
import { ContextualActionsBanner } from "@/components/contextual-actions-banner"
import { LIASearchSidebar } from "./LIASearchSidebar"
import { CandidatesFilterPanel } from "./CandidatesFilterPanel"
import { CompactLIAPrompt } from "./CompactLIAPrompt"
import { SearchControlsBar } from "./SearchControlsBar"
import { ActiveFiltersBadge } from "./ActiveFiltersBadge"
import { CandidatesTableArea } from "./CandidatesTableArea"
import { CandidatePreviewSidePanel } from "./CandidatePreviewSidePanel"
import type { Candidate } from "./types"
import type { TableFilters } from "@/hooks/use-candidate-filters"
import type { SearchFilters } from "@/components/search/advanced-filters-modal"
import type { ParsedEntities, SearchMode, SearchMetadata } from "@/components/search/smart-search-input"
import type { SearchAnalytics } from "@/components/proactive-insight-card"
import type { CalibrationCandidate } from "@/components/calibration-card"
import type { SearchTab, ChatMessage, TableColumn } from "./CandidateSearchResultsView.types"

export interface CandidateSearchResultsViewProps {
  // Search query state
  lastSearchQuery: string
  lastSearchEntities: ParsedEntities | null
  // Back / modal openers
  onBack: () => void
  onOpenEditQueryModal: (value: string) => void
  onOpenAdvancedSearch: () => void
  // Contextual actions banner
  selectedCandidatesForBatch: Set<string>
  selectedPearchCount: number
  deselectAllCandidates: () => void
  onAddToVacancy: () => void
  onAddToList: () => void
  isAddingToList: boolean
  candidates: Candidate[]
  onShareSearch: () => void
  onBulkEmail: () => void
  onBulkWSIScreening: () => void
  onToggleFavoriteBatch: () => void
  onHideBatch: () => void
  onSaveToLocalBase: () => void
  isSavingToBase: boolean
  // Cross-tab banner
  showCrossTabBanner: boolean
  crossTabFilter: Record<string, unknown>
  clearCrossTabFilter: () => void
  // Viewing list banner
  viewingList: { id: string; name: string; color?: string } | null
  setViewingList: (value: null) => void
  setShowSearchResults: (value: boolean) => void
  setSearchTerm: (value: string) => void
  setLastSearchQuery: (value: string) => void
  setActiveTab: (tab: string) => void
  // Compact LIA prompt
  showExpandedLIA: boolean
  isLIAThinking: boolean
  liaPromptValue: string
  setLiaPromptValue: (value: string) => void
  setShowExpandedLIA: (value: boolean) => void
  onAICommand: (cmd: string) => void
  // Controls bar
  searchSortBy: string
  setSearchSortBy: (value: string) => void
  sortedCandidates: Candidate[]
  selectAllCandidates: () => void
  showTableFiltersPanel: boolean
  setShowTableFiltersPanel: (value: boolean) => void
  getActiveTableFiltersCount: () => number
  showColumnConfig: boolean
  onToggleColumnConfig: () => void
  tableColumns: TableColumn[]
  // Active filters badge
  quickFilters: Set<string>
  searchTerm: string
  getActiveAdvancedFiltersCount: () => number
  // LIA Sidebar
  isLiaSuperChat: boolean
  setIsLiaSuperChat: (value: boolean) => void
  liaWidth: number
  setLiaWidth: (value: number) => void
  isResizingLIA: boolean
  setIsResizingLIA: (value: boolean) => void
  activeSearchTab: SearchTab
  setActiveSearchTab: (tab: SearchTab) => void
  chatMessages: ChatMessage[]
  setChatMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>
  searchResults: {
    local: Candidate[]
    global: Candidate[]
    localCount: number
    globalCount: number
    query: string
    isLoading: boolean
    showGlobalResults: boolean
    globalDismissed: boolean
  }
  setSearchResults: React.Dispatch<React.SetStateAction<{
    local: Candidate[]
    global: Candidate[]
    localCount: number
    globalCount: number
    query: string
    isLoading: boolean
    showGlobalResults: boolean
    globalDismissed: boolean
  }>>
  currentSearchSource: string
  searchSource: string
  pearchSearchOptions: {
    searchType: 'fast' | 'pro'
    limit: number
    showEmails: boolean
    showPhoneNumbers: boolean
    highFreshness: boolean
    requireEmails: boolean
    requirePhoneNumbers: boolean
  }
  activeSearchFilters: SearchFilters
  setActiveSearchFilters: React.Dispatch<React.SetStateAction<SearchFilters>>
  isCreatingArchetype: boolean
  setIsCreatingArchetype: (value: boolean) => void
  archetypeCreationStep: 'initial' | 'input' | 'extracting' | 'review' | 'saving'
  setArchetypeCreationStep: (step: 'initial' | 'input' | 'extracting' | 'review' | 'saving') => void
  setNewArchetypeData: React.Dispatch<React.SetStateAction<Record<string, unknown>>>
  setShowSaveAsArchetypeModal: (value: boolean) => void
  setShowGlobalExpansionConfirm: (value: boolean) => void
  setCandidates: React.Dispatch<React.SetStateAction<Candidate[]>>
  setHasSearchResults: (value: boolean) => void
  setSearchResultsCount: (value: number) => void
  setLocalResultsCount: (value: number) => void
  setPearchResultsCount: (value: number) => void
  setDisplayedResultsCount: (value: number) => void
  onLIAChatMessage: (msg: string) => void
  onQuickAction: (action: Record<string, unknown>) => void
  onCalibrationLike: (candidate: CalibrationCandidate) => void
  onCalibrationDislike: (candidate: CalibrationCandidate) => void
  setUserCollapsedLIA: (value: boolean) => void
  // Filters panel
  tableFilters: TableFilters
  setTableFilters: React.Dispatch<React.SetStateAction<TableFilters>>
  newSoftSkillFilter: string
  setNewSoftSkillFilter: (value: string) => void
  newCertificationFilter: string
  setNewCertificationFilter: (value: string) => void
  toggleTableFilter: (category: keyof TableFilters, value: string) => void
  clearAllTableFilters: () => void
  // Table
  isLoading: boolean
  visibleCandidates: Candidate[]
  visibleTableColumns: TableColumn[]
  columnWidths: Record<string, number>
  setColumnWidths: React.Dispatch<React.SetStateAction<Record<string, number>>>
  setTableColumns: React.Dispatch<React.SetStateAction<TableColumn[]>>
  pinnedCandidates: Set<string>
  favorites: Set<string>
  sortBy: string
  sortOrder: 'asc' | 'desc'
  setSortBy: (value: string) => void
  setSortOrder: (value: 'asc' | 'desc') => void
  setSelectedCandidatesForBatch: React.Dispatch<React.SetStateAction<Set<string>>>
  onCandidateClick: (candidate: Candidate) => void
  onTogglePin: (id: string) => void
  onToggleFavorite: (id: string) => void
  renderCellValue: (candidate: Candidate, columnId: string) => React.ReactNode
  tableContainerRef: React.RefObject<HTMLDivElement>
  // Pagination
  showSearchResults: boolean
  currentPage: number
  setCurrentPage: React.Dispatch<React.SetStateAction<number>>
  itemsPerPage: number
  getPaginatedCandidates: () => { total: number; totalPages: number }
  clearAllFilters: () => void
  // Load more
  displayedResultsCount: number
  isLoadingMore: boolean
  onLoadMore: () => void
  // Column config
  columnSearchTerm: string
  setColumnSearchTerm: (value: string) => void
  setShowColumnConfig: (value: boolean) => void
  // Candidate preview
  showCandidatePreview: boolean
  previewCandidate: Candidate | null
  previewWidth: number
  onPreviewResize: (e: React.MouseEvent) => void
  isPreviewMaximized: boolean
  onCloseCandidatePreview: () => void
  onTogglePreviewMaximize: () => void
  onCandidatePageOpen: (candidate: Candidate) => void
  setSelectedCandidateForAction: (candidate: Candidate) => void
  setShowScheduleModal: (value: boolean) => void
  onStartWSITextScreening: (candidate: Candidate) => void
  onSendEmail: (candidate: Candidate) => void
  onSendWhatsApp: (candidate: Candidate) => void
  onSendTriagem: (candidate: Candidate) => void
  onSendAgendamento: (candidate: Candidate) => void
  onSendFeedback: (candidate: Candidate) => void
  setPreviewCandidate: (candidate: Candidate) => void
  // Share search helpers
  setShareSearchCandidates: React.Dispatch<React.SetStateAction<Array<{ id: string; name: string; email?: string; avatar_url?: string; current_title?: string; linkedin_url?: string }>>>
  setShareSearchTitle: (value: string) => void
  setShowShareSearchModal: (value: boolean) => void
  // Toast
  toast: (opts: { title: string; description?: string; variant?: string }) => void
  // Talent funnel
  talentFunnel: {
    toggleFavoriteCandidate: (id: string) => void
    hideCandidate: (id: string) => void
  }
  // Edit query modal
  setEditQueryValue: (value: string) => void
  setShowEditQueryModal: (value: boolean) => void
  setShowAddToVacancyModal: (value: boolean) => void
  // Add to list modal
  setShowAddToListModal?: (value: boolean) => void
}

export function CandidateSearchResultsView({
  lastSearchQuery,
  lastSearchEntities,
  onBack,
  onOpenEditQueryModal,
  onOpenAdvancedSearch,
  selectedCandidatesForBatch,
  selectedPearchCount,
  deselectAllCandidates,
  onAddToVacancy,
  onAddToList,
  isAddingToList,
  candidates,
  onShareSearch,
  onBulkEmail,
  onBulkWSIScreening,
  onToggleFavoriteBatch,
  onHideBatch,
  onSaveToLocalBase,
  isSavingToBase,
  showCrossTabBanner,
  crossTabFilter,
  clearCrossTabFilter,
  viewingList,
  setViewingList,
  setShowSearchResults,
  setSearchTerm,
  setLastSearchQuery,
  setActiveTab,
  showExpandedLIA,
  isLIAThinking,
  liaPromptValue,
  setLiaPromptValue,
  setShowExpandedLIA,
  onAICommand,
  searchSortBy,
  setSearchSortBy,
  sortedCandidates,
  selectAllCandidates,
  showTableFiltersPanel,
  setShowTableFiltersPanel,
  getActiveTableFiltersCount,
  showColumnConfig,
  onToggleColumnConfig,
  tableColumns,
  quickFilters,
  searchTerm,
  getActiveAdvancedFiltersCount,
  isLiaSuperChat,
  setIsLiaSuperChat,
  liaWidth,
  setLiaWidth,
  isResizingLIA,
  setIsResizingLIA,
  activeSearchTab,
  setActiveSearchTab,
  chatMessages,
  setChatMessages,
  searchResults,
  setSearchResults,
  currentSearchSource,
  searchSource,
  pearchSearchOptions,
  activeSearchFilters,
  setActiveSearchFilters,
  isCreatingArchetype,
  setIsCreatingArchetype,
  archetypeCreationStep,
  setArchetypeCreationStep,
  setNewArchetypeData,
  setShowSaveAsArchetypeModal,
  setShowGlobalExpansionConfirm,
  setCandidates,
  setHasSearchResults,
  setSearchResultsCount,
  setLocalResultsCount,
  setPearchResultsCount,
  setDisplayedResultsCount,
  onLIAChatMessage,
  onQuickAction,
  onCalibrationLike,
  onCalibrationDislike,
  setUserCollapsedLIA,
  tableFilters,
  setTableFilters,
  newSoftSkillFilter,
  setNewSoftSkillFilter,
  newCertificationFilter,
  setNewCertificationFilter,
  toggleTableFilter,
  clearAllTableFilters,
  isLoading,
  visibleCandidates,
  visibleTableColumns,
  columnWidths,
  setColumnWidths,
  setTableColumns,
  pinnedCandidates,
  favorites,
  sortBy,
  sortOrder,
  setSortBy,
  setSortOrder,
  setSelectedCandidatesForBatch,
  onCandidateClick,
  onTogglePin,
  onToggleFavorite,
  renderCellValue,
  tableContainerRef,
  showSearchResults,
  currentPage,
  setCurrentPage,
  itemsPerPage,
  getPaginatedCandidates,
  clearAllFilters,
  displayedResultsCount,
  isLoadingMore,
  onLoadMore,
  columnSearchTerm,
  setColumnSearchTerm,
  setShowColumnConfig,
  showCandidatePreview,
  previewCandidate,
  previewWidth,
  onPreviewResize,
  isPreviewMaximized,
  onCloseCandidatePreview,
  onTogglePreviewMaximize,
  onCandidatePageOpen,
  setSelectedCandidateForAction,
  setShowScheduleModal,
  onStartWSITextScreening,
  onSendEmail,
  onSendWhatsApp,
  onSendTriagem,
  onSendAgendamento,
  onSendFeedback,
  setPreviewCandidate,
  setShareSearchCandidates,
  setShareSearchTitle,
  setShowShareSearchModal,
  toast,
  talentFunnel,
  setEditQueryValue,
  setShowEditQueryModal,
  setShowAddToVacancyModal,
}: CandidateSearchResultsViewProps) {
  const chatScrollRef = useRef<HTMLDivElement>(null)

  return (
    <div className="flex flex-col h-[calc(100vh-9rem)] gap-2">
      {/* Header com query da busca e opções de edição */}
      <SearchResultsHeader
        lastSearchQuery={lastSearchQuery}
        lastSearchEntities={lastSearchEntities}
        onBack={onBack}
        onOpenEditQueryModal={(value) => {
          setEditQueryValue(value)
          setShowEditQueryModal(true)
        }}
        onOpenAdvancedSearch={onOpenAdvancedSearch}
      />

      {/* Contextual Actions Banner - Ações para candidatos selecionados */}
      <ContextualActionsBanner
        selectedCount={selectedCandidatesForBatch.size}
        pearchCount={selectedPearchCount}
        onDeselectAll={deselectAllCandidates}
        onAddToVacancy={() => setShowAddToVacancyModal(true)}
        onAddToList={onAddToList}
        isAddingToList={isAddingToList}
        onShareSearch={() => {
          const selectedList = candidates.filter(c => selectedCandidatesForBatch.has(c.id))
          const searchTitle = lastSearchQuery || `Busca - ${new Date().toLocaleDateString('pt-BR')}`
          setShareSearchCandidates(selectedList.map(c => ({
            id: c.id,
            name: c.name,
            email: c.email,
            avatar_url: c.avatar,
            current_title: c.position,
            linkedin_url: c.linkedin
          })))
          setShareSearchTitle(searchTitle)
          setShowShareSearchModal(true)
        }}
        onSendMessage={onBulkEmail}
        onWSIScreening={onBulkWSIScreening}
        onToggleFavorite={() => {
          selectedCandidatesForBatch.forEach(id => talentFunnel.toggleFavoriteCandidate(id))
          toast({
            title: "Favoritos atualizados",
            description: `${selectedCandidatesForBatch.size} candidato(s) adicionado(s) aos favoritos`
          })
        }}
        onHide={() => {
          selectedCandidatesForBatch.forEach(id => talentFunnel.hideCandidate(id))
          toast({
            title: "Candidatos ocultos",
            description: `${selectedCandidatesForBatch.size} candidato(s) oculto(s) da pesquisa`
          })
          deselectAllCandidates()
        }}
        onSaveToLocalBase={onSaveToLocalBase}
        isSavingToBase={isSavingToBase}
      />

      {/* Banner Cross-Tab Filter */}
      <CrossTabFilterBanner
        showCrossTabBanner={showCrossTabBanner}
        crossTabFilter={crossTabFilter}
        clearCrossTabFilter={clearCrossTabFilter}
      />

      {/* Banner Visualizando Lista */}
      <ViewingListBanner
        viewingList={viewingList}
        candidates={candidates}
        setViewingList={setViewingList}
        setShowSearchResults={setShowSearchResults}
        setSearchTerm={setSearchTerm}
        setLastSearchQuery={setLastSearchQuery}
        setActiveTab={setActiveTab}
      />

      {/* Toolbar Compacto - Prompt LIA + Controles */}
      {!showExpandedLIA && (
        <div className="flex items-center justify-between gap-4 mb-1 mt-1">
          <CompactLIAPrompt
            isLIAThinking={isLIAThinking}
            liaPromptValue={liaPromptValue}
            setLiaPromptValue={setLiaPromptValue}
            setShowExpandedLIA={setShowExpandedLIA}
            onAICommand={onAICommand}
          />

          <SearchControlsBar
            selectedCandidatesForBatch={selectedCandidatesForBatch}
            searchSortBy={searchSortBy}
            sortedCandidatesLength={sortedCandidates.length}
            selectAllCandidates={selectAllCandidates}
            showTableFiltersPanel={showTableFiltersPanel}
            setShowTableFiltersPanel={setShowTableFiltersPanel}
            getActiveTableFiltersCount={getActiveTableFiltersCount}
            showColumnConfig={showColumnConfig}
            onToggleColumnConfig={onToggleColumnConfig}
            tableColumns={tableColumns}
          />
        </div>
      )}

      {/* Badge de Filtros Ativos */}
      <ActiveFiltersBadge
        quickFilters={quickFilters}
        searchTerm={searchTerm}
        getActiveAdvancedFiltersCount={getActiveAdvancedFiltersCount}
        selectedCandidatesForBatch={selectedCandidatesForBatch}
        deselectAllCandidates={deselectAllCandidates}
      />

      {/* Results Layout with Sidebars */}
      <div className="flex gap-4 overflow-hidden transition-colors motion-reduce:transition-none duration-300 flex-1 min-h-0 w-full">
        {/* LIA Sidebar Expandida */}
        {showExpandedLIA && (
          <LIASearchSidebar
            isLiaSuperChat={isLiaSuperChat}
            setIsLiaSuperChat={setIsLiaSuperChat}
            liaWidth={liaWidth}
            setLiaWidth={setLiaWidth}
            isResizingLIA={isResizingLIA}
            setIsResizingLIA={setIsResizingLIA}
            // @ts-ignore TODO: fix type
            activeSearchTab={activeSearchTab}
            // @ts-ignore TODO: fix type
            setActiveSearchTab={setActiveSearchTab}
            liaPromptValue={liaPromptValue}
            // @ts-ignore TODO: fix type
            setLiaPromptValue={setLiaPromptValue}
            chatMessages={chatMessages}
            setChatMessages={setChatMessages}
            searchResults={searchResults}
            // @ts-ignore TODO: fix type
            setSearchResults={setSearchResults}
            currentSearchSource={currentSearchSource}
            searchSource={searchSource}
            pearchSearchOptions={pearchSearchOptions}
            // @ts-ignore TODO: fix type
            activeSearchFilters={activeSearchFilters}
            setActiveSearchFilters={setActiveSearchFilters}
            showTableFiltersPanel={showTableFiltersPanel}
            setShowTableFiltersPanel={setShowTableFiltersPanel}
            isCreatingArchetype={isCreatingArchetype}
            setIsCreatingArchetype={setIsCreatingArchetype}
            archetypeCreationStep={archetypeCreationStep}
            // @ts-ignore TODO: fix type
            setArchetypeCreationStep={setArchetypeCreationStep}
            setNewArchetypeData={setNewArchetypeData}
            setShowSaveAsArchetypeModal={setShowSaveAsArchetypeModal}
            setShowGlobalExpansionConfirm={setShowGlobalExpansionConfirm}
            selectedCandidatesForBatch={selectedCandidatesForBatch}
            // @ts-ignore TODO: fix type
            setCandidates={setCandidates}
            setHasSearchResults={setHasSearchResults}
            setSearchResultsCount={setSearchResultsCount}
            setLocalResultsCount={setLocalResultsCount}
            setPearchResultsCount={setPearchResultsCount}
            setShowSearchResults={setShowSearchResults}
            setDisplayedResultsCount={setDisplayedResultsCount}
            onLIAChatMessage={onLIAChatMessage}
            onAICommand={onAICommand}
            // @ts-ignore TODO: fix type
            onQuickAction={onQuickAction}
            // @ts-ignore TODO: fix type
            onCalibrationLike={onCalibrationLike}
            // @ts-ignore TODO: fix type
            onCalibrationDislike={onCalibrationDislike}
            // @ts-ignore TODO: fix type
            chatScrollRef={chatScrollRef}
            onClose={() => {
              setShowExpandedLIA(false)
              setUserCollapsedLIA(true)
              setIsLiaSuperChat(false)
            }}
          />
        )}

        {/* Filtros da Tabela de Resultados */}
        {showTableFiltersPanel && (
          <CandidatesFilterPanel
            tableFilters={tableFilters}
            setTableFilters={setTableFilters}
            searchSortBy={searchSortBy}
            onSortChange={setSearchSortBy}
            newSoftSkillFilter={newSoftSkillFilter}
            setNewSoftSkillFilter={setNewSoftSkillFilter}
            newCertificationFilter={newCertificationFilter}
            setNewCertificationFilter={setNewCertificationFilter}
            activeFiltersCount={getActiveTableFiltersCount()}
            onToggleFilter={toggleTableFilter}
            onClearAll={clearAllTableFilters}
            onClose={() => setShowTableFiltersPanel(false)}
          />
        )}

        {/* Main Content Area - Candidatos Table */}
        <CandidatesTableArea
          isLiaSuperChat={isLiaSuperChat}
          setIsLiaSuperChat={setIsLiaSuperChat}
          sortedCandidates={sortedCandidates}
          selectedCandidatesForBatch={selectedCandidatesForBatch}
          isLoading={isLoading}
          visibleCandidates={visibleCandidates}
          visibleTableColumns={visibleTableColumns}
          columnWidths={columnWidths}
          setColumnWidths={setColumnWidths}
          setTableColumns={setTableColumns}
          pinnedCandidates={pinnedCandidates}
          favorites={favorites}
          sortBy={sortBy}
          sortOrder={sortOrder}
          setSortBy={setSortBy}
          setSortOrder={setSortOrder}
          setSelectedCandidatesForBatch={setSelectedCandidatesForBatch}
          onCandidateClick={onCandidateClick}
          onTogglePin={onTogglePin}
          onToggleFavorite={onToggleFavorite}
          renderCellValue={renderCellValue}
          tableContainerRef={tableContainerRef}
          showSearchResults={showSearchResults}
          currentPage={currentPage}
          setCurrentPage={setCurrentPage}
          itemsPerPage={itemsPerPage}
          getPaginatedCandidates={getPaginatedCandidates}
          clearAllFilters={clearAllFilters}
          displayedResultsCount={displayedResultsCount}
          isLoadingMore={isLoadingMore}
          onLoadMore={onLoadMore}
        />

        {/* Column Configuration Sidebar */}
        <ColumnConfigSidebar
          showColumnConfig={showColumnConfig}
          tableColumns={tableColumns}
          setTableColumns={setTableColumns}
          columnSearchTerm={columnSearchTerm}
          setColumnSearchTerm={setColumnSearchTerm}
          setShowColumnConfig={setShowColumnConfig}
        />

        {/* Candidate Preview - Painel lateral direito */}
        <CandidatePreviewSidePanel
          showCandidatePreview={showCandidatePreview}
          previewCandidate={previewCandidate}
          previewWidth={previewWidth}
          onPreviewResize={onPreviewResize}
          isPreviewMaximized={isPreviewMaximized}
          onCloseCandidatePreview={onCloseCandidatePreview}
          onTogglePreviewMaximize={onTogglePreviewMaximize}
          sortedCandidates={sortedCandidates}
          onCandidatePageOpen={onCandidatePageOpen}
          setSelectedCandidateForAction={setSelectedCandidateForAction}
          setShowScheduleModal={setShowScheduleModal}
          setSelectedCandidatesForBatch={setSelectedCandidatesForBatch}
          setShowAddToVacancyModal={setShowAddToVacancyModal}
          onToggleFavorite={onToggleFavorite}
          favorites={favorites}
          onStartWSITextScreening={onStartWSITextScreening}
          onSendEmail={onSendEmail}
          onSendWhatsApp={onSendWhatsApp}
          onSendTriagem={onSendTriagem}
          onSendAgendamento={onSendAgendamento}
          onSendFeedback={onSendFeedback}
          setPreviewCandidate={setPreviewCandidate}
        />
      </div>
    </div>
  )
}
