"use client"

import { useState, useCallback, useMemo } from "react"
import type { TableColumn } from "../types"
import { useUIPreferencesStore } from "@/stores/ui-preferences-store"

export interface UseTableColumnsOptions {
  storageKey?: string
  defaultColumns: TableColumn[]
}

export function useTableColumns({ storageKey, defaultColumns }: UseTableColumnsOptions) {
  const { getTableColumnConfig, setTableColumnConfig, removeTableColumnConfig } = useUIPreferencesStore()

  const [columns, setColumns] = useState<TableColumn[]>(() => {
    if (storageKey) {
      try {
        const saved = getTableColumnConfig(storageKey)
        if (saved && saved.length > 0) {
          return defaultColumns.map(col => ({
            ...col,
            visible: saved.find((p) => p.id === col.id)?.visible ?? col.visible,
            order: saved.find((p) => p.id === col.id)?.order ?? col.order
          }))
        }
      } catch {
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
        setTableColumnConfig(storageKey, updated.map(({ id, visible, order }) => ({ id, visible: visible !== false, order: order ?? 0 })))
      }
      return updated
    })
  }, [storageKey, setTableColumnConfig])

  const showColumn = useCallback((columnId: string) => {
    setColumns(prev => {
      const updated = prev.map(col => 
        col.id === columnId ? { ...col, visible: true } : col
      )
      if (storageKey) {
        setTableColumnConfig(storageKey, updated.map(({ id, visible, order }) => ({ id, visible: visible !== false, order: order ?? 0 })))
      }
      return updated
    })
  }, [storageKey, setTableColumnConfig])

  const hideColumn = useCallback((columnId: string) => {
    setColumns(prev => {
      const updated = prev.map(col => 
        col.id === columnId ? { ...col, visible: false } : col
      )
      if (storageKey) {
        setTableColumnConfig(storageKey, updated.map(({ id, visible, order }) => ({ id, visible: visible !== false, order: order ?? 0 })))
      }
      return updated
    })
  }, [storageKey, setTableColumnConfig])

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
        setTableColumnConfig(storageKey, updated.map(({ id, visible, order }) => ({ id, visible: visible !== false, order: order ?? 0 })))
      }
      return updated
    })
  }, [storageKey, setTableColumnConfig])

  const resetColumns = useCallback(() => {
    setColumns(defaultColumns)
    if (storageKey) {
      removeTableColumnConfig(storageKey)
    }
  }, [defaultColumns, storageKey, removeTableColumnConfig])

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
