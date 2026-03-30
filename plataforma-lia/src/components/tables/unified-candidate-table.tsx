"use client"

import React, { useState, useMemo, useCallback, useRef, useEffect } from "react"
import { ArrowUp, ArrowDown, ArrowUpDown, GripVertical, Loader2, MoreVertical, Globe } from "lucide-react"

// Lazy import virtualizer — only loaded when enableVirtualScroll is true
let useVirtualizer: typeof import("@tanstack/react-virtual").useVirtualizer | null = null
try {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  useVirtualizer = require("@tanstack/react-virtual").useVirtualizer
} catch {
  // Package not installed — virtualisation disabled
}
import type { UnifiedTableProps, TableColumn, TableSortConfig } from "./types"
import { CandidateTableRow } from "./candidate-table-row"
import { reorderColumns } from "./column-definitions"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from "@/lib/design-tokens"

export function UnifiedCandidateTable({
  candidates,
  columns,
  selectedIds = new Set(),
  pinnedIds = new Set(),
  favoriteIds = new Set(),
  sortConfig,
  isLoading = false,
  emptyMessage = "Nenhum candidato encontrado",
  showCheckboxes = false,
  showPagination = false,
  pageSize = 50,
  enableVirtualScroll = false,
  enableColumnResize = false,
  enableColumnReorder = false,
  jobVacancyId,
  isInteractive = false,
  onColumnResize,
  onColumnReorder,
  onCandidateClick,
  onSelectionChange,
  onSortChange,
  onTogglePin,
  onToggleFavorite,
  onStatusChange,
  onStageChange,
  onTransitionRequest,
  renderActions,
  renderLeftOverlayActions,
  renderCustomCell,
  renderCustomHeader,
  getStageBorderColor,
  getNeedsAction,
  className = ""
}: UnifiedTableProps) {
  const [currentPage, setCurrentPage] = useState(1)
  const [internalSort, setInternalSort] = useState<TableSortConfig | undefined>(sortConfig)

  // Virtual scroll container ref (used when enableVirtualScroll = true)
  const virtualScrollRef = useRef<HTMLDivElement>(null)

  const rowVirtualizer = enableVirtualScroll && useVirtualizer
    ? useVirtualizer({
        count: sortedCandidates.length,
        getScrollElement: () => virtualScrollRef.current,
        estimateSize: () => 56,
        overscan: 20,
      })
    : null

  const [resizingColumnId, setResizingColumnId] = useState<string | null>(null)
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>(() => {
    const initialWidths: Record<string, number> = {}
    columns.forEach(col => {
      if (typeof col.width === 'number') {
        initialWidths[col.id] = col.width
      }
    })
    return initialWidths
  })
  const resizeStartX = useRef<number>(0)
  const resizeStartWidth = useRef<number>(0)
  const resizeHandlersRef = useRef<{ move: ((e: MouseEvent) => void) | null; up: (() => void) | null }>({ move: null, up: null })

  useEffect(() => {
    return () => {
      if (resizeHandlersRef.current.move) {
        document.removeEventListener('mousemove', resizeHandlersRef.current.move)
      }
      if (resizeHandlersRef.current.up) {
        document.removeEventListener('mouseup', resizeHandlersRef.current.up)
      }
    }
  }, [])

  const [draggedColumnId, setDraggedColumnId] = useState<string | null>(null)
  const [dropTargetColumnId, setDropTargetColumnId] = useState<string | null>(null)

  const activeSort = sortConfig ?? internalSort

  const visibleColumns = useMemo(() => 
    columns.filter(col => col.visible !== false).sort((a, b) => (a.order ?? 0) - (b.order ?? 0)),
    [columns]
  )

  const sortedCandidates = useMemo(() => {
    if (!activeSort) return candidates

    return [...candidates].sort((a, b) => {
      let aValue: unknown
      let bValue: unknown
      const field = activeSort.field

      if (field === 'score' || field === 'lia_score') {
        aValue = (a.liaAnalysis?.score || a.lia_score || a.score || 0)
        bValue = (b.liaAnalysis?.score || b.lia_score || b.score || 0)
      } else if (field === 'candidate' || field === 'name') {
        aValue = a.name || ''
        bValue = b.name || ''
      } else if (field === 'company' || field === 'current_company') {
        aValue = a.current_company || a.workHistory?.[0]?.company || ''
        bValue = b.current_company || b.workHistory?.[0]?.company || ''
      } else if (field === 'position' || field === 'current_title') {
        aValue = a.position || a.current_title || ''
        bValue = b.position || b.current_title || ''
      } else if (field === 'location') {
        aValue = a.location || a.location_city || ''
        bValue = b.location || b.location_city || ''
      } else {
        aValue = a[field as keyof typeof a]
        bValue = b[field as keyof typeof b]
      }

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return activeSort.direction === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue)
      }

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return activeSort.direction === 'asc' 
          ? aValue - bValue
          : bValue - aValue
      }

      return 0
    })
  }, [candidates, activeSort])

  const paginatedCandidates = useMemo(() => {
    if (!showPagination) return sortedCandidates
    const start = (currentPage - 1) * pageSize
    return sortedCandidates.slice(start, start + pageSize)
  }, [sortedCandidates, currentPage, pageSize, showPagination])

  const totalPages = Math.ceil(sortedCandidates.length / pageSize)

  const handleSort = useCallback((columnId: string) => {
    const column = columns.find(c => c.id === columnId)
    if (!column?.sortable) return

    const newSort: TableSortConfig = {
      field: columnId,
      direction: activeSort?.field === columnId && activeSort.direction === 'desc' ? 'asc' : 'desc'
    }

    if (onSortChange) {
      onSortChange(newSort)
    } else {
      setInternalSort(newSort)
    }
  }, [columns, activeSort, onSortChange])

  const handleToggleSelect = useCallback((candidateId: string) => {
    const newSelection = new Set(selectedIds)
    if (newSelection.has(candidateId)) {
      newSelection.delete(candidateId)
    } else {
      newSelection.add(candidateId)
    }
    onSelectionChange?.(newSelection)
  }, [selectedIds, onSelectionChange])

  const handleSelectAll = useCallback(() => {
    const pageIds = new Set(paginatedCandidates.map(c => c.id))
    const allPageSelected = paginatedCandidates.every(c => selectedIds.has(c.id))
    
    if (allPageSelected) {
      const newSelection = new Set(selectedIds)
      pageIds.forEach(id => newSelection.delete(id))
      onSelectionChange?.(newSelection)
    } else {
      const newSelection = new Set(selectedIds)
      pageIds.forEach(id => newSelection.add(id))
      onSelectionChange?.(newSelection)
    }
  }, [selectedIds, paginatedCandidates, onSelectionChange])

  const handleResizeStart = useCallback((e: React.MouseEvent, columnId: string, currentWidth: number) => {
    if (!enableColumnResize) return
    e.preventDefault()
    e.stopPropagation()
    
    if (resizeHandlersRef.current.move) {
      document.removeEventListener('mousemove', resizeHandlersRef.current.move)
    }
    if (resizeHandlersRef.current.up) {
      document.removeEventListener('mouseup', resizeHandlersRef.current.up)
    }
    
    setResizingColumnId(columnId)
    resizeStartX.current = e.clientX
    resizeStartWidth.current = currentWidth

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const delta = moveEvent.clientX - resizeStartX.current
      const newWidth = Math.max(50, resizeStartWidth.current + delta)
      
      setColumnWidths(prev => ({
        ...prev,
        [columnId]: newWidth
      }))
    }

    const handleMouseUp = () => {
      setColumnWidths(prev => {
        const finalWidth = prev[columnId] ?? resizeStartWidth.current
        onColumnResize?.(columnId, finalWidth)
        return prev
      })
      setResizingColumnId(null)
      if (resizeHandlersRef.current.move) {
        document.removeEventListener('mousemove', resizeHandlersRef.current.move)
      }
      if (resizeHandlersRef.current.up) {
        document.removeEventListener('mouseup', resizeHandlersRef.current.up)
      }
      resizeHandlersRef.current = { move: null, up: null }
    }

    resizeHandlersRef.current = { move: handleMouseMove, up: handleMouseUp }
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }, [enableColumnResize, onColumnResize])

  const handleDragStart = useCallback((e: React.DragEvent, columnId: string) => {
    if (!enableColumnReorder) return
    
    setDraggedColumnId(columnId)
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', columnId)
    
    if (e.currentTarget instanceof HTMLElement) {
      e.currentTarget.style.opacity = '0.5'
    }
  }, [enableColumnReorder])

  const handleDragEnd = useCallback((e: React.DragEvent) => {
    setDraggedColumnId(null)
    setDropTargetColumnId(null)
    
    if (e.currentTarget instanceof HTMLElement) {
      e.currentTarget.style.opacity = '1'
    }
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent, columnId: string) => {
    if (!enableColumnReorder || !draggedColumnId) return
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    
    if (columnId !== draggedColumnId) {
      setDropTargetColumnId(columnId)
    }
  }, [enableColumnReorder, draggedColumnId])

  const handleDragLeave = useCallback(() => {
    setDropTargetColumnId(null)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent, targetColumnId: string) => {
    e.preventDefault()
    
    if (!draggedColumnId || draggedColumnId === targetColumnId) {
      setDraggedColumnId(null)
      setDropTargetColumnId(null)
      return
    }

    const reorderedColumns = reorderColumns(columns, draggedColumnId, targetColumnId)
    onColumnReorder?.(reorderedColumns)
    
    setDraggedColumnId(null)
    setDropTargetColumnId(null)
  }, [draggedColumnId, columns, onColumnReorder])

  const getColumnWidth = useCallback((column: TableColumn): number | string => {
    if (columnWidths[column.id]) {
      return columnWidths[column.id]
    }
    return column.width ?? 'auto'
  }, [columnWidths])

  const getSortIcon = (columnId: string, isSortable: boolean) => {
    if (!isSortable) return null
    if (activeSort?.field !== columnId) {
      return <ArrowUpDown className="w-3 h-3 lia-text-secondary" />
    }
    return activeSort.direction === 'asc' 
      ? <ArrowUp className="w-3 h-3 lia-text-base" />
      : <ArrowDown className="w-3 h-3 lia-text-base" />
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin lia-text-secondary" />
        <span className="ml-2 text-sm lia-text-secondary">Carregando candidatos...</span>
      </div>
    )
  }

  if (candidates.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <span className="text-sm lia-text-secondary">{emptyMessage}</span>
      </div>
    )
  }

  return (
    <div className={`bg-white dark:bg-lia-bg-primary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle ${className}`}>
      <div
        ref={enableVirtualScroll ? virtualScrollRef : undefined}
        className="overflow-x-auto"
        style={enableVirtualScroll ? { overflowY: "auto", maxHeight: "600px" } : undefined}
      >
        <table className="w-full" style={{tableLayout: enableColumnResize ? 'fixed' : 'auto'}}>
          <thead className="sticky top-0 z-10 bg-white dark:bg-lia-bg-primary border-b border-lia-border-subtle dark:border-lia-border-subtle">
            <tr>
              {showCheckboxes && (
                <th className="px-3 py-2.5 w-[50px]">
                  <div
                    onClick={handleSelectAll}
                    className="cursor-pointer w-5 h-5 rounded-md border-2 flex items-center justify-center transition-colors border-lia-border-default dark:border-lia-border-default hover:border-gray-500"
                  >
                    {paginatedCandidates.length > 0 && paginatedCandidates.every(c => selectedIds.has(c.id)) && (
                      <div className="w-2.5 h-2.5 bg-gray-900 rounded-sm" />
                    )}
                  </div>
                </th>
              )}
              {visibleColumns.map((column) => {
                const width = getColumnWidth(column)
                const isDragging = draggedColumnId === column.id
                const isDropTarget = dropTargetColumnId === column.id

                return (
                  <th
                    key={column.id}
                    className={`
 px-3 py-3 relative group select-none text-xs font-semibold text-gray-800 dark:text-lia-text-primary
                      ${column.align === 'center' ? 'text-center' : column.align === 'right' ? 'text-right' : 'text-left'}
                      ${isDragging ? 'opacity-50' : ''}
                      ${isDropTarget ? 'bg-wedo-cyan/10' : ''}
                      ${column.sortable ? 'cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50' : ''}
                    `}
                    style={{width: typeof width === 'number' ? `${width}px` : width,
                      minWidth: column.minWidth || '50px'}}
                    draggable={enableColumnReorder}
                    onDragStart={(e) => handleDragStart(e, column.id)}
                    onDragEnd={handleDragEnd}
                    onDragOver={(e) => handleDragOver(e, column.id)}
                    onDragLeave={handleDragLeave}
                    onDrop={(e) => handleDrop(e, column.id)}
                    onClick={() => column.sortable && handleSort(column.id)}
                  >
                    <div className="flex items-center gap-1">
                      {enableColumnReorder && (
                        <GripVertical className="w-3 h-3 lia-text-secondary opacity-0 group-hover:opacity-100 transition-opacity cursor-grab" />
                      )}
                      {renderCustomHeader?.(column.id, column.label) ?? (
                        column.id === 'acoes' || column.id === 'actions' ? (
                          <>
                            <span className="sr-only">Ações</span>
                            <MoreVertical className="w-4 h-4 text-gray-600 dark:text-lia-text-secondary" aria-hidden="true" />
                          </>
                        ) : (
                          <span className="flex items-center gap-1">
                            {column.isGlobalSearch && (
                              <Globe className="w-3 h-3 text-gray-600 dark:text-lia-text-tertiary" />
                            )}
                            {column.label}
                          </span>
                        )
                      )}
                      {getSortIcon(column.id, column.sortable ?? false)}
                    </div>
                    
                    {/* Resize Handle - Sempre visível */}
                    {enableColumnResize && (
                      <div
                        className={`absolute right-0 top-0 h-full w-2 cursor-col-resize transition-colors ${
 resizingColumnId === column.id 
                            ? 'bg-gray-400 w-1' 
                            : 'bg-transparent hover:bg-gray-300 group-hover:bg-gray-200'
                        }`}
                        style={{zIndex: 20}}
                        onMouseDown={(e) => {
                          e.stopPropagation()
                          const thElement = e.currentTarget.parentElement
                          const currentWidth = thElement?.offsetWidth ?? 100
                          handleResizeStart(e, column.id, currentWidth)
                        }}
                        onClick={(e) => e.stopPropagation()}
                      />
                    )}
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody
            className="divide-y divide-gray-100 dark:divide-gray-700"
            style={rowVirtualizer ? {
              position: "relative",
              height: `${rowVirtualizer.getTotalSize()}px`,
            } : undefined}
          >
            {rowVirtualizer
              ? rowVirtualizer.getVirtualItems().map((virtualRow) => {
                  const candidate = sortedCandidates[virtualRow.index]
                  if (!candidate) return null
                  return (
                    <CandidateTableRow
                      key={candidate.id}
                      candidate={candidate}
                      columns={showCheckboxes
                        ? [{ id: 'checkbox', label: '', visible: true }, ...visibleColumns]
                        : visibleColumns
                      }
                      isSelected={selectedIds.has(candidate.id)}
                      isPinned={pinnedIds.has(candidate.id)}
                      isFavorite={favoriteIds.has(candidate.id)}
                      showCheckbox={showCheckboxes}
                      needsAction={getNeedsAction?.(candidate) ?? false}
                      jobVacancyId={jobVacancyId}
                      isInteractive={isInteractive}
                      onRowClick={() => onCandidateClick?.(candidate)}
                      onToggleSelect={() => handleToggleSelect(candidate.id)}
                      onTogglePin={onTogglePin ? () => onTogglePin(candidate.id) : undefined}
                      onToggleFavorite={onToggleFavorite ? () => onToggleFavorite(candidate.id) : undefined}
                      onStatusChange={onStatusChange}
                      onStageChange={onStageChange}
                      onTransitionRequest={onTransitionRequest}
                      renderActions={renderActions ? () => renderActions(candidate) : undefined}
                      renderLeftOverlayActions={renderLeftOverlayActions ? () => renderLeftOverlayActions(candidate) : undefined}
                      renderCustomCell={renderCustomCell ? (colId) => renderCustomCell(candidate, colId) : undefined}
                      stageBorderColor={getStageBorderColor?.(candidate)}
                      style={{position: "absolute",
                        top: 0,
                        left: 0,
                        width: "100%",
                        height: `${virtualRow.size}px`,
                        transform: `translateY(${virtualRow.start}px)`}}
                    />
                  )
                })
              : paginatedCandidates.map((candidate) => (
                  <CandidateTableRow
                    key={candidate.id}
                    candidate={candidate}
                    columns={showCheckboxes
                      ? [{ id: 'checkbox', label: '', visible: true }, ...visibleColumns]
                      : visibleColumns
                    }
                    isSelected={selectedIds.has(candidate.id)}
                    isPinned={pinnedIds.has(candidate.id)}
                    isFavorite={favoriteIds.has(candidate.id)}
                    showCheckbox={showCheckboxes}
                    needsAction={getNeedsAction?.(candidate) ?? false}
                    jobVacancyId={jobVacancyId}
                    isInteractive={isInteractive}
                    onRowClick={() => onCandidateClick?.(candidate)}
                    onToggleSelect={() => handleToggleSelect(candidate.id)}
                    onTogglePin={onTogglePin ? () => onTogglePin(candidate.id) : undefined}
                    onToggleFavorite={onToggleFavorite ? () => onToggleFavorite(candidate.id) : undefined}
                    onStatusChange={onStatusChange}
                    onStageChange={onStageChange}
                    onTransitionRequest={onTransitionRequest}
                    renderActions={renderActions ? () => renderActions(candidate) : undefined}
                    renderLeftOverlayActions={renderLeftOverlayActions ? () => renderLeftOverlayActions(candidate) : undefined}
                    renderCustomCell={renderCustomCell ? (colId) => renderCustomCell(candidate, colId) : undefined}
                    stageBorderColor={getStageBorderColor?.(candidate)}
                  />
                ))
            }
          </tbody>
        </table>
      </div>

      {showPagination && totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
          <span className="text-xs lia-text-secondary">
            Mostrando {((currentPage - 1) * pageSize) + 1} - {Math.min(currentPage * pageSize, sortedCandidates.length)} de {sortedCandidates.length}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 text-xs rounded-md border border-lia-border-default dark:border-lia-border-default hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Anterior
            </button>
            <span className="text-xs text-gray-600 dark:text-lia-text-tertiary">
              Página {currentPage} de {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 text-xs rounded-md border border-lia-border-default dark:border-lia-border-default hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Próxima
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
