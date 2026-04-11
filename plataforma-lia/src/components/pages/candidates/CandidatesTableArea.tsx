"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Users, ChevronRight } from "lucide-react"
import { UnifiedCandidateTable } from "@/components/tables"
import type { TableCandidate } from "@/components/tables"
import { CandidatesLoadMoreFooter } from "./CandidatesLoadMoreFooter"
import type { Candidate } from "./types"
import type { TableColumn } from "./CandidateSearchResultsView.types"

export interface CandidatesTableAreaProps {
  isLiaSuperChat: boolean
  setIsLiaSuperChat: (value: boolean) => void
  sortedCandidates: Candidate[]
  selectedCandidatesForBatch: Set<string>
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
  showSearchResults: boolean
  currentPage: number
  setCurrentPage: React.Dispatch<React.SetStateAction<number>>
  itemsPerPage: number
  getPaginatedCandidates: () => { total: number; totalPages: number }
  clearAllFilters: () => void
  displayedResultsCount: number
  isLoadingMore: boolean
  onLoadMore: () => void
}

export function CandidatesTableArea({
  isLiaSuperChat,
  setIsLiaSuperChat,
  sortedCandidates,
  selectedCandidatesForBatch,
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
}: CandidatesTableAreaProps) {
  return (
    <div data-testid="candidates-table-area" className={`bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-md transition-colors motion-reduce:transition-none duration-300 ${
      isLiaSuperChat
        ? 'w-14 flex-shrink-0'
        : 'flex-1 min-w-0 h-full'
    }`}>
      {isLiaSuperChat ? (
        <div className="h-full flex flex-col items-center py-4 gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsLiaSuperChat(false)}
            className="h-10 w-10 p-0 rounded-xl hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
            title="Expandir tabela de candidatos"
          >
            <ChevronRight className="w-5 h-5 text-lia-text-primary" />
          </Button>

          <div className="flex flex-col items-center gap-2 text-lia-text-primary">
            <Users className="w-5 h-5" />
            <span
              className="text-xs font-medium"
              style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }}
              aria-live="polite"
              aria-atomic="true"
            >
              Candidatos ({sortedCandidates.length})
            </span>
          </div>

          {selectedCandidatesForBatch.size > 0 && (
            <Badge className="bg-lia-btn-primary-bg dark:bg-lia-bg-secondary text-white text-xs px-1.5 py-0.5">
              {selectedCandidatesForBatch.size}
            </Badge>
          )}
        </div>
      ) : (
        <div className="h-full flex flex-col overflow-hidden">
          <div ref={tableContainerRef} className="flex-1 relative overflow-auto">
            {isLoading && (
              <div
                className="flex items-center justify-center h-full absolute inset-0 z-20 bg-lia-bg-primary dark:bg-lia-bg-primary"
                role="status"
                aria-live="polite"
                aria-label="Carregando..."
              >
                <div className="text-center" role="status" aria-live="polite" aria-label="Carregando...">
                  <div
                    className="animate-spin motion-reduce:animate-none rounded-full h-10 w-10 border-b-2 border-wedo-cyan/30 mx-auto mb-4"
                    role="status"
                    aria-live="polite"
                    aria-label="Carregando..."
                  ></div>
                  <p className="text-lia-text-primary text-sm" aria-live="polite" aria-atomic="true">
                    Carregando candidatos...
                  </p>
                </div>
              </div>
            )}

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
                sortConfig={sortBy ? { field: sortBy, direction: sortOrder } : undefined}
                isLoading={false}
                emptyMessage="Nenhum candidato encontrado"
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
                    Mostrando {((currentPage - 1) * itemsPerPage) + 1} -{' '}
                    {Math.min(currentPage * itemsPerPage, getPaginatedCandidates().total)} de{' '}
                    {getPaginatedCandidates().total} candidatos
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={() => setCurrentPage(1)} disabled={currentPage === 1} className="h-8">
                      Primeira
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                      className="h-8"
                    >
                      Anterior
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
                      Próxima
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(getPaginatedCandidates().totalPages)}
                      disabled={currentPage === getPaginatedCandidates().totalPages}
                      className="h-8"
                    >
                      Última
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {!isLoading && sortedCandidates.length === 0 && (
              <div className="bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl p-8 text-center">
                <Users className="w-12 h-12 text-lia-text-primary mx-auto mb-4" />
                <h3 className="text-lg font-medium text-lia-text-primary mb-2">
                  Nenhum candidato encontrado
                </h3>
                <p className="text-lia-text-primary mb-4">
                  Tente ajustar os filtros ou termos de busca
                </p>
                <Button variant="outline" onClick={clearAllFilters}>
                  Limpar filtros
                </Button>
              </div>
            )}
          </div>

          <CandidatesLoadMoreFooter
            showSearchResults={showSearchResults}
            displayedResultsCount={displayedResultsCount}
            sortedCandidatesLength={sortedCandidates.length}
            isLoadingMore={isLoadingMore}
            onLoadMore={onLoadMore}
          />
        </div>
      )}
    </div>
  )
}
