export type ChatMode = "fullscreen" | "sidebar" | "floating" | "minimized"

export type ChatScope = "page" | "universal"

export interface UnifiedChatProps {
  mode: ChatMode
  onModeChange: (mode: ChatMode) => void
  className?: string
}
