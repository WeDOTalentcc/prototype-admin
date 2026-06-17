"use client"

import React, { useState, useRef, useCallback, useEffect } from "react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { Send, Volume2, VolumeX } from "lucide-react"
import { AudioRecordButton } from "@/components/ui/audio-record-button"

interface InputBarProps {
  onSend: (text: string) => void
  onAudioTranscription?: (text: string) => void
  isSending?: boolean
  disabled?: boolean
  audioEnabled?: boolean
  placeholder?: string
  className?: string
  autoPlayVoice?: boolean
  onToggleAutoPlayVoice?: () => void
  transcriptionUrl?: string
}

export function InputBar({
  onSend,
  onAudioTranscription,
  isSending = false,
  disabled = false,
  audioEnabled = true,
  placeholder,
  className,
  autoPlayVoice = false,
  onToggleAutoPlayVoice,
  transcriptionUrl,
}: InputBarProps) {
  const t = useTranslations("triagem.inputBar")
  const effectivePlaceholder = placeholder ?? t("placeholder")
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
 "sticky bottom-0 z-10 bg-lia-bg-primary dark:bg-lia-bg-secondary border-t border-lia-border-subtle dark:border-lia-border-subtle px-4 py-3",
        className
      )}
    >
      <div className="flex items-end gap-2">
        {onToggleAutoPlayVoice && (
          <button
            type="button"
            onClick={onToggleAutoPlayVoice}
            aria-label={autoPlayVoice ? t("autoplayOn") : t("autoplayOff")}
            title={autoPlayVoice ? t("autoplayOnTitle") : t("autoplayOffTitle")}
            className={cn(
              "flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-lg transition-colors",
              autoPlayVoice
                ? "bg-wedo-cyan/10 text-wedo-cyan-text hover:bg-wedo-cyan/20"
                : "border border-lia-border-default text-lia-text-tertiary hover:text-lia-text-secondary hover:bg-lia-bg-tertiary"
            )}
          >
            {autoPlayVoice ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
          </button>
        )}

        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={effectivePlaceholder}
          disabled={isDisabled}
          rows={1}
          aria-label={t("textareaAria")}
          className="flex-1 resize-none w-full px-3 py-2 text-sm border border-lia-border-default dark:border-lia-border-default rounded-lg bg-lia-bg-primary dark:bg-lia-bg-primary text-lia-text-primary placeholder-lia-input-placeholder dark:placeholder-lia-input-placeholder focus:border-lia-input-border-focus dark:focus:border-lia-input-border-focus focus:ring-2 focus:ring-wedo-cyan/20 focus:outline-none disabled:opacity-50"
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
          aria-label={t("sendAria")}
          className="flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-lg bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors motion-reduce:transition-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 focus:outline-none"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
