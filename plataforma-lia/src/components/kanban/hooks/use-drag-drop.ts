import { useState, useCallback, useMemo } from 'react'
import type { KanbanCandidate, CandidatesDataMap, DynamicStage, DragState } from '../types'

export interface UseDragDropProps {
  candidatesData: CandidatesDataMap
  setCandidatesData?: React.Dispatch<React.SetStateAction<CandidatesDataMap>>
  dynamicStages: DynamicStage[]
  onTransitionRequired?: (candidates: KanbanCandidate[], fromStage: string, toStage: string) => void
}

export interface UseDragDropReturn {
  draggedCandidate: KanbanCandidate | null
  dragOverColumn: string | null
  handleDragStart: (e: React.DragEvent, candidate: KanbanCandidate, fromColumn: string) => void
  handleDragEnd: (e: React.DragEvent) => void
  handleDragOver: (e: React.DragEvent, columnId: string) => void
  handleDragLeave: (e: React.DragEvent) => void
  handleDrop: (e: React.DragEvent, toColumn: string) => void
  isDragging: boolean
  isDragEnabled: boolean
}

export function useDragDrop({
  candidatesData,
  setCandidatesData,
  dynamicStages,
  onTransitionRequired
}: UseDragDropProps): UseDragDropReturn {
  const [dragState, setDragState] = useState<DragState>({
    candidate: null,
    fromColumn: null,
    overColumn: null
  })

  const isDragEnabled = useMemo(() => {
    return typeof setCandidatesData === 'function'
  }, [setCandidatesData])

  const handleDragStart = useCallback((
    e: React.DragEvent,
    candidate: KanbanCandidate,
    fromColumn: string
  ) => {
    if (!isDragEnabled) {
      e.preventDefault()
      return
    }
    
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', JSON.stringify({
      candidateId: candidate.id,
      fromColumn
    }))
    
    setDragState({
      candidate,
      fromColumn,
      overColumn: null
    })
  }, [isDragEnabled])

  const handleDragEnd = useCallback((e: React.DragEvent) => {
    setDragState({
      candidate: null,
      fromColumn: null,
      overColumn: null
    })
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent, columnId: string) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    
    setDragState(prev => ({
      ...prev,
      overColumn: columnId
    }))
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    const relatedTarget = e.relatedTarget as HTMLElement
    if (!relatedTarget || !e.currentTarget.contains(relatedTarget)) {
      setDragState(prev => ({
        ...prev,
        overColumn: null
      }))
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent, toColumn: string) => {
    e.preventDefault()
    
    if (!isDragEnabled || !setCandidatesData) {
      setDragState({
        candidate: null,
        fromColumn: null,
        overColumn: null
      })
      return
    }
    
    const { candidate, fromColumn } = dragState
    
    if (!candidate || !fromColumn || fromColumn === toColumn) {
      setDragState({
        candidate: null,
        fromColumn: null,
        overColumn: null
      })
      return
    }

    if (onTransitionRequired) {
      onTransitionRequired([candidate], fromColumn, toColumn)
      setDragState({
        candidate: null,
        fromColumn: null,
        overColumn: null
      })
      return
    }

    setCandidatesData(prev => {
      const newData = { ...prev }
      
      newData[fromColumn] = (prev[fromColumn] || []).filter(c => c.id !== candidate.id)
      
      const updatedCandidate: KanbanCandidate = {
        ...candidate,
        stage: toColumn
      }
      
      newData[toColumn] = [...(prev[toColumn] || []), updatedCandidate]
      
      return newData
    })

    setDragState({
      candidate: null,
      fromColumn: null,
      overColumn: null
    })
  }, [dragState, setCandidatesData, onTransitionRequired, isDragEnabled])

  return {
    draggedCandidate: dragState.candidate,
    dragOverColumn: dragState.overColumn,
    handleDragStart,
    handleDragEnd,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    isDragging: dragState.candidate !== null,
    isDragEnabled
  }
}
