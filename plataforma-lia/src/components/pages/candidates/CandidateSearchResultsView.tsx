"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { SearchResultsHeader } from "./SearchResultsHeader"
import { CrossTabFilterBanner } from "./CrossTabFilterBanner"
import { ViewingListBanner } from "./ViewingListBanner"
import { ColumnConfigSidebar } from "./ColumnConfigSidebar"
import { BulkActionsBar } from "@/components/ui/bulk-actions-bar"
import { Briefcase, List, Share2, Mail, ClipboardCheck, Star, EyeOff, Database } from "lucide-react"
import { CandidatesFilterPanel } from "./CandidatesFilterPanel"
import { SearchControlsBar } from "./SearchControlsBar"
import { ActiveFiltersBadge } from "./ActiveFiltersBadge"
import { CandidatesTableArea } from "./CandidatesTableArea"
import { CandidatePreviewSidePanel } from "./CandidatePreviewSidePanel"
import type { Candidate } from "./types"
import type { TableFilters } from "@/hooks/candidates/use-candidate-filters"
import type { ParsedEntities } from "@/components/search/smart-search-input"
import type { TableColumn } from "./CandidateSearchResultsView.types"
import { toast } from "sonner"

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
  // Filters panel
  tableFilters: TableFilters
  setTableFilters: React.Dispatch<React.SetStateAction<TableFilters>>
  newSoftSkillFilter: string
  setNewSoftSkillFilter: (value: string) => void
  newCertificationFilter: string
  setNewCertificationFilter: (value: string) => void
  toggleTableFilter: (category: keyof TableFilters, value: string) => void
  clearAllTableFilters: () => void
  onReSearchWithFilters?: () => void
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
  isEnrichingContacts?: boolean
  filteredNoContact?: number
  enrichmentAttempted?: number
  filteredCandidates?: import('./hooks/useCandidatesExecuteSearch').DiscardedCandidate[]
  onDiscardedCandidateEnriched?: (result: import('./FilteredNoContactModal').DiscardedEnrichmentResult) => void
  error?: string | null
  onRetry?: () => void
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
  tableFilters,
  setTableFilters,
  newSoftSkillFilter,
  setNewSoftSkillFilter,
  newCertificationFilter,
  setNewCertificationFilter,
  toggleTableFilter,
  clearAllTableFilters,
  onReSearchWithFilters,
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
  talentFunnel,
  setEditQueryValue,
  setShowEditQueryModal,
  setShowAddToVacancyModal,
  isEnrichingContacts,
  filteredNoContact,
  enrichmentAttempted,
  filteredCandidates,
  onDiscardedCandidateEnriched,
  error,
  onRetry,
}: CandidateSearchResultsViewProps) {
  const t = useTranslations('candidates')

  return (
    <div data-testid="candidate-search-results-view" className="flex flex-col h-[calc(100vh-9rem)] gap-2">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0 flex-1">
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
        </div>

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

      <BulkActionsBar
        selectedCount={selectedCandidatesForBatch.size}
        onDeselectAll={deselectAllCandidates}
        className="mb-4"
        actions={[
          {
            id: 'add_to_vacancy',
            label: t('results.vacancy'),
            icon: <Briefcase className="w-3.5 h-3.5 text-lia-text-secondary" />,
            onClick: () => setShowAddToVacancyModal(true),
          },
          {
            id: 'add_to_list',
            label: isAddingToList ? t('results.importing') : t('results.list'),
            icon: <List className="w-3.5 h-3.5 text-lia-text-secondary" />,
            onClick: onAddToList,
            disabled: isAddingToList,
            loading: isAddingToList,
            loadingLabel: t('results.importing'),
          },
          {
            id: 'share_search',
            label: t('results.share'),
            icon: <Share2 className="w-3.5 h-3.5 text-lia-text-secondary" />,
            onClick: () => {
              const selectedList = candidates.filter(c => selectedCandidatesForBatch.has(c.id))
              const searchTitle = lastSearchQuery || t('results.searchTitle', { date: new Date().toLocaleDateString('pt-BR') })
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
            },
          },
          {
            id: 'send_message',
            label: t('results.message'),
            icon: <Mail className="w-3.5 h-3.5 text-lia-text-secondary" />,
            onClick: onBulkEmail,
          },
          {
            id: 'wsi_screening',
            label: t('results.wsiScreening'),
            icon: <ClipboardCheck className="w-3.5 h-3.5 text-lia-text-secondary" />,
            onClick: onBulkWSIScreening,
          },
          {
            id: 'favorites',
            label: t('results.favorites'),
            icon: <Star className="w-3.5 h-3.5 text-status-warning" />,
            onClick: () => {
              selectedCandidatesForBatch.forEach(id => talentFunnel.toggleFavoriteCandidate(id))
              toast.success(t('results.favoritesUpdated'), { description: t('results.favoritesUpdatedDesc', { count: selectedCandidatesForBatch.size }) })
            },
          },
          {
            id: 'hide',
            label: t('results.hide'),
            icon: <EyeOff className="w-3.5 h-3.5 text-lia-text-secondary" />,
            onClick: () => {
              selectedCandidatesForBatch.forEach(id => talentFunnel.hideCandidate(id))
              toast.success(t('results.candidatesHidden'), { description: t('results.candidatesHiddenDesc', { count: selectedCandidatesForBatch.size }) })
              deselectAllCandidates()
            },
          },
          {
            id: 'save_to_base',
            label: t('results.saveToBase', { count: selectedPearchCount }),
            icon: <Database className="w-3.5 h-3.5 text-lia-text-secondary" />,
            onClick: onSaveToLocalBase,
            disabled: isSavingToBase,
            loading: isSavingToBase,
            hidden: !(selectedPearchCount > 0),
          },
        ]}
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
            onReSearchWithFilters={onReSearchWithFilters}
            onClose={() => setShowTableFiltersPanel(false)}
          />
        )}

        {/* Main Content Area - Candidatos Table */}
        <CandidatesTableArea
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
          isEnrichingContacts={isEnrichingContacts}
          filteredNoContact={filteredNoContact}
          enrichmentAttempted={enrichmentAttempted}
          filteredCandidates={filteredCandidates}
          onDiscardedCandidateEnriched={onDiscardedCandidateEnriched}
          error={error}
          onRetry={onRetry}
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
