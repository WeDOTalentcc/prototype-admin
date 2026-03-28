import type { BackendRecord } from '@/types/api'
"use client"

import { useState, useEffect, useCallback } from "react"
import { liaApi } from "@/services/lia-api"
import type { CandidateLocal } from "@/services/lia-api"

export type SearchMode = 'natural' | 'similar' | 'jd' | 'boolean' | 'archetypes'
export type SearchSource = 'local' | 'global' | 'hybrid'

export interface SearchHistoryItem {
  id: string
  query: string
  mode: SearchMode
  source: SearchSource
  timestamp: string
  resultsCount?: number
  entities?: Record<string, any>
  metadata?: Record<string, any>
}

export interface SavedSearch {
  id: string
  name: string
  description?: string
  query: string
  mode: SearchMode
  source: SearchSource
  filters?: Record<string, any>
  entities?: Record<string, any>
  metadata?: Record<string, any>
  isFavorite: boolean
  usageCount: number
  lastUsed?: string
  avgResults?: number
  createdAt: string
  updatedAt: string
}

export interface FavoriteCandidate {
  candidateId: string
  note?: string
  addedAt: string
  isPinned: boolean
}

const STORAGE_KEYS = {
  HISTORY: 'lia-search-history',
  SAVED_SEARCHES: 'lia-saved-searches',
  FAVORITES: 'lia-favorite-candidates',
  PINNED: 'lia-pinned-candidates'
}

const MAX_HISTORY_ITEMS = 100
const MAX_SAVED_SEARCHES = 100

const normalizeSearchSource = (source: string): SearchSource => {
  if (source === 'pearch') return 'global'
  if (source === 'local' || source === 'global' || source === 'hybrid') return source
  return 'local'
}

async function fetchFavoritesFromAPI(): Promise<Map<string, FavoriteCandidate>> {
  try {
    const response = await fetch('/api/backend-proxy/candidates/favorites')
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
          isPinned: item.is_pinned || false
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
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note, is_pinned: isPinned || false })
    })
    return response.ok
  } catch (error) {
    return false
  }
}

async function updateFavoriteAPI(candidateId: string, note?: string, isPinned?: boolean): Promise<boolean> {
  try {
    const response = await fetch(`/api/backend-proxy/candidates/${candidateId}/favorite`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note, is_pinned: isPinned })
    })
    return response.ok
  } catch (error) {
    return false
  }
}

export function useTalentFunnel() {
  const [history, setHistory] = useState<SearchHistoryItem[]>([])
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([])
  const [favorites, setFavorites] = useState<Map<string, FavoriteCandidate>>(new Map())
  const [favoriteCandidatesData, setFavoriteCandidatesData] = useState<CandidateLocal[]>([])
  const [favoritesDataLoading, setFavoritesDataLoading] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadFromStorage()
  }, [])

  const loadFromStorage = async () => {
    try {
      const historyData = localStorage.getItem(STORAGE_KEYS.HISTORY)
      if (historyData) {
        const parsed = JSON.parse(historyData) as SearchHistoryItem[]
        const normalized = parsed.map(item => ({
          ...item,
          source: normalizeSearchSource(item.source)
        }))
        setHistory(normalized)
      }

      const savedSearchesData = localStorage.getItem(STORAGE_KEYS.SAVED_SEARCHES)
      if (savedSearchesData) {
        const parsed = JSON.parse(savedSearchesData) as SavedSearch[]
        const normalized = parsed.map(search => ({
          ...search,
          source: normalizeSearchSource(search.source)
        }))
        setSavedSearches(normalized)
      }

      const apiFavorites = await fetchFavoritesFromAPI()
      if (apiFavorites.size > 0) {
        setFavorites(apiFavorites)
        localStorage.setItem(STORAGE_KEYS.FAVORITES, JSON.stringify(Object.fromEntries(apiFavorites)))
        fetchFavoriteCandidatesFullData(Array.from(apiFavorites.keys()))
      } else {
        const favoritesData = localStorage.getItem(STORAGE_KEYS.FAVORITES)
        if (favoritesData) {
          const parsed = JSON.parse(favoritesData)
          const favMap = new Map<string, FavoriteCandidate>(Object.entries(parsed))
          setFavorites(favMap)
          if (favMap.size > 0) {
            fetchFavoriteCandidatesFullData(Array.from(favMap.keys()))
          }
        }
      }
    } catch (error) {
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
    const validIds = candidateIds.filter(id => uuidRegex.test(id))
    if (validIds.length === 0) {
      setFavoriteCandidatesData([])
      return
    }
    setFavoritesDataLoading(true)
    try {
      const result = await liaApi.getCandidates({
        ids: validIds.join(','),
        limit: validIds.length,
        offset: 0
      })
      const items = result.candidates || (result as BackendRecord).items as typeof result.candidates || []
      setFavoriteCandidatesData(items)
    } catch (error) {
    } finally {
      setFavoritesDataLoading(false)
    }
  }

  const addToHistory = useCallback((item: Omit<SearchHistoryItem, 'id' | 'timestamp'>) => {
    const newItem: SearchHistoryItem = {
      ...item,
      id: `history-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString()
    }

    setHistory(prev => {
      const updated = [newItem, ...prev].slice(0, MAX_HISTORY_ITEMS)
      localStorage.setItem(STORAGE_KEYS.HISTORY, JSON.stringify(updated))
      return updated
    })

    return newItem
  }, [])

  const removeFromHistory = useCallback((id: string) => {
    setHistory(prev => {
      const updated = prev.filter(item => item.id !== id)
      localStorage.setItem(STORAGE_KEYS.HISTORY, JSON.stringify(updated))
      return updated
    })
  }, [])

  const clearHistory = useCallback(() => {
    setHistory([])
    localStorage.setItem(STORAGE_KEYS.HISTORY, JSON.stringify([]))
  }, [])

  const addSavedSearch = useCallback((search: Omit<SavedSearch, 'id' | 'createdAt' | 'updatedAt' | 'usageCount' | 'isFavorite'>) => {
    const now = new Date().toISOString()
    const newSearch: SavedSearch = {
      ...search,
      id: `saved-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      isFavorite: false,
      usageCount: 0,
      createdAt: now,
      updatedAt: now
    }

    setSavedSearches(prev => {
      const updated = [newSearch, ...prev].slice(0, MAX_SAVED_SEARCHES)
      localStorage.setItem(STORAGE_KEYS.SAVED_SEARCHES, JSON.stringify(updated))
      return updated
    })

    return newSearch
  }, [])

  const updateSavedSearch = useCallback((id: string, updates: Partial<SavedSearch>) => {
    setSavedSearches(prev => {
      const updated = prev.map(search => 
        search.id === id 
          ? { ...search, ...updates, updatedAt: new Date().toISOString() }
          : search
      )
      localStorage.setItem(STORAGE_KEYS.SAVED_SEARCHES, JSON.stringify(updated))
      return updated
    })
  }, [])

  const removeSavedSearch = useCallback((id: string) => {
    setSavedSearches(prev => {
      const updated = prev.filter(search => search.id !== id)
      localStorage.setItem(STORAGE_KEYS.SAVED_SEARCHES, JSON.stringify(updated))
      return updated
    })
  }, [])

  const toggleSavedSearchFavorite = useCallback((id: string) => {
    setSavedSearches(prev => {
      const updated = prev.map(search =>
        search.id === id
          ? { ...search, isFavorite: !search.isFavorite, updatedAt: new Date().toISOString() }
          : search
      )
      localStorage.setItem(STORAGE_KEYS.SAVED_SEARCHES, JSON.stringify(updated))
      return updated
    })
  }, [])

  const incrementSavedSearchUsage = useCallback((id: string, resultsCount?: number) => {
    setSavedSearches(prev => {
      const updated = prev.map(search => {
        if (search.id === id) {
          const newUsageCount = search.usageCount + 1
          const newAvgResults = resultsCount !== undefined
            ? Math.round(((search.avgResults || 0) * search.usageCount + resultsCount) / newUsageCount)
            : search.avgResults
          
          return {
            ...search,
            usageCount: newUsageCount,
            avgResults: newAvgResults,
            lastUsed: new Date().toISOString(),
            updatedAt: new Date().toISOString()
          }
        }
        return search
      })
      localStorage.setItem(STORAGE_KEYS.SAVED_SEARCHES, JSON.stringify(updated))
      return updated
    })
  }, [])

  const saveHistoryAsSearch = useCallback((historyItem: SearchHistoryItem, name: string, description?: string) => {
    return addSavedSearch({
      name,
      description,
      query: historyItem.query,
      mode: historyItem.mode,
      source: historyItem.source,
      entities: historyItem.entities,
      metadata: historyItem.metadata
    })
  }, [addSavedSearch])

  const addFavoriteCandidate = useCallback((candidateId: string, note?: string) => {
    const favorite: FavoriteCandidate = {
      candidateId,
      note,
      addedAt: new Date().toISOString(),
      isPinned: false
    }

    setFavorites(prev => {
      const updated = new Map(prev)
      updated.set(candidateId, favorite)
      localStorage.setItem(STORAGE_KEYS.FAVORITES, JSON.stringify(Object.fromEntries(updated)))
      return updated
    })

    return favorite
  }, [])

  const removeFavoriteCandidate = useCallback((candidateId: string) => {
    setFavorites(prev => {
      const updated = new Map(prev)
      updated.delete(candidateId)
      localStorage.setItem(STORAGE_KEYS.FAVORITES, JSON.stringify(Object.fromEntries(updated)))
      return updated
    })
  }, [])

  const toggleFavoriteCandidate = useCallback((candidateId: string, note?: string) => {
    setFavorites(prev => {
      const updated = new Map(prev)
      const wasRemoved = updated.has(candidateId)
      if (wasRemoved) {
        updated.delete(candidateId)
        setFavoriteCandidatesData(prevData => prevData.filter(c => c.id !== candidateId))
      } else {
        updated.set(candidateId, {
          candidateId,
          note,
          addedAt: new Date().toISOString(),
          isPinned: false
        })
        fetchFavoriteCandidatesFullData([...Array.from(updated.keys())])
      }
      localStorage.setItem(STORAGE_KEYS.FAVORITES, JSON.stringify(Object.fromEntries(updated)))
      return updated
    })
    
    toggleFavoriteAPI(candidateId, note).catch(err => {
    })
  }, [])

  const togglePinnedCandidate = useCallback((candidateId: string) => {
    setFavorites(prev => {
      const updated = new Map(prev)
      const existing = updated.get(candidateId)
      const newIsPinned = existing ? !existing.isPinned : true
      if (existing) {
        updated.set(candidateId, { ...existing, isPinned: newIsPinned })
      } else {
        updated.set(candidateId, {
          candidateId,
          addedAt: new Date().toISOString(),
          isPinned: true
        })
      }
      localStorage.setItem(STORAGE_KEYS.FAVORITES, JSON.stringify(Object.fromEntries(updated)))
      
      if (existing) {
        updateFavoriteAPI(candidateId, existing.note, newIsPinned).catch(err => {
        })
      } else {
        toggleFavoriteAPI(candidateId, undefined, true).catch(err => {
        })
      }
      
      return updated
    })
  }, [])

  const updateFavoriteNote = useCallback((candidateId: string, note: string) => {
    setFavorites(prev => {
      const updated = new Map(prev)
      const existing = updated.get(candidateId)
      if (existing) {
        updated.set(candidateId, { ...existing, note })
        localStorage.setItem(STORAGE_KEYS.FAVORITES, JSON.stringify(Object.fromEntries(updated)))
        
        updateFavoriteAPI(candidateId, note, existing.isPinned).catch(err => {
        })
      }
      return updated
    })
  }, [])

  const isFavorite = useCallback((candidateId: string) => {
    return favorites.has(candidateId)
  }, [favorites])

  const isPinned = useCallback((candidateId: string) => {
    return favorites.get(candidateId)?.isPinned || false
  }, [favorites])

  const getFavoriteNote = useCallback((candidateId: string) => {
    return favorites.get(candidateId)?.note
  }, [favorites])

  const getFavoriteIds = useCallback(() => {
    return new Set(favorites.keys())
  }, [favorites])

  const getPinnedIds = useCallback(() => {
    return new Set(
      Array.from(favorites.entries())
        .filter(([_, fav]) => fav.isPinned)
        .map(([id]) => id)
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
    getFavoriteNotes
  }
}
