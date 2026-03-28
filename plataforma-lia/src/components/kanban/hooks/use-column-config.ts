'use client'

import { useState, useEffect, useCallback } from 'react'

export const DEFAULT_COLUMN_ORDER = [
  'checkbox', 'id', 'notaLiaGeral', 'scoreLiaTriagem', 'scoreLiaCV', 'testeTecnico', 
  'testeIngles', 'bigFive', 'alertas', 'candidato', 'cargo', 'empresa', 'etapa', 'status', 'acoes'
] as const

export type ColumnId = typeof DEFAULT_COLUMN_ORDER[number]

export interface UseColumnConfigOptions {
  storageKey?: string
  defaultOrder?: string[]
}

export interface UseColumnConfigReturn {
  columnOrder: string[]
  setColumnOrder: (order: string[] | ((prev: string[]) => string[])) => void
  draggedColumnId: string | null
  setDraggedColumnId: (id: string | null) => void
  dragOverColumnId: string | null
  setDragOverColumnId: (id: string | null) => void
  handleColumnDragStart: (columnId: string) => void
  handleColumnDragOver: (columnId: string, e: React.DragEvent) => void
  handleColumnDrop: (targetColumnId: string, e: React.DragEvent) => void
  handleColumnDragEnd: () => void
  resetColumnOrder: () => void
}

export function useColumnConfig(options: UseColumnConfigOptions = {}): UseColumnConfigReturn {
  const {
    storageKey = 'job-kanban-table-column-order',
    defaultOrder = [...DEFAULT_COLUMN_ORDER]
  } = options

  const [columnOrder, setColumnOrder] = useState<string[]>(defaultOrder)
  const [draggedColumnId, setDraggedColumnId] = useState<string | null>(null)
  const [dragOverColumnId, setDragOverColumnId] = useState<string | null>(null)

  useEffect(() => {
    if (typeof window === 'undefined') return
    
    const savedOrder = localStorage.getItem(storageKey)
    
    if (savedOrder) {
      try {
        const parsed = JSON.parse(savedOrder) as string[]
        const validOrder = defaultOrder.filter(id => parsed.includes(id))
        
        if (validOrder.length === defaultOrder.length) {
          const orderedCols = parsed.filter((id: string) => defaultOrder.includes(id))
          const finalOrder = ['checkbox', ...orderedCols.filter((id: string) => id !== 'checkbox' && id !== 'acoes'), 'acoes']
          setColumnOrder(finalOrder)
        } else {
          setColumnOrder(defaultOrder)
        }
      } catch (e) {
        setColumnOrder(defaultOrder)
      }
    }
  }, [storageKey, defaultOrder])

  const handleColumnDragStart = useCallback((columnId: string) => {
    if (columnId === 'checkbox' || columnId === 'acoes') return
    setDraggedColumnId(columnId)
  }, [])

  const handleColumnDragOver = useCallback((columnId: string, e: React.DragEvent) => {
    e.preventDefault()
    if (columnId === 'checkbox' || columnId === 'acoes') return
    setDragOverColumnId(columnId)
  }, [])

  const handleColumnDrop = useCallback((targetColumnId: string, e: React.DragEvent) => {
    e.preventDefault()
    if (!draggedColumnId || draggedColumnId === targetColumnId) {
      setDraggedColumnId(null)
      setDragOverColumnId(null)
      return
    }

    if (targetColumnId === 'checkbox' || targetColumnId === 'acoes') {
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
      
      if (typeof window !== 'undefined') {
        localStorage.setItem(storageKey, JSON.stringify(newOrder))
      }
      
      return newOrder
    })

    setDraggedColumnId(null)
    setDragOverColumnId(null)
  }, [draggedColumnId, storageKey])

  const handleColumnDragEnd = useCallback(() => {
    setDraggedColumnId(null)
    setDragOverColumnId(null)
  }, [])

  const resetColumnOrder = useCallback(() => {
    setColumnOrder(defaultOrder)
    if (typeof window !== 'undefined') {
      localStorage.removeItem(storageKey)
    }
  }, [defaultOrder, storageKey])

  return {
    columnOrder,
    setColumnOrder,
    draggedColumnId,
    setDraggedColumnId,
    dragOverColumnId,
    setDragOverColumnId,
    handleColumnDragStart,
    handleColumnDragOver,
    handleColumnDrop,
    handleColumnDragEnd,
    resetColumnOrder
  }
}
