"use client"

import { useState, useCallback, useEffect, useMemo } from "react"

export interface ColumnConfig {
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
  columns: ColumnConfig[]
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

function isClient(): boolean {
  return typeof window !== 'undefined'
}

function safeLocalStorageGet(key: string): string | null {
  if (!isClient()) return null
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function safeLocalStorageSet(key: string, value: string): void {
  if (!isClient()) return
  try {
    localStorage.setItem(key, value)
  } catch {
  }
}

function safeLocalStorageRemove(key: string): void {
  if (!isClient()) return
  try {
    localStorage.removeItem(key)
  } catch {
  }
}

export function useTableFeatures(options: UseTableFeaturesOptions): UseTableFeaturesReturn {
  const { 
    tableId, 
    columns, 
    defaultSortField = null, 
    defaultSortOrder = 'desc'
  } = options

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

    const savedWidths = safeLocalStorageGet(`${tableId}-column-widths`)
    if (savedWidths) {
      try {
        const parsed = JSON.parse(savedWidths)
        const validWidths: Record<string, number> = {}
        columns.forEach(col => {
          if (typeof parsed[col.id] === 'number' && parsed[col.id] >= (col.minWidth || 60)) {
            validWidths[col.id] = parsed[col.id]
          } else {
            validWidths[col.id] = col.defaultWidth
          }
        })
        setColumnWidths(validWidths)
      } catch {
        setColumnWidths(defaultWidths)
      }
    }

    const savedOrder = safeLocalStorageGet(`${tableId}-column-order`)
    if (savedOrder) {
      try {
        const parsed = JSON.parse(savedOrder) as string[]
        
        const existingMovableFromSaved = parsed.filter(id => 
          movableColumnIds.includes(id)
        )
        const missingMovable = movableColumnIds.filter(id => 
          !parsed.includes(id)
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

    const savedSort = safeLocalStorageGet(`${tableId}-sort-state`)
    if (savedSort) {
      try {
        const parsed = JSON.parse(savedSort)
        if (parsed.field && columns.some(c => c.sortKey === parsed.field)) {
          setSortState(parsed)
        }
      } catch {
        // Keep default sort state
      }
    }
  }, [isHydrated, tableId, columns, defaultWidths, defaultOrder, movableColumnIds, fixedColumnIds])

  const isColumnFixed = useCallback((columnId: string): boolean => {
    return fixedColumnIds.includes(columnId)
  }, [fixedColumnIds])

  const handleSort = useCallback((field: string) => {
    setSortState(prev => {
      const newState: SortState = {
        field,
        order: prev.field === field ? (prev.order === 'asc' ? 'desc' : 'asc') : 'desc'
      }
      safeLocalStorageSet(`${tableId}-sort-state`, JSON.stringify(newState))
      return newState
    })
  }, [tableId])

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
        safeLocalStorageSet(`${tableId}-column-widths`, JSON.stringify(updated))
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
  }, [columnWidths, columns, tableId, defaultWidths, isColumnFixed])

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
      safeLocalStorageSet(`${tableId}-column-order`, JSON.stringify(movableOrderOnly))
      
      return newOrder
    })

    setDraggedColumnId(null)
    setDragOverColumnId(null)
  }, [draggedColumnId, tableId, fixedColumnIds, isColumnFixed])

  const handleColumnDragEnd = useCallback(() => {
    setDraggedColumnId(null)
    setDragOverColumnId(null)
  }, [])

  const resetColumnOrder = useCallback(() => {
    setColumnOrder(defaultOrder)
    safeLocalStorageRemove(`${tableId}-column-order`)
  }, [tableId, defaultOrder])

  const resetColumnWidths = useCallback(() => {
    setColumnWidths(defaultWidths)
    safeLocalStorageRemove(`${tableId}-column-widths`)
  }, [tableId, defaultWidths])

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
