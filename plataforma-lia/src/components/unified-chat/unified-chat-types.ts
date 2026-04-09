export type ChatMode = "fullscreen" | "sidebar" | "floating"

export interface SuggestionCard {
  icon: string
  label: string
  description?: string
  action: string
}

export interface ConversationMeta {
  id: string
  title: string
  updatedAt: string
}

export interface UnifiedChatProps {
  mode: ChatMode
  onModeChange: (mode: ChatMode) => void
  className?: string
}
