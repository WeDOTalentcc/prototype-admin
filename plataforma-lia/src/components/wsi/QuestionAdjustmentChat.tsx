"use client"

import React, { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Send, Loader2, Brain, User, MessageCircle } from "lucide-react"
import { cn } from "@/lib/utils"

interface AdjustedQuestion {
  id?: string
  question?: string
  category?: string
  [key: string]: unknown
}

interface QuestionDiff {
  type?: 'added' | 'removed' | 'modified'
  question?: string
  [key: string]: unknown
}

interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  adjustedQuestions?: AdjustedQuestion[]
  diff?: QuestionDiff[]
}

interface QuestionAdjustmentChatProps {
  jobId: string
  blockId: string
  currentQuestions: AdjustedQuestion[]
  jobContext?: {
    title?: string
    seniority?: string
    department?: string
    skills?: string[]
  }
  onAdjustmentComplete?: (adjustedQuestions: AdjustedQuestion[], diff: QuestionDiff[], iterationCount?: number, maxIterations?: number) => void
  disabled?: boolean
  className?: string
}

export function QuestionAdjustmentChat({
  jobId,
  blockId,
  currentQuestions,
  jobContext,
  onAdjustmentComplete,
  disabled = false,
  className
}: QuestionAdjustmentChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Descreva o ajuste que deseja nas perguntas deste bloco. Por exemplo: \"Quero uma pergunta mais focada em gestão de conflitos\" ou \"Substitua a pergunta sobre liderança por algo sobre trabalho em equipe\".",
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading || disabled) return

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: input.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      const response = await fetch("/api/backend-proxy/wsi/questions/adjust", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_id: jobId,
          block_id: blockId,
          adjustment_prompt: userMessage.content,
          current_questions: currentQuestions,
          job_context: jobContext
        })
      })

      if (response.status === 429) {
        const errorData = await response.json().catch(() => ({}))
        const errorMessage: ChatMessage = {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: errorData.detail || "Limite de ajustes atingido para este bloco. Gere novas perguntas para reiniciar o contador.",
          timestamp: new Date()
        }
        setMessages(prev => [...prev, errorMessage])
        setIsLoading(false)
        return
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const errorMessage: ChatMessage = {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: errorData.detail || errorData.error || `Erro ao processar ajuste (${response.status}). Tente novamente.`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, errorMessage])
        setIsLoading(false)
        return
      }

      const data = await response.json()

      if (data.success) {
        const assistantMessage: ChatMessage = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: data.lia_message || "Perguntas ajustadas! Veja o antes/depois abaixo.",
          timestamp: new Date(),
          adjustedQuestions: data.adjusted_questions,
          diff: data.diff
        }
        setMessages(prev => [...prev, assistantMessage])

        if (onAdjustmentComplete && data.adjusted_questions) {
          onAdjustmentComplete(data.adjusted_questions, data.diff || [], data.iteration_count, data.max_iterations)
        }
      } else {
        const errorMessage: ChatMessage = {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: data.error || data.detail || "Não consegui processar o ajuste. Tente descrever de outra forma.",
          timestamp: new Date()
        }
        setMessages(prev => [...prev, errorMessage])
      }
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: "Erro de conexão. Tente novamente.",
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className={cn("flex flex-col h-full", className)}>
      <div className="flex items-center gap-1.5 mb-2">
        <MessageCircle className="h-3.5 w-3.5 text-lia-text-secondary" />
        <span className="text-xs font-semibold text-lia-text-primary">Chat de Ajuste</span>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-3 pr-1 min-h-0"
       
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
 "flex gap-2",
              msg.role === "user" ? "justify-end" : "justify-start"
            )}
          >
            {msg.role === "assistant" && (
              <div className="w-6 h-6 rounded-full flex items-center justify-center shrink-0 bg-wedo-cyan/15">
                <Brain className="h-3 w-3 text-wedo-cyan" />
              </div>
            )}
            <div
              className={cn(
 "max-w-[85%] rounded-md px-3 py-2",
                msg.role === "user"
                  ? "bg-lia-btn-primary-bg text-lia-btn-primary-text"
                  : "bg-lia-bg-secondary border border-lia-border-subtle text-lia-text-primary"
              )}
            >
              <p className="text-xs leading-relaxed whitespace-pre-wrap">
                {msg.content}
              </p>
              {msg.diff && msg.diff.length > 0 && (
                <div className="mt-2 pt-2 border-t border-lia-border-subtle/50">
                  <p className="text-micro font-medium text-lia-text-secondary">
                    {msg.diff.length} alteração(ões) feita(s) ↓
                  </p>
                </div>
              )}
            </div>
            {msg.role === "user" && (
              <div className="w-6 h-6 rounded-full bg-lia-interactive-active flex items-center justify-center shrink-0">
                <User className="h-3 w-3 text-lia-text-secondary" />
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="flex gap-2" role="status" aria-live="polite" aria-label="Carregando...">
            <div className="w-6 h-6 rounded-full flex items-center justify-center shrink-0 bg-wedo-cyan/15" role="status" aria-live="polite" aria-label="Carregando...">
              <Brain className="h-3 w-3 text-wedo-cyan" />
            </div>
            <div className="bg-lia-bg-secondary border border-lia-border-subtle rounded-xl px-3 py-2" role="status" aria-live="polite" aria-label="Carregando...">
              <div className="flex items-center gap-2" role="status" aria-live="polite" aria-label="Carregando...">
                <Loader2 className="h-3 w-3 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
                <span className="text-xs text-lia-text-secondary">Regenerando perguntas...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="mt-2 relative">
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={disabled ? "Edições bloqueadas" : "Descreva o ajuste desejado..."}
          disabled={disabled || isLoading}
          className="w-full h-16 pl-3 pr-10 py-2 text-xs border border-lia-border-subtle rounded-xl resize-none focus:outline-none focus:ring-2 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ '--focus-ring-color': 'var(--wedo-cyan-border)' } as React.CSSProperties}
        />
        <Button
          variant="ghost"
          size="sm"
          className="absolute right-1.5 bottom-1.5 h-7 w-7 p-0 rounded-md bg-lia-btn-primary-bg hover:bg-lia-interactive-hover transition-colors cursor-pointer"
          onClick={handleSend}
          disabled={!input.trim() || isLoading || disabled}
        >
          <Send className="h-3.5 w-3.5 text-white" />
        </Button>
      </div>
    </div>
  )
}

export default QuestionAdjustmentChat
