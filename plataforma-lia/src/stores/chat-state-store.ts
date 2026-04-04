import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { registerStoreReset } from './auth-store'

export interface StoredWizardSnapshot {
  stage: string
  basicInfoFields: Record<string, unknown>
  technicalSkills: unknown[]
  behavioralCompetencies: unknown[]
  salaryInfo: Record<string, unknown>
  wsiQuestions: unknown[]
  detectedCriteria: Record<string, unknown>
  generatedJobDescription: string
  fastTrackSourceJobId: string | null
  timestamp: number
}

export interface StoredGeneralChatSnapshot {
  conversationId: string | null
  lastMessageIndex: number
  timestamp: number
}

export interface StoredUserCommand {
  id: string
  title: string
  command: string
  description: string
  category: string
  examples: string[]
  tags: string[]
  result?: string
  createdAt: string
  lastUsed?: string
  usageCount: number
  rating: number
  author: string
}

interface ChatStateState {
  conversationIds: Record<string, string>
  contextSnapshots: { wizard: StoredWizardSnapshot | null; general: StoredGeneralChatSnapshot | null }
  wizardDraftId: string | null
  userCommands: StoredUserCommand[]
}

interface ChatStateActions {
  setConversationId: (key: string, id: string) => void
  getConversationId: (key: string) => string | null
  removeConversationId: (key: string) => void
  setContextSnapshots: (snapshots: { wizard: StoredWizardSnapshot | null; general: StoredGeneralChatSnapshot | null }) => void
  clearContextSnapshots: () => void
  setWizardDraftId: (id: string | null) => void
  setUserCommands: (commands: StoredUserCommand[]) => void
  resetStore: () => void
}

export type ChatStateStore = ChatStateState & ChatStateActions

const initialState: ChatStateState = {
  conversationIds: {},
  contextSnapshots: { wizard: null, general: null },
  wizardDraftId: null,
  userCommands: [],
}

export const useChatStateStore = create<ChatStateStore>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        setConversationId: (key, id) =>
          set(
            (state) => ({
              conversationIds: { ...state.conversationIds, [key]: id },
            }),
            false,
            'chatState/setConversationId'
          ),

        getConversationId: (key) => get().conversationIds[key] || null,

        removeConversationId: (key) =>
          set(
            (state) => {
              const updated = { ...state.conversationIds }
              delete updated[key]
              return { conversationIds: updated }
            },
            false,
            'chatState/removeConversationId'
          ),

        setContextSnapshots: (snapshots) =>
          set({ contextSnapshots: snapshots }, false, 'chatState/setContextSnapshots'),

        clearContextSnapshots: () =>
          set(
            { contextSnapshots: { wizard: null, general: null } },
            false,
            'chatState/clearContextSnapshots'
          ),

        setWizardDraftId: (id) =>
          set({ wizardDraftId: id }, false, 'chatState/setWizardDraftId'),

        setUserCommands: (commands) =>
          set({ userCommands: commands }, false, 'chatState/setUserCommands'),

        resetStore: () => set(initialState, false, 'chatState/reset'),
      }),
      { name: 'lia-chat-state-store' }
    ),
    { name: 'ChatStateStore' }
  )
)

registerStoreReset(() => useChatStateStore.getState().resetStore())
