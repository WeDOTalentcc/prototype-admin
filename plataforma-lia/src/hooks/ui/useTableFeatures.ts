"use client"

import { useState, useCallback, useEffect, useMemo } from "react"
import { useTableFeaturesStore } from "@/stores/table-features-store"

export interface TableColumnConfig {
  id: string
  label: string
  sortKey?: string
  defaultWidth: number
  minWidth?: number
  align?: 'left' | 'center' | 'right'
  fixed?: boolean
}

export interface SortState {
  field: string | null
  order: 'asc' | 'desc'
}

export interface UseTableFeaturesOptions {
  tableId: string
  columns: TableColumnConfig[]
  defaultSortField?: string
  defaultSortOrder?: 'asc' | 'desc'
}

export interface UseTableFeaturesReturn {
  columnWidths: Record<string, number>
  columnOrder: string[]
  sortState: SortState
  draggedColumnId: string | null
  dragOverColumnId: string | null
  handleSort: (field: string) => void
  getSortIcon: (field: string) => 'asc' | 'desc' | null
  startResize: (columnId: string, event: React.MouseEvent) => void
  handleColumnDragStart: (columnId: string, event: React.DragEvent) => void
  handleColumnDragOver: (columnId: string, event: React.DragEvent) => void
  handleColumnDragLeave: () => void
  handleColumnDrop: (targetColumnId: string, event: React.DragEvent) => void
  handleColumnDragEnd: () => void
  resetColumnOrder: () => void
  resetColumnWidths: () => void
  getColumnWidth: (columnId: string) => number
  isColumnDragging: (columnId: string) => boolean
  isColumnDragOver: (columnId: string) => boolean
  isColumnFixed: (columnId: string) => boolean
  movableColumnOrder: string[]
  fixedColumnIds: string[]
}

export function useTableFeatures(options: UseTableFeaturesOptions): UseTableFeaturesReturn {
  const { 
    tableId, 
    columns, 
    defaultSortField = null, 
    defaultSortOrder = 'desc'
  } = options

  const tableStore = useTableFeaturesStore()

  const fixedColumnIds = useMemo(() => 
    columns.filter(col => col.fixed).map(col => col.id),
    [columns]
  )

  const movableColumnIds = useMemo(() => 
    columns.filter(col => !col.fixed).map(col => col.id),
    [columns]
  )

  const defaultWidths = useMemo(() => 
    columns.reduce((acc, col) => {
      acc[col.id] = col.defaultWidth
      return acc
    }, {} as Record<string, number>),
    [columns]
  )

  const defaultOrder = useMemo(() => 
    columns.map(col => col.id),
    [columns]
  )

  const [columnWidths, setColumnWidths] = useState<Record<string, number>>(defaultWidths)
  const [columnOrder, setColumnOrder] = useState<string[]>(defaultOrder)
  const [sortState, setSortState] = useState<SortState>({
    field: defaultSortField,
    order: defaultSortOrder
  })
  const [draggedColumnId, setDraggedColumnId] = useState<string | null>(null)
  const [dragOverColumnId, setDragOverColumnId] = useState<string | null>(null)
  const [isHydrated, setIsHydrated] = useState(false)

  useEffect(() => {
    setIsHydrated(true)
  }, [])

  useEffect(() => {
    if (!isHydrated) return

    const savedWidths = tableStore.getTableWidths(tableId)
    if (savedWidths) {
      try {
        const validWidths: Record<string, number> = {}
        columns.forEach(col => {
          if (typeof savedWidths[col.id] === 'number' && savedWidths[col.id] >= (col.minWidth || 60)) {
            validWidths[col.id] = savedWidths[col.id]
          } else {
            validWidths[col.id] = col.defaultWidth
          }
        })
        setColumnWidths(validWidths)
      } catch {
        setColumnWidths(defaultWidths)
      }
    }

    const savedOrder = tableStore.getTableOrder(tableId)
    if (savedOrder) {
      try {
        const existingMovableFromSaved = savedOrder.filter(id => 
          movableColumnIds.includes(id)
        )
        const missingMovable = movableColumnIds.filter(id => 
          !savedOrder.includes(id)
        )
        const reconciledMovableOrder = [...existingMovableFromSaved, ...missingMovable]
        
        const fixedBefore = fixedColumnIds.filter(id => {
          const colIndex = columns.findIndex(c => c.id === id)
          const firstMovableIndex = columns.findIndex(c => !c.fixed)
          return colIndex < firstMovableIndex
        })
        const fixedAfter = fixedColumnIds.filter(id => !fixedBefore.includes(id))
        
        const finalOrder = [...fixedBefore, ...reconciledMovableOrder, ...fixedAfter]
        setColumnOrder(finalOrder)
      } catch {
        setColumnOrder(defaultOrder)
      }
    }

    const savedSort = tableStore.getTableSort(tableId)
    if (savedSort) {
      try {
        if (savedSort.field && columns.some(c => c.sortKey === savedSort.field)) {
          setSortState(savedSort)
        }
      } catch (error) {
        console.error("[useTableFeatures] Error:", error)
      }
    }
  }, [isHydrated, tableId, columns, defaultWidths, defaultOrder, movableColumnIds, fixedColumnIds, tableStore])

  const isColumnFixed = useCallback((columnId: string): boolean => {
    return fixedColumnIds.includes(columnId)
  }, [fixedColumnIds])

  const handleSort = useCallback((field: string) => {
    setSortState(prev => {
      const newState: SortState = {
        field,
        order: prev.field === field ? (prev.order === 'asc' ? 'desc' : 'asc') : 'desc'
      }
      tableStore.setTableSort(tableId, newState)
      return newState
    })
  }, [tableId, tableStore])

  const getSortIcon = useCallback((field: string): 'asc' | 'desc' | null => {
    if (sortState.field !== field) return null
    return sortState.order
  }, [sortState])

  const startResize = useCallback((columnId: string, event: React.MouseEvent) => {
    if (isColumnFixed(columnId)) return
    
    event.preventDefault()
    event.stopPropagation()

    const startX = event.clientX
    const startWidth = columnWidths[columnId] || defaultWidths[columnId] || 100
    const column = columns.find(c => c.id === columnId)
    const minWidth = column?.minWidth || 60

    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = Math.max(minWidth, startWidth + (e.clientX - startX))
      setColumnWidths(prev => {
        const updated = { ...prev, [columnId]: newWidth }
        tableStore.setTableWidths(tableId, updated)
        return updated
      })
    }

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }

    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }, [columnWidths, columns, tableId, defaultWidths, isColumnFixed, tableStore])

  const handleColumnDragStart = useCallback((columnId: string, event: React.DragEvent) => {
    if (isColumnFixed(columnId)) {
      event.preventDefault()
      return
    }
    
    setDraggedColumnId(columnId)
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', columnId)
    
    const dragImage = document.createElement('div')
    dragImage.className = 'fixed pointer-events-none bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-default dark:border-lia-border-default rounded-md px-3 py-1.5 text-xs font-medium text-lia-text-secondary dark:text-lia-text-secondary z-50'
    const column = columns.find(c => c.id === columnId)
    dragImage.textContent = column?.label || columnId
    document.body.appendChild(dragImage)
    event.dataTransfer.setDragImage(dragImage, 50, 15)
    
    setTimeout(() => {
      if (document.body.contains(dragImage)) {
        document.body.removeChild(dragImage)
      }
    }, 0)
  }, [columns, isColumnFixed])

  const handleColumnDragOver = useCallback((columnId: string, event: React.DragEvent) => {
    if (isColumnFixed(columnId)) {
      event.dataTransfer.dropEffect = 'none'
      return
    }
    
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
    
    if (draggedColumnId && draggedColumnId !== columnId) {
      setDragOverColumnId(columnId)
    }
  }, [draggedColumnId, isColumnFixed])

  const handleColumnDragLeave = useCallback(() => {
    setDragOverColumnId(null)
  }, [])

  const handleColumnDrop = useCallback((targetColumnId: string, event: React.DragEvent) => {
    event.preventDefault()
    
    if (!draggedColumnId || 
        draggedColumnId === targetColumnId || 
        isColumnFixed(targetColumnId) ||
        isColumnFixed(draggedColumnId)) {
      setDraggedColumnId(null)
      setDragOverColumnId(null)
      return
    }

    setColumnOrder(prev => {
      const newOrder = [...prev]
      const draggedIndex = newOrder.indexOf(draggedColumnId)
      const targetIndex = newOrder.indexOf(targetColumnId)
      
      if (draggedIndex === -1 || targetIndex === -1) return prev
      
      newOrder.splice(draggedIndex, 1)
      newOrder.splice(targetIndex, 0, draggedColumnId)
      
      const movableOrderOnly = newOrder.filter(id => !fixedColumnIds.includes(id))
      tableStore.setTableOrder(tableId, movableOrderOnly)
      
      return newOrder
    })

    setDraggedColumnId(null)
    setDragOverColumnId(null)
  }, [draggedColumnId, tableId, fixedColumnIds, isColumnFixed, tableStore])

  const handleColumnDragEnd = useCallback(() => {
    setDraggedColumnId(null)
    setDragOverColumnId(null)
  }, [])

  const resetColumnOrder = useCallback(() => {
    setColumnOrder(defaultOrder)
    tableStore.removeTableOrder(tableId)
  }, [tableId, defaultOrder, tableStore])

  const resetColumnWidths = useCallback(() => {
    setColumnWidths(defaultWidths)
    tableStore.removeTableWidths(tableId)
  }, [tableId, defaultWidths, tableStore])

  const getColumnWidth = useCallback((columnId: string): number => {
    const width = columnWidths[columnId] ?? defaultWidths[columnId]
    const column = columns.find(c => c.id === columnId)
    const minWidth = column?.minWidth || 60
    return Math.max(width || column?.defaultWidth || 100, minWidth)
  }, [columnWidths, defaultWidths, columns])

  const isColumnDragging = useCallback((columnId: string): boolean => {
    return draggedColumnId === columnId
  }, [draggedColumnId])

  const isColumnDragOver = useCallback((columnId: string): boolean => {
    return dragOverColumnId === columnId && !isColumnFixed(columnId)
  }, [dragOverColumnId, isColumnFixed])

  const movableColumnOrder = useMemo(() => 
    columnOrder.filter(id => !fixedColumnIds.includes(id)),
    [columnOrder, fixedColumnIds]
  )

  return {
    columnWidths,
    columnOrder,
    sortState,
    draggedColumnId,
    dragOverColumnId,
    handleSort,
    getSortIcon,
    startResize,
    handleColumnDragStart,
    handleColumnDragOver,
    handleColumnDragLeave,
    handleColumnDrop,
    handleColumnDragEnd,
    resetColumnOrder,
    resetColumnWidths,
    getColumnWidth,
    isColumnDragging,
    isColumnDragOver,
    isColumnFixed,
    movableColumnOrder,
    fixedColumnIds
  }
}
