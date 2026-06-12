// src/stores/lia-panel-store.ts
import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { registerStoreReset } from './auth-store'

interface LiaPanelState {
  focusedToolCallId: string | null
  _panelOpenBySession: Record<string, boolean>
  openForToolCall: (callId: string, sessionId: string) => void
  closePanel: (sessionId: string) => void
  isPanelOpenForSession: (sessionId: string) => boolean
}

export const useLiaPanelStore = create<LiaPanelState>()(
  devtools(
    (set, get) => ({
      focusedToolCallId: null,
      _panelOpenBySession: {},

      openForToolCall: (callId, sessionId) =>
        set({
          focusedToolCallId: callId,
          _panelOpenBySession: { ...get()._panelOpenBySession, [sessionId]: true },
        }),

      // focusedToolCallId is intentionally preserved on close — Phase 1 uses it
      // for exit-animation and re-open scenarios (panel re-opens focused on same call).
      closePanel: (sessionId) =>
        set({
          _panelOpenBySession: { ...get()._panelOpenBySession, [sessionId]: false },
        }),

      isPanelOpenForSession: (sessionId) =>
        get()._panelOpenBySession[sessionId] ?? false,
    }),
    { name: 'LiaPanelStore' }
  )
)

registerStoreReset(() =>
  useLiaPanelStore.setState({ focusedToolCallId: null, _panelOpenBySession: {} })
)
