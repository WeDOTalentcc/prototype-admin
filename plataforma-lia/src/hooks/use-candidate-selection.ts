"use client"

import React, { useCallback } from "react"
import { useCandidatesStore } from "@/stores/candidates-store"

export interface BulkActionResult {
  successCount: number
  failureCount: number
  errors: string[]
}

export interface UseCandidateSelectionReturn {
  selectedCandidates: Set<string>
  setSelectedCandidates: React.Dispatch<React.SetStateAction<Set<string>>>
  lastSelectedIndex: number | null
  isAllSelected: boolean
  selectedCount: number
  selectCandidate: (id: string, shiftKey?: boolean, index?: number, allIds?: string[]) => void
  deselectCandidate: (id: string) => void
  toggleSelectAll: (allIds: string[]) => void
  clearSelection: () => void
  isSelected: (id: string) => boolean
}

export function useCandidateSelection(): UseCandidateSelectionReturn {
  const selectedCandidates = useCandidatesStore((s) => s.selectedCandidates)
  const setSelectedCandidates = useCandidatesStore((s) => s.setSelectedCandidates) as React.Dispatch<React.SetStateAction<Set<string>>>
  const lastSelectedIndex = useCandidatesStore((s) => s.lastSelectedIndex)
  const setLastSelectedIndex = useCandidatesStore((s) => s.setLastSelectedIndex)

  const selectCandidate = useCallback(
    (id: string, shiftKey = false, index?: number, allIds: string[] = []) => {
      setSelectedCandidates((prev: Set<string>) => {
        const next = new Set(prev)
        if (shiftKey && lastSelectedIndex !== null && index !== undefined && allIds.length > 0) {
          const start = Math.min(lastSelectedIndex, index)
          const end = Math.max(lastSelectedIndex, index)
          for (let i = start; i <= end; i++) {
            if (allIds[i]) next.add(allIds[i])
          }
        } else {
          if (next.has(id)) { next.delete(id) } else { next.add(id) }
        }
        return next
      })
      if (index !== undefined) setLastSelectedIndex(index)
    },
    [lastSelectedIndex, setSelectedCandidates, setLastSelectedIndex]
  )

  const deselectCandidate = useCallback((id: string) => {
    setSelectedCandidates((prev: Set<string>) => {
      const next = new Set(prev)
      next.delete(id)
      return next
    })
  }, [setSelectedCandidates])

  const toggleSelectAll = useCallback((allIds: string[]) => {
    setSelectedCandidates((prev: Set<string>) => {
      const allSelected = allIds.every(id => prev.has(id))
      if (allSelected) return new Set<string>()
      return new Set(allIds)
    })
    setLastSelectedIndex(null)
  }, [setSelectedCandidates, setLastSelectedIndex])

  const clearSelection = useCallback(() => {
    setSelectedCandidates(new Set<string>())
    setLastSelectedIndex(null)
  }, [setSelectedCandidates, setLastSelectedIndex])

  const isSelected = useCallback(
    (id: string) => selectedCandidates.has(id),
    [selectedCandidates]
  )

  return {
    selectedCandidates,
    setSelectedCandidates,
    lastSelectedIndex,
    isAllSelected: false,
    selectedCount: selectedCandidates.size,
    selectCandidate,
    deselectCandidate,
    toggleSelectAll,
    clearSelection,
    isSelected,
  }
}
