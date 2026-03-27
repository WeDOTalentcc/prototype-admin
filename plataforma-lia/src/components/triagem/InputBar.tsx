"use client"

import React, { useState, useRef, useCallback, useEffect } from "react"
import { cn } from "@/lib/utils"
import { Send, Volume2, VolumeX, PhoneOff } from "lucide-react"
import { AudioRecordButton } from "@/components/ui/audio-record-button"

interface InputBarProps {
  onSend: (text: string) => void
  onAudioTranscription?: (text: string) => void
  isSending?: boolean
  disabled?: boolean
  audioEnabled?: boolean
  placeholder?: string
  className?: string
  voiceMode?: boolean
  isMuted?: boolean
  onToggleMute?: () => void
  onEndConversation?: () => void
}

export function InputBar({
  onSend,
  onAudioTranscription,
  isSending = false,
  disabled = false,
  audioEnabled = true,
  placeholder = "Digite sua resposta...",
  className,
  voiceMode = false,
  isMuted = false,
  onToggleMute,
  onEndConversation,
}: InputBarProps) {
  const [text, setText] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const adjustHeight = useCallback(() => {
    const textarea = textareaRef.current
    if (!textarea) return
    textarea.style.height = "auto"
    textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`
  }, [])

  useEffect(() => {
    adjustHeight()
  }, [text, adjustHeight])

  const handleSend = useCallback(() => {
    const trimmed = text.trim()
    if (!trimmed || isSending || disabled) return
    onSend(trimmed)
    setText("")
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
    }
  }, [text, isSending, disabled, onSend])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend]
  )

  const handleTranscription = useCallback(
    (transcribedText: string) => {
      if (onAudioTranscription) {
        onAudioTranscription(transcribedText)
      } else {
        onSend(transcribedText)
      }
    },
    [onAudioTranscription, onSend]
  )

  const isDisabled = isSending || disabled

  return (
    <div
      className={cn(
        "sticky bottom-0 z-10 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-4 py-3",
        className
      )}
    >
      {voiceMode && (
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            {onToggleMute && (
              <button
                type="button"
                onClick={onToggleMute}
                aria-label={isMuted ? "Ativar áudio da LIA" : "Silenciar áudio da LIA"}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors font-['Open_Sans',sans-serif]",
                  isMuted
                    ? "bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600"
                    : "bg-wedo-cyan/10 text-wedo-cyan hover:bg-wedo-cyan/20"
                )}
              >
                {isMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
                {isMuted ? "Áudio desativado" : "Áudio ativado"}
              </button>
            )}
          </div>
          {onEndConversation && (
            <button
              type="button"
              onClick={onEndConversation}
              disabled={isDisabled}
              aria-label="Finalizar conversa"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-['Open_Sans',sans-serif]"
            >
              <PhoneOff className="w-3.5 h-3.5" />
              Finalizar Conversa
            </button>
          )}
        </div>
      )}
      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isDisabled}
          rows={1}
          aria-label="Campo de resposta"
          className="flex-1 resize-none w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:border-gray-900 dark:focus:border-gray-100 focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-100/20 focus:outline-none disabled:opacity-50 font-['Open_Sans',sans-serif]"
        />

        {audioEnabled && (
          <AudioRecordButton
            onTranscription={handleTranscription}
            disabled={isDisabled}
          />
        )}

        <button
          type="button"
          onClick={handleSend}
          disabled={isDisabled || !text.trim()}
          aria-label="Enviar mensagem"
          className="flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-md bg-gray-900 dark:bg-gray-50 text-white dark:text-gray-900 hover:bg-gray-800 dark:hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:outline-none"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
