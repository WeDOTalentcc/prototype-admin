import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

interface TriagemPersistedEntry {
  messages: unknown[]
  pageState: string
}

interface TriagemState {
  sessions: Record<string, TriagemPersistedEntry>
}

interface TriagemActions {
  setSessionState: (token: string, entry: TriagemPersistedEntry) => void
  getSessionState: (token: string) => TriagemPersistedEntry | null
  removeSessionState: (token: string) => void
}

export type TriagemStore = TriagemState & TriagemActions

export const useTriagemStore = create<TriagemStore>()(
  devtools(
    persist(
      (set, get) => ({
        sessions: {},

        setSessionState: (token, entry) =>
          set(
            (state) => ({
              sessions: { ...state.sessions, [token]: entry },
            }),
            false,
            'triagem/setSessionState'
          ),

        getSessionState: (token) => {
          const { sessions } = get()
          return sessions[token] ?? null
        },

        removeSessionState: (token) =>
          set(
            (state) => {
              const updated = { ...state.sessions }
              delete updated[token]
              return { sessions: updated }
            },
            false,
            'triagem/removeSessionState'
          ),
      }),
      {
        name: 'lia-triagem-store',
        partialize: (state) => ({
          sessions: state.sessions,
        }),
      }
    ),
    { name: 'TriagemStore' }
  )
)
