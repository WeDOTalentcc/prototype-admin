'use client'

import { useCallback } from 'react'
import { useNavigationStore } from '@/stores/navigation-store'
import type { JobsNavState, TalentFunnelNavState } from '@/stores/navigation-store'

export function useNavigationPersistence() {
  const storeSaveJobsState = useNavigationStore(s => s.saveJobsState)
  const storeGetJobsNavState = useNavigationStore(s => s.getJobsNavState)
  const storeSaveTalentFunnelState = useNavigationStore(s => s.saveTalentFunnelState)
  const storeGetTalentFunnelNavState = useNavigationStore(s => s.getTalentFunnelNavState)
  const storeSetJobsNavState = useNavigationStore(s => s.setJobsNavState)
  const storeSetTalentFunnelNavState = useNavigationStore(s => s.setTalentFunnelNavState)

  const saveJobsState = useCallback((jobId: string, view?: 'kanban' | 'table', tab?: string) => {
    storeSaveJobsState(jobId, view, tab)
  }, [storeSaveJobsState])

  const getJobsState = useCallback((): JobsNavState | undefined => {
    return storeGetJobsNavState() ?? undefined
  }, [storeGetJobsNavState])

  const saveTalentFunnelState = useCallback((tab: 'search' | 'favorites' | 'lists', searchQuery?: string) => {
    storeSaveTalentFunnelState(tab, searchQuery)
  }, [storeSaveTalentFunnelState])

  const getTalentFunnelState = useCallback((): TalentFunnelNavState | undefined => {
    return storeGetTalentFunnelNavState() ?? undefined
  }, [storeGetTalentFunnelNavState])

  const clearState = useCallback((section?: 'jobs' | 'talentFunnel') => {
    if (section === 'jobs') {
      storeSetJobsNavState(null)
    } else if (section === 'talentFunnel') {
      storeSetTalentFunnelNavState(null)
    } else {
      storeSetJobsNavState(null)
      storeSetTalentFunnelNavState(null)
    }
  }, [storeSetJobsNavState, storeSetTalentFunnelNavState])

  return {
    saveJobsState,
    getJobsState,
    saveTalentFunnelState,
    getTalentFunnelState,
    clearState
  }
}
