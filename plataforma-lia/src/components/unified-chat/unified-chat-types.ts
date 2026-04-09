export type ChatMode = "fullscreen" | "sidebar" | "floating"

export type ChatScope = "page" | "universal"

export interface UnifiedChatProps {
  mode: ChatMode
  onModeChange: (mode: ChatMode) => void
  className?: string
}
