import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

interface CommandHistoryItem {
  command: string
  timestamp: string
  filters?: Record<string, unknown>
  actions?: string[]
  complexity: number
  sessionId: string
}

interface TemplateSettings {
  enabled: boolean
  minComplexity: number
  minRepetitions: number
  frequency: 'never' | 'weekly' | 'daily' | 'smart'
  showEndOfSession: boolean
}

interface TemplateState {
  commandHistory: CommandHistoryItem[]
  settings: TemplateSettings
}

interface TemplateActions {
  setCommandHistory: (history: CommandHistoryItem[]) => void
  setSettings: (settings: TemplateSettings) => void
}

export type TemplateStore = TemplateState & TemplateActions

const DEFAULT_SETTINGS: TemplateSettings = {
  enabled: true,
  minComplexity: 5,
  minRepetitions: 3,
  frequency: 'smart',
  showEndOfSession: true,
}

export const useTemplateStore = create<TemplateStore>()(
  devtools(
    persist(
      (set) => ({
        commandHistory: [],
        settings: DEFAULT_SETTINGS,

        setCommandHistory: (history) =>
          set({ commandHistory: history }, false, 'template/setCommandHistory'),

        setSettings: (settings) =>
          set({ settings }, false, 'template/setSettings'),
      }),
      {
        name: 'lia-template-store',
        partialize: (state) => ({
          commandHistory: state.commandHistory,
          settings: state.settings,
        }),
      }
    ),
    { name: 'TemplateStore' }
  )
)
