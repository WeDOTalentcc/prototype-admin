"use client"

import React from"react"
import { Button } from"@/components/ui/button"
import { Users, Loader2, Eye } from"lucide-react"
import { UnifiedCandidateTable } from"@/components/tables"
import type { TableCandidate } from"@/components/tables"
import { CandidatesLoadMoreFooter } from"./CandidatesLoadMoreFooter"
import type { Candidate } from"./types"
import type { TableColumn } from"./CandidateSearchResultsView.types"
import { useTranslations } from "next-intl"
import { FilteredNoContactModal, type DiscardedEnrichmentResult } from "./FilteredNoContactModal"
import type { DiscardedCandidate } from "./hooks/useCandidatesExecuteSearch"

export interface CandidatesTableAreaProps {
  sortedCandidates: Candidate[]
  selectedCandidatesForBatch: Set<string>
  isLoading: boolean
  error?: string | null
  onRetry?: () => void
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
  showSearchResults: boolean
  currentPage: number
  setCurrentPage: React.Dispatch<React.SetStateAction<number>>
  itemsPerPage: number
  getPaginatedCandidates: () => { total: number; totalPages: number }
  clearAllFilters: () => void
  displayedResultsCount: number
  isLoadingMore: boolean
  onLoadMore: () => void
  isEnrichingContacts?: boolean
  /**
   * Task #394: número de candidatos descartados pelo backend após tentativa
   * de enriquecimento Apify por continuarem sem email/telefone. Mostramos um
   * aviso para o usuário entender por que o total caiu.
   */
  filteredNoContact?: number
  /**
   * Task #399: número de candidatos que passaram pelo hook de enriquecimento
   * Apify nesta busca. Mostramos um banner para o usuário entender o custo
   * real (em chamadas Apify) da busca.
   */
  enrichmentAttempted?: number
  /**
   * Task #400: lista de candidatos descartados (id, nome, linkedin etc.) para
   * o usuário inspecionar e exportar via CSV — clicando no aviso.
   */
  filteredCandidates?: DiscardedCandidate[]
  /**
   * Task #402: callback executado quando o usuário re-enriquece um candidato
   * descartado e o Apify finalmente devolve email/telefone. O parent deve
   * adicionar o candidato à lista principal de resultados e removê-lo do
   * conjunto de descartados.
   */
  onDiscardedCandidateEnriched?: (result: DiscardedEnrichmentResult) => void
}

export function CandidatesTableArea({
  sortedCandidates,
  selectedCandidatesForBatch,
  isLoading,
  error,
  onRetry,
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
  isEnrichingContacts,
  filteredNoContact,
  enrichmentAttempted,
  filteredCandidates,
  onDiscardedCandidateEnriched,
}: CandidatesTableAreaProps) {
  const t = useTranslations('candidates')
  const [showFilteredModal, setShowFilteredModal] = React.useState(false)
  const discardedList = filteredCandidates ?? []
  return (
    <div data-testid="candidates-table-area" className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-md transition-colors motion-reduce:transition-none duration-300 flex-1 min-w-0 h-full">
      <div className="h-full flex flex-col overflow-hidden">
          <div ref={tableContainerRef} className="flex-1 relative overflow-auto flex flex-col">
            {isLoading && (
              <div
                className="flex items-center justify-center h-full absolute inset-0 z-20 bg-lia-bg-primary dark:bg-lia-bg-primary"
                role="status"
                aria-live="polite"
                aria-label={t('table.loadingAriaLabel')}
              >
                <div className="text-center" role="status" aria-live="polite" aria-label={t('table.loadingAriaLabel')}>
                  <div
                    className="animate-spin motion-reduce:animate-none rounded-full h-10 w-10 border-b-2 border-wedo-cyan/30 mx-auto mb-4"
                    role="status"
                    aria-live="polite"
                    aria-label={t('table.loadingAriaLabel')}
                  ></div>
                  <p className="text-lia-text-primary text-sm" aria-live="polite" aria-atomic="true">
                    {t('table.loadingCandidates')}
                  </p>
                </div>
              </div>
            )}

            {isEnrichingContacts && (
              <div className="flex items-center gap-2 px-4 py-2 bg-status-info/10 border border-status-info/20 rounded-lg mx-2 mt-2">
                <Loader2 className="h-4 w-4 animate-spin text-status-info" />
                <span className="text-sm text-status-info font-medium">{t('table.enrichingContacts')}</span>
              </div>
            )}

            {!isEnrichingContacts && filteredNoContact !== undefined && filteredNoContact > 0 && (
              <div
                data-testid="filtered-no-contact-banner"
                className="flex items-center justify-between gap-2 px-4 py-2 bg-status-warning/10 border border-status-warning/20 rounded-lg mx-2 mt-2"
                role="status"
                aria-live="polite"
              >
                <span className="text-sm text-status-warning font-medium">
                  {t('table.filteredNoContact', { count: filteredNoContact })}
                </span>
                {discardedList.length > 0 && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="h-7 shrink-0"
                    onClick={() => setShowFilteredModal(true)}
                    data-testid="filtered-no-contact-view-button"
                  >
                    <Eye className="h-3.5 w-3.5 mr-1" />
                    {t('table.viewDiscarded')}
                  </Button>
                )}
              </div>
            )}

            {!isEnrichingContacts && enrichmentAttempted !== undefined && enrichmentAttempted > 0 && (
              <div
                data-testid="enrichment-attempted-banner"
                className="flex items-center gap-2 px-4 py-2 bg-status-info/10 border border-status-info/20 rounded-lg mx-2 mt-2"
                role="status"
                aria-live="polite"
              >
                <span className="text-sm text-status-info font-medium">
                  {t('table.enrichmentAttempted', { count: enrichmentAttempted, total: sortedCandidates.length })}
                </span>
              </div>
            )}

            <FilteredNoContactModal
              open={showFilteredModal}
              onOpenChange={setShowFilteredModal}
              candidates={discardedList}
              onCandidateEnriched={onDiscardedCandidateEnriched}
            />

            {!isLoading && sortedCandidates.length > 0 && (
              <UnifiedCandidateTable
                candidates={visibleCandidates as unknown as TableCandidate[]}
                columns={visibleTableColumns.map((col) => ({
                  id: col.id,
                  label: col.label,
                  visible: col.visible,
                  sortable: true,
                  width: columnWidths[col.id] || 120,
                  minWidth: 80,
                  align: col.id === 'name' ? 'left' as const : 'center' as const,
                  order: col.order,
                  isGlobalSearch: col.isGlobalSearch
                }))}
                selectedIds={selectedCandidatesForBatch}
                pinnedIds={pinnedCandidates}
                favoriteIds={favorites}
                sortConfig={(showSearchResults || !sortBy) ? undefined : { field: sortBy, direction: sortOrder }}
                isLoading={false}
                emptyMessage={t('table.emptyMessage')}
                showCheckboxes={true}
                showPagination={false}
                enableColumnResize={true}
                enableColumnReorder={true}
                enableVirtualScroll={visibleCandidates.length > 50}
                onColumnResize={(columnId, newWidth) => {
                  setColumnWidths(prev => ({ ...prev, [columnId]: newWidth }))
                }}
                onColumnReorder={(reorderedColumns) => {
                  setTableColumns((prev: TableColumn[]) => prev.map((col: TableColumn) => {
                    const reordered = reorderedColumns.find(r => r.id === col.id)
                    return reordered ? { ...col, order: reordered.order ?? col.order } : col
                  }))
                }}
                onCandidateClick={(candidate) => onCandidateClick(candidate as unknown as Candidate)}
                onSelectionChange={(ids) => setSelectedCandidatesForBatch(ids)}
                onSortChange={(config) => {
                  setSortBy(config.field)
                  setSortOrder(config.direction)
                }}
                onTogglePin={(candidateId) => onTogglePin(candidateId)}
                onToggleFavorite={(candidateId: string) => onToggleFavorite(candidateId)}
                renderCustomCell={(candidate, columnId) => renderCellValue(candidate as unknown as Candidate, columnId)}
              />
            )}

            {!isLoading && !showSearchResults && getPaginatedCandidates().totalPages > 1 && (
              <div className="bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl p-3 mt-2">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-lia-text-primary">
                    {t('table.showingPagination', { start: ((currentPage - 1) * itemsPerPage) + 1, end: Math.min(currentPage * itemsPerPage, getPaginatedCandidates().total), total: getPaginatedCandidates().total })}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={() => setCurrentPage(1)} disabled={currentPage === 1} className="h-8">
                      {t('table.first')}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                      className="h-8"
                    >
                      {t('table.previous')}
                    </Button>

                    <div className="flex items-center gap-1">
                      {Array.from({ length: getPaginatedCandidates().totalPages }, (_, i) => i + 1)
                        .filter(page =>
                          page === 1 ||
                          page === getPaginatedCandidates().totalPages ||
                          (page >= currentPage - 1 && page <= currentPage + 1)
                        )
                        .map((page, index, array) => (
                          <React.Fragment key={page}>
                            {index > 0 && page - array[index - 1] > 1 && (
                              <span className="px-2 text-lia-text-primary">...</span>
                            )}
                            <Button
                              variant={currentPage === page ? 'primary' : 'outline'}
                              size="sm"
                              onClick={() => setCurrentPage(page)}
                              className="h-8 w-8 p-0"
                            >
                              {page}
                            </Button>
                          </React.Fragment>
                        ))
                      }
                    </div>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(prev => Math.min(getPaginatedCandidates().totalPages, prev + 1))}
                      disabled={currentPage === getPaginatedCandidates().totalPages}
                      className="h-8"
                    >
                      {t('table.next')}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(getPaginatedCandidates().totalPages)}
                      disabled={currentPage === getPaginatedCandidates().totalPages}
                      className="h-8"
                    >
                      {t('table.last')}
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {!isLoading && sortedCandidates.length === 0 && error && (
              <div className="bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl p-8 text-center">
                <Users className="w-12 h-12 text-status-error mx-auto mb-4" />
                <h3 className="text-lg font-medium text-lia-text-primary mb-2">
                  {t('table.errorTitle')}
                </h3>
                <p className="text-lia-text-primary mb-4">
                  {error}
                </p>
                {onRetry && (
                  <Button variant="outline" onClick={onRetry}>
                    {t('table.tryAgain')}
                  </Button>
                )}
              </div>
            )}

            {!isLoading && sortedCandidates.length === 0 && !error && (
              <div className="bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl p-8 text-center">
                <Users className="w-12 h-12 text-lia-text-primary mx-auto mb-4" />
                <h3 className="text-lg font-medium text-lia-text-primary mb-2">
                  {t('table.emptyTitle')}
                </h3>
                <p className="text-lia-text-primary mb-4">
                  {t('table.emptyDescription')}
                </p>
                <Button variant="outline" onClick={clearAllFilters}>
                  {t('table.clearFilters')}
                </Button>
              </div>
            )}
            <div className="flex-1" aria-hidden="true" />

            <CandidatesLoadMoreFooter
              showSearchResults={showSearchResults}
              displayedResultsCount={displayedResultsCount}
              sortedCandidatesLength={sortedCandidates.length}
              isLoadingMore={isLoadingMore}
              onLoadMore={onLoadMore}
            />
          </div>
      </div>
    </div>
  )
}
