'use client'

import { useState, useCallback, useRef } from 'react'

interface InterpretContextParams {
  candidate_id: string
  candidate_name?: string
  job_title?: string
  job_id?: string
  from_stage: string
  to_stage: string
  action_behavior: string
  prompt?: string
  company_id?: string
  message_history?: InterpretChatMessage[]
  conversation_id?: string
}

export interface TaskItem {
  type: string
  description: string
  data_type?: string
  status: string
}

export interface LearnedSuggestion {
  key: string
  value: string
  frequency: number
  source: string
}

interface InterpretContextResult {
  suggested_sub_status: string
  suggested_action: 'lia_auto' | 'manual' | 'just_move'
  action_label: string
  urgency: 'normal' | 'high' | 'low'
  lia_message?: string
  extracted_preferences?: Record<string, string>
  ai_powered?: boolean
  confidence?: number
  tasks?: TaskItem[]
  out_of_scope?: boolean
  candidate_info?: Record<string, unknown>
  learned_suggestions?: LearnedSuggestion[]
  fairness_result?: {
    is_fair: boolean
    warnings: string[]
    educational_message?: string
  }
  layer?: number
  conversation_id?: string
}

export interface InterpretChatMessage {
  role: 'user' | 'lia'
  content: string
  timestamp: number
  metadata?: {
    suggested_sub_status?: string
    suggested_action?: 'lia_auto' | 'manual' | 'just_move'
    extracted_preferences?: Record<string, string>
    ai_powered?: boolean
    confidence?: number
    tasks?: TaskItem[]
    out_of_scope?: boolean
    candidate_info?: Record<string, unknown>
    learned_suggestions?: LearnedSuggestion[]
    fairness_result?: {
      is_fair: boolean
      warnings: string[]
      educational_message?: string
    }
    layer?: number
    executionPlan?: Record<string, unknown>
    execution_plan?: Record<string, unknown>
  }
}

export function useInterpretContext() {
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<InterpretContextResult | null>(null)
  const [messages, setMessages] = useState<InterpretChatMessage[]>([])
  const [conversationId, setConversationId] = useState<string | undefined>(undefined)

  const messagesRef = useRef<InterpretChatMessage[]>([])
  messagesRef.current = messages
  const conversationIdRef = useRef<string | undefined>(undefined)
  conversationIdRef.current = conversationId

  const sendMessage = useCallback(async (
    userMessage: string,
    params: Omit<InterpretContextParams, 'prompt' | 'message_history'>
  ) => {
    const userChatMessage: InterpretChatMessage = {
      role: 'user',
      content: userMessage,
      timestamp: Date.now(),
    }
    setMessages(prev => [...prev, userChatMessage])
    setIsLoading(true)

    try {
      const currentMessages = [...messagesRef.current, userChatMessage]
      const response = await fetch('/api/backend-proxy/interpret-context', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...params,
          prompt: userMessage,
          conversation_id: conversationIdRef.current,
          message_history: currentMessages.map(m => ({
            role: m.role,
            content: m.content,
            timestamp: m.timestamp,
          })),
        })
      })
      if (response.ok) {
        const data: InterpretContextResult = await response.json()
        setResult(data)
        if (data.conversation_id) {
          setConversationId(data.conversation_id)
        }

        if (data.lia_message) {
          const liaChatMessage: InterpretChatMessage = {
            role: 'lia',
            content: data.lia_message,
            timestamp: Date.now(),
            metadata: {
              suggested_sub_status: data.suggested_sub_status,
              suggested_action: data.suggested_action,
              extracted_preferences: data.extracted_preferences,
              ai_powered: data.ai_powered,
              confidence: data.confidence,
              tasks: data.tasks,
              out_of_scope: data.out_of_scope,
              candidate_info: data.candidate_info,
              learned_suggestions: data.learned_suggestions,
              fairness_result: data.fairness_result,
              layer: data.layer,
            }
          }
          setMessages(prev => [...prev, liaChatMessage])
        }
        return data
      }
    } catch (error) {
      const errorMessage: InterpretChatMessage = {
        role: 'lia',
        content: 'Desculpe, não consegui processar sua mensagem. Tente novamente.',
        timestamp: Date.now(),
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
    return null
  }, [])

  const interpret = useCallback(async (params: InterpretContextParams) => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/backend-proxy/interpret-context', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      })
      if (response.ok) {
        const data = await response.json()
        setResult(data)
        return data
      }
    } catch (error) {
    } finally {
      setIsLoading(false)
    }
    return null
  }, [])

  const reset = useCallback(() => {
    setResult(null)
    setMessages([])
    setConversationId(undefined)
  }, [])

  return { interpret, sendMessage, messages, result, isLoading, reset, conversationId }
}
