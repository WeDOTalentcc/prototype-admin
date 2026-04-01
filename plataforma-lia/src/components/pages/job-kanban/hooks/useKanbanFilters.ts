"use client"

import { useState, useEffect, useCallback } from "react"
import type { ShortList } from "@/hooks/use-short-list"

// ── Types ──────────────────────────────────────────────────────────────────

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

// ── Hook ──────────────────────────────────────────────────────────────────

export function useKanbanFilters({
  talentFunnel,
  shortLists,
  createShortList,
  addCandidateToShortList,
  removeCandidateFromShortList,
  jobId,
  jobTitle,
}: UseKanbanFiltersParams) {
  // ── Search ───────────────────────────────────────────────────────────────
  const [searchQuery, setSearchQuery] = useState("")

  // ── Candidate selection ──────────────────────────────────────────────────
  const [selectedCandidates, setSelectedCandidates] = useState<Set<string>>(new Set())

  // ── Favorites ────────────────────────────────────────────────────────────
  const [favoriteCandidates, setFavoriteCandidates] = useState<Set<string>>(new Set())

  // Sync favorites from useTalentFunnel hook
  useEffect(() => {
    const favoriteIds = talentFunnel.getFavoriteIds()
    setFavoriteCandidates(favoriteIds)
  }, [talentFunnel.favorites]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleToggleFavorite = useCallback((candidateId: string) => {
    talentFunnel.toggleFavoriteCandidate(candidateId)
    // Local state will be synced via the useEffect above
  }, [talentFunnel])

  // ── Short lists ──────────────────────────────────────────────────────────
  const [shortListedCandidateIds, setShortListedCandidateIds] = useState<Set<string>>(new Set())
  const [activeShortListId, setActiveShortListId] = useState<string | null>(null)

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

  // ── Filter helpers ───────────────────────────────────────────────────────

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

  // ── Return ───────────────────────────────────────────────────────────────
  return {
    // Search
    searchQuery,
    setSearchQuery,
    filterCandidates,
    // Selection
    selectedCandidates,
    setSelectedCandidates,
    // Favorites
    favoriteCandidates,
    setFavoriteCandidates,
    handleToggleFavorite,
    // Short lists
    shortListedCandidateIds,
    setShortListedCandidateIds,
    activeShortListId,
    setActiveShortListId,
    handleToggleShortList,
  }
}

export type KanbanFiltersState = ReturnType<typeof useKanbanFilters>
