"use client"

import { useState, useCallback, useMemo } from "react"

export interface BulkSelectionState {
  selectedCandidates: Set<string>
  isSelectionMode: boolean
}

export interface UseBulkSelectionOptions {
  maxSelections?: number
  onSelectionChange?: (selected: Set<string>) => void
}

export interface UseBulkSelectionReturn {
  selectedCandidates: Set<string>
  selectedCount: number
  isSelectionMode: boolean
  selectCandidate: (candidateId: string) => void
  deselectCandidate: (candidateId: string) => void
  toggleCandidate: (candidateId: string) => void
  selectMultiple: (candidateIds: string[]) => void
  deselectMultiple: (candidateIds: string[]) => void
  selectAll: (candidateIds: string[]) => void
  clearSelection: () => void
  isSelected: (candidateId: string) => boolean
  toggleSelectionMode: () => void
  enableSelectionMode: () => void
  disableSelectionMode: () => void
  getSelectedCandidatesArray: () => string[]
}

export function useBulkSelection(options: UseBulkSelectionOptions = {}): UseBulkSelectionReturn {
  const { maxSelections, onSelectionChange } = options
  
  const [selectedCandidates, setSelectedCandidates] = useState<Set<string>>(new Set())
  const [isSelectionMode, setIsSelectionMode] = useState(false)
  
  const selectedCount = useMemo(() => selectedCandidates.size, [selectedCandidates])
  
  const updateSelection = useCallback((newSelection: Set<string>) => {
    setSelectedCandidates(newSelection)
    onSelectionChange?.(newSelection)
  }, [onSelectionChange])
  
  const selectCandidate = useCallback((candidateId: string) => {
    setSelectedCandidates(prev => {
      if (maxSelections && prev.size >= maxSelections) {
        return prev
      }
      const newSet = new Set(prev)
      newSet.add(candidateId)
      onSelectionChange?.(newSet)
      return newSet
    })
    if (!isSelectionMode) {
      setIsSelectionMode(true)
    }
  }, [maxSelections, onSelectionChange, isSelectionMode])
  
  const deselectCandidate = useCallback((candidateId: string) => {
    setSelectedCandidates(prev => {
      const newSet = new Set(prev)
      newSet.delete(candidateId)
      onSelectionChange?.(newSet)
      return newSet
    })
  }, [onSelectionChange])
  
  const toggleCandidate = useCallback((candidateId: string) => {
    setSelectedCandidates(prev => {
      const newSet = new Set(prev)
      if (newSet.has(candidateId)) {
        newSet.delete(candidateId)
      } else {
        if (maxSelections && newSet.size >= maxSelections) {
          return prev
        }
        newSet.add(candidateId)
      }
      onSelectionChange?.(newSet)
      return newSet
    })
    if (!isSelectionMode) {
      setIsSelectionMode(true)
    }
  }, [maxSelections, onSelectionChange, isSelectionMode])
  
  const selectMultiple = useCallback((candidateIds: string[]) => {
    setSelectedCandidates(prev => {
      const newSet = new Set(prev)
      for (const id of candidateIds) {
        if (maxSelections && newSet.size >= maxSelections) {
          break
        }
        newSet.add(id)
      }
      onSelectionChange?.(newSet)
      return newSet
    })
    if (!isSelectionMode) {
      setIsSelectionMode(true)
    }
  }, [maxSelections, onSelectionChange, isSelectionMode])
  
  const deselectMultiple = useCallback((candidateIds: string[]) => {
    setSelectedCandidates(prev => {
      const newSet = new Set(prev)
      for (const id of candidateIds) {
        newSet.delete(id)
      }
      onSelectionChange?.(newSet)
      return newSet
    })
  }, [onSelectionChange])
  
  const selectAll = useCallback((candidateIds: string[]) => {
    const allSelected = candidateIds.every(id => selectedCandidates.has(id))
    
    if (allSelected) {
      setSelectedCandidates(prev => {
        const newSet = new Set(prev)
        for (const id of candidateIds) {
          newSet.delete(id)
        }
        onSelectionChange?.(newSet)
        return newSet
      })
    } else {
      setSelectedCandidates(prev => {
        const newSet = new Set(prev)
        for (const id of candidateIds) {
          if (maxSelections && newSet.size >= maxSelections) {
            break
          }
          newSet.add(id)
        }
        onSelectionChange?.(newSet)
        return newSet
      })
      if (!isSelectionMode) {
        setIsSelectionMode(true)
      }
    }
  }, [selectedCandidates, maxSelections, onSelectionChange, isSelectionMode])
  
  const clearSelection = useCallback(() => {
    setSelectedCandidates(new Set())
    onSelectionChange?.(new Set())
  }, [onSelectionChange])
  
  const isSelected = useCallback((candidateId: string) => {
    return selectedCandidates.has(candidateId)
  }, [selectedCandidates])
  
  const toggleSelectionMode = useCallback(() => {
    setIsSelectionMode(prev => {
      if (prev) {
        setSelectedCandidates(new Set())
        onSelectionChange?.(new Set())
      }
      return !prev
    })
  }, [onSelectionChange])
  
  const enableSelectionMode = useCallback(() => {
    setIsSelectionMode(true)
  }, [])
  
  const disableSelectionMode = useCallback(() => {
    setIsSelectionMode(false)
    setSelectedCandidates(new Set())
    onSelectionChange?.(new Set())
  }, [onSelectionChange])
  
  const getSelectedCandidatesArray = useCallback(() => {
    return Array.from(selectedCandidates)
  }, [selectedCandidates])
  
  return {
    selectedCandidates,
    selectedCount,
    isSelectionMode,
    selectCandidate,
    deselectCandidate,
    toggleCandidate,
    selectMultiple,
    deselectMultiple,
    selectAll,
    clearSelection,
    isSelected,
    toggleSelectionMode,
    enableSelectionMode,
    disableSelectionMode,
    getSelectedCandidatesArray,
  }
}
