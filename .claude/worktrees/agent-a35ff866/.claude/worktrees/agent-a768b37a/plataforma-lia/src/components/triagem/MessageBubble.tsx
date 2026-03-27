"use client"

import React, { useState } from "react"
import { cn } from "@/lib/utils"
import { LIAIcon } from "@/components/ui/lia-icon"
import { AudioPlayer } from "@/components/ui/audio-player"
import type { TriagemMessage } from "@/components/triagem/types"

interface MessageBubbleProps {
  message: TriagemMessage
  candidateName?: string
  className?: string
  autoPlayAudio?: boolean
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

function formatTimestamp(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
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

function parseSimpleMarkdown(text: string): string {
  const escaped = escapeHtml(text)
  return escaped
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/\n/g, "<br />")
}

export function MessageBubble({ message, candidateName = "Candidato", className, autoPlayAudio = false }: MessageBubbleProps) {
  const isLia = message.role === "lia"
  const [isAudioPlaying, setIsAudioPlaying] = useState(false)

  return (
    <div
      className={cn(
        "flex gap-3 animate-in fade-in slide-in-from-bottom-2 duration-300",
        isLia ? "justify-start" : "justify-end",
        className
      )}
      aria-label={isLia ? "Mensagem da LIA" : "Sua mensagem"}
    >
      {isLia && (
        <div className="flex-shrink-0 mt-1">
          <LIAIcon
            size="sm"
            className="bg-[#60BED1]/10"
            speaking={isAudioPlaying}
          />
        </div>
      )}

      <div className="flex flex-col gap-1 max-w-[80%]">
        <div
          className={cn(
            "px-4 py-3 text-sm font-['Open_Sans',sans-serif] leading-relaxed rounded-md",
            isLia
              ? "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100"
              : "bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900"
          )}
          dangerouslySetInnerHTML={{ __html: parseSimpleMarkdown(message.content) }}
        />
        {isLia && message.audioUrl && (
          <AudioPlayer
            src={message.audioUrl}
            className="mt-2"
            autoPlay={autoPlayAudio}
            onPlay={() => setIsAudioPlaying(true)}
            onPause={() => setIsAudioPlaying(false)}
            onEnded={() => setIsAudioPlaying(false)}
          />
        )}
        <span
          className={cn(
            "text-[10px] font-['Inter',sans-serif] text-gray-400 dark:text-gray-500",
            isLia ? "text-left" : "text-right"
          )}
        >
          {formatTimestamp(message.timestamp)}
        </span>
      </div>

      {!isLia && (
        <div className="flex-shrink-0 mt-1">
          <div
            className="w-8 h-8 rounded-md bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-xs font-semibold text-gray-600 dark:text-gray-300 font-['Inter',sans-serif]"
            aria-hidden="true"
          >
            {getInitials(candidateName)}
          </div>
        </div>
      )}
    </div>
  )
}
