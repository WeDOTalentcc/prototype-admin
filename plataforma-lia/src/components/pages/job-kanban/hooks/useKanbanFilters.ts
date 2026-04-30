"use client"

import { useEffect, useCallback } from "react"
import { useState } from "react"
import { useKanbanStore } from "@/stores/kanban-store"
import type { ShortList } from "@/hooks/candidates/use-short-list"

interface TalentFunnelLike {
  getFavoriteIds: () => Set<string>
  toggleFavoriteCandidate: (id: string) => void
  favorites: unknown
}

export interface UseKanbanFiltersParams {
  talentFunnel: TalentFunnelLike
  shortLists: ShortList[]
  createShortList: (jobId: string, name: string) => Promise<ShortList | null>
  addCandidateToShortList: (listId: string, candidateId: string) => Promise<boolean>
  removeCandidateFromShortList: (listId: string, candidateId: string) => Promise<boolean>
  jobId: string | undefined
  jobTitle: string | undefined
}

export function useKanbanFilters({
  talentFunnel,
  shortLists,
  createShortList,
  addCandidateToShortList,
  removeCandidateFromShortList,
  jobId,
  jobTitle,
}: UseKanbanFiltersParams) {
  const searchQuery = useKanbanStore((s) => s.searchQuery)
  const setSearchQuery = useKanbanStore((s) => s.setSearchQuery)

  const selectedCandidates = useKanbanStore((s) => s.selectedCandidates)
  const setSelectedCandidates = useKanbanStore((s) => s.setSelectedCandidates)

  const [favoriteCandidates, setFavoriteCandidates] = useState<Set<string>>(new Set())

  useEffect(() => {
    const favoriteIds = talentFunnel.getFavoriteIds()
    setFavoriteCandidates(favoriteIds)
  }, [talentFunnel.favorites]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleToggleFavorite = useCallback((candidateId: string) => {
    talentFunnel.toggleFavoriteCandidate(candidateId)
  }, [talentFunnel])

  const [shortListedCandidateIds, setShortListedCandidateIds] = useState<Set<string>>(new Set())
  const [activeShortListId, setActiveShortListId] = useState<string | null>(null)

  // Guide: initialize shortListedCandidateIds from backend shortLists data on mount/update.
  // Without this, existing short-listed candidates show no visual bookmark on page load.
  // candidateIds is now populated by the backend (ShortListResponse.candidate_ids).
  useEffect(() => {
    if (!shortLists || shortLists.length === 0) return
    const allCandidateIds = shortLists.flatMap((sl) => sl.candidateIds ?? [])
    if (allCandidateIds.length > 0) {
      setShortListedCandidateIds(new Set(allCandidateIds))
    }
    if (!activeShortListId && shortLists[0]?.id) {
      setActiveShortListId(shortLists[0].id)
    }
  }, [shortLists]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleToggleShortList = useCallback(async (candidateId: string) => {
    const isInList = shortListedCandidateIds.has(candidateId)
    let listId: string | null = activeShortListId || shortLists[0]?.id || null

    if (!listId) {
      const newList = await createShortList(jobId || '', `Short List — ${jobTitle || 'Vaga'}`)
      if (!newList) return
      listId = newList.id
      setActiveShortListId(newList.id)
    }

    if (isInList) {
      const ok = await removeCandidateFromShortList(listId, candidateId)
      if (ok) setShortListedCandidateIds(prev => { const next = new Set(prev); next.delete(candidateId); return next })
    } else {
      const ok = await addCandidateToShortList(listId, candidateId)
      if (ok) setShortListedCandidateIds(prev => new Set([...prev, candidateId]))
    }
  }, [shortListedCandidateIds, activeShortListId, shortLists, createShortList, addCandidateToShortList, removeCandidateFromShortList, jobId, jobTitle])

  const filterCandidates = useCallback((candidates: Record<string, unknown>[]) => {
    if (!searchQuery) return candidates

    const query = searchQuery.toLowerCase()
    return candidates.filter(candidate => {
      const name = candidate.name as string | undefined
      const role = candidate.role as string | undefined
      const company = candidate.company as string | undefined
      const location = candidate.location as string | undefined
      const currentCompany = candidate.currentCompany as string | undefined
      return (
        (name?.toLowerCase() ?? '').includes(query) ||
        (role?.toLowerCase() ?? '').includes(query) ||
        (company?.toLowerCase() ?? '').includes(query) ||
        (location?.toLowerCase() ?? '').includes(query) ||
        (currentCompany?.toLowerCase() ?? '').includes(query)
      )
    })
  }, [searchQuery])

  return {
    searchQuery,
    setSearchQuery,
    filterCandidates,
    selectedCandidates,
    setSelectedCandidates,
    favoriteCandidates,
    setFavoriteCandidates,
    handleToggleFavorite,
    shortListedCandidateIds,
    setShortListedCandidateIds,
    activeShortListId,
    setActiveShortListId,
    handleToggleShortList,
  }
}

export type KanbanFiltersState = ReturnType<typeof useKanbanFilters>
