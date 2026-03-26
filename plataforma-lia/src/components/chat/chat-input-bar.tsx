"use client"

import React, { useState, useRef, useCallback } from "react"
import { Send, Brain, Mic, Loader2 } from "lucide-react"
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
  placeholder = "Envie mensagem para a LIA...",
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
        "flex items-end gap-2 rounded-[24px] border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2",
        className
      )}
    >
      <div className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center mb-0.5">
        <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
      </div>

      <textarea
        ref={textareaRef}
        value={message}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={isLoading}
        maxLength={maxLength}
        rows={1}
        aria-label="Mensagem para a LIA"
        className={cn(
          "flex-1 bg-transparent text-[13px] font-['Open_Sans',sans-serif]",
          "text-gray-900 dark:text-gray-50 placeholder:text-gray-400 dark:placeholder:text-gray-500",
          "focus:outline-none leading-relaxed min-w-0 resize-none"
        )}
        style={{ maxHeight: "120px" }}
      />

      {showMic && (
        <button
          type="button"
          onClick={onMicClick}
          className="flex-shrink-0 p-1.5 rounded-full text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors mb-0.5"
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
            ? "bg-chat-cyan text-white hover:opacity-90"
            : "bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed"
        )}
        aria-label="Enviar mensagem"
      >
        {isLoading ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : (
          <Send className="w-3.5 h-3.5" />
        )}
      </button>
    </div>
  )
}
