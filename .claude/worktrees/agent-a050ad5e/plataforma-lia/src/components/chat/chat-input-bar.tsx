"use client"

import React, { useState, useRef, useCallback } from "react"
import { Send, Paperclip, Mic, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface ChatInputBarProps {
  onSend: (message: string) => void
  isLoading?: boolean
  placeholder?: string
  className?: string
}

export function ChatInputBar({
  onSend,
  isLoading = false,
  placeholder = "Digite sua mensagem para a LIA...",
  className,
}: ChatInputBarProps) {
  const [message, setMessage] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const adjustHeight = useCallback(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = "auto"
      textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`
    }
  }, [])

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
      setMessage(e.target.value)
      adjustHeight()
    },
    [adjustHeight]
  )

  const canSend = message.trim().length > 0 && !isLoading

  return (
    <div
      className={cn(
        "flex items-end gap-2 rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-2",
        className
      )}
    >
      <button
        type="button"
        className="flex-shrink-0 p-2 rounded-md text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors focus-visible:ring-2 focus-visible:ring-gray-400"
        aria-label="Anexar arquivo"
      >
        <Paperclip className="w-4 h-4" />
      </button>

      <textarea
        ref={textareaRef}
        value={message}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        rows={1}
        className={cn(
          "flex-1 resize-none bg-transparent text-[13px] font-['Open_Sans',sans-serif]",
          "text-gray-900 dark:text-gray-50 placeholder:text-gray-400 dark:placeholder:text-gray-500",
          "focus:outline-none py-2 px-1 max-h-[160px] leading-relaxed"
        )}
        disabled={isLoading}
      />

      <button
        type="button"
        className="flex-shrink-0 p-2 rounded-md text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors focus-visible:ring-2 focus-visible:ring-gray-400"
        aria-label="Gravar áudio"
      >
        <Mic className="w-4 h-4" />
      </button>

      <button
        type="button"
        onClick={handleSend}
        disabled={!canSend}
        className={cn(
          "flex-shrink-0 p-2 rounded-md transition-colors focus-visible:ring-2 focus-visible:ring-gray-400",
          canSend
            ? "bg-gray-900 dark:bg-gray-50 text-white dark:text-gray-900 hover:bg-gray-800 dark:hover:bg-gray-200"
            : "bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed"
        )}
        aria-label="Enviar mensagem"
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Send className="w-4 h-4" />
        )}
      </button>
    </div>
  )
}
