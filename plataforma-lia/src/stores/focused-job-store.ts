import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface FocusedJob {
  id: string
  title: string
  candidateCount: number
  todayInterviewCount: number
}

interface FocusedJobState {
  focusedJob: FocusedJob | null
}

interface FocusedJobActions {
  setFocusedJob: (job: FocusedJob) => void
  clearFocusedJob: () => void
}

type FocusedJobStore = FocusedJobState & FocusedJobActions

export const useFocusedJobStore = create<FocusedJobStore>()(
  persist(
    (set) => ({
      focusedJob: null,
      setFocusedJob: (job) => set({ focusedJob: job }),
      clearFocusedJob: () => set({ focusedJob: null }),
    }),
    {
      name: 'focused-job-storage',
    }
  )
)
