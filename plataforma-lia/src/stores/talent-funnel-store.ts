import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

export type SearchMode = 'natural' | 'similar' | 'jd' | 'boolean' | 'archetypes'
export type SearchSource = 'local' | 'global' | 'hybrid'

export interface SearchHistoryItem {
  id: string
  query: string
  mode: SearchMode
  source: SearchSource
  timestamp: string
  resultsCount?: number
  entities?: Record<string, unknown>
  metadata?: Record<string, unknown>
}

export interface SavedSearch {
  id: string
  name: string
  description?: string
  query: string
  mode: SearchMode
  source: SearchSource
  filters?: Record<string, unknown>
  entities?: Record<string, unknown>
  metadata?: Record<string, unknown>
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

interface TalentFunnelState {
  history: SearchHistoryItem[]
  savedSearches: SavedSearch[]
  favoritesMap: Record<string, FavoriteCandidate>
}

interface TalentFunnelActions {
  setHistory: (history: SearchHistoryItem[]) => void
  setSavedSearches: (searches: SavedSearch[]) => void
  setFavoritesMap: (favorites: Record<string, FavoriteCandidate>) => void
}

export type TalentFunnelStore = TalentFunnelState & TalentFunnelActions

export const useTalentFunnelStore = create<TalentFunnelStore>()(
  devtools(
    persist(
      (set) => ({
        history: [],
        savedSearches: [],
        favoritesMap: {},

        setHistory: (history) =>
          set({ history }, false, 'talentFunnel/setHistory'),

        setSavedSearches: (searches) =>
          set({ savedSearches: searches }, false, 'talentFunnel/setSavedSearches'),

        setFavoritesMap: (favorites) =>
          set({ favoritesMap: favorites }, false, 'talentFunnel/setFavoritesMap'),
      }),
      {
        name: 'lia-talent-funnel-store',
        partialize: (state) => ({
          history: state.history,
          savedSearches: state.savedSearches,
          favoritesMap: state.favoritesMap,
        }),
      }
    ),
    { name: 'TalentFunnelStore' }
  )
)
