// src/stores/lia-panel-store.ts
import { create } from 'zustand'
import { registerStoreReset } from './auth-store'

interface LiaPanelState {
  focusedToolCallId: string | null
  _panelOpenBySession: Record<string, boolean>
  openForToolCall: (callId: string, sessionId: string) => void
  closePanel: (sessionId: string) => void
  isPanelOpenForSession: (sessionId: string) => boolean
}

export const useLiaPanelStore = create<LiaPanelState>((set, get) => ({
  focusedToolCallId: null,
  _panelOpenBySession: {},

  openForToolCall: (callId, sessionId) =>
    set({
      focusedToolCallId: callId,
      _panelOpenBySession: { ...get()._panelOpenBySession, [sessionId]: true },
    }),

  closePanel: (sessionId) =>
    set({
      _panelOpenBySession: { ...get()._panelOpenBySession, [sessionId]: false },
    }),

  isPanelOpenForSession: (sessionId) =>
    get()._panelOpenBySession[sessionId] ?? false,
}))

registerStoreReset(() =>
  useLiaPanelStore.setState({ focusedToolCallId: null, _panelOpenBySession: {} })
)
