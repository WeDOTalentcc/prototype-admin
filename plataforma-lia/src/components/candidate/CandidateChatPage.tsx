'use client'

import React, { useState, useCallback, useEffect, useRef } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import { CandidateChatHeader } from './CandidateChatHeader'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt: Date
}

interface ApplicationContext {
  vacancy_title?: string
  company_name?: string
  stage?: string
  logo_url?: string
}

interface CandidateChatPageProps {
  token: string
  vacancyId?: string
  context?: ApplicationContext
}

export function CandidateChatPage({ token, vacancyId, context }: CandidateChatPageProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Olá! Sou a LIA, assistente de recrutamento. Posso te ajudar a acompanhar seu processo seletivo. O que gostaria de saber?',
      createdAt: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = useCallback(async () => {
    const text = input.trim()
    if (!text || loading) return

    const userMsg: Message = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: text,
      createdAt: new Date(),
    }

    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)
    setError(null)

    try {
      const res = await fetch('/api/backend-proxy/candidate/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, token, vacancy_id: vacancyId }),
      })

      const data = await res.json()

      if (!res.ok) {
        if (res.status === 429) {
          setError('Você enviou muitas mensagens. Aguarde alguns minutos e tente novamente.')
        } else {
          setError('Não consegui processar sua mensagem. Tente novamente.')
        }
        return
      }

      const reply = (data?.data?.response ?? data?.response ?? 'Desculpe, não entendi. Pode repetir?') as string

      setMessages((prev) => [
        ...prev,
        { id: `a-${Date.now()}`, role: 'assistant', content: reply, createdAt: new Date() },
      ])
    } catch {
      setError('Erro de conexão. Verifique sua internet e tente novamente.')
    } finally {
      setLoading(false)
    }
  }, [input, loading, token, vacancyId])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        sendMessage()
      }
    },
    [sendMessage]
  )

  return (
    <div className="flex flex-col h-screen bg-background">
      <CandidateChatHeader
        companyName={context?.company_name}
        vacancyTitle={context?.vacancy_title}
        stage={context?.stage}
        logoUrl={context?.logo_url}
      />

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              'flex',
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            )}
          >
            <div
              className={cn(
                'max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed',
                msg.role === 'user'
                  ? 'bg-wedo-cyan text-white rounded-br-sm'
                  : 'bg-muted text-foreground rounded-bl-sm'
              )}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-2xl rounded-bl-sm px-4 py-2.5">
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            </div>
          </div>
        )}

        {error && (
          <div className="flex justify-center">
            <p className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">
              {error}
            </p>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-border bg-background px-4 py-3">
        <div className="flex items-end gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Pergunte sobre seu processo seletivo..."
            className="min-h-[44px] max-h-32 resize-none rounded-xl text-sm"
            rows={1}
            disabled={loading}
          />
          <Button
            size="icon"
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="h-11 w-11 shrink-0 rounded-xl bg-wedo-cyan hover:bg-wedo-cyan/90"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
        <p className="mt-2 text-center text-xs text-muted-foreground">
          LIA só tem acesso ao seu processo seletivo nesta empresa.
        </p>
      </div>
    </div>
  )
}
