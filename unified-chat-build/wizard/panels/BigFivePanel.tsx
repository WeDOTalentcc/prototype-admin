"use client"

import React from "react"
import { Brain } from "lucide-react"
import type { BigFiveData } from "../wizard-types"

interface Props {
  data: Record<string, unknown>
}

const TRAIT_CONFIG: Record<string, { label: string; color: string }> = {
  openness: { label: "Abertura", color: "bg-purple-500" },
  conscientiousness: { label: "Conscienciosidade", color: "bg-blue-500" },
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
        <p className="text-sm text-lia-text-secondary font-['Open_Sans',sans-serif]">
          Extraindo perfil Big Five do JD...
        </p>
      </div>
    )
  }

  const traits = Object.entries(TRAIT_CONFIG).map(([key, cfg]) => ({
    key,
    ...cfg,
    score: (profile as Record<string, number>)[key] ?? 0,
    evidence: profile.evidences?.[key] || [],
    rank: rankings.find((r) => r.trait === key)?.rank,
  }))

  return (
    <div className="p-4 space-y-4 font-['Open_Sans',sans-serif]">
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
                  <span className="text-wedo-cyan mr-1">#{t.rank}</span>
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
                  <p key={i} className="text-[10px] text-lia-text-disabled italic leading-tight">
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
