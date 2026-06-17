"use client"

import React from "react"
import { ArrowUp, ArrowDown, GripVertical, ChevronsUpDown } from "lucide-react"
import { cn } from "@/lib/utils"
import type { UseTableFeaturesReturn, TableColumnConfig as ColumnConfig } from "@/hooks/ui/useTableFeatures"

interface ResizableTableHeaderProps {
  columnId: string
  label: string
  width: number
  minWidth?: number
  sortable?: boolean
  isSorted?: boolean
  sortDirection?: "asc" | "desc"
  isDragging?: boolean
  isDragOver?: boolean
  isResizing?: boolean
  isFixed?: boolean
  align?: 'left' | 'center' | 'right'
  className?: string
  onSort?: () => void
  onResizeStart?: (e: React.MouseEvent) => void
  onDragStart?: (e: React.DragEvent) => void
  onDragOver?: (e: React.DragEvent) => void
  onDragLeave?: () => void
  onDrop?: (e: React.DragEvent) => void
  onDragEnd?: () => void
  children?: React.ReactNode
}

export const ResizableTableHeader = React.memo(function ResizableTableHeader({
  columnId,
  label,
  width,
  minWidth = 60,
  sortable = true,
  isSorted = false,
  sortDirection = "asc",
  isDragging = false,
  isDragOver = false,
  isResizing = false,
  isFixed = false,
  align = 'left',
  className,
  onSort,
  onResizeStart,
  onDragStart,
  onDragOver,
  onDragLeave,
  onDrop,
  onDragEnd,
  children,
}: ResizableTableHeaderProps) {
  const alignClass = align === 'left' ? 'text-left' : 
                     align === 'right' ? 'text-right' : 'text-center'

  const safeWidth = Math.max(width || minWidth, minWidth)

  return (
    <th
      className={cn(
 "relative py-1.5 px-3 font-medium text-lia-text-primary text-xs uppercase tracking-wide select-none transition-colors",
        alignClass,
        isDragging && !isFixed && "opacity-50 bg-lia-bg-tertiary dark:bg-lia-bg-secondary",
        isDragOver && !isFixed && "bg-lia-bg-tertiary dark:bg-lia-bg-secondary border-l-2 border-lia-border-medium",
        isResizing && "bg-lia-bg-tertiary dark:bg-lia-bg-secondary",
        className
      )}
      style={{width: `${safeWidth}px`, 
        minWidth: `${minWidth}px`}}
      draggable={!isFixed && !!onDragStart}
      onDragStart={!isFixed ? onDragStart : undefined}
      onDragOver={!isFixed ? onDragOver : undefined}
      onDragLeave={!isFixed ? onDragLeave : undefined}
      onDrop={!isFixed ? onDrop : undefined}
      onDragEnd={!isFixed ? onDragEnd : undefined}
    >
      <div className="flex items-center gap-1 group">
        {!isFixed && onDragStart && (
          <GripVertical 
            className="w-3 h-3 text-lia-text-secondary opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none cursor-grab active:cursor-grabbing flex-shrink-0" 
          />
        )}
        
        {children || (
          <button
            onClick={sortable ? onSort : undefined}
            className={cn(
 "flex items-center gap-1 flex-1 min-w-0",
              sortable && "cursor-pointer hover:text-lia-text-primary"
            )}
            title={sortable ? `Ordenar por ${label}` : undefined}
          >
            <span className="truncate">
              {label}
            </span>
            {sortable && isSorted ? (
              sortDirection === "asc" 
                ? <ArrowUp className="w-3 h-3 flex-shrink-0 text-lia-text-secondary" />
                : <ArrowDown className="w-3 h-3 flex-shrink-0 text-lia-text-secondary" />
            ) : sortable && (
              <ChevronsUpDown className="w-3 h-3 flex-shrink-0 opacity-0 group-hover:opacity-50 transition-opacity motion-reduce:transition-none" />
            )}
          </button>
        )}
      </div>

      {!isFixed && onResizeStart && (
        <div
          className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-lia-border-medium transition-colors motion-reduce:transition-none opacity-0 group-hover:opacity-100"
          onMouseDown={onResizeStart}
          onClick={(e) => e.stopPropagation()}
          title="Arraste para redimensionar"
        >
          <div className="absolute right-0 top-1/2 -translate-y-1/2 w-0.5 h-4 bg-lia-border-default hover:bg-lia-border-medium transition-colors motion-reduce:transition-none" />
        </div>
      )}
    </th>
  )
})

interface TableHeaderRowProps {
  children: React.ReactNode
  className?: string
}
ResizableTableHeader.displayName = 'ResizableTableHeader'

export const TableHeaderRow = React.memo(function TableHeaderRow({ children, className }: TableHeaderRowProps) {
  return (
    <thead className={cn("bg-lia-bg-primary border-b border-lia-border-subtle sticky top-0 z-10", className)}>
      <tr>{children}</tr>
    </thead>
  )
})

interface ConnectedTableHeaderProps {
  column: ColumnConfig
  tableFeatures: UseTableFeaturesReturn
  children?: React.ReactNode
  className?: string
}
TableHeaderRow.displayName = 'TableHeaderRow'

export function ConnectedTableHeader({
  column,
  tableFeatures,
  children,
  className
}: ConnectedTableHeaderProps) {
  const {
    getColumnWidth,
    getSortIcon,
    handleSort,
    startResize,
    handleColumnDragStart,
    handleColumnDragOver,
    handleColumnDragLeave,
    handleColumnDrop,
    handleColumnDragEnd,
    isColumnDragging,
    isColumnDragOver,
    isColumnFixed
  } = tableFeatures

  const sortDirection = column.sortKey ? getSortIcon(column.sortKey) : null
  const isFixed = isColumnFixed(column.id)

  return (
    <ResizableTableHeader
      columnId={column.id}
      label={column.label}
      width={getColumnWidth(column.id)}
      minWidth={column.minWidth}
      sortable={!!column.sortKey}
      isSorted={sortDirection !== null}
      sortDirection={sortDirection || 'asc'}
      isDragging={isColumnDragging(column.id)}
      isDragOver={isColumnDragOver(column.id)}
      isFixed={isFixed}
      align={column.align}
      className={className}
      onSort={column.sortKey ? () => handleSort(column.sortKey!) : undefined}
      onResizeStart={!isFixed ? (e) => startResize(column.id, e) : undefined}
      onDragStart={!isFixed ? (e) => handleColumnDragStart(column.id, e) : undefined}
      onDragOver={(e) => handleColumnDragOver(column.id, e)}
      onDragLeave={handleColumnDragLeave}
      onDrop={(e) => handleColumnDrop(column.id, e)}
      onDragEnd={handleColumnDragEnd}
    >
      {children}
    </ResizableTableHeader>
  )
}

interface DynamicTableHeadersProps {
  columns: ColumnConfig[]
  tableFeatures: UseTableFeaturesReturn
  renderCell?: (column: ColumnConfig) => React.ReactNode
  includeFixed?: boolean
}

export function DynamicTableHeaders({
  columns,
  tableFeatures,
  renderCell,
  includeFixed = false
}: DynamicTableHeadersProps) {
  const { movableColumnOrder, isColumnFixed } = tableFeatures
  
  const columnsToRender = includeFixed 
    ? columns.filter(col => !col.fixed || includeFixed)
    : columns.filter(col => !col.fixed)
  
  const orderedColumns = movableColumnOrder
    .filter(id => columnsToRender.some(col => col.id === id))
    .map(id => columnsToRender.find(col => col.id === id))
    .filter((col): col is ColumnConfig => col !== undefined)

  return (
    <>
      {orderedColumns.map((column) => (
        <ConnectedTableHeader
          key={column.id}
          column={column}
          tableFeatures={tableFeatures}
        >
          {renderCell ? renderCell(column) : undefined}
        </ConnectedTableHeader>
      ))}
    </>
  )
}

interface FixedTableHeaderProps {
  column: ColumnConfig
  tableFeatures: UseTableFeaturesReturn
  children?: React.ReactNode
  className?: string
}

export function FixedTableHeader({
  column,
  tableFeatures,
  children,
  className
}: FixedTableHeaderProps) {
  const { getColumnWidth, getSortIcon, handleSort } = tableFeatures
  const sortDirection = column.sortKey ? getSortIcon(column.sortKey) : null

  return (
    <ResizableTableHeader
      columnId={column.id}
      label={column.label}
      width={getColumnWidth(column.id)}
      minWidth={column.minWidth}
      sortable={!!column.sortKey}
      isSorted={sortDirection !== null}
      sortDirection={sortDirection || 'asc'}
      isFixed={true}
      align={column.align}
      className={className}
      onSort={column.sortKey ? () => handleSort(column.sortKey!) : undefined}
    >
      {children}
    </ResizableTableHeader>
  )
}
