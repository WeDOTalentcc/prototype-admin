"use client"

import { useState, useEffect, useRef, useCallback } from "react"

export interface PolicyData {
  id?: string
  company_id: string
  pipeline_rules: Record<string, unknown>
  scheduling_rules: Record<string, unknown>
  communication_rules: Record<string, unknown>
  screening_rules: Record<string, unknown>
  automation_rules: Record<string, unknown>
  pipeline_templates: unknown[]
  learned_patterns: unknown[]
  setup_progress: number
  setup_completed_at: string | null
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export interface ChatResponse {
  reply: string
  current_block: string | null
  current_question: number | null
  total_questions: number
  setup_progress: number
  updated_fields: Record<string, unknown>
  block_completed: boolean
  all_completed: boolean
}

export interface ProgressData {
  company_id: string
  setup_progress: number
  setup_completed_at: string | null
  blocks_completed: Record<string, boolean>
}

const API_BASE = "/api/backend-proxy/hiring-policy"

function generateSessionId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

export function useHiringPolicies() {
  const [policy, setPolicy] = useState<PolicyData | null>(null)
  const [progress, setProgress] = useState<ProgressData | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [expandedBlocks, setExpandedBlocks] = useState<Set<string>>(new Set(['pipeline_rules']))
  const [sessionId] = useState(() => generateSessionId())
  const [editingField, setEditingField] = useState<{ block: string; field: string } | null>(null)
  const [isSavingBlock, setIsSavingBlock] = useState(false)
  const [recentlyUpdated, setRecentlyUpdated] = useState<Set<string>>(new Set())
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null)

  const chatEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = useCallback(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  const fetchPolicy = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}`)
      if (res.ok) {
        const data = await res.json()
        setPolicy(data)
      }
    } catch (err) {
    }
  }, [])

  const fetchProgress = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/progress`)
      if (res.ok) {
        const data = await res.json()
        setProgress(data)
      }
    } catch (err) {
    }
  }, [])

  useEffect(() => {
    const init = async () => {
      setIsLoading(true)
      await Promise.all([fetchPolicy(), fetchProgress()])
      setIsLoading(false)

      setMessages([{
        role: 'assistant',
        content: 'Vou ajudar você a configurar as políticas de contratação da sua empresa. Vamos começar pelo **Pipeline e Processo**. Quantas entrevistas no mínimo você exige antes de fazer uma oferta?',
        timestamp: new Date()
      }])
    }
    init()
  }, [fetchPolicy, fetchProgress])

  const handleSendMessage = async () => {
    const text = inputValue.trim()
    if (!text || isSending) return

    const userMessage: ChatMessage = {
      role: 'user',
      content: text,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsSending(true)

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          session_id: sessionId
        })
      })

      if (res.ok) {
        const data: ChatResponse = await res.json()
        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: data.reply,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, assistantMessage])

        if (data.updated_fields && Object.keys(data.updated_fields).length > 0) {
          await fetchPolicy()
          const updatedKeys = Object.keys(data.updated_fields)
          setRecentlyUpdated(new Set(updatedKeys))
          setTimeout(() => setRecentlyUpdated(new Set()), 2000)
        }
        if (data.setup_progress !== undefined) {
          setProgress(prev => prev ? { ...prev, setup_progress: data.setup_progress } : prev)
        }
        if (data.block_completed && data.current_block) {
          setProgress(prev => prev ? {
            ...prev,
            blocks_completed: { ...prev.blocks_completed, [data.current_block!]: true }
          } : prev)
        }
      } else {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: 'Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.',
          timestamp: new Date()
        }])
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Erro de conexao. Verifique sua internet e tente novamente.',
        timestamp: new Date()
      }])
    } finally {
      setIsSending(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const toggleBlock = (blockKey: string) => {
    setExpandedBlocks(prev => {
      const next = new Set(prev)
      if (next.has(blockKey)) {
        next.delete(blockKey)
      } else {
        next.add(blockKey)
      }
      return next
    })
  }

  const startEditing = (block: string, field: string) => {
    setEditingField({ block, field })
  }

  const cancelEditing = () => {
    setEditingField(null)
  }

  const saveFieldValue = async (block: string, field: string, value: unknown) => {
    setIsSavingBlock(true)
    setSaveError(null)
    try {
      let parsedValue: unknown = value
      if (field === 'allowed_hours' && typeof value === 'string') {
        const trimmed = value.trim()
        if (trimmed === '') {
          parsedValue = null
        } else {
        const m = trimmed.match(/^\s*(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\s*$/)
        if (!m) {
          throw new Error('Horario invalido. Use o formato HH:MM - HH:MM (ex.: 09:00 - 18:00).')
        }
        parsedValue = { start: m[1], end: m[2] }
        }
      }
      if (field === 'allowed_days' && typeof value === 'string') {
        parsedValue = value.split(',').map(s => s.trim()).filter(Boolean)
      }

      const res = await fetch(`${API_BASE}/block`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          block,
          data: { [field]: parsedValue }
        })
      })

      if (!res.ok) {
        let detail = 'Falha ao salvar campo.'
        try {
          const data = await res.json()
          if (data?.detail) {
            detail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
          } else if (data?.error) {
            detail = String(data.error)
          }
        } catch { /* ignore */ }
        if (res.status === 401 || res.status === 403) {
          detail = 'Sessao expirada ou sem permissao. Recarregue a pagina.'
        } else if (res.status >= 500) {
          detail = 'Backend indisponivel. Tente novamente em instantes.'
        }
        throw new Error(detail)
      }

      const updated = await res.json()
      setPolicy(updated)
      setRecentlyUpdated(new Set([field]))
      setTimeout(() => setRecentlyUpdated(new Set()), 2000)
      await fetchProgress()
      setSaveSuccess('Campo atualizado com sucesso!')
      setTimeout(() => setSaveSuccess(null), 3000)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao salvar campo.'
      setSaveError(message)
      setTimeout(() => setSaveError(null), 5000)
    } finally {
      setIsSavingBlock(false)
      setEditingField(null)
    }
  }

  const setupProgress = progress?.setup_progress ?? policy?.setup_progress ?? 0

  return {
    policy,
    progress,
    messages,
    inputValue,
    setInputValue,
    isSending,
    isLoading,
    expandedBlocks,
    chatEndRef,
    inputRef,
    setupProgress,
    handleSendMessage,
    handleKeyDown,
    toggleBlock,
    editingField,
    startEditing,
    cancelEditing,
    saveFieldValue,
    isSavingBlock,
    recentlyUpdated,
    saveError,
    saveSuccess,
  }
}
