"use client"

import { useState, useCallback, useMemo } from "react"
import type { TableColumn } from "../types"

export interface UseTableColumnsOptions {
  storageKey?: string
  defaultColumns: TableColumn[]
}

export function useTableColumns({ storageKey, defaultColumns }: UseTableColumnsOptions) {
  const [columns, setColumns] = useState<TableColumn[]>(() => {
    if (storageKey && typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem(storageKey)
        if (saved) {
          const parsed = JSON.parse(saved)
          return defaultColumns.map(col => ({
            ...col,
            visible: parsed.find((p: { id: string; visible: boolean }) => p.id === col.id)?.visible ?? col.visible,
            order: parsed.find((p: { id: string; order: number }) => p.id === col.id)?.order ?? col.order
          }))
        }
      } catch {
        // Ignore parse errors
      }
    }
    return defaultColumns
  })

  const visibleColumns = useMemo(() => 
    columns
      .filter(col => col.visible !== false)
      .sort((a, b) => (a.order ?? 0) - (b.order ?? 0)),
    [columns]
  )

  const toggleColumn = useCallback((columnId: string) => {
    setColumns(prev => {
      const updated = prev.map(col => 
        col.id === columnId ? { ...col, visible: !col.visible } : col
      )
      if (storageKey) {
        localStorage.setItem(storageKey, JSON.stringify(
          updated.map(({ id, visible, order }) => ({ id, visible, order }))
        ))
      }
      return updated
    })
  }, [storageKey])

  const showColumn = useCallback((columnId: string) => {
    setColumns(prev => {
      const updated = prev.map(col => 
        col.id === columnId ? { ...col, visible: true } : col
      )
      if (storageKey) {
        localStorage.setItem(storageKey, JSON.stringify(
          updated.map(({ id, visible, order }) => ({ id, visible, order }))
        ))
      }
      return updated
    })
  }, [storageKey])

  const hideColumn = useCallback((columnId: string) => {
    setColumns(prev => {
      const updated = prev.map(col => 
        col.id === columnId ? { ...col, visible: false } : col
      )
      if (storageKey) {
        localStorage.setItem(storageKey, JSON.stringify(
          updated.map(({ id, visible, order }) => ({ id, visible, order }))
        ))
      }
      return updated
    })
  }, [storageKey])

  const reorderColumns = useCallback((fromIndex: number, toIndex: number) => {
    setColumns(prev => {
      const visible = prev.filter(c => c.visible !== false).sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
      const [moved] = visible.splice(fromIndex, 1)
      visible.splice(toIndex, 0, moved)
      
      const updated = prev.map(col => {
        const newOrder = visible.findIndex(v => v.id === col.id)
        return newOrder >= 0 ? { ...col, order: newOrder } : col
      })

      if (storageKey) {
        localStorage.setItem(storageKey, JSON.stringify(
          updated.map(({ id, visible, order }) => ({ id, visible, order }))
        ))
      }
      return updated
    })
  }, [storageKey])

  const resetColumns = useCallback(() => {
    setColumns(defaultColumns)
    if (storageKey) {
      localStorage.removeItem(storageKey)
    }
  }, [defaultColumns, storageKey])

  const getColumnById = useCallback((columnId: string) => 
    columns.find(col => col.id === columnId),
    [columns]
  )

  const isColumnVisible = useCallback((columnId: string) => {
    const column = columns.find(col => col.id === columnId)
    return column?.visible !== false
  }, [columns])

  return {
    columns,
    visibleColumns,
    setColumns,
    toggleColumn,
    showColumn,
    hideColumn,
    reorderColumns,
    resetColumns,
    getColumnById,
    isColumnVisible
  }
}
