"use client"

import { useState, useEffect } from "react"

export interface JobsColumnWidths {
  [key: string]: number
  id: number
  vaga: number
  candidatos: number
  performance: number
  status: number
  recrutador: number
  gestor: number
  screeningStatus: number
  prazoTriagem: number
  prazoShortlist: number
  prazoEncerramento: number
  roteiro: number
  acoes: number
}

export interface UseJobsTableColumnsState {
  jobsColumnWidths: JobsColumnWidths
  jobsColumnOrder: string[]
  jobsSortColumn: string | null
  jobsSortDirection: 'asc' | 'desc'
  draggedJobColumnId: string | null
  dragOverJobColumnId: string | null
  resizingJobColumn: string | null
  showColumnConfig: boolean
}

export interface UseJobsTableColumnsActions {
  setJobsColumnWidths: React.Dispatch<React.SetStateAction<JobsColumnWidths>>
  setJobsColumnOrder: React.Dispatch<React.SetStateAction<string[]>>
  setJobsSortColumn: (column: string | null) => void
  setJobsSortDirection: (direction: 'asc' | 'desc') => void
  setShowColumnConfig: (show: boolean) => void
  handleJobsSort: (columnKey: string) => void
  startJobsColumnResize: (columnKey: string, e: React.MouseEvent) => void
  handleJobsColumnDragStart: (columnId: string, e: React.DragEvent) => void
  handleJobsColumnDragOver: (columnId: string, e: React.DragEvent) => void
  handleJobsColumnDragLeave: () => void
  handleJobsColumnDrop: (targetColumnId: string, e: React.DragEvent) => void
  handleJobsColumnDragEnd: () => void
  handleToggleColumnConfig: () => void
}

export interface UseJobsTableColumnsReturn {
  state: UseJobsTableColumnsState
  actions: UseJobsTableColumnsActions
}

const DEFAULT_COLUMN_WIDTHS: JobsColumnWidths = {
  id: 80,
  vaga: 200,
  candidatos: 100,
  performance: 180,
  status: 120,
  recrutador: 140,
  gestor: 140,
  screeningStatus: 100,
  prazoTriagem: 100,
  prazoShortlist: 100,
  prazoEncerramento: 100,
  roteiro: 100,
  acoes: 80,
}

const DEFAULT_COLUMN_ORDER = [
  'checkbox', 'id', 'vaga', 'candidatos', 'performance', 'status', 'screeningStatus',
  'recrutador', 'gestor', 'prazoTriagem', 'prazoShortlist', 'prazoEncerramento', 'acoes'
]

export function useJobsTableColumns(): UseJobsTableColumnsReturn {
  const [jobsColumnWidths, setJobsColumnWidths] = useState<JobsColumnWidths>(DEFAULT_COLUMN_WIDTHS)
  const [jobsColumnOrder, setJobsColumnOrder] = useState<string[]>(DEFAULT_COLUMN_ORDER)
  const [jobsSortColumn, setJobsSortColumn] = useState<string | null>(null)
  const [jobsSortDirection, setJobsSortDirection] = useState<'asc' | 'desc'>('asc')
  const [draggedJobColumnId, setDraggedJobColumnId] = useState<string | null>(null)
  const [dragOverJobColumnId, setDragOverJobColumnId] = useState<string | null>(null)
  const [resizingJobColumn, setResizingJobColumn] = useState<string | null>(null)
  const [showColumnConfig, setShowColumnConfig] = useState(false)

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
    const startWidth = jobsColumnWidths[columnKey as keyof typeof jobsColumnWidths] || 100
    let currentWidth = startWidth

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const diff = moveEvent.clientX - startX
      currentWidth = Math.max(50, startWidth + diff)
      setJobsColumnWidths(prev => ({ ...prev, [columnKey]: currentWidth }))
    }

    const handleMouseUp = () => {
      setResizingJobColumn(null)
      setJobsColumnWidths(prev => {
        const updatedWidths = { ...prev, [columnKey]: currentWidth }
        if (typeof window !== 'undefined') {
          localStorage.setItem('jobs-table-column-widths', JSON.stringify(updatedWidths))
        }
        return updatedWidths
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

  const handleJobsColumnDragLeave = () => {
    setDragOverJobColumnId(null)
  }

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

      if (typeof window !== 'undefined') {
        localStorage.setItem('jobs-table-column-order', JSON.stringify(newOrder))
      }

      return newOrder
    })

    setDraggedJobColumnId(null)
    setDragOverJobColumnId(null)
  }

  const handleJobsColumnDragEnd = () => {
    setDraggedJobColumnId(null)
    setDragOverJobColumnId(null)
  }

  const handleToggleColumnConfig = () => {
    setShowColumnConfig(!showColumnConfig)
  }

  useEffect(() => {
    if (typeof window === 'undefined') return

    const savedOrder = localStorage.getItem('jobs-table-column-order')
    if (savedOrder) {
      try {
        const parsed = JSON.parse(savedOrder) as string[]
        const savedCols = parsed.filter((id: string) => DEFAULT_COLUMN_ORDER.includes(id))
        const missingCols = DEFAULT_COLUMN_ORDER.filter(id => !parsed.includes(id) && id !== 'checkbox' && id !== 'acoes')
        const innerCols = savedCols.filter((id: string) => id !== 'checkbox' && id !== 'acoes')
        const acoesIndex = innerCols.length
        innerCols.splice(acoesIndex, 0, ...missingCols)
        const finalOrder = ['checkbox', ...innerCols, 'acoes']
        setJobsColumnOrder(finalOrder)
      } catch (e) {
      }
    }

    const savedWidths = localStorage.getItem('jobs-table-column-widths')
    if (savedWidths) {
      try {
        const parsed = JSON.parse(savedWidths)
        setJobsColumnWidths(prev => ({ ...prev, ...parsed }))
      } catch (e) {
      }
    }
  }, [])

  return {
    state: {
      jobsColumnWidths,
      jobsColumnOrder,
      jobsSortColumn,
      jobsSortDirection,
      draggedJobColumnId,
      dragOverJobColumnId,
      resizingJobColumn,
      showColumnConfig,
    },
    actions: {
      setJobsColumnWidths,
      setJobsColumnOrder,
      setJobsSortColumn,
      setJobsSortDirection,
      setShowColumnConfig,
      handleJobsSort,
      startJobsColumnResize,
      handleJobsColumnDragStart,
      handleJobsColumnDragOver,
      handleJobsColumnDragLeave,
      handleJobsColumnDrop,
      handleJobsColumnDragEnd,
      handleToggleColumnConfig,
    },
  }
}
