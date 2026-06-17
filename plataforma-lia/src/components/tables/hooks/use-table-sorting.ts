"use client"

import { useState, useCallback, useMemo } from "react"
import type { TableSortConfig, TableCandidate } from "../types"

export function useTableSorting(initialSort?: TableSortConfig) {
  const [sortConfig, setSortConfig] = useState<TableSortConfig | undefined>(initialSort)

  const handleSort = useCallback((field: string) => {
    setSortConfig(prev => ({
      field,
      direction: prev?.field === field && prev.direction === 'desc' ? 'asc' : 'desc'
    }))
  }, [])

  const resetSort = useCallback(() => {
    setSortConfig(undefined)
  }, [])

  const sortCandidates = useCallback((candidates: TableCandidate[]) => {
    if (!sortConfig) return candidates

    return [...candidates].sort((a, b) => {
      let aValue: unknown = a[sortConfig.field as keyof typeof a]
      let bValue: unknown = b[sortConfig.field as keyof typeof b]

      if (sortConfig.field === 'score' || sortConfig.field === 'lia_score') {
        aValue = (a.liaAnalysis?.score || a.lia_score || a.score || 0)
        bValue = (b.liaAnalysis?.score || b.lia_score || b.score || 0)
      }

      if (sortConfig.field === 'name') {
        aValue = a.name?.toLowerCase() || ''
        bValue = b.name?.toLowerCase() || ''
      }

      if (sortConfig.field === 'position' || sortConfig.field === 'current_title') {
        aValue = (a.position || a.current_title || '').toLowerCase()
        bValue = (b.position || b.current_title || '').toLowerCase()
      }

      if (sortConfig.field === 'company' || sortConfig.field === 'current_company') {
        aValue = (a.current_company || a.workHistory?.[0]?.company || '').toLowerCase()
        bValue = (b.current_company || b.workHistory?.[0]?.company || '').toLowerCase()
      }

      if (sortConfig.field === 'location' || sortConfig.field === 'location_city') {
        aValue = (a.location || a.location_city || '').toLowerCase()
        bValue = (b.location || b.location_city || '').toLowerCase()
      }

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortConfig.direction === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue)
      }

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortConfig.direction === 'asc' 
          ? aValue - bValue
          : bValue - aValue
      }

      return 0
    })
  }, [sortConfig])

  return {
    sortConfig,
    setSortConfig,
    handleSort,
    resetSort,
    sortCandidates
  }
}
