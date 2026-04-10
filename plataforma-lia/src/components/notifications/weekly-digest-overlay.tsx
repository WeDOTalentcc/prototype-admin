"use client"

import { useEffect, useState } from "react"
import { createPortal } from "react-dom"
import { X } from "lucide-react"
import { WeeklyDigestChatMessage } from "./weekly-digest-chat-message"
import type { WeeklyDigestData } from "./weekly-digest-notification"

interface WeeklyDigestOverlayProps {
  digest: WeeklyDigestData
  recruiterName?: string
  onDismiss: () => void
  onViewMetrics?: () => void
  onDetailRiskJobs?: () => void
}

export function WeeklyDigestOverlay({
  digest,
  recruiterName,
  onDismiss,
  onViewMetrics,
  onDetailRiskJobs,
}: WeeklyDigestOverlayProps) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    return () => setMounted(false)
  }, [])

  if (!mounted) return null

  const content = (
    <div
      className="fixed inset-0 z-modal flex items-end justify-end p-4 sm:p-6 pointer-events-none"
      aria-live="polite"
      aria-label="Resumo Semanal"
    >
      <div
        className="w-full max-w-[420px] pointer-events-auto shadow-2xl rounded-xl overflow-hidden
          animate-in slide-in-from-bottom-4 fade-in duration-300"
      >
        <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-xl overflow-hidden">
          <div className="bg-gradient-to-r from-wedo-cyan to-wedo-cyan-dark px-4 py-2.5 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center">
                <span className="text-white text-[10px] font-bold">L</span>
              </div>
              <span className="text-white font-semibold text-sm">Chat LIA</span>
              <span className="bg-white/20 text-white text-[10px] px-1.5 py-0.5 rounded-full">online</span>
            </div>
            <button
              onClick={onDismiss}
              className="text-white/70 hover:text-white transition-colors p-1 rounded"
              aria-label="Fechar resumo semanal"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="p-4 bg-lia-bg-secondary dark:bg-lia-bg-primary/50 max-h-[70vh] overflow-y-auto">
            <WeeklyDigestChatMessage
              digest={digest}
              recruiterName={recruiterName}
              onDetailRiskJobs={onDetailRiskJobs}
              onViewMetrics={onViewMetrics}
            />
          </div>
        </div>
      </div>
    </div>
  )

  return createPortal(content, document.body)
}
