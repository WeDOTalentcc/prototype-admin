"use client"

import React, { useState, useEffect } from "react"
import { X } from "lucide-react"

/**
 * FirstUseTooltips — shows feature hints once per user.
 *
 * Appears on first interaction with specific features:
 * - @mention: "Use @ para mencionar vagas ou candidatos"
 * - /commands: "Use / para acessar comandos rapidos"
 * - file upload: "Arraste um PDF para o chat"
 * - voice: "Clique no microfone para ditar"
 *
 * Each tooltip shown ONCE per user (localStorage).
 */

export type TooltipId = "mention" | "commands" | "file_upload" | "voice"

interface TooltipConfig {
  id: TooltipId
  text: string
  trigger: string // description of when to show
}

const TOOLTIPS: TooltipConfig[] = [
  { id: "mention", text: "Use @ para mencionar vagas ou candidatos no chat", trigger: "first_message" },
  { id: "commands", text: "Use / para acessar comandos rapidos como /criar vaga", trigger: "first_message" },
  { id: "file_upload", text: "Arraste um PDF de curriculo ou JD direto no chat", trigger: "first_file_area_hover" },
  { id: "voice", text: "Clique no microfone para ditar sua mensagem", trigger: "first_voice_area_hover" },
]

const STORAGE_KEY = "lia-first-use-tooltips"

function getSeenTooltips(): Set<string> {
  if (typeof window === "undefined") return new Set()
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? new Set(JSON.parse(stored)) : new Set()
  } catch {
    return new Set()
  }
}

function markTooltipSeen(id: string): void {
  if (typeof window === "undefined") return
  try {
    const seen = getSeenTooltips()
    seen.add(id)
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...seen]))
  } catch { /* ignore */ }
}

interface Props {
  /** Which tooltip to potentially show */
  tooltipId: TooltipId
  /** Only show after user has sent at least 1 message */
  messageCount: number
  /** Position relative to trigger element */
  position?: "above" | "below"
  children: React.ReactNode
}

export function FirstUseTooltip({ tooltipId, messageCount, position = "above", children }: Props) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    // Show tooltip after first message, if not yet seen
    if (messageCount >= 1) {
      const seen = getSeenTooltips()
      if (!seen.has(tooltipId)) {
        // Small delay so it doesn't flash immediately
        const timer = setTimeout(() => setVisible(true), 2000)
        return () => clearTimeout(timer)
      }
    }
  }, [messageCount, tooltipId])

  const handleDismiss = () => {
    markTooltipSeen(tooltipId)
    setVisible(false)
  }

  // Auto-dismiss after 8 seconds
  useEffect(() => {
    if (visible) {
      const timer = setTimeout(handleDismiss, 8000)
      return () => clearTimeout(timer)
    }
  }, [visible])

  return (
    <div className="relative inline-flex">
      {children}
      {visible && (
        <div
          className={`absolute z-50 ${
            position === "above" ? "bottom-full mb-2" : "top-full mt-2"
          } left-1/2 -translate-x-1/2 w-56`}
        >
          <div className="flex items-start gap-2 px-3 py-2 rounded-md bg-lia-bg-elevated border border-lia-border-subtle shadow-lg">
            <p className="flex-1 text-[11px] text-lia-text-primary leading-relaxed">
              {TOOLTIPS.find((t) => t.id === tooltipId)?.text}
            </p>
            <button
              onClick={handleDismiss}
              className="p-0.5 rounded text-lia-text-disabled hover:text-lia-text-secondary flex-shrink-0"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
          {/* Arrow */}
          <div
            className={`absolute left-1/2 -translate-x-1/2 w-2 h-2 bg-lia-bg-elevated border border-lia-border-subtle rotate-45 ${
              position === "above" ? "-bottom-1 border-t-0 border-l-0" : "-top-1 border-b-0 border-r-0"
            }`}
          />
        </div>
      )}
    </div>
  )
}
