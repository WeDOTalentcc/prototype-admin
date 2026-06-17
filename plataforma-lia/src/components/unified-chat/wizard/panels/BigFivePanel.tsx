"use client"

import React from "react"
import { Brain } from "lucide-react"
import type { BigFiveData } from "../wizard-types"
import { FallbackBanner } from "./FallbackBanner"
import { AiDegradedModeBanner } from "./AiDegradedModeBanner"

interface Props {
  data: Record<string, unknown>
}

const TRAIT_CONFIG: Record<string, { label: string; color: string }> = {
  openness: { label: "Abertura", color: "bg-wedo-purple" },
  conscientiousness: { label: "Conscienciosidade", color: "bg-wedo-cyan" },
  extraversion: { label: "Extroversao", color: "bg-amber-500" },
  agreeableness: { label: "Amabilidade", color: "bg-green-500" },
  stability: { label: "Estabilidade", color: "bg-teal-500" },
}

/**
 * BigFivePanel — displays the Big Five personality profile extracted from the JD.
 * Shows 5 horizontal bars with scores, plus evidence quotes.
 */
export function BigFivePanel({ data }: Props) {
  const d = data as unknown as BigFiveData
  const profile = d?.bigfive_profile
  const rankings = d?.trait_rankings || []

  if (!profile) {
    return (
      <div className="p-4 text-center">
        <div className="w-5 h-5 mx-auto mb-2 border-2 border-wedo-cyan border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-lia-text-secondary">
          Extraindo perfil Big Five do JD...
        </p>
      </div>
    )
  }

  const traits = Object.entries(TRAIT_CONFIG).map(([key, cfg]) => ({
    key,
    ...cfg,
    score: (profile as unknown as Record<string, number>)[key] ?? 0,
    evidence: profile.evidences?.[key] || [],
    rank: rankings.find((r) => r.trait === key)?.rank,
  }))

  return (
    <div className="p-4 space-y-4">
      {/* Task #1070 — banner de modo degradado agregado (sessao/tenant). */}
      <AiDegradedModeBanner state={d.ai_degraded_mode ?? null} />
      {/* Task #1065 — banner de fallback determinístico (timeout do LLM
          → traços neutros 0.5). FallbackBanner usa `mx-4 mt-3` mas o
          wrapper aqui já tem `p-4`, então usamos `-mx-4 -mt-4 mb-0`
          para anular as margens herdadas e encostar no topo do card. */}
      {d?.bigfive_used_fallback && (
        <div className="-mx-4 -mt-4 [&>div]:mt-0 [&>div]:mx-0 [&>div]:rounded-none [&>div]:border-x-0 [&>div]:border-t-0">
          <FallbackBanner
            reason={d.bigfive_fallback_reason ?? "timeout"}
            onRetry={() =>
              window.dispatchEvent(
                new CustomEvent("lia:wizard-retry-stage", {
                  detail: { stage: "bigfive" },
                }),
              )
            }
          />
        </div>
      )}
      {/* Header */}
      <div className="flex items-center gap-2">
        <Brain className="w-4 h-4 text-wedo-cyan" />
        <span className="text-xs font-medium text-lia-text-secondary">
          Perfil Big Five (NEO-PI-R)
        </span>
      </div>

      {/* Trait bars */}
      <div className="space-y-3">
        {traits.map((t) => (
          <div key={t.key} className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="text-lia-text-primary font-medium">
                {t.rank != null && (
                  <span className="text-lia-text-secondary mr-1">#{t.rank}</span>
                )}
                {t.label}
              </span>
              <span className="text-lia-text-secondary">{t.score}/100</span>
            </div>
            <div className="h-2 rounded-full bg-lia-bg-tertiary overflow-hidden">
              <div
                className={`h-full rounded-full ${t.color} transition-all duration-500`}
                style={{ width: `${Math.min(100, Math.max(0, t.score))}%` }}
              />
            </div>
            {/* Evidence quotes */}
            {t.evidence.length > 0 && (
              <div className="pl-2 border-l-2 border-lia-border-subtle">
                {t.evidence.slice(0, 2).map((e, i) => (
                  // A-09 / WCAG 2.1 AA 1.4.3: was `text-[10px] text-lia-text-muted`
                  // (~9 px / ~2.85:1 contrast). Promoted to `text-xs` (12 px) +
                  // `text-lia-text-secondary` (#6B7280, ≥4.5:1 on white).
                  <p key={i} className="text-xs text-lia-text-secondary italic leading-tight">
                    "{e}"
                  </p>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Ranked summary */}
      {rankings.length > 0 && (
        <div className="rounded-md bg-lia-bg-secondary p-2.5">
          <p className="text-[11px] text-lia-text-secondary">
            Traits prioritarios para esta vaga:{" "}
            <span className="text-lia-text-primary font-medium">
              {rankings
                .sort((a, b) => a.rank - b.rank)
                .slice(0, 3)
                .map((r) => TRAIT_CONFIG[r.trait]?.label || r.trait)
                .join(", ")}
            </span>
          </p>
        </div>
      )}
    </div>
  )
}
