"use client"

import React, { useEffect, useState } from "react"
import Link from "next/link"
import { ArrowRight, Brain, X } from "lucide-react"
import { getReadinessOverview, type ReadinessOverview } from "@/services/lia-api/readiness-api"

const DISMISS_KEY = "lia.readiness.cta.dismissed_at"
const DISMISS_TTL_MS = 1000 * 60 * 60 * 24 * 7 // 7 days

/**
 * Banner CTA shown on the Vagas page when the recruiter has imported jobs
 * that still need preparation (Task #429).
 *
 * - Self-fetches the readiness overview (no prop drilling required).
 * - Hides itself silently if the API errors or there's nothing to do.
 * - Recruiter can dismiss it for 7 days.
 */
export function ReadinessHubCTA({ href }: { href: string }) {
  const [overview, setOverview] = useState<ReadinessOverview | null>(null)
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    try {
      const at = window.localStorage.getItem(DISMISS_KEY)
      if (at && Date.now() - Number(at) < DISMISS_TTL_MS) {
        setDismissed(true)
        return
      }
    } catch { /* SSR or quota — ignore */ }
    let cancelled = false
    getReadinessOverview()
      .then((o) => { if (!cancelled) setOverview(o) })
      .catch(() => { /* silent */ })
    return () => { cancelled = true }
  }, [])

  const needsAction = (overview?.action_required ?? 0) + (overview?.queued_actions ?? 0)
  if (dismissed || !overview || needsAction === 0) return null

  return (
    <div className="flex items-center justify-between gap-3 px-3 py-2 mb-2 rounded-lg bg-gradient-to-r from-wedo-cyan/10 via-violet-500/5 to-transparent border border-wedo-cyan/30">
      <div className="flex items-center gap-2 min-w-0">
        <Brain className="w-4 h-4 text-wedo-cyan shrink-0" />
        <span className="text-xs text-lia-text-primary truncate">
          <strong>{overview.action_required}</strong> vaga(s) aguardando você no Hub de Prontidão
          {overview.queued_actions > 0 && (
            <span className="text-lia-text-secondary"> · {overview.queued_actions} ações automáticas pendentes</span>
          )}
        </span>
      </div>
      <div className="flex items-center gap-1 shrink-0">
        <Link
          href={href}
          prefetch={false}
          className="inline-flex items-center gap-1 text-xs font-medium text-wedo-cyan hover:underline px-2 py-1"
        >
          Abrir Hub <ArrowRight className="w-3.5 h-3.5" />
        </Link>
        <button
          type="button"
          aria-label="Dispensar"
          className="p-1 text-lia-text-tertiary hover:text-lia-text-secondary"
          onClick={() => {
            try { window.localStorage.setItem(DISMISS_KEY, String(Date.now())) } catch {}
            setDismissed(true)
          }}
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  )
}
