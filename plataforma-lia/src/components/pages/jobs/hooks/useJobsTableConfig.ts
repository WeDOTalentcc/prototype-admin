"use client"

import React, { useState, useEffect } from "react"
import { useJobColumnConfig } from "@/hooks/jobs/useJobColumnConfig"
import { useUIPreferencesStore } from "@/stores/ui-preferences-store"

// ---------------------------------------------------------------------------
// useJobsTableConfig
// Responsável por: configuração de colunas visíveis (useJobColumnConfig),
// widths de colunas (resize), ordem das colunas (drag & drop), sort.
// ---------------------------------------------------------------------------

interface UseJobsTableConfigReturn {
  state: {
    columnConfig: ReturnType<typeof useJobColumnConfig>['columns']
    visibleColumnIds: string[]
    savedColumnViews: ReturnType<typeof useJobColumnConfig>['savedViews']
    showColumnConfig: boolean
    jobsColumnWidths: Record<string, number>
    jobsColumnOrder: string[]
    jobsSortColumn: string | null
    jobsSortDirection: 'asc' | 'desc'
    draggedJobColumnId: string | null
    dragOverJobColumnId: string | null
    resizingJobColumn: string | null
    hookToTableColumnMap: Record<string, string>
  }
  actions: {
    toggleColumn: ReturnType<typeof useJobColumnConfig>['toggleColumn']
    resetColumnsToDefault: ReturnType<typeof useJobColumnConfig>['resetToDefault']
    saveColumnView: ReturnType<typeof useJobColumnConfig>['saveView']
    applyColumnView: ReturnType<typeof useJobColumnConfig>['applyView']
    deleteColumnView: ReturnType<typeof useJobColumnConfig>['deleteView']
    getColumnsByCategory: ReturnType<typeof useJobColumnConfig>['getColumnsByCategory']
    setShowColumnConfig: (v: boolean) => void
    handleToggleColumnConfig: () => void
    handleJobsSort: (columnKey: string) => void
    startJobsColumnResize: (columnKey: string, e: React.MouseEvent) => void
    handleJobsColumnDragStart: (columnId: string, e: React.DragEvent) => void
    handleJobsColumnDragOver: (columnId: string, e: React.DragEvent) => void
    handleJobsColumnDragLeave: () => void
    handleJobsColumnDrop: (targetColumnId: string, e: React.DragEvent) => void
    handleJobsColumnDragEnd: () => void
  }
}

const DEFAULT_COLUMN_ORDER = [
  'checkbox', 'id', 'vaga', 'candidatos', 'performance', 'status',
  'screeningStatus', 'prontidao', 'recrutador', 'gestor', 'prazoTriagem', 'prazoShortlist', 'prazoEncerramento', 'acoes',
]

const DEFAULT_COLUMN_WIDTHS: Record<string, number> = {
  id: 80, vaga: 200, candidatos: 100, performance: 180, status: 120,
  recrutador: 140, gestor: 140, screeningStatus: 100, prontidao: 140, prazoTriagem: 100,
  prazoShortlist: 100, prazoEncerramento: 100, roteiro: 100, acoes: 80,
}

const HOOK_TO_TABLE_COLUMN_MAP: Record<string, string> = {
  'id': 'id', 'status': 'status', 'screeningStatus': 'screeningStatus',
  'title': 'vaga', 'candidates': 'candidatos', 'performance': 'performance',
  'recruiter': 'recrutador', 'manager': 'gestor', 'deadlineScreening': 'prazoTriagem',
  'deadlineShortlist': 'prazoShortlist', 'deadlineClosing': 'prazoEncerramento',
  'readiness': 'prontidao',
}

export function useJobsTableConfig(): UseJobsTableConfigReturn {
  const {
    columns: columnConfig,
    visibleColumnIds,
    savedViews: savedColumnViews,
    toggleColumn,
    resetToDefault: resetColumnsToDefault,
    saveView: saveColumnView,
    applyView: applyColumnView,
    deleteView: deleteColumnView,
    getColumnsByCategory,
  } = useJobColumnConfig()

  const [showColumnConfig, setShowColumnConfig] = useState(false)
  const [jobsColumnWidths, setJobsColumnWidths] = useState<Record<string, number>>(DEFAULT_COLUMN_WIDTHS)
  const [jobsColumnOrder, setJobsColumnOrder] = useState<string[]>(DEFAULT_COLUMN_ORDER)
  const [jobsSortColumn, setJobsSortColumn] = useState<string | null>(null)
  const [jobsSortDirection, setJobsSortDirection] = useState<'asc' | 'desc'>('asc')
  const [draggedJobColumnId, setDraggedJobColumnId] = useState<string | null>(null)
  const [dragOverJobColumnId, setDragOverJobColumnId] = useState<string | null>(null)
  const [resizingJobColumn, setResizingJobColumn] = useState<string | null>(null)

  const storedJobsColumnOrder = useUIPreferencesStore(s => s.jobsTableColumnOrder)
  const storedJobsColumnWidths = useUIPreferencesStore(s => s.jobsTableColumnWidths)
  const setStoredJobsColumnOrder = useUIPreferencesStore(s => s.setJobsTableColumnOrder)
  const setStoredJobsColumnWidths = useUIPreferencesStore(s => s.setJobsTableColumnWidths)

  useEffect(() => {
    if (typeof window === 'undefined') return

    if (storedJobsColumnOrder) {
      try {
        const parsed = storedJobsColumnOrder
        const savedCols = parsed.filter((id: string) => DEFAULT_COLUMN_ORDER.includes(id))
        const missingCols = DEFAULT_COLUMN_ORDER.filter(id => !parsed.includes(id) && id !== 'checkbox' && id !== 'acoes')
        const innerCols = savedCols.filter((id: string) => id !== 'checkbox' && id !== 'acoes')
        innerCols.splice(innerCols.length, 0, ...missingCols)
        setJobsColumnOrder(['checkbox', ...innerCols, 'acoes'])
      } catch {
      }
    }

    if (storedJobsColumnWidths) {
      try {
        setJobsColumnWidths(prev => ({ ...prev, ...storedJobsColumnWidths }))
      } catch {
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleToggleColumnConfig = () => setShowColumnConfig(prev => !prev)

  const handleJobsSort = (columnKey: string) => {
    if (jobsSortColumn === columnKey) {
      setJobsSortDirection(prev => prev === 'asc' ? 'desc' : 'asc')
    } else {
      setJobsSortColumn(columnKey)
      setJobsSortDirection('asc')
    }
  }

  const startJobsColumnResize = (columnKey: string, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setResizingJobColumn(columnKey)
    const startX = e.clientX
    const startWidth = jobsColumnWidths[columnKey] || 100
    let currentWidth = startWidth

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const diff = moveEvent.clientX - startX
      currentWidth = Math.max(50, startWidth + diff)
      setJobsColumnWidths(prev => ({ ...prev, [columnKey]: currentWidth }))
    }

    const handleMouseUp = () => {
      setResizingJobColumn(null)
      setJobsColumnWidths(prev => {
        const updated = { ...prev, [columnKey]: currentWidth }
        setStoredJobsColumnWidths(updated)
        return updated
      })
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }

  const handleJobsColumnDragStart = (columnId: string, e: React.DragEvent) => {
    if (columnId === 'checkbox' || columnId === 'acoes') return
    setDraggedJobColumnId(columnId)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleJobsColumnDragOver = (columnId: string, e: React.DragEvent) => {
    e.preventDefault()
    if (columnId === 'checkbox' || columnId === 'acoes') return
    if (draggedJobColumnId && draggedJobColumnId !== columnId) {
      setDragOverJobColumnId(columnId)
    }
  }

  const handleJobsColumnDragLeave = () => setDragOverJobColumnId(null)

  const handleJobsColumnDrop = (targetColumnId: string, e: React.DragEvent) => {
    e.preventDefault()
    if (!draggedJobColumnId || targetColumnId === 'checkbox' || targetColumnId === 'acoes') {
      setDraggedJobColumnId(null)
      setDragOverJobColumnId(null)
      return
    }

    setJobsColumnOrder(prev => {
      const newOrder = [...prev]
      const draggedIndex = newOrder.indexOf(draggedJobColumnId)
      const targetIndex = newOrder.indexOf(targetColumnId)
      if (draggedIndex === -1 || targetIndex === -1) return prev
      newOrder.splice(draggedIndex, 1)
      newOrder.splice(targetIndex, 0, draggedJobColumnId)
      setStoredJobsColumnOrder(newOrder)
      return newOrder
    })

    setDraggedJobColumnId(null)
    setDragOverJobColumnId(null)
  }

  const handleJobsColumnDragEnd = () => {
    setDraggedJobColumnId(null)
    setDragOverJobColumnId(null)
  }

  return {
    state: {
      columnConfig,
      visibleColumnIds,
      savedColumnViews,
      showColumnConfig,
      jobsColumnWidths,
      jobsColumnOrder,
      jobsSortColumn,
      jobsSortDirection,
      draggedJobColumnId,
      dragOverJobColumnId,
      resizingJobColumn,
      hookToTableColumnMap: HOOK_TO_TABLE_COLUMN_MAP,
    },
    actions: {
      toggleColumn,
      resetColumnsToDefault,
      saveColumnView,
      applyColumnView,
      deleteColumnView,
      getColumnsByCategory,
      setShowColumnConfig,
      handleToggleColumnConfig,
      handleJobsSort,
      startJobsColumnResize,
      handleJobsColumnDragStart,
      handleJobsColumnDragOver,
      handleJobsColumnDragLeave,
      handleJobsColumnDrop,
      handleJobsColumnDragEnd,
    },
  }
}
