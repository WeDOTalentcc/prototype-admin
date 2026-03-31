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

  if (paginated.totalPages <= 1) {
    return null
  }

  return (
    <div className="bg-white dark:bg-lia-bg-primary rounded-md p-3">
      <div className="flex items-center justify-between">
        <div className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
          Mostrando {((currentPage - 1) * itemsPerPage) + 1} - {Math.min(currentPage * itemsPerPage, paginated.total)} de {paginated.total} candidatos
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onCurrentPageChange(1)}
            disabled={currentPage === 1}
            className="h-8"
          >
            Primeira
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onCurrentPageChange(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className="h-8"
          >
            Anterior
          </Button>

          {/* Page numbers */}
          <div className="flex items-center gap-1">
            {Array.from({ length: paginated.totalPages }, (_, i) => i + 1)
              .filter(page => {
                return page === 1 ||
                       page === paginated.totalPages ||
                       (page >= currentPage - 1 && page <= currentPage + 1)
              })
              .map((page, index, array) => (
                <React.Fragment key={page}>
                  {index > 0 && page - array[index - 1] > 1 && (
                    <span className="px-2 text-lia-text-secondary">...</span>
                  )}
                  <Button
                    variant={currentPage === page ? "secondary" : "outline"}
                    size="sm"
                    onClick={() => onCurrentPageChange(page)}
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
            onClick={() => onCurrentPageChange(Math.min(paginated.totalPages, currentPage + 1))}
            disabled={currentPage === paginated.totalPages}
            className="h-8"
          >
            Próxima
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onCurrentPageChange(paginated.totalPages)}
            disabled={currentPage === paginated.totalPages}
            className="h-8"
          >
            Última
          </Button>
        </div>
      </div>
    </div>
  )
}
