import { useMemo } from 'react'

export type ChatLayoutMode = 'empty' | 'chat-only' | 'chat-with-panel'

interface UseChatLayoutProps {
  isEmptyChat: boolean
  isPanelOpen: boolean
}

interface ChatLayoutResult {
  mode: ChatLayoutMode
  chatContainerClass: string
  inputContainerClass: string
  messagesContainerClass: string
}

/**
 * Hook to manage chat layout states with responsive behavior
 * 
 * States:
 * 1. empty - Empty chat, centered prompt
 * 2. chat-only - Active chat without panel, centered
 * 3. chat-with-panel - Chat with context panel, 60/40 split
 */
export function useChatLayout({ isEmptyChat, isPanelOpen }: UseChatLayoutProps): ChatLayoutResult {
  const mode: ChatLayoutMode = useMemo(() => {
    if (isEmptyChat) return 'empty'
    if (isPanelOpen) return 'chat-with-panel'
    return 'chat-only'
  }, [isEmptyChat, isPanelOpen])

  const chatContainerClass = useMemo(() => {
    switch (mode) {
      case 'empty':
        return 'flex flex-col items-center justify-center px-4'
      case 'chat-only':
        return 'flex flex-col px-4'
      case 'chat-with-panel':
        return 'flex flex-col w-full'
      default:
        return ''
    }
  }, [mode])

  const inputContainerClass = useMemo(() => {
    switch (mode) {
      case 'empty':
        return 'w-full max-w-3xl mx-auto transition-colors duration-200 ease-in-out'
      case 'chat-only':
        return 'w-full max-w-3xl mx-auto transition-colors duration-200 ease-in-out'
      case 'chat-with-panel':
        return 'w-full transition-colors duration-200 ease-in-out'
      default:
        return ''
    }
  }, [mode])

  const messagesContainerClass = useMemo(() => {
    switch (mode) {
      case 'empty':
        return 'w-full max-w-3xl transition-colors duration-200'
      case 'chat-only':
        return 'w-full max-w-4xl transition-colors duration-200'
      case 'chat-with-panel':
        return 'w-full transition-colors duration-200'
      default:
        return ''
    }
  }, [mode])

  return {
    mode,
    chatContainerClass,
    inputContainerClass,
    messagesContainerClass
  }
}
