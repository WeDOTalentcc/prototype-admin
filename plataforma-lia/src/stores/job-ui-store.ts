import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

export interface PendingCommunicationAction {
  jobId: string
  template?: string
  candidateIds?: string[]
  channel?: 'email' | 'whatsapp'
  action?: string
}

interface JobUIState {
  pendingCommunicationAction: PendingCommunicationAction | null
  jobCreationMode: string | null
}

interface JobUIActions {
  setPendingCommunicationAction: (action: PendingCommunicationAction | null) => void
  consumePendingCommunicationAction: (jobId: string) => PendingCommunicationAction | null
  setJobCreationMode: (jobId: string | null) => void
  consumeJobCreationMode: (backendId: string) => boolean
}

export type JobUIStore = JobUIState & JobUIActions

export const useJobUIStore = create<JobUIStore>()(
  devtools(
    persist(
      (set, get) => ({
        pendingCommunicationAction: null,
        jobCreationMode: null,

        setPendingCommunicationAction: (action) =>
          set({ pendingCommunicationAction: action }, false, 'jobUI/setPendingCommunicationAction'),

        consumePendingCommunicationAction: (jobId: string) => {
          const { pendingCommunicationAction } = get()
          if (pendingCommunicationAction && String(pendingCommunicationAction.jobId) === String(jobId)) {
            set({ pendingCommunicationAction: null }, false, 'jobUI/consumePendingCommunicationAction')
            return pendingCommunicationAction
          }
          return null
        },

        setJobCreationMode: (jobId) =>
          set({ jobCreationMode: jobId }, false, 'jobUI/setJobCreationMode'),

        consumeJobCreationMode: (backendId: string) => {
          const { jobCreationMode } = get()
          if (jobCreationMode && jobCreationMode === backendId) {
            set({ jobCreationMode: null }, false, 'jobUI/consumeJobCreationMode')
            return true
          }
          return false
        },
      }),
      {
        name: 'lia-job-ui-store',
      }
    ),
    { name: 'JobUIStore' }
  )
)
