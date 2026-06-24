// src/stores/ia-session-store.ts
// IASidebar session management store (PR 4)
// React Query owns sessions[] + titles (staleTime 30s)
// Zustand owns: isIASidebarOpen, activeConversationId, localUnreadCounts

import { create } from "zustand"
import { devtools } from "zustand/middleware"
import { registerStoreReset } from "./auth-store"

interface IASessionStoreState {
  isIASidebarOpen: boolean
  activeConversationId: string | null
  // client-side unread deltas (cleared on mark-read)
  localUnreadCounts: Record<string, number>

  openIASidebar: () => void
  closeIASidebar: () => void
  toggleIASidebar: () => void
  setActiveConversation: (id: string | null) => void
  markLocalRead: (id: string) => void
  incrementLocalUnread: (id: string) => void
}

export const useIASessionStore = create<IASessionStoreState>()(
  devtools(
    (set, get) => ({
      isIASidebarOpen: false,
      activeConversationId: null,
      localUnreadCounts: {},

      openIASidebar: () => set({ isIASidebarOpen: true }),
      closeIASidebar: () => set({ isIASidebarOpen: false }),
      toggleIASidebar: () => set((s) => ({ isIASidebarOpen: !s.isIASidebarOpen })),

      setActiveConversation: (id) => {
        set({ activeConversationId: id })
        // Clear local unread count when user opens a conversation
        if (id) {
          set((s) => ({
            localUnreadCounts: { ...s.localUnreadCounts, [id]: 0 },
          }))
        }
      },

      markLocalRead: (id) =>
        set((s) => ({
          localUnreadCounts: { ...s.localUnreadCounts, [id]: 0 },
        })),

      incrementLocalUnread: (id) => {
        // Only increment if NOT the active conversation
        const { activeConversationId } = get()
        if (id !== activeConversationId) {
          set((s) => ({
            localUnreadCounts: {
              ...s.localUnreadCounts,
              [id]: (s.localUnreadCounts[id] ?? 0) + 1,
            },
          }))
        }
      },
    }),
    { name: "ia-session-store" }
  )
)

registerStoreReset(() =>
  useIASessionStore.setState({
    isIASidebarOpen: false,
    activeConversationId: null,
    localUnreadCounts: {},
  })
)
