"use client"

import { useState, useCallback, useRef, useEffect } from "react"

export interface TableColumn {
  id: string
  label: string
  visible: boolean
  order: number
  minWidth?: number
  maxWidth?: number
  sortable?: boolean
}

export interface SortConfig {
  column: string | null
  direction: "asc" | "desc"
}

export interface UseTableFeaturesOptions {
  initialColumns: TableColumn[]
  initialWidths: Record<string, number>
  initialSort?: SortConfig
  minColumnWidth?: number
  storageKey?: string
}

export function useTableFeatures({
  initialColumns,
  initialWidths,
  initialSort = { column: null, direction: "asc" },
  minColumnWidth = 60,
  storageKey,
}: UseTableFeaturesOptions) {
  const [columns, setColumns] = useState<TableColumn[]>(initialColumns)
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>(initialWidths)
  const [sortConfig, setSortConfig] = useState<SortConfig>(initialSort)
  const [draggedColumn, setDraggedColumn] = useState<string | null>(null)
  const [dragOverColumn, setDragOverColumn] = useState<string | null>(null)
  const [isResizing, setIsResizing] = useState(false)
  const resizeRef = useRef<{ columnId: string; startX: number; startWidth: number } | null>(null)

  useEffect(() => {
    if (storageKey) {
      const savedWidths = localStorage.getItem(`${storageKey}-widths`)
      const savedColumns = localStorage.getItem(`${storageKey}-columns`)
      const savedSort = localStorage.getItem(`${storageKey}-sort`)
      
      if (savedWidths) {
        try {
          setColumnWidths(JSON.parse(savedWidths))
        } catch (e) {}
      }
      if (savedColumns) {
        try {
          setColumns(JSON.parse(savedColumns))
        } catch (e) {}
      }
      if (savedSort) {
        try {
          setSortConfig(JSON.parse(savedSort))
        } catch (e) {}
      }
    }
  }, [storageKey])

  useEffect(() => {
    if (storageKey) {
      localStorage.setItem(`${storageKey}-widths`, JSON.stringify(columnWidths))
    }
  }, [columnWidths, storageKey])

  useEffect(() => {
    if (storageKey) {
      localStorage.setItem(`${storageKey}-columns`, JSON.stringify(columns))
    }
  }, [columns, storageKey])

  useEffect(() => {
    if (storageKey) {
      localStorage.setItem(`${storageKey}-sort`, JSON.stringify(sortConfig))
    }
  }, [sortConfig, storageKey])

  const handleResizeStart = useCallback((columnId: string, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsResizing(true)
    resizeRef.current = {
      columnId,
      startX: e.clientX,
      startWidth: columnWidths[columnId] || 100,
    }

    const handleMouseMove = (e: MouseEvent) => {
      if (!resizeRef.current) return
      const diff = e.clientX - resizeRef.current.startX
      const newWidth = Math.max(minColumnWidth, resizeRef.current.startWidth + diff)
      setColumnWidths((prev) => ({
        ...prev,
        [resizeRef.current!.columnId]: newWidth,
      }))
    }

    const handleMouseUp = () => {
      setIsResizing(false)
      resizeRef.current = null
      document.removeEventListener("mousemove", handleMouseMove)
      document.removeEventListener("mouseup", handleMouseUp)
      document.body.style.cursor = ""
      document.body.style.userSelect = ""
    }

    document.addEventListener("mousemove", handleMouseMove)
    document.addEventListener("mouseup", handleMouseUp)
    document.body.style.cursor = "col-resize"
    document.body.style.userSelect = "none"
  }, [columnWidths, minColumnWidth])

  const handleSort = useCallback((columnId: string) => {
    setSortConfig((prev) => ({
      column: columnId,
      direction: prev.column === columnId && prev.direction === "asc" ? "desc" : "asc",
    }))
  }, [])

  const handleDragStart = useCallback((columnId: string, e: React.DragEvent) => {
    setDraggedColumn(columnId)
    e.dataTransfer.effectAllowed = "move"
    e.dataTransfer.setData("text/plain", columnId)
    
    const dragImage = document.createElement("div")
    dragImage.style.opacity = "0"
    document.body.appendChild(dragImage)
    e.dataTransfer.setDragImage(dragImage, 0, 0)
    setTimeout(() => document.body.removeChild(dragImage), 0)
  }, [])

  const handleDragOver = useCallback((columnId: string, e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = "move"
    if (draggedColumn && draggedColumn !== columnId) {
      setDragOverColumn(columnId)
    }
  }, [draggedColumn])

  const handleDragLeave = useCallback(() => {
    setDragOverColumn(null)
  }, [])

  const handleDrop = useCallback((targetColumnId: string, e: React.DragEvent) => {
    e.preventDefault()
    if (!draggedColumn || draggedColumn === targetColumnId) {
      setDraggedColumn(null)
      setDragOverColumn(null)
      return
    }

    setColumns((prev) => {
      const newColumns = [...prev]
      const draggedIndex = newColumns.findIndex((c) => c.id === draggedColumn)
      const targetIndex = newColumns.findIndex((c) => c.id === targetColumnId)
      
      if (draggedIndex === -1 || targetIndex === -1) return prev
      
      const [removed] = newColumns.splice(draggedIndex, 1)
      newColumns.splice(targetIndex, 0, removed)
      
      return newColumns.map((col, idx) => ({ ...col, order: idx }))
    })

    setDraggedColumn(null)
    setDragOverColumn(null)
  }, [draggedColumn])

  const handleDragEnd = useCallback(() => {
    setDraggedColumn(null)
    setDragOverColumn(null)
  }, [])

  const setColumnWidth = useCallback((columnId: string, width: number) => {
    setColumnWidths((prev) => ({
      ...prev,
      [columnId]: Math.max(minColumnWidth, width),
    }))
  }, [minColumnWidth])

  const toggleColumnVisibility = useCallback((columnId: string) => {
    setColumns((prev) =>
      prev.map((col) =>
        col.id === columnId ? { ...col, visible: !col.visible } : col
      )
    )
  }, [])

  const resetToDefaults = useCallback(() => {
    setColumns(initialColumns)
    setColumnWidths(initialWidths)
    setSortConfig(initialSort)
  }, [initialColumns, initialWidths, initialSort])

  const visibleColumns = columns
    .filter((col) => col.visible)
    .sort((a, b) => a.order - b.order)

  return {
    columns,
    visibleColumns,
    columnWidths,
    sortConfig,
    draggedColumn,
    dragOverColumn,
    isResizing,
    setColumns,
    setColumnWidths,
    setColumnWidth,
    setSortConfig,
    handleResizeStart,
    handleSort,
    handleDragStart,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    handleDragEnd,
    toggleColumnVisibility,
    resetToDefaults,
  }
}
