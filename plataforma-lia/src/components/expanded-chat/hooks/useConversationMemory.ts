'use client'

import { useState, useCallback, useRef, useEffect } from 'react'

const BACKEND_URL = '/api/backend-proxy'

export interface Message {
  id: string
  conversation_id: string
  role: string
  content: string
  intent?: string
  tool_calls?: Array<Record<string, unknown>>
  metadata?: Record<string, unknown>
  created_at?: string
}

export interface ConversationContext {
  conversation_id: string
  context_type: string
  context_id?: string
  summary?: string
  recent_messages: Array<{ role: string; content: string; intent?: string }>
}

export interface Conversation {
  id: string
  user_id: string
  context_type: string
  context_id?: string
  title?: string
  summary?: string
  intent?: string
  status: string
  is_active: boolean
  message_count: number
  created_at?: string
  updated_at?: string
}

export interface UseConversationMemoryOptions {
  autoInit?: boolean
  summaryThreshold?: number
  maxMessages?: number
  onError?: (error: Error) => void
  onConversationLoaded?: (conversation: Conversation) => void
}

export interface UseConversationMemoryReturn {
  conversationId: string | null
  messages: Message[]
  summary: string | null
  isLoading: boolean
  error: Error | null
  conversation: Conversation | null
  initConversation: (userId: string, contextType: string, contextId?: string) => Promise<void>
  addMessage: (role: string, content: string, intent?: string) => Promise<Message | null>
  getContext: () => Promise<ConversationContext | null>
  clearConversation: () => void
  refreshConversation: () => Promise<void>
  archiveConversation: () => Promise<boolean>
  updateSummary: (force?: boolean) => Promise<string | null>
}

function getStorageKey(contextType: string, contextId?: string): string {
  return `lia_conversation_${contextType}_${contextId || 'default'}`
}

function loadConversationId(contextType: string, contextId?: string): string | null {
  if (typeof window === 'undefined') return null
  try {
    return localStorage.getItem(getStorageKey(contextType, contextId))
  } catch {
    return null
  }
}

function saveConversationId(contextType: string, contextId: string | undefined, conversationId: string): void {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(getStorageKey(contextType, contextId), conversationId)
  } catch {
  }
}

function clearStoredConversationId(contextType: string, contextId?: string): void {
  if (typeof window === 'undefined') return
  try {
    localStorage.removeItem(getStorageKey(contextType, contextId))
  } catch {
  }
}

function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('access_token')
}

function getAuthHeaders(): HeadersInit {
  const token = getAccessToken()
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  }
}

export function useConversationMemory(options: UseConversationMemoryOptions = {}): UseConversationMemoryReturn {
  const {
    summaryThreshold = 10,
    maxMessages = 50,
    onError,
    onConversationLoaded,
  } = options

  const [conversationId, setConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [summary, setSummary] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [conversation, setConversation] = useState<Conversation | null>(null)

  const currentContextRef = useRef<{ contextType: string; contextId?: string } | null>(null)
  const messageCountRef = useRef(0)

  const handleError = useCallback((err: Error) => {
    setError(err)
    onError?.(err)
  }, [onError])

  const createConversation = useCallback(async (
    userId: string,
    contextType: string,
    contextId?: string
  ): Promise<Conversation | null> => {
    try {
      const response = await fetch(`${BACKEND_URL}/conversations`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          user_id: userId,
          context_type: contextType,
          context_id: contextId,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }))
        throw new Error(errorData.detail || 'Failed to create conversation')
      }

      return response.json()
    } catch (err) {
      handleError(err instanceof Error ? err : new Error(String(err)))
      return null
    }
  }, [handleError])

  const fetchConversation = useCallback(async (
    convId: string,
    includeMessages = true
  ): Promise<{ conversation: Conversation; messages: Message[]; summary: string | null } | null> => {
    try {
      const params = new URLSearchParams({
        include_messages: String(includeMessages),
        include_summaries: 'true',
        message_limit: String(maxMessages),
      })

      const response = await fetch(`${BACKEND_URL}/conversations/${convId}?${params}`, {
        headers: getAuthHeaders(),
      })

      if (!response.ok) {
        if (response.status === 404) {
          return null
        }
        const errorData = await response.json().catch(() => ({ detail: response.statusText }))
        throw new Error(errorData.detail || 'Failed to fetch conversation')
      }

      const data = await response.json()
      return {
        conversation: data.conversation,
        messages: data.messages || [],
        summary: data.summary || null,
      }
    } catch (err) {
      handleError(err instanceof Error ? err : new Error(String(err)))
      return null
    }
  }, [maxMessages, handleError])

  const initConversation = useCallback(async (
    userId: string,
    contextType: string,
    contextId?: string
  ): Promise<void> => {
    setIsLoading(true)
    setError(null)

    try {
      currentContextRef.current = { contextType, contextId }

      const storedId = loadConversationId(contextType, contextId)

      if (storedId) {
        const existing = await fetchConversation(storedId)
        
        if (existing && existing.conversation.is_active) {
          setConversationId(storedId)
          setConversation(existing.conversation)
          setMessages(existing.messages)
          setSummary(existing.summary)
          messageCountRef.current = existing.conversation.message_count
          onConversationLoaded?.(existing.conversation)
          return
        }
        
        clearStoredConversationId(contextType, contextId)
      }

      const newConversation = await createConversation(userId, contextType, contextId)
      
      if (newConversation) {
        saveConversationId(contextType, contextId, newConversation.id)
        setConversationId(newConversation.id)
        setConversation(newConversation)
        setMessages([])
        setSummary(null)
        messageCountRef.current = 0
        onConversationLoaded?.(newConversation)
      }
    } finally {
      setIsLoading(false)
    }
  }, [fetchConversation, createConversation, onConversationLoaded])

  const addMessage = useCallback(async (
    role: string,
    content: string,
    intent?: string
  ): Promise<Message | null> => {
    if (!conversationId) {
      return null
    }

    setError(null)

    try {
      const response = await fetch(`${BACKEND_URL}/conversations/${conversationId}/messages`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          role,
          content,
          intent,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }))
        throw new Error(errorData.detail || 'Failed to add message')
      }

      const message: Message = await response.json()
      
      setMessages(prev => {
        const updated = [...prev, message]
        if (updated.length > maxMessages) {
          return updated.slice(-maxMessages)
        }
        return updated
      })

      messageCountRef.current += 1

      if (messageCountRef.current > 0 && messageCountRef.current % summaryThreshold === 0) {
        updateSummary(false).catch(() => {})
      }

      return message
    } catch (err) {
      handleError(err instanceof Error ? err : new Error(String(err)))
      return null
    }
  }, [conversationId, maxMessages, summaryThreshold, handleError])

  const updateSummary = useCallback(async (force = false): Promise<string | null> => {
    if (!conversationId) return null

    try {
      const response = await fetch(`${BACKEND_URL}/conversations/${conversationId}/summary`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ force }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }))
        throw new Error(errorData.detail || 'Failed to update summary')
      }

      const data = await response.json()
      if (data.summary) {
        setSummary(data.summary)
      }
      return data.summary
    } catch (err) {
      handleError(err instanceof Error ? err : new Error(String(err)))
      return null
    }
  }, [conversationId, handleError])

  const getContext = useCallback(async (): Promise<ConversationContext | null> => {
    if (!conversationId || !currentContextRef.current) {
      return null
    }

    try {
      const response = await fetch(`${BACKEND_URL}/conversations/${conversationId}/context?max_messages=20`, {
        headers: getAuthHeaders(),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }))
        throw new Error(errorData.detail || 'Failed to get context')
      }

      const data = await response.json()
      
      return {
        conversation_id: conversationId,
        context_type: currentContextRef.current.contextType,
        context_id: currentContextRef.current.contextId,
        summary: data.summary || summary,
        recent_messages: data.messages || messages.slice(-20).map(m => ({
          role: m.role,
          content: m.content,
          intent: m.intent,
        })),
      }
    } catch (err) {
      handleError(err instanceof Error ? err : new Error(String(err)))
      return null
    }
  }, [conversationId, summary, messages, handleError])

  const clearConversation = useCallback(() => {
    if (currentContextRef.current) {
      clearStoredConversationId(
        currentContextRef.current.contextType,
        currentContextRef.current.contextId
      )
    }
    
    setConversationId(null)
    setConversation(null)
    setMessages([])
    setSummary(null)
    setError(null)
    messageCountRef.current = 0
    currentContextRef.current = null
  }, [])

  const refreshConversation = useCallback(async (): Promise<void> => {
    if (!conversationId) return

    setIsLoading(true)
    try {
      const data = await fetchConversation(conversationId)
      if (data) {
        setConversation(data.conversation)
        setMessages(data.messages)
        setSummary(data.summary)
        messageCountRef.current = data.conversation.message_count
      }
    } finally {
      setIsLoading(false)
    }
  }, [conversationId, fetchConversation])

  const archiveConversation = useCallback(async (): Promise<boolean> => {
    if (!conversationId) return false

    try {
      const response = await fetch(`${BACKEND_URL}/conversations/${conversationId}/archive`, {
        method: 'POST',
        headers: getAuthHeaders(),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }))
        throw new Error(errorData.detail || 'Failed to archive conversation')
      }

      clearConversation()
      return true
    } catch (err) {
      handleError(err instanceof Error ? err : new Error(String(err)))
      return false
    }
  }, [conversationId, clearConversation, handleError])

  return {
    conversationId,
    messages,
    summary,
    isLoading,
    error,
    conversation,
    initConversation,
    addMessage,
    getContext,
    clearConversation,
    refreshConversation,
    archiveConversation,
    updateSummary,
  }
}
