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
  transcriptionUrl?: string
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
  transcriptionUrl,
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
 "sticky bottom-0 z-10 bg-white dark:bg-lia-bg-secondary border-t border-lia-border-subtle dark:border-lia-border-subtle px-4 py-3",
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
 "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors font-['Open_Sans',sans-serif]",
                  isMuted
                    ? "bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-secondary dark:text-lia-text-secondary hover:bg-lia-border-default dark:hover:bg-lia-border-medium"
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
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-status-error/10 dark:bg-status-error/20 text-status-error dark:text-status-error hover:bg-status-error/15 dark:hover:bg-status-error/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors motion-reduce:transition-none font-['Open_Sans',sans-serif]"
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
          className="flex-1 resize-none w-full px-3 py-2 text-sm border border-lia-border-default dark:border-lia-border-default rounded-lg bg-white dark:bg-lia-bg-primary text-lia-text-primary dark:text-lia-text-primary placeholder-lia-input-placeholder dark:placeholder-lia-input-placeholder focus:border-lia-input-border-focus dark:focus:border-lia-input-border-focus focus:ring-2 focus:ring-wedo-cyan/20 focus:outline-none disabled:opacity-50 font-['Open_Sans',sans-serif]"
        />

        {audioEnabled && (
          <AudioRecordButton
            onTranscription={handleTranscription}
            disabled={isDisabled}
            transcriptionUrl={transcriptionUrl}
          />
        )}

        <button
          type="button"
          onClick={handleSend}
          disabled={isDisabled || !text.trim()}
          aria-label="Enviar mensagem"
          className="flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-lg bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors motion-reduce:transition-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 focus:outline-none"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
