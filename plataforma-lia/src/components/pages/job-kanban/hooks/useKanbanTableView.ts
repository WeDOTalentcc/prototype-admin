"use client"

import { useState, useEffect, useCallback, useMemo, useRef } from "react"
import { type TableColumn, getDefaultTableColumns } from "@/components/tables"
import { type DynamicStage } from "@/components/pages/job-kanban/utils/kanbanStageUtils"
import { calculateNotaLiaGeral } from "@/components/pages/job-kanban/utils/kanbanHelpers"
import { useUIPreferencesStore } from "@/stores/ui-preferences-store"

export function useKanbanTableView({
  dynamicStages,
  candidatesData,
  viewMode,
}: {
  dynamicStages: DynamicStage[]
  candidatesData: Record<string, Record<string, unknown>[]>
  viewMode: string
}) {
  // Column config
  const [showColumnConfig, setShowColumnConfig] = useState(false)
  const [tableColumns, setTableColumns] = useState<TableColumn[]>(() => getDefaultTableColumns())
  const [columnSearchTerm, setColumnSearchTerm] = useState('')

  // Filter panels
  const [showTableFiltersPanel, setShowTableFiltersPanel] = useState(false)
  const [showKanbanFiltersPanel, setShowKanbanFiltersPanel] = useState(false)

  // Kanban-specific filters
  const [kanbanScoreMin, setKanbanScoreMin] = useState(0)
  const [kanbanStatusFilter, setKanbanStatusFilter] = useState<string[]>([])
  const [kanbanWorkModelFilter, setKanbanWorkModelFilter] = useState<string[]>([])
  const [kanbanOriginFilter, setKanbanOriginFilter] = useState<string[]>([])

  // Table sort
  const [tableSortColumn, setTableSortColumn] = useState<string>('notaLiaGeral')
  const [tableSortDirection, setTableSortDirection] = useState<'asc' | 'desc'>('desc')
  const [tableStageFilter, setTableStageFilter] = useState<string[]>([])
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 50

  // Column widths
  const [tableColumnWidths, setTableColumnWidths] = useState({
    checkbox: 50, id: 70, notaLiaGeral: 100, scoreLiaTriagem: 100,
    scoreLiaCV: 100, testeTecnico: 90, testeIngles: 80, bigFive: 90,
    alertas: 50, candidato: 200, cargo: 150, empresa: 130, etapa: 110,
    status: 100, acoes: 100
  })

  // Drag & drop for table columns
  const [draggedTableColumnId, setDraggedTableColumnId] = useState<string | null>(null)
  const [dragOverTableColumnId, setDragOverTableColumnId] = useState<string | null>(null)
  const defaultColumnOrder = [
    'checkbox', 'id', 'notaLiaGeral', 'scoreLiaTriagem', 'scoreLiaCV', 'testeTecnico',
    'testeIngles', 'bigFive', 'alertas', 'candidato', 'cargo', 'empresa', 'etapa', 'status', 'acoes'
  ]
  const [tableColumnOrder, setTableColumnOrder] = useState<string[]>(defaultColumnOrder)

  const storedKanbanColumnOrder = useUIPreferencesStore(s => s.jobKanbanTableColumnOrder)
  const setStoredKanbanColumnOrder = useUIPreferencesStore(s => s.setJobKanbanTableColumnOrder)

  useEffect(() => {
    if (storedKanbanColumnOrder) {
      try {
        const parsed = storedKanbanColumnOrder
        const validOrder = defaultColumnOrder.filter(id => parsed.includes(id))
        if (validOrder.length === defaultColumnOrder.length) {
          const orderedCols = parsed.filter((id: string) => defaultColumnOrder.includes(id))
          const finalOrder = ['checkbox', ...orderedCols.filter((id: string) => id !== 'checkbox' && id !== 'acoes'), 'acoes']
          setTableColumnOrder(finalOrder)
        } else {
          setTableColumnOrder(defaultColumnOrder)
        }
      } catch {
        setTableColumnOrder(defaultColumnOrder)
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: run only on mount to restore saved column order
  }, [])

  // Close panels when view mode changes
  useEffect(() => {
    setShowTableFiltersPanel(false)
    setShowKanbanFiltersPanel(false)
    setShowColumnConfig(false)
  }, [viewMode])

  // Stable column resize handler
  const handleTableColumnResize = useCallback((columnId: string, width: number) => {
    setTableColumnWidths(prev => ({ ...prev, [columnId]: width }))
  }, [])

  // Table sort
  const handleTableSort = (column: string) => {
    if (tableSortColumn === column) {
      setTableSortDirection(tableSortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setTableSortColumn(column)
      setTableSortDirection('asc')
    }
  }

  // Column resize (mouse-based)
  const startTableColumnResize = (column: string, event: React.MouseEvent) => {
    event.preventDefault()
    event.stopPropagation()
    const startX = event.clientX
    const startWidth = tableColumnWidths[column as keyof typeof tableColumnWidths] || 100
    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = Math.max(50, startWidth + (e.clientX - startX))
      setTableColumnWidths(prev => ({ ...prev, [column]: newWidth }))
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
  }

  // Column drag & drop
  const handleTableColumnDragStart = (columnId: string, e: React.DragEvent) => {
    if (columnId === 'checkbox' || columnId === 'acoes') return
    setDraggedTableColumnId(columnId)
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', columnId)
    const dragImage = document.createElement('div')
    dragImage.style.opacity = '0'
    document.body.appendChild(dragImage)
    e.dataTransfer.setDragImage(dragImage, 0, 0)
    setTimeout(() => document.body.removeChild(dragImage), 0)
  }

  const handleTableColumnDragOver = (columnId: string, e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    if (draggedTableColumnId && draggedTableColumnId !== columnId && columnId !== 'checkbox' && columnId !== 'acoes') {
      setDragOverTableColumnId(columnId)
    }
  }

  const handleTableColumnDragLeave = () => { setDragOverTableColumnId(null) }

  const handleTableColumnDrop = (targetColumnId: string, e: React.DragEvent) => {
    e.preventDefault()
    if (!draggedTableColumnId || draggedTableColumnId === targetColumnId) {
      setDraggedTableColumnId(null); setDragOverTableColumnId(null); return
    }
    if (targetColumnId === 'checkbox' || targetColumnId === 'acoes') {
      setDraggedTableColumnId(null); setDragOverTableColumnId(null); return
    }
    setTableColumnOrder(prev => {
      const newOrder = [...prev]
      const draggedIndex = newOrder.indexOf(draggedTableColumnId)
      const targetIndex = newOrder.indexOf(targetColumnId)
      if (draggedIndex === -1 || targetIndex === -1) return prev
      newOrder.splice(draggedIndex, 1)
      newOrder.splice(targetIndex, 0, draggedTableColumnId)
      setStoredKanbanColumnOrder(newOrder)
      return newOrder
    })
    setDraggedTableColumnId(null); setDragOverTableColumnId(null)
  }

  const handleTableColumnDragEnd = () => {
    setDraggedTableColumnId(null); setDragOverTableColumnId(null)
  }

  // Flatten all candidates for table view
   
  const getAllCandidates = useCallback(() => {
    const allCandidates: Record<string, unknown>[] = []
    const stageMapping: Record<string, { name: string; color: string }> = {}
    dynamicStages.forEach(stage => {
      let color = 'bg-lia-bg-tertiary text-lia-text-primary'
      if (stage.isHired) color = 'bg-lia-btn-primary-bg text-lia-btn-primary-text dark:bg-lia-bg-secondary font-bold'
      else if (stage.isRejection || stage.id === 'offer_declined') color = 'bg-lia-border-medium text-lia-text-primary dark:bg-lia-bg-elevated font-medium'
      else if (stage.stageType === 'final') color = 'bg-lia-border-default text-lia-text-primary dark:bg-lia-bg-elevated font-bold'
      stageMapping[stage.id] = { name: stage.displayName, color }
    })
    Object.entries(candidatesData).forEach(([stage, candidates]) => {
      if (candidates && Array.isArray(candidates)) {
        candidates.forEach(candidate => {
          allCandidates.push({
            ...candidate,
            stage: stageMapping[stage]?.name || stage,
            stageColor: stageMapping[stage]?.color || 'bg-lia-bg-tertiary text-lia-text-primary'
          })
        })
      }
    })
    return allCandidates
  }, [dynamicStages, candidatesData])

  // Filter + sort for table view
  const getFilteredAndSortedCandidates = (searchQuery: string) => {
    let candidates = getAllCandidates()
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      candidates = candidates.filter((c: Record<string, unknown>) =>
        ((c.name as string) || '').toLowerCase().includes(query) ||
        ((c.role as string) || '').toLowerCase().includes(query) ||
        ((c.location as string) || '').toLowerCase().includes(query) ||
        ((c.currentCompany as string) || '').toLowerCase().includes(query)
      )
    }
    if (tableStageFilter.length > 0) {
      candidates = candidates.filter((c: Record<string, unknown>) => tableStageFilter.includes(c.stage as string))
    }
    candidates.sort((a: Record<string, unknown>, b: Record<string, unknown>) => {
      let aVal: string | number, bVal: string | number
      switch (tableSortColumn) {
        case 'name': aVal = ((a.name as string) || '').toLowerCase(); bVal = ((b.name as string) || '').toLowerCase(); break
        case 'scoreLiaTriagem': aVal = (a.liaScore as number) || (a.score as number) || 0; bVal = (b.liaScore as number) || (b.score as number) || 0; break
        case 'scoreLiaCV': aVal = (a.skillsMatch as number) || (a.fitScore as number) || 0; bVal = (b.skillsMatch as number) || (b.fitScore as number) || 0; break
        case 'testeTecnico': aVal = (a.technicalTestScore as number) || 0; bVal = (b.technicalTestScore as number) || 0; break
        case 'testeIngles': aVal = (a.englishTestScore as number) || 0; bVal = (b.englishTestScore as number) || 0; break
        case 'location': aVal = ((a.location as string) || '').toLowerCase(); bVal = ((b.location as string) || '').toLowerCase(); break
        case 'stage': aVal = ((a.stage as string) || '').toLowerCase(); bVal = ((b.stage as string) || '').toLowerCase(); break
        default: aVal = calculateNotaLiaGeral(a as unknown as Parameters<typeof calculateNotaLiaGeral>[0]); bVal = calculateNotaLiaGeral(b as unknown as Parameters<typeof calculateNotaLiaGeral>[0])
      }
      if (aVal < bVal) return tableSortDirection === 'asc' ? -1 : 1
      if (aVal > bVal) return tableSortDirection === 'asc' ? 1 : -1
      return 0
    })
    return candidates
  }

  // Pagination
  const getPaginatedCandidates = (searchQuery: string) => {
    const filtered = getFilteredAndSortedCandidates(searchQuery)
    const startIndex = (currentPage - 1) * itemsPerPage
    const endIndex = startIndex + itemsPerPage
    return { candidates: filtered.slice(startIndex, endIndex), total: filtered.length, totalPages: Math.ceil(filtered.length / itemsPerPage) }
  }

  // Stage filter helpers
  const toggleStageFilter = (stageName: string) => {
    setTableStageFilter(prev => prev.includes(stageName) ? prev.filter(s => s !== stageName) : [...prev, stageName])
    setCurrentPage(1)
  }
  const clearStageFilters = () => { setTableStageFilter([]); setCurrentPage(1) }
  const getStageCount = (stageName: string) => getAllCandidates().filter(c => c.stage === stageName).length

  const getConversionRate = (currentStage: string) => {
    const stageOrder = ['Funil', 'Triagem', 'Entrevista', 'Final', 'Aprovados', 'Reprovados']
    const currentIndex = stageOrder.indexOf(currentStage)
    if (currentIndex <= 0) return null
    const previousStage = stageOrder[currentIndex - 1]
    const previousCount = getStageCount(previousStage)
    const currentCount = getStageCount(currentStage)
    if (previousCount === 0) return null
    const rate = Math.round((currentCount / previousCount) * 100)
    return {
      rate, previousStage,
      color: rate >= 70 ? 'text-lia-text-secondary' : rate >= 50 ? 'text-lia-text-primary' : 'text-lia-text-secondary'
    }
  }

  // Pipeline stages (for table header)
  const pipelineStages = useMemo(() =>
    dynamicStages.map(stage => ({
      id: stage.id, name: stage.displayName,
      color: stage.isHired ? 'bg-lia-bg-tertiary text-lia-text-primary font-medium' : 'bg-lia-bg-tertiary text-lia-text-primary',
      count: candidatesData[stage.id]?.length || 0
    })),
    [dynamicStages, candidatesData]
  )

  // Kanban columns (for kanban board)
  const kanbanColumns = useMemo(() =>
    dynamicStages.map(stage => ({
      id: stage.id, title: stage.displayName,
      count: candidatesData[stage.id]?.length || 0,
      color: 'bg-lia-bg-secondary border-lia-border-subtle', stageColor: stage.color
    })),
    [dynamicStages, candidatesData]
  )

  return {
    state: {
      showColumnConfig, tableColumns, columnSearchTerm,
      showTableFiltersPanel, showKanbanFiltersPanel,
      kanbanScoreMin, kanbanStatusFilter, kanbanWorkModelFilter, kanbanOriginFilter,
      tableSortColumn, tableSortDirection, tableStageFilter, currentPage, itemsPerPage,
      tableColumnWidths, draggedTableColumnId, dragOverTableColumnId, tableColumnOrder,
      pipelineStages, kanbanColumns,
    },
    actions: {
      setShowColumnConfig, setTableColumns, setColumnSearchTerm,
      setShowTableFiltersPanel, setShowKanbanFiltersPanel,
      setKanbanScoreMin, setKanbanStatusFilter, setKanbanWorkModelFilter, setKanbanOriginFilter,
      setTableSortColumn, setTableSortDirection, setTableStageFilter, setCurrentPage,
      setTableColumnWidths, setDraggedTableColumnId, setDragOverTableColumnId, setTableColumnOrder,
      handleTableColumnResize, handleTableSort, startTableColumnResize,
      handleTableColumnDragStart, handleTableColumnDragOver, handleTableColumnDragLeave,
      handleTableColumnDrop, handleTableColumnDragEnd,
      getAllCandidates, getFilteredAndSortedCandidates, getPaginatedCandidates,
      toggleStageFilter, clearStageFilters, getStageCount, getConversionRate,
    },
  }
}

export type KanbanTableViewState = ReturnType<typeof useKanbanTableView>
