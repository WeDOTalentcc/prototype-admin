"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Brain, X, ArrowRight } from "lucide-react"
import { textStyles } from "@/lib/design-tokens"

const DISMISS_KEY = "lia.setup-banner.dismissed-at"
const COMPLETE_THRESHOLD = 80

interface ProgressPayload {
  overall?: number
  sections?: Record<string, number>
}

export function SetupProgressBanner() {
  const [progress, setProgress] = useState<number | null>(null)
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    if (typeof window === "undefined") return
    const ts = window.localStorage.getItem(DISMISS_KEY)
    if (ts) {
      const parsed = Number(ts)
      if (!Number.isNaN(parsed) && Date.now() - parsed < 24 * 60 * 60 * 1000) {
        setDismissed(true)
      }
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const res = await fetch("/api/backend-proxy/settings/progress/")
        if (!res.ok) return
        const data: ProgressPayload = await res.json()
        if (!cancelled && typeof data.overall === "number") {
          setProgress(data.overall)
        }
      } catch {
        // silent — banner just won't show
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [])

  if (dismissed) return null
  if (progress === null) return null
  if (progress >= COMPLETE_THRESHOLD) return null

  const remaining = Math.max(0, COMPLETE_THRESHOLD - progress)

  return (
    <div
      role="status"
      aria-live="polite"
      data-testid="setup-progress-banner"
      className="
        relative flex items-center gap-3 px-4 py-3
        rounded-xl border border-lia-border-subtle
        bg-lia-bg-secondary dark:bg-lia-bg-elevated
        text-lia-text-primary
      "
    >
      <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-lia-bg-tertiary dark:bg-lia-bg-secondary flex-shrink-0">
        <Brain className="w-4 h-4 text-wedo-cyan" aria-hidden />
      </div>
      <div className="flex-1 min-w-0">
        <p className={`${textStyles.body} font-medium`}>
          Sua configuração está {progress}% completa
        </p>
        <p className={`${textStyles.description} mt-0.5`}>
          Faltam ~{remaining}% para a LIA personalizar suas vagas. Quer continuar agora?
        </p>
        <div className="w-full bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-1 mt-2 overflow-hidden">
          <div
            className="h-1 rounded-full bg-lia-btn-primary-bg transition-[width] duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
      <Link
        href="/onboarding"
        className="
          inline-flex items-center gap-1 text-sm font-medium
          px-3 py-1.5 rounded-lg
          bg-lia-btn-primary-bg text-white
          hover:opacity-90 transition-colors motion-reduce:transition-none
          flex-shrink-0
        "
      >
        Continuar
        <ArrowRight className="w-3.5 h-3.5" aria-hidden />
      </Link>
      <button
        type="button"
        onClick={() => {
          if (typeof window !== "undefined") {
            window.localStorage.setItem(DISMISS_KEY, String(Date.now()))
          }
          setDismissed(true)
        }}
        aria-label="Dispensar por 24h"
        className="p-1 rounded hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none flex-shrink-0"
      >
        <X className="w-4 h-4 text-lia-text-secondary" aria-hidden />
      </button>
    </div>
  )
}
