"use client"

import { useState, useCallback, useMemo } from "react"
import type { Candidate } from "../types"

interface UseCandidatesSelectionOptions {
  maxSelection?: number
  onSelectionChange?: (selectedIds: string[]) => void
}

interface UseCandidatesSelectionResult {
  selectedIds: Set<string>
  selectedCandidates: Candidate[]
  isSelected: (candidateId: string) => boolean
  select: (candidateId: string) => void
  deselect: (candidateId: string) => void
  toggle: (candidateId: string) => void
  selectAll: () => void
  deselectAll: () => void
  selectRange: (startId: string, endId: string) => void
  hasSelection: boolean
  selectionCount: number
  isMaxReached: boolean
}

export function useCandidatesSelection(
  candidates: Candidate[],
  options: UseCandidatesSelectionOptions = {}
): UseCandidatesSelectionResult {
  const { maxSelection, onSelectionChange } = options
  
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())

  const updateSelection = useCallback((newSelection: Set<string>) => {
    setSelectedIds(newSelection)
    onSelectionChange?.(Array.from(newSelection))
  }, [onSelectionChange])

  const isSelected = useCallback((candidateId: string) => {
    return selectedIds.has(candidateId)
  }, [selectedIds])

  const select = useCallback((candidateId: string) => {
    if (maxSelection && selectedIds.size >= maxSelection) {
      return
    }
    
    const newSelection = new Set(selectedIds)
    newSelection.add(candidateId)
    updateSelection(newSelection)
  }, [selectedIds, maxSelection, updateSelection])

  const deselect = useCallback((candidateId: string) => {
    const newSelection = new Set(selectedIds)
    newSelection.delete(candidateId)
    updateSelection(newSelection)
  }, [selectedIds, updateSelection])

  const toggle = useCallback((candidateId: string) => {
    if (selectedIds.has(candidateId)) {
      deselect(candidateId)
    } else {
      select(candidateId)
    }
  }, [selectedIds, select, deselect])

  const selectAll = useCallback(() => {
    const candidateIds = candidates.map((c) => c.id)
    const limit = maxSelection ? Math.min(maxSelection, candidateIds.length) : candidateIds.length
    const newSelection = new Set(candidateIds.slice(0, limit))
    updateSelection(newSelection)
  }, [candidates, maxSelection, updateSelection])

  const deselectAll = useCallback(() => {
    updateSelection(new Set())
  }, [updateSelection])

  const selectRange = useCallback((startId: string, endId: string) => {
    const startIndex = candidates.findIndex((c) => c.id === startId)
    const endIndex = candidates.findIndex((c) => c.id === endId)
    
    if (startIndex === -1 || endIndex === -1) return
    
    const [from, to] = startIndex < endIndex 
      ? [startIndex, endIndex] 
      : [endIndex, startIndex]
    
    const rangeIds = candidates.slice(from, to + 1).map((c) => c.id)
    
    const newSelection = new Set(selectedIds)
    for (const id of rangeIds) {
      if (maxSelection && newSelection.size >= maxSelection) break
      newSelection.add(id)
    }
    
    updateSelection(newSelection)
  }, [candidates, selectedIds, maxSelection, updateSelection])

  const selectedCandidates = useMemo(() => {
    return candidates.filter((c) => selectedIds.has(c.id))
  }, [candidates, selectedIds])

  const hasSelection = selectedIds.size > 0
  const selectionCount = selectedIds.size
  const isMaxReached = maxSelection ? selectedIds.size >= maxSelection : false

  return {
    selectedIds,
    selectedCandidates,
    isSelected,
    select,
    deselect,
    toggle,
    selectAll,
    deselectAll,
    selectRange,
    hasSelection,
    selectionCount,
    isMaxReached,
  }
}
