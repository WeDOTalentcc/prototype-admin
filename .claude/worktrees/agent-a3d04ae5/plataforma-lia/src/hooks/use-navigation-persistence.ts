'use client'

import { useCallback } from 'react'

const STORAGE_KEY = 'lia-navigation-state'
const TTL_MS = 7 * 24 * 60 * 60 * 1000 // 7 dias

interface JobsNavState {
  lastJobId?: string
  lastView?: 'kanban' | 'table'
  lastTab?: string
  timestamp: number
}

interface TalentFunnelNavState {
  lastTab?: 'search' | 'favorites' | 'lists'
  lastSearchQuery?: string
  timestamp: number
}

interface NavigationState {
  jobs?: JobsNavState
  talentFunnel?: TalentFunnelNavState
}

export function useNavigationPersistence() {
  const getState = useCallback((): NavigationState => {
    if (typeof window === 'undefined') return {}
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (!stored) return {}
      const state = JSON.parse(stored) as NavigationState
      // Limpar estados expirados
      const now = Date.now()
      if (state.jobs && now - state.jobs.timestamp > TTL_MS) {
        delete state.jobs
      }
      if (state.talentFunnel && now - state.talentFunnel.timestamp > TTL_MS) {
        delete state.talentFunnel
      }
      return state
    } catch {
      return {}
    }
  }, [])

  const saveJobsState = useCallback((jobId: string, view?: 'kanban' | 'table', tab?: string) => {
    if (typeof window === 'undefined') return
    try {
      const state = getState()
      state.jobs = {
        lastJobId: jobId,
        lastView: view,
        lastTab: tab,
        timestamp: Date.now()
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
    } catch {}
  }, [getState])

  const getJobsState = useCallback((): JobsNavState | undefined => {
    return getState().jobs
  }, [getState])

  const saveTalentFunnelState = useCallback((tab: 'search' | 'favorites' | 'lists', searchQuery?: string) => {
    if (typeof window === 'undefined') return
    try {
      const state = getState()
      state.talentFunnel = {
        lastTab: tab,
        lastSearchQuery: searchQuery,
        timestamp: Date.now()
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
    } catch {}
  }, [getState])

  const getTalentFunnelState = useCallback((): TalentFunnelNavState | undefined => {
    return getState().talentFunnel
  }, [getState])

  const clearState = useCallback((section?: 'jobs' | 'talentFunnel') => {
    if (typeof window === 'undefined') return
    try {
      if (section) {
        const state = getState()
        delete state[section]
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
      } else {
        localStorage.removeItem(STORAGE_KEY)
      }
    } catch {}
  }, [getState])

  return {
    saveJobsState,
    getJobsState,
    saveTalentFunnelState,
    getTalentFunnelState,
    clearState
  }
}
