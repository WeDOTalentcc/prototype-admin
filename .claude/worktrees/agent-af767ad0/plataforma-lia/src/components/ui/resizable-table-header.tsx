"use client"

import React from "react"
import { ArrowUp, ArrowDown, GripVertical, ChevronsUpDown } from "lucide-react"
import { cn } from "@/lib/utils"
import type { UseTableFeaturesReturn, ColumnConfig } from "@/hooks/useTableFeatures"

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

export function ResizableTableHeader({
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
        "relative py-1.5 px-3 font-medium text-gray-800 dark:text-gray-200 text-xs uppercase tracking-wide select-none transition-colors",
        alignClass,
        isDragging && !isFixed && "opacity-50 bg-gray-100 dark:bg-gray-800",
        isDragOver && !isFixed && "bg-gray-100 dark:bg-gray-800 border-l-2 border-gray-400",
        isResizing && "bg-gray-100 dark:bg-gray-800",
        className
      )}
      style={{ 
        width: `${safeWidth}px`, 
        minWidth: `${minWidth}px`, 
        fontFamily: 'Open Sans, sans-serif' 
      }}
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
            className="w-3 h-3 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity cursor-grab active:cursor-grabbing flex-shrink-0" 
          />
        )}
        
        {children || (
          <button
            onClick={sortable ? onSort : undefined}
            className={cn(
              "flex items-center gap-1 flex-1 min-w-0",
              sortable && "cursor-pointer hover:text-gray-950 dark:hover:text-gray-50"
            )}
            title={sortable ? `Ordenar por ${label}` : undefined}
          >
            <span className="truncate">
              {label}
            </span>
            {sortable && isSorted ? (
              sortDirection === "asc" 
                ? <ArrowUp className="w-3 h-3 flex-shrink-0 text-gray-700 dark:text-gray-300" />
                : <ArrowDown className="w-3 h-3 flex-shrink-0 text-gray-700 dark:text-gray-300" />
            ) : sortable && (
              <ChevronsUpDown className="w-3 h-3 flex-shrink-0 opacity-0 group-hover:opacity-50 transition-opacity" />
            )}
          </button>
        )}
      </div>

      {!isFixed && onResizeStart && (
        <div
          className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-gray-400 transition-colors opacity-0 group-hover:opacity-100"
          onMouseDown={onResizeStart}
          onClick={(e) => e.stopPropagation()}
          title="Arraste para redimensionar"
        >
          <div className="absolute right-0 top-1/2 -translate-y-1/2 w-0.5 h-4 bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 transition-colors" />
        </div>
      )}
    </th>
  )
}

interface TableHeaderRowProps {
  children: React.ReactNode
  className?: string
}

export function TableHeaderRow({ children, className }: TableHeaderRowProps) {
  return (
    <thead className={cn("bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10", className)}>
      <tr>{children}</tr>
    </thead>
  )
}

interface ConnectedTableHeaderProps {
  column: ColumnConfig
  tableFeatures: UseTableFeaturesReturn
  children?: React.ReactNode
  className?: string
}

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
