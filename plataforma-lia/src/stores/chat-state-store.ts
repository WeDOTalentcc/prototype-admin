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
  wizardDraft: Record<string, unknown> | null
  userCommands: StoredUserCommand[]
  liaTemplates: Record<string, unknown>[]
}

interface ChatStateActions {
  setConversationId: (key: string, id: string) => void
  getConversationId: (key: string) => string | null
  removeConversationId: (key: string) => void
  setContextSnapshots: (snapshots: { wizard: StoredWizardSnapshot | null; general: StoredGeneralChatSnapshot | null }) => void
  clearContextSnapshots: () => void
  setWizardDraftId: (id: string | null) => void
  setWizardDraft: (draft: Record<string, unknown> | null) => void
  setUserCommands: (commands: StoredUserCommand[]) => void
  setLiaTemplates: (templates: Record<string, unknown>[]) => void
  resetStore: () => void
}

export type ChatStateStore = ChatStateState & ChatStateActions

const initialState: ChatStateState = {
  conversationIds: {},
  contextSnapshots: { wizard: null, general: null },
  wizardDraftId: null,
  wizardDraft: null,
  userCommands: [],
  liaTemplates: [],
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

        setWizardDraft: (draft) =>
          set({ wizardDraft: draft }, false, 'chatState/setWizardDraft'),

        setUserCommands: (commands) =>
          set({ userCommands: commands }, false, 'chatState/setUserCommands'),

        setLiaTemplates: (templates) =>
          set({ liaTemplates: templates }, false, 'chatState/setLiaTemplates'),

        resetStore: () => set(initialState, false, 'chatState/reset'),
      }),
      {
        name: 'lia-chat-state-store',
        partialize: (state) => {
          const { conversationIds: _conversationIds, ...rest } = state as ChatStateStore
          return rest
        },
      }
    ),
    { name: 'ChatStateStore' }
  )
)

registerStoreReset(() => useChatStateStore.getState().resetStore())
