import { useState, useCallback, useMemo } from 'react'

export interface UseCandidateSelectionProps {
  allCandidateIds?: string[]
}

export interface UseCandidateSelectionReturn {
  selectedCandidates: Set<string>
  favoriteCandidates: Set<string>
  toggleSelect: (candidateId: string) => void
  selectAll: (candidateIds?: string[]) => void
  clearSelection: () => void
  toggleFavorite: (candidateId: string) => void
  isSelected: (candidateId: string) => boolean
  isFavorite: (candidateId: string) => boolean
  selectedCount: number
  favoriteCount: number
  hasSelection: boolean
}

export function useCandidateSelection({
  allCandidateIds = []
}: UseCandidateSelectionProps = {}): UseCandidateSelectionReturn {
  const [selectedCandidates, setSelectedCandidates] = useState<Set<string>>(new Set())
  const [favoriteCandidates, setFavoriteCandidates] = useState<Set<string>>(new Set())

  const toggleSelect = useCallback((candidateId: string) => {
    setSelectedCandidates(prev => {
      const newSet = new Set(prev)
      if (newSet.has(candidateId)) {
        newSet.delete(candidateId)
      } else {
        newSet.add(candidateId)
      }
      return newSet
    })
  }, [])

  const selectAll = useCallback((candidateIds?: string[]) => {
    const idsToSelect = candidateIds ?? allCandidateIds
    setSelectedCandidates(new Set(idsToSelect))
  }, [allCandidateIds])

  const clearSelection = useCallback(() => {
    setSelectedCandidates(new Set())
  }, [])

  const toggleFavorite = useCallback((candidateId: string) => {
    setFavoriteCandidates(prev => {
      const newSet = new Set(prev)
      if (newSet.has(candidateId)) {
        newSet.delete(candidateId)
      } else {
        newSet.add(candidateId)
      }
      return newSet
    })
  }, [])

  const isSelected = useCallback((candidateId: string): boolean => {
    return selectedCandidates.has(candidateId)
  }, [selectedCandidates])

  const isFavorite = useCallback((candidateId: string): boolean => {
    return favoriteCandidates.has(candidateId)
  }, [favoriteCandidates])

  const selectedCount = useMemo(() => selectedCandidates.size, [selectedCandidates])
  const favoriteCount = useMemo(() => favoriteCandidates.size, [favoriteCandidates])
  const hasSelection = useMemo(() => selectedCandidates.size > 0, [selectedCandidates])

  return {
    selectedCandidates,
    favoriteCandidates,
    toggleSelect,
    selectAll,
    clearSelection,
    toggleFavorite,
    isSelected,
    isFavorite,
    selectedCount,
    favoriteCount,
    hasSelection
  }
}
