"use client"

import React from "react"
import { Button } from "@/components/ui/button"

interface PaginatedResult {
  candidates: unknown[]
  total: number
  totalPages: number
}

interface KanbanTablePaginationProps {
  currentPage: number
  itemsPerPage: number
  getPaginatedCandidates: () => PaginatedResult
  onCurrentPageChange: (page: number) => void
}

export function KanbanTablePagination({
  currentPage,
  itemsPerPage,
  getPaginatedCandidates,
  onCurrentPageChange,
}: KanbanTablePaginationProps) {
  const paginated = getPaginatedCandidates()
  if (paginated.totalPages <= 1) return null
  return (
    <>
{/* Paginação */}
{getPaginatedCandidates().totalPages > 1 && (
  <div className="bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl p-3">
    <div className="flex items-center justify-between">
      <div className="text-sm text-lia-text-secondary">
        Mostrando {((currentPage - 1) * itemsPerPage) + 1} - {Math.min(currentPage * itemsPerPage, getPaginatedCandidates().total)} de {getPaginatedCandidates().total} candidatos
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onCurrentPageChange(1)}
          disabled={currentPage === 1}
          className="h-8 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
        >
          Primeira
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onCurrentPageChange(Math.max(1, currentPage - 1))}
          disabled={currentPage === 1}
          className="h-8 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
        >
          Anterior
        </Button>

        {/* Page numbers */}
        <div className="flex items-center gap-1">
          {Array.from({ length: getPaginatedCandidates().totalPages }, (_, i) => i + 1)
            .filter(page => {
              // Show first page, last page, current page, and pages around current
              return page === 1 ||
                     page === getPaginatedCandidates().totalPages ||
                     (page >= currentPage - 1 && page <= currentPage + 1)
            })
            .map((page, index, array) => (
              <React.Fragment key={page}>
                {/* Show ellipsis if there's a gap */}
                {index > 0 && page - array[index - 1] > 1 && (
                  <span className="px-2 text-lia-text-secondary">...</span>
                )}
                <Button
                  variant={currentPage === page ? 'secondary' : 'outline'}
                  size="sm"
                  onClick={() => onCurrentPageChange(page)}
                  className="h-8 w-8 p-0 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
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
          onClick={() => onCurrentPageChange(Math.min(getPaginatedCandidates().totalPages, currentPage + 1))}
          disabled={currentPage === getPaginatedCandidates().totalPages}
          className="h-8 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
        >
          Próxima
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onCurrentPageChange(getPaginatedCandidates().totalPages)}
          disabled={currentPage === getPaginatedCandidates().totalPages}
          className="h-8 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
        >
          Última
        </Button>
      </div>
    </div>
  </div>
)}
    </>
  )
}
