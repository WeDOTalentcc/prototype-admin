"use client"

import { useState, useCallback } from "react"
import type { TableCandidate } from "../types"

export function useTableSelection() {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())

  const toggleSelect = useCallback((id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }, [])

  const selectAll = useCallback((candidates: TableCandidate[]) => {
    setSelectedIds(new Set(candidates.map(c => c.id)))
  }, [])

  const deselectAll = useCallback(() => {
    setSelectedIds(new Set())
  }, [])

  const toggleSelectAll = useCallback((candidates: TableCandidate[]) => {
    if (selectedIds.size === candidates.length) {
      deselectAll()
    } else {
      selectAll(candidates)
    }
  }, [selectedIds.size, selectAll, deselectAll])

  const isSelected = useCallback((id: string) => selectedIds.has(id), [selectedIds])

  const selectRange = useCallback((candidates: TableCandidate[], fromIndex: number, toIndex: number) => {
    const start = Math.min(fromIndex, toIndex)
    const end = Math.max(fromIndex, toIndex)
    const rangeIds = candidates.slice(start, end + 1).map(c => c.id)
    setSelectedIds(prev => new Set([...prev, ...rangeIds]))
  }, [])

  const getSelectedCandidates = useCallback((candidates: TableCandidate[]) => 
    candidates.filter(c => selectedIds.has(c.id)),
    [selectedIds]
  )

  return {
    selectedIds,
    setSelectedIds,
    toggleSelect,
    selectAll,
    deselectAll,
    toggleSelectAll,
    isSelected,
    selectRange,
    getSelectedCandidates,
    selectedCount: selectedIds.size
  }
}
