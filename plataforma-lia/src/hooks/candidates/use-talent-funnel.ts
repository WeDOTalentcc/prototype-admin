"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { liaApi } from "@/services/lia-api"
import type { CandidateLocal } from "@/services/lia-api"
import { useTalentFunnelStore } from "@/stores/talent-funnel-store"
import type {
  SearchMode,
  SearchSource,
  SearchHistoryItem,
  SavedSearch,
  FavoriteCandidate,
} from "@/stores/talent-funnel-store"

export type { SearchMode, SearchSource, SearchHistoryItem, SavedSearch, FavoriteCandidate }

const MAX_HISTORY_ITEMS = 100
const MAX_SAVED_SEARCHES = 100

const normalizeSearchSource = (source: string): SearchSource => {
  if (source === "pearch") return "global"
  if (source === "local" || source === "global" || source === "hybrid") return source
  return "local"
}

async function fetchFavoritesFromAPI(): Promise<Map<string, FavoriteCandidate>> {
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 5000)
    const response = await fetch("/api/backend-proxy/candidates/favorites", { signal: controller.signal })
    clearTimeout(timeoutId)
    if (!response.ok) {
      return new Map()
    }
    const data = await response.json()
    const favoritesMap = new Map<string, FavoriteCandidate>()
    if (data.items) {
      for (const item of data.items) {
        favoritesMap.set(item.candidate_id, {
          candidateId: item.candidate_id,
          note: item.note,
          addedAt: item.created_at,
          isPinned: item.is_pinned || false,
        })
      }
    }
    return favoritesMap
  } catch {
    return new Map()
  }
}

async function toggleFavoriteAPI(candidateId: string, note?: string, isPinned?: boolean): Promise<boolean> {
  try {
    const response = await fetch(`/api/backend-proxy/candidates/${candidateId}/favorite`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ note, is_pinned: isPinned || false }),
    })
    return response.ok
  } catch {
    return false
  }
}

async function updateFavoriteAPI(candidateId: string, note?: string, isPinned?: boolean): Promise<boolean> {
  try {
    const response = await fetch(`/api/backend-proxy/candidates/${candidateId}/favorite`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ note, is_pinned: isPinned }),
    })
    return response.ok
  } catch {
    return false
  }
}

export function useTalentFunnel() {
  const store = useTalentFunnelStore()
  const [history, setHistory] = useState<SearchHistoryItem[]>([])
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([])
  const [favorites, setFavorites] = useState<Map<string, FavoriteCandidate>>(new Map())
  // Refs keep current values accessible in callbacks without stale closures,
  // and allow store.setXxx() to be called outside setState updaters (avoids
  // "Cannot update a component while rendering" — Zustand set() notifies
  // subscribers synchronously; calling it inside a setState updater triggers
  // that notification during React reconciliation).
  const historyRef = useRef<SearchHistoryItem[]>([])
  const savedSearchesRef = useRef<SavedSearch[]>([])
  const favoritesRef = useRef<Map<string, FavoriteCandidate>>(new Map())
  historyRef.current = history
  savedSearchesRef.current = savedSearches
  favoritesRef.current = favorites
  const [favoriteCandidatesData, setFavoriteCandidatesData] = useState<CandidateLocal[]>([])
  const [favoritesDataLoading, setFavoritesDataLoading] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadFromStorage()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const loadFromStorage = async () => {
    try {
      const storedHistory = store.history
      if (storedHistory.length > 0) {
        const normalized = storedHistory.map((item) => ({
          ...item,
          source: normalizeSearchSource(item.source),
        }))
        setHistory(normalized)
      }

      const storedSearches = store.savedSearches
      if (storedSearches.length > 0) {
        const normalized = storedSearches.map((search) => ({
          ...search,
          source: normalizeSearchSource(search.source),
        }))
        setSavedSearches(normalized)
      }

      const apiFavorites = await fetchFavoritesFromAPI()
      if (apiFavorites.size > 0) {
        setFavorites(apiFavorites)
        store.setFavoritesMap(Object.fromEntries(apiFavorites))
        fetchFavoriteCandidatesFullData(Array.from(apiFavorites.keys()))
      } else {
        const storedFavorites = store.favoritesMap
        if (Object.keys(storedFavorites).length > 0) {
          const favMap = new Map<string, FavoriteCandidate>(Object.entries(storedFavorites))
          setFavorites(favMap)
          if (favMap.size > 0) {
            fetchFavoriteCandidatesFullData(Array.from(favMap.keys()))
          }
        }
      }
    } catch {
    } finally {
      setIsLoading(false)
    }
  }

  const fetchFavoriteCandidatesFullData = async (candidateIds: string[]) => {
    if (candidateIds.length === 0) {
      setFavoriteCandidatesData([])
      return
    }
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    const validIds = candidateIds.filter((id) => uuidRegex.test(id))
    if (validIds.length === 0) {
      setFavoriteCandidatesData([])
      return
    }
    setFavoritesDataLoading(true)
    try {
      const result = await liaApi.getCandidates({
        ids: validIds.join(","),
        limit: validIds.length,
        offset: 0,
      })
      const items =
        result.candidates ||
        ((result as unknown as Record<string, unknown>).items as typeof result.candidates) ||
        []
      setFavoriteCandidatesData(items)
    } catch {
    } finally {
      setFavoritesDataLoading(false)
    }
  }

  const addToHistory = useCallback(
    (item: Omit<SearchHistoryItem, "id" | "timestamp">) => {
      const newItem: SearchHistoryItem = {
        ...item,
        id: `history-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date().toISOString(),
      }
      const updated = [newItem, ...historyRef.current].slice(0, MAX_HISTORY_ITEMS)
      historyRef.current = updated
      setHistory(updated)
      store.setHistory(updated)
      return newItem
    },
    [store],
  )

  const removeFromHistory = useCallback(
    (id: string) => {
      const updated = historyRef.current.filter((item) => item.id !== id)
      historyRef.current = updated
      setHistory(updated)
      store.setHistory(updated)
    },
    [store],
  )

  const clearHistory = useCallback(() => {
    historyRef.current = []
    setHistory([])
    store.setHistory([])
  }, [store])

  const addSavedSearch = useCallback(
    (
      search: Omit<
        SavedSearch,
        "id" | "createdAt" | "updatedAt" | "usageCount" | "isFavorite"
      >,
    ) => {
      const now = new Date().toISOString()
      const newSearch: SavedSearch = {
        ...search,
        id: `saved-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        isFavorite: false,
        usageCount: 0,
        createdAt: now,
        updatedAt: now,
      }
      const updated = [newSearch, ...savedSearchesRef.current].slice(0, MAX_SAVED_SEARCHES)
      savedSearchesRef.current = updated
      setSavedSearches(updated)
      store.setSavedSearches(updated)
      return newSearch
    },
    [store],
  )

  const updateSavedSearch = useCallback(
    (id: string, updates: Partial<SavedSearch>) => {
      const updated = savedSearchesRef.current.map((search) =>
        search.id === id
          ? { ...search, ...updates, updatedAt: new Date().toISOString() }
          : search,
      )
      savedSearchesRef.current = updated
      setSavedSearches(updated)
      store.setSavedSearches(updated)
    },
    [store],
  )

  const removeSavedSearch = useCallback(
    (id: string) => {
      const updated = savedSearchesRef.current.filter((search) => search.id !== id)
      savedSearchesRef.current = updated
      setSavedSearches(updated)
      store.setSavedSearches(updated)
    },
    [store],
  )

  const toggleSavedSearchFavorite = useCallback(
    (id: string) => {
      const updated = savedSearchesRef.current.map((search) =>
        search.id === id
          ? { ...search, isFavorite: !search.isFavorite, updatedAt: new Date().toISOString() }
          : search,
      )
      savedSearchesRef.current = updated
      setSavedSearches(updated)
      store.setSavedSearches(updated)
    },
    [store],
  )

  const incrementSavedSearchUsage = useCallback(
    (id: string, resultsCount?: number) => {
      const updated = savedSearchesRef.current.map((search) => {
        if (search.id === id) {
          const newUsageCount = search.usageCount + 1
          const newAvgResults =
            resultsCount !== undefined
              ? Math.round(
                  ((search.avgResults || 0) * search.usageCount + resultsCount) / newUsageCount,
                )
              : search.avgResults
          return {
            ...search,
            usageCount: newUsageCount,
            avgResults: newAvgResults,
            lastUsed: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          }
        }
        return search
      })
      savedSearchesRef.current = updated
      setSavedSearches(updated)
      store.setSavedSearches(updated)
    },
    [store],
  )

  const saveHistoryAsSearch = useCallback(
    (historyItem: SearchHistoryItem, name: string, description?: string) => {
      return addSavedSearch({
        name,
        description,
        query: historyItem.query,
        mode: historyItem.mode,
        source: historyItem.source,
        entities: historyItem.entities,
        metadata: historyItem.metadata,
      })
    },
    [addSavedSearch],
  )

  const addFavoriteCandidate = useCallback(
    (candidateId: string, note?: string) => {
      const favorite: FavoriteCandidate = {
        candidateId,
        note,
        addedAt: new Date().toISOString(),
        isPinned: false,
      }
      const updated = new Map(favoritesRef.current)
      updated.set(candidateId, favorite)
      favoritesRef.current = updated
      setFavorites(updated)
      store.setFavoritesMap(Object.fromEntries(updated))
      return favorite
    },
    [store],
  )

  const removeFavoriteCandidate = useCallback(
    (candidateId: string) => {
      const updated = new Map(favoritesRef.current)
      updated.delete(candidateId)
      favoritesRef.current = updated
      setFavorites(updated)
      store.setFavoritesMap(Object.fromEntries(updated))
    },
    [store],
  )

  const toggleFavoriteCandidate = useCallback(
    (candidateId: string, note?: string) => {
      const updated = new Map(favoritesRef.current)
      const wasPresent = updated.has(candidateId)
      if (wasPresent) {
        updated.delete(candidateId)
        setFavoriteCandidatesData((prevData) => prevData.filter((c) => c.id !== candidateId))
      } else {
        updated.set(candidateId, {
          candidateId,
          note,
          addedAt: new Date().toISOString(),
          isPinned: false,
        })
        fetchFavoriteCandidatesFullData([...Array.from(updated.keys())])
      }
      favoritesRef.current = updated
      setFavorites(updated)
      store.setFavoritesMap(Object.fromEntries(updated))
      toggleFavoriteAPI(candidateId, note).catch((err) => {
        console.warn("[useTalentFunnel] toggleFavoriteAPI fire-and-forget failed", err)
      })
    },
    [store],
  )

  const togglePinnedCandidate = useCallback(
    (candidateId: string) => {
      const updated = new Map(favoritesRef.current)
      const existing = updated.get(candidateId)
      const newIsPinned = existing ? !existing.isPinned : true
      if (existing) {
        updated.set(candidateId, { ...existing, isPinned: newIsPinned })
      } else {
        updated.set(candidateId, {
          candidateId,
          addedAt: new Date().toISOString(),
          isPinned: true,
        })
      }
      favoritesRef.current = updated
      setFavorites(updated)
      store.setFavoritesMap(Object.fromEntries(updated))
      if (existing) {
        updateFavoriteAPI(candidateId, existing.note, newIsPinned).catch((err) => {
          console.warn("[useTalentFunnel] updateFavoriteAPI (pin) fire-and-forget failed", err)
        })
      } else {
        toggleFavoriteAPI(candidateId, undefined, true).catch((err) => {
          console.warn("[useTalentFunnel] toggleFavoriteAPI (pin) fire-and-forget failed", err)
        })
      }
    },
    [store],
  )

  const updateFavoriteNote = useCallback(
    (candidateId: string, note: string) => {
      const existing = favoritesRef.current.get(candidateId)
      if (!existing) return
      const updated = new Map(favoritesRef.current)
      updated.set(candidateId, { ...existing, note })
      favoritesRef.current = updated
      setFavorites(updated)
      store.setFavoritesMap(Object.fromEntries(updated))
      updateFavoriteAPI(candidateId, note, existing.isPinned).catch((err) => {
        console.warn("[useTalentFunnel] updateFavoriteAPI (note) fire-and-forget failed", err)
      })
    },
    [store],
  )

  const isFavorite = useCallback(
    (candidateId: string) => {
      return favorites.has(candidateId)
    },
    [favorites],
  )

  const isPinned = useCallback(
    (candidateId: string) => {
      return favorites.get(candidateId)?.isPinned || false
    },
    [favorites],
  )

  const getFavoriteNote = useCallback(
    (candidateId: string) => {
      return favorites.get(candidateId)?.note
    },
    [favorites],
  )

  const getFavoriteIds = useCallback(() => {
    return new Set(favorites.keys())
  }, [favorites])

  const getPinnedIds = useCallback(() => {
    return new Set(
      Array.from(favorites.entries())
        .filter(([, fav]) => fav.isPinned)
        .map(([id]) => id),
    )
  }, [favorites])

  const getFavoriteNotes = useCallback(() => {
    const notes = new Map<string, string>()
    favorites.forEach((fav, id) => {
      if (fav.note) {
        notes.set(id, fav.note)
      }
    })
    return notes
  }, [favorites])

  return {
    isLoading,
    history,
    savedSearches,
    favorites,
    favoriteCandidatesData,
    favoritesDataLoading,
    addToHistory,
    removeFromHistory,
    clearHistory,
    addSavedSearch,
    updateSavedSearch,
    removeSavedSearch,
    toggleSavedSearchFavorite,
    incrementSavedSearchUsage,
    saveHistoryAsSearch,
    addFavoriteCandidate,
    removeFavoriteCandidate,
    toggleFavoriteCandidate,
    togglePinnedCandidate,
    updateFavoriteNote,
    isFavorite,
    isPinned,
    getFavoriteNote,
    getFavoriteIds,
    getPinnedIds,
    getFavoriteNotes,
  }
}
