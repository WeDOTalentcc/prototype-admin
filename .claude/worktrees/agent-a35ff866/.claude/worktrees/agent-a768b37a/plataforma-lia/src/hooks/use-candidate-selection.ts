/**
 * useCandidateSelection — Sprint E god object extraction
 *
 * Extracted from candidates-page.tsx (12375 lines).
 * Contains candidate selection state and bulk action logic.
 *
 * TODO (Sprint E phase 2): Replace the scattered useState declarations
 * (lines ~901-902) and related selection handlers in CandidatesPage with
 * a call to this hook.
 */
"use client"

import React, { useState, useCallback } from "react"

// ── Types ─────────────────────────────────────────────────────────────────────

export interface BulkActionResult {
  successCount: number
  failureCount: number
  errors: string[]
}

// ── Hook ─────────────────────────────────────────────────────────────────────

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

/**
 * Manages multi-select state for the candidates table.
 * Supports shift-click range selection.
 * Ready to be imported in CandidatesPage as part of Sprint E phase 2 extraction.
 */
export function useCandidateSelection(): UseCandidateSelectionReturn {
  const [selectedCandidates, setSelectedCandidates] = useState<Set<string>>(new Set())
  const [lastSelectedIndex, setLastSelectedIndex] = useState<number | null>(null)

  const selectCandidate = useCallback(
    (id: string, shiftKey = false, index?: number, allIds: string[] = []) => {
      setSelectedCandidates(prev => {
        const next = new Set(prev)
        if (shiftKey && lastSelectedIndex !== null && index !== undefined && allIds.length > 0) {
          // Range selection
          const start = Math.min(lastSelectedIndex, index)
          const end = Math.max(lastSelectedIndex, index)
          for (let i = start; i <= end; i++) {
            if (allIds[i]) next.add(allIds[i])
          }
        } else {
          next.has(id) ? next.delete(id) : next.add(id)
        }
        return next
      })
      if (index !== undefined) setLastSelectedIndex(index)
    },
    [lastSelectedIndex]
  )

  const deselectCandidate = useCallback((id: string) => {
    setSelectedCandidates(prev => {
      const next = new Set(prev)
      next.delete(id)
      return next
    })
  }, [])

  const toggleSelectAll = useCallback((allIds: string[]) => {
    setSelectedCandidates(prev => {
      const allSelected = allIds.every(id => prev.has(id))
      if (allSelected) return new Set()
      return new Set(allIds)
    })
    setLastSelectedIndex(null)
  }, [])

  const clearSelection = useCallback(() => {
    setSelectedCandidates(new Set())
    setLastSelectedIndex(null)
  }, [])

  const isSelected = useCallback(
    (id: string) => selectedCandidates.has(id),
    [selectedCandidates]
  )

  return {
    selectedCandidates,
    setSelectedCandidates,
    lastSelectedIndex,
    isAllSelected: false, // computed by caller based on current page
    selectedCount: selectedCandidates.size,
    selectCandidate,
    deselectCandidate,
    toggleSelectAll,
    clearSelection,
    isSelected,
  }
}
