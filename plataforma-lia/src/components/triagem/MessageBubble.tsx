"use client"

import React, { useState, useCallback, useRef, useEffect, memo } from "react"
import { useLocale, useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { LIAIcon } from "@/components/ui/lia-icon"
import { AudioPlayer } from "@/components/ui/audio-player"
import { Volume2, Loader2 } from "lucide-react"
import type { TriagemMessage } from "@/components/triagem/types"
import { sanitizeHtml } from "@/lib/sanitize"

interface MessageBubbleProps {
  message: TriagemMessage
  candidateName?: string
  className?: string
  autoPlayAudio?: boolean
  ttsToken?: string
}

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((w) => w[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase()
}

function formatTimestamp(iso: string, locale: string): string {
  try {
    const d = new Date(iso)
    const intlLocale = locale === "en" ? "en-US" : "pt-BR"
    return d.toLocaleTimeString(intlLocale, { hour: "2-digit", minute: "2-digit" })
  } catch {
    return ""
  }
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;")
}

function cleanThoughtTags(text: string): string {
  const hadThought = /<thought>/i.test(text)
  let cleaned = text.replace(/<thought>[\s\S]*?<\/thought>/gi, '')
  cleaned = cleaned.replace(/<thought>[\s\S]*/gi, '')
  cleaned = cleaned.replace(/^\s*[\n\r]+/, '').replace(/[\n\r]+\s*$/, '')
  if (hadThought) return cleaned
  return cleaned || text
}

function parseSimpleMarkdown(text: string): string {
  const escaped = escapeHtml(text)
  return escaped
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/\n/g, "<br />")
}

function base64ToAudioUrl(base64Data: string): string {
  const binaryStr = atob(base64Data)
  const bytes = new Uint8Array(binaryStr.length)
  for (let i = 0; i < binaryStr.length; i++) {
    bytes[i] = binaryStr.charCodeAt(i)
  }
  const blob = new Blob([bytes], { type: "audio/mp3" })
  return URL.createObjectURL(blob)
}

const MessageBubble = memo(function MessageBubble({
  message,
  candidateName = "Candidato",
  className,
  autoPlayAudio = false,
  ttsToken,
}: MessageBubbleProps) {
  const locale = useLocale()
  const t = useTranslations("triagem.messageBubble")
  const liaMsgAria = t("liaMessageAria")
  const myMsgAria = t("myMessageAria")
  const playAria = t("playAria")
  const pauseAria = t("pauseAria")
  const isLia = message.role === "lia"
  const [isAudioPlaying, setIsAudioPlaying] = useState(false)
  const [isTtsLoading, setIsTtsLoading] = useState(false)
  const [ttsFailed, setTtsFailed] = useState(false)
  const [ttsAudioUrl, setTtsAudioUrl] = useState<string | null>(null)
  const ttsAudioRef = useRef<HTMLAudioElement | null>(null)
  const prevBlobUrlRef = useRef<string | null>(null)

  const effectiveAudioUrl = message.audioUrl || ttsAudioUrl

  useEffect(() => {
    if (prevBlobUrlRef.current && prevBlobUrlRef.current !== ttsAudioUrl) {
      URL.revokeObjectURL(prevBlobUrlRef.current)
    }
    prevBlobUrlRef.current = ttsAudioUrl
  }, [ttsAudioUrl])

  useEffect(() => {
    return () => {
      if (ttsAudioRef.current) {
        ttsAudioRef.current.pause()
        ttsAudioRef.current.src = ""
        ttsAudioRef.current = null
      }
      if (prevBlobUrlRef.current) {
        URL.revokeObjectURL(prevBlobUrlRef.current)
      }
    }
  }, [])

  const autoPlayTriggeredRef = useRef(false)

  const playAudioFromUrl = useCallback((url: string) => {
    if (ttsAudioRef.current) {
      ttsAudioRef.current.pause()
      ttsAudioRef.current.src = ""
    }
    const audio = new Audio(url)
    ttsAudioRef.current = audio
    audio.addEventListener("play", () => setIsAudioPlaying(true))
    audio.addEventListener("pause", () => setIsAudioPlaying(false))
    audio.addEventListener("ended", () => setIsAudioPlaying(false))
    audio.play().catch(() => {})
  }, [])

  const fetchAndPlayTts = useCallback(async () => {
    if (!ttsToken) return
    setIsTtsLoading(true)
    try {
      const response = await fetch(`/api/backend-proxy/triagem/${ttsToken}/tts/${message.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      })
      if (!response.ok) {
        setTtsFailed(true)
        setTimeout(() => setTtsFailed(false), 2000)
        return
      }
      const data = await response.json()
      if (data.audio_base64) {
        const url = base64ToAudioUrl(data.audio_base64)
        setTtsAudioUrl(url)
        playAudioFromUrl(url)
      }
    } catch {
      setTtsFailed(true)
      setTimeout(() => setTtsFailed(false), 2000)
    } finally {
      setIsTtsLoading(false)
    }
  }, [ttsToken, message.id, playAudioFromUrl])

  useEffect(() => {
    if (!autoPlayAudio || !isLia) return
    if (autoPlayTriggeredRef.current) return

    const msgAge = Date.now() - new Date(message.timestamp).getTime()
    if (msgAge > 15000) return

    if (effectiveAudioUrl) {
      autoPlayTriggeredRef.current = true
      playAudioFromUrl(effectiveAudioUrl)
      return
    }

    if (ttsToken && !isTtsLoading) {
      autoPlayTriggeredRef.current = true
      fetchAndPlayTts()
    }
  }, [autoPlayAudio, effectiveAudioUrl, isLia, ttsToken, isTtsLoading, fetchAndPlayTts, playAudioFromUrl, message.timestamp])

  const handleTtsPlay = useCallback(async () => {
    if (isTtsLoading) return

    if (isAudioPlaying && ttsAudioRef.current) {
      ttsAudioRef.current.pause()
      setIsAudioPlaying(false)
      return
    }

    if (effectiveAudioUrl) {
      playAudioFromUrl(effectiveAudioUrl)
      return
    }

    await fetchAndPlayTts()
  }, [isTtsLoading, isAudioPlaying, effectiveAudioUrl, playAudioFromUrl, fetchAndPlayTts])

  return (
    <div
      className={cn(
        "flex gap-2.5 animate-in fade-in slide-in-from-bottom-2 duration-300",
        isLia ? "justify-start" : "justify-end",
        className
      )}
      aria-label={isLia ? liaMsgAria : myMsgAria}
    >
      {isLia && (
        <div className="flex-shrink-0 mt-0.5">
          <LIAIcon
            size="sm"
            className="bg-wedo-cyan/10"
            speaking={isAudioPlaying}
          />
        </div>
      )}

      <div className={cn("flex flex-col gap-1 max-w-[80%]", isLia ? "items-start" : "items-end")}>
        {isLia && (
          <div className="flex items-center gap-1.5 px-1">
            <span className="text-xs font-bold text-lia-text-primary font-['Inter',sans-serif]">LIA</span>
            <span className="text-xs text-lia-text-muted font-['Inter',sans-serif] tabular-nums">
              {formatTimestamp(message.timestamp, locale)}
            </span>
          </div>
        )}
        <div className="flex items-end gap-1.5">
          <div
            className={cn(
              "px-3.5 py-2.5 text-sm leading-relaxed",
              isLia
                ? "bg-wedo-cyan/[0.04] text-lia-text-primary rounded-[14px] rounded-bl-[4px]"
                : "bg-lia-bg-tertiary text-lia-text-secondary rounded-[14px] rounded-br-[4px]"
            )}
            dangerouslySetInnerHTML={{ __html: sanitizeHtml(parseSimpleMarkdown(cleanThoughtTags(message.content))) }}
          />
          {isLia && ttsToken && (
            <button
              type="button"
              onClick={handleTtsPlay}
              disabled={isTtsLoading}
              aria-label={isAudioPlaying ? pauseAria : playAria}
              className={cn(
                "flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-full transition-colors",
                ttsFailed
                  ? "text-status-error"
                  : isAudioPlaying
                    ? "bg-wedo-cyan/20 text-wedo-cyan-text"
                    : "bg-transparent text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-bg-tertiary",
                isTtsLoading && "cursor-wait"
              )}
            >
              {isTtsLoading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Volume2 className="w-3.5 h-3.5" />
              )}
            </button>
          )}
        </div>
        {isLia && message.audioUrl && !ttsToken && (
          <AudioPlayer
            src={message.audioUrl}
            className="mt-2"
            autoPlay={autoPlayAudio}
            onPlay={() => setIsAudioPlaying(true)}
            onPause={() => setIsAudioPlaying(false)}
            onEnded={() => setIsAudioPlaying(false)}
          />
        )}
        {!isLia && (
          <span className="text-xs text-lia-text-muted font-['Inter',sans-serif] tabular-nums px-1">
            {formatTimestamp(message.timestamp, locale)}
          </span>
        )}
      </div>

      {!isLia && (
        <div className="flex-shrink-0 mt-0.5">
          <div
            className="w-7 h-7 rounded-full bg-lia-interactive-active flex items-center justify-center text-xs font-semibold text-lia-text-tertiary font-['Inter',sans-serif]"
            aria-hidden="true"
          >
            {getInitials(candidateName)}
          </div>
        </div>
      )}
    </div>
  )
})
MessageBubble.displayName = "MessageBubble"

export { MessageBubble }
