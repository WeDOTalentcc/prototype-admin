import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

export interface RecentItem {
  id: string
  type: 'vaga' | 'chat' | 'candidato' | 'banco' | string
  title: string
  subtitle?: string
  timestamp: number
  meta?: {
    jobId?: string
    candidateId?: string
    conversationId?: string
    jobTitle?: string
    poolId?: string
    poolName?: string
    [key: string]: unknown
  }
}

const MAX_ITEMS = 15

interface RecentItemsState {
  items: RecentItem[]
}

interface RecentItemsActions {
  setItems: (items: RecentItem[]) => void
  addItem: (item: RecentItem) => void
  removeItem: (id: string, type: string) => void
  clearAll: () => void
}

export type RecentItemsStore = RecentItemsState & RecentItemsActions

export const useRecentItemsStore = create<RecentItemsStore>()(
  devtools(
    persist(
      (set) => ({
        items: [],

        setItems: (items) =>
          set({ items }, false, 'recentItems/setItems'),

        addItem: (item) =>
          set(
            (state) => {
              const filtered = state.items.filter(
                (existing) => !(existing.id === item.id && existing.type === item.type)
              )
              const updated = [item, ...filtered].slice(0, MAX_ITEMS)
              return { items: updated }
            },
            false,
            'recentItems/addItem'
          ),

        removeItem: (id, type) =>
          set(
            (state) => ({
              items: state.items.filter(
                (item) => !(item.id === id && item.type === type)
              ),
            }),
            false,
            'recentItems/removeItem'
          ),

        clearAll: () =>
          set({ items: [] }, false, 'recentItems/clearAll'),
      }),
      {
        name: 'lia-recent-items-store',
        partialize: (state) => ({
          items: state.items,
        }),
      }
    ),
    { name: 'RecentItemsStore' }
  )
)
