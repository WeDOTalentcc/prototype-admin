"use client"

/**
 * OnboardingProgressBar — P2-2 Sprint B.3.
 *
 * ProgressBar real-time pra setup completude da empresa.
 * Atualiza automaticamente quando:
 *   1. settings UI muda (via lia:settings-updated event)
 *   2. chat LIA persiste novo campo (mesmo event via Sprint 3 G9 wire)
 *
 * Variants:
 *   - "compact" — barra fina + % inline (header banner, sidebar)
 *   - "full" — barra grossa + milestones (25/50/75) + label completa
 *
 * Audit ref: ~/Documents/wedotalent_audit_2026-05-26/P2-2_ONBOARDING_CONVERSACIONAL_ADR.md Sprint B.3
 */

import { CheckCircle2 } from "lucide-react"
import { useEffect, useState, useCallback } from "react"

export type ProgressVariant = "compact" | "full"

interface Props {
  variant?: ProgressVariant
  initialProgress?: number  // se já temos value, evita primeiro fetch
  showLabel?: boolean
  className?: string
}

const MILESTONES = [25, 50, 75, 100]

async function fetchProgress(): Promise<number> {
  try {
    const res = await fetch("/api/backend-proxy/settings/progress/", {
      credentials: "include",
    })
    if (!res.ok) {
      console.warn(`[OnboardingProgressBar] HTTP ${res.status}`)
      return 0
    }
    const data = await res.json()
    const overall = data.overall ?? data.setup_progress ?? 0
    return Math.max(0, Math.min(100, Number(overall)))
  } catch (err) {
    console.warn("[OnboardingProgressBar] fetch failed", err)
    return 0
  }
}

export function OnboardingProgressBar({
  variant = "compact",
  initialProgress,
  showLabel = true,
  className = "",
}: Props) {
  const [progress, setProgress] = useState<number>(initialProgress ?? 0)
  const [loading, setLoading] = useState<boolean>(initialProgress === undefined)

  const refresh = useCallback(async () => {
    setLoading(true)
    const value = await fetchProgress()
    setProgress(value)
    setLoading(false)
  }, [])

  // Initial fetch
  useEffect(() => {
    if (initialProgress === undefined) {
      refresh()
    }
  }, [initialProgress, refresh])

  // Real-time updates via lia:settings-updated event
  useEffect(() => {
    if (typeof window === "undefined") return
    const handler = () => {
      // Re-fetch quando settings mudam
      refresh()
    }
    window.addEventListener("lia:settings-updated", handler)
    return () => window.removeEventListener("lia:settings-updated", handler)
  }, [refresh])

  const isComplete = progress >= 100

  if (variant === "compact") {
    return (
      <div
        data-testid="onboarding-progress-compact"
        role="progressbar"
        aria-valuenow={progress}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Configuração ${progress}% completa`}
        className={`flex items-center gap-2 ${className}`}
      >
        <div className="flex-1 h-1.5 bg-lia-bg-secondary rounded-full overflow-hidden">
          <div
            className={`h-full transition-[width] duration-500 motion-reduce:transition-none ${
              isComplete ? "bg-status-success" : "bg-wedo-cyan"
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
        {showLabel && (
          <span className="text-xs font-medium text-lia-text-secondary tabular-nums">
            {progress}%
          </span>
        )}
      </div>
    )
  }

  // variant=full
  return (
    <div
      data-testid="onboarding-progress-full"
      role="progressbar"
      aria-valuenow={progress}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`Configuração ${progress}% completa`}
      className={`space-y-2 ${className}`}
    >
      {showLabel && (
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-lia-text-primary">
            Configuração da empresa
          </span>
          <span className="text-sm font-semibold text-lia-text-secondary tabular-nums">
            {progress}%
          </span>
        </div>
      )}
      <div className="relative h-2 bg-lia-bg-secondary rounded-full overflow-hidden">
        <div
          className={`h-full transition-[width] duration-500 motion-reduce:transition-none ${
            isComplete ? "bg-status-success" : "bg-wedo-cyan"
          }`}
          style={{ width: `${progress}%` }}
        />
        {/* Milestone markers */}
        {MILESTONES.slice(0, -1).map((m) => (
          <div
            key={m}
            data-testid={`milestone-${m}`}
            className="absolute top-0 bottom-0 w-px bg-lia-bg-primary opacity-50"
            style={{ left: `${m}%` }}
            aria-hidden="true"
          />
        ))}
      </div>
      {showLabel && (
        <div className="flex justify-between text-[10px] text-lia-text-secondary">
          {MILESTONES.map((m) => (
            <span key={m} className={progress >= m ? "text-wedo-cyan-text font-medium" : ""}>
              {m === 100 && progress >= 100 ? (
                <CheckCircle2 className="w-3 h-3 inline" aria-hidden="true" />
              ) : (
                `${m}%`
              )}
            </span>
          ))}
        </div>
      )}
      {isComplete && (
        <p className="text-xs text-status-success font-medium" data-testid="complete-message">
          ✓ Configuração completa!
        </p>
      )}
    </div>
  )
}
