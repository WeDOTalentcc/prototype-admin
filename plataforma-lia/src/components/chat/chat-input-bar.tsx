"use client"

import React, { useState, useRef, useCallback } from "react"
import { Send, Mic, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface ChatInputBarProps {
  onSend: (message: string) => void
  isLoading?: boolean
  placeholder?: string
  className?: string
  maxLength?: number
  showMic?: boolean
  onMicClick?: () => void
}

export function ChatInputBar({
  onSend,
  isLoading = false,
  placeholder = "Envie uma mensagem...",
  className,
  maxLength = 2000,
  showMic = true,
  onMicClick,
}: ChatInputBarProps) {
  const [message, setMessage] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = useCallback(() => {
    const trimmed = message.trim()
    if (!trimmed || isLoading) return
    onSend(trimmed)
    setMessage("")
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
    }
  }, [message, isLoading, onSend])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend]
  )

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      if (e.target.value.length <= maxLength) {
        setMessage(e.target.value)
        e.target.style.height = "auto"
        e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`
      }
    },
    [maxLength]
  )

  const canSend = message.trim().length > 0 && !isLoading

  return (
    <div
      className={cn(
        "flex items-end gap-2 px-3 py-2 rounded-xl border border-lia-border-subtle bg-lia-bg-primary",
        className
      )}
    >
      <textarea
        ref={textareaRef}
        value={message}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={isLoading}
        maxLength={maxLength}
        rows={1}
        aria-label="Mensagem para a IA"
        className={cn(
          "flex-1 bg-transparent text-base-ui",
          "text-lia-text-primary placeholder:text-lia-text-disabled",
          "focus:outline-none leading-relaxed min-w-0 resize-none max-h-[120px]"
        )}
      />

      {showMic && (
        <button
          type="button"
          onClick={onMicClick}
          className="flex-shrink-0 p-1.5 rounded-full text-lia-text-tertiary hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none mb-0.5"
          aria-label="Gravar áudio"
        >
          <Mic className="w-4 h-4" />
        </button>
      )}

      <button
        type="button"
        onClick={handleSend}
        disabled={!canSend}
        className={cn(
          "flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center transition-colors mb-0.5",
          canSend
            ? "bg-wedo-cyan text-white hover:opacity-90"
            : "bg-lia-interactive-active text-lia-text-tertiary cursor-not-allowed"
        )}
        aria-label="Enviar mensagem"
      >
        {isLoading ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
        ) : (
          <Send className="w-3.5 h-3.5" />
        )}
      </button>
    </div>
  )
}
