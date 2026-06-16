import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { registerStoreReset } from './auth-store'

export interface NavigateToCandidateData {
  candidateId?: string
  candidateName?: string
  jobId?: string
  jobTitle?: string
  currentStage?: string
  interviewType?: string
  action?: string
  openTransitionModal?: boolean
}

export interface NavigateToRecentCandidateData {
  candidateId?: string
}

export interface CandidatesFilterData {
  type?: string
  company?: string
  companies?: string[]
  source?: string
  [key: string]: unknown
}

export interface JobsNavState {
  lastJobId?: string
  lastView?: 'kanban' | 'table'
  lastTab?: string
  timestamp: number
}

export interface TalentFunnelNavState {
  lastTab?: 'search' | 'favorites' | 'lists'
  lastSearchQuery?: string
  timestamp: number
}

interface NavigationState {
  navigateToCandidate: NavigateToCandidateData | null
  liaPrompt: string | null
  navigateToRecentCandidate: NavigateToRecentCandidateData | null
  candidatesFilterData: CandidatesFilterData | null
  jobsNavState: JobsNavState | null
  talentFunnelNavState: TalentFunnelNavState | null
  liaSelectedCommand: string | null
  liaChatPrefill: string | null
  liaFilterSuggestion: string | null
  liaFilterPage: string | null
}

interface NavigationActions {
  setNavigateToCandidate: (data: NavigateToCandidateData | null) => void
  setLiaPrompt: (prompt: string | null) => void
  setNavigateToRecentCandidate: (data: NavigateToRecentCandidateData | null) => void
  consumeNavigateToCandidate: () => { nav: NavigateToCandidateData; prompt: string | null } | null
  consumeNavigateToRecentCandidate: () => NavigateToRecentCandidateData | null
  setCandidatesFilterData: (data: CandidatesFilterData | null) => void
  consumeCandidatesFilterData: () => CandidatesFilterData | null
  setJobsNavState: (data: JobsNavState | null) => void
  setTalentFunnelNavState: (data: TalentFunnelNavState | null) => void
  saveJobsState: (jobId: string, view?: 'kanban' | 'table', tab?: string) => void
  saveTalentFunnelState: (tab: 'search' | 'favorites' | 'lists', searchQuery?: string) => void
  getJobsNavState: () => JobsNavState | null
  getTalentFunnelNavState: () => TalentFunnelNavState | null
  setLiaSelectedCommand: (command: string | null) => void
  setLiaChatPrefill: (text: string | null) => void
  setLiaFilterSuggestion: (suggestion: string | null) => void
  setLiaFilterPage: (page: string | null) => void
  resetStore: () => void
}

export type NavigationStore = NavigationState & NavigationActions

const NAV_TTL_MS = 7 * 24 * 60 * 60 * 1000

export const useNavigationStore = create<NavigationStore>()(
  devtools(
    persist(
      (set, get) => ({
        navigateToCandidate: null,
        liaPrompt: null,
        navigateToRecentCandidate: null,
        candidatesFilterData: null,
        jobsNavState: null,
        talentFunnelNavState: null,
        liaSelectedCommand: null,
        liaChatPrefill: null,
        liaFilterSuggestion: null,
        liaFilterPage: null,

        setNavigateToCandidate: (data) =>
          set({ navigateToCandidate: data }, false, 'navigation/setNavigateToCandidate'),

        setLiaPrompt: (prompt) =>
          set({ liaPrompt: prompt }, false, 'navigation/setLiaPrompt'),

        setNavigateToRecentCandidate: (data) =>
          set({ navigateToRecentCandidate: data }, false, 'navigation/setNavigateToRecentCandidate'),

        consumeNavigateToCandidate: () => {
          const { navigateToCandidate, liaPrompt } = get()
          if (!navigateToCandidate) return null
          set({ navigateToCandidate: null, liaPrompt: null }, false, 'navigation/consumeNavigateToCandidate')
          return { nav: navigateToCandidate, prompt: liaPrompt }
        },

        consumeNavigateToRecentCandidate: () => {
          const { navigateToRecentCandidate } = get()
          if (!navigateToRecentCandidate) return null
          set({ navigateToRecentCandidate: null }, false, 'navigation/consumeNavigateToRecentCandidate')
          return navigateToRecentCandidate
        },

        setCandidatesFilterData: (data) =>
          set({ candidatesFilterData: data }, false, 'navigation/setCandidatesFilterData'),

        consumeCandidatesFilterData: () => {
          const { candidatesFilterData } = get()
          if (!candidatesFilterData) return null
          set({ candidatesFilterData: null }, false, 'navigation/consumeCandidatesFilterData')
          return candidatesFilterData
        },

        setJobsNavState: (data) =>
          set({ jobsNavState: data }, false, 'navigation/setJobsNavState'),

        setTalentFunnelNavState: (data) =>
          set({ talentFunnelNavState: data }, false, 'navigation/setTalentFunnelNavState'),

        saveJobsState: (jobId, view, tab) =>
          set({
            jobsNavState: { lastJobId: jobId, lastView: view, lastTab: tab, timestamp: Date.now() }
          }, false, 'navigation/saveJobsState'),

        saveTalentFunnelState: (tab, searchQuery) =>
          set({
            talentFunnelNavState: { lastTab: tab, lastSearchQuery: searchQuery, timestamp: Date.now() }
          }, false, 'navigation/saveTalentFunnelState'),

        getJobsNavState: () => {
          const { jobsNavState } = get()
          if (!jobsNavState) return null
          if (Date.now() - jobsNavState.timestamp > NAV_TTL_MS) return null
          return jobsNavState
        },

        getTalentFunnelNavState: () => {
          const { talentFunnelNavState } = get()
          if (!talentFunnelNavState) return null
          if (Date.now() - talentFunnelNavState.timestamp > NAV_TTL_MS) return null
          return talentFunnelNavState
        },

        setLiaSelectedCommand: (command) =>
          set({ liaSelectedCommand: command }, false, 'navigation/setLiaSelectedCommand'),

        setLiaChatPrefill: (text) =>
          set({ liaChatPrefill: text }, false, 'navigation/setLiaChatPrefill'),

        setLiaFilterSuggestion: (suggestion) =>
          set({ liaFilterSuggestion: suggestion }, false, 'navigation/setLiaFilterSuggestion'),

        setLiaFilterPage: (page) =>
          set({ liaFilterPage: page }, false, 'navigation/setLiaFilterPage'),

        resetStore: () =>
          set({
            navigateToCandidate: null,
            liaPrompt: null,
            navigateToRecentCandidate: null,
            candidatesFilterData: null,
            jobsNavState: null,
            talentFunnelNavState: null,
            liaSelectedCommand: null,
            liaChatPrefill: null,
            liaFilterSuggestion: null,
            liaFilterPage: null,
          }, false, 'navigation/reset'),
      }),
      {
        name: 'lia-navigation-store',
        partialize: (state) => ({
          navigateToCandidate: state.navigateToCandidate,
          liaPrompt: state.liaPrompt,
          navigateToRecentCandidate: state.navigateToRecentCandidate,
          candidatesFilterData: state.candidatesFilterData,
          jobsNavState: state.jobsNavState,
          talentFunnelNavState: state.talentFunnelNavState,
          liaSelectedCommand: state.liaSelectedCommand,
          liaChatPrefill: state.liaChatPrefill,
          liaFilterSuggestion: state.liaFilterSuggestion,
          liaFilterPage: state.liaFilterPage,
        }),
      }
    ),
    { name: 'NavigationStore' }
  )
)

registerStoreReset(() => useNavigationStore.getState().resetStore())
