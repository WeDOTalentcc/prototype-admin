"use client"

import React from "react"
import { cn } from "@/lib/utils"
import { Brain, Zap, Target } from "lucide-react"
import type { CompetencyData, ScreeningMode } from "../wizard-types"

interface Props {
  data: Record<string, unknown>
  onUpdate?: (updates: Record<string, unknown>) => void
}

/**
 * CompetencyPanel — F4+F5: seniority resolution + screening mode selector.
 * Shows seniority signals, competency tree, and compact/full mode toggle.
 */
export function CompetencyPanel({ data, onUpdate }: Props) {
  const d = data as unknown as CompetencyData
  const seniority = d.seniority || ""
  const mode = d.screening_mode
  const distribution = d.distribution
  const tree = d.competency_tree || []

  // Deduplicate skills by name
  const dedup = (items: typeof tree) => {
    const seen = new Set<string>()
    return items.filter((c) => {
      if (seen.has(c.skill)) return false
      seen.add(c.skill)
      return true
    })
  }
  const techSkills = dedup(tree.filter((c) => c.block === "technical"))
  const behavSkills = dedup(tree.filter((c) => c.block === "behavioral"))

  const handleModeSelect = (m: ScreeningMode) => {
    onUpdate?.({ screening_mode: m })
  }

  return (
    <div className="flex flex-col">
      {/* Seniority resolved */}
      <div className="px-4 py-3 border-b border-lia-border-subtle">
        <div className="flex items-center gap-2">
          <Target className="w-4 h-4 text-wedo-cyan" />
          <span className="text-sm font-semibold text-lia-text-primary font-['Open_Sans',sans-serif]">
            {d.seniority_display || seniority}
          </span>
          {d.seniority_confidence > 0 && (
            <span className="text-[10px] text-lia-text-tertiary font-['Open_Sans',sans-serif]">
              ({Math.round(d.seniority_confidence * 100)}% confianca)
            </span>
          )}
        </div>

        {/* Seniority signals */}
        {d.seniority_signals?.length > 0 && (
          <div className="mt-2 space-y-1">
            {d.seniority_signals.map((s, i) => (
              <div key={i} className="flex items-center justify-between text-xs font-['Open_Sans',sans-serif]">
                <span className="text-lia-text-secondary">{s.signal}</span>
                <span className="text-lia-text-primary">{s.value}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Screening mode selector */}
      <div className="px-4 py-3 border-b border-lia-border-subtle">
        <p className="text-xs font-medium text-lia-text-secondary font-['Open_Sans',sans-serif] mb-2">
          Modo de triagem
        </p>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => handleModeSelect("compact")}
            className={cn(
              "flex flex-col items-center gap-1 px-3 py-2.5 rounded-md border text-center transition-colors motion-reduce:transition-none",
              mode === "compact"
                ? "border-wedo-cyan bg-wedo-cyan/5 text-wedo-cyan"
                : "border-lia-border-subtle text-lia-text-secondary hover:border-lia-text-tertiary hover:bg-lia-bg-secondary",
            )}
          >
            <Zap className="w-4 h-4" />
            <span className="text-xs font-medium font-['Open_Sans',sans-serif]">Compacto</span>
            <span className="text-[10px] font-['Open_Sans',sans-serif]">7 perguntas</span>
          </button>
          <button
            onClick={() => handleModeSelect("full")}
            className={cn(
              "flex flex-col items-center gap-1 px-3 py-2.5 rounded-md border text-center transition-colors motion-reduce:transition-none",
              mode === "full"
                ? "border-wedo-cyan bg-wedo-cyan/5 text-wedo-cyan"
                : "border-lia-border-subtle text-lia-text-secondary hover:border-lia-text-tertiary hover:bg-lia-bg-secondary",
            )}
          >
            <Brain className="w-4 h-4" />
            <span className="text-xs font-medium font-['Open_Sans',sans-serif]">Completo</span>
            <span className="text-[10px] font-['Open_Sans',sans-serif]">12 perguntas</span>
          </button>
        </div>

        {/* Distribution preview */}
        {distribution && (
          <div className="mt-2 flex items-center gap-3 text-[10px] text-lia-text-tertiary font-['Open_Sans',sans-serif]">
            <span>{distribution.technical} tecnicas</span>
            <span className="w-px h-3 bg-lia-border-subtle" />
            <span>{distribution.behavioral} comportamentais</span>
          </div>
        )}
      </div>

      {/* Competency tree */}
      <div className="px-4 py-3 space-y-3">
        {techSkills.length > 0 && (
          <div>
            <p className="text-xs font-medium text-lia-text-secondary font-['Open_Sans',sans-serif] mb-1.5">
              Tecnicas ({techSkills.length})
            </p>
            <div className="flex flex-wrap gap-1.5">
              {techSkills.map((s, i) => (
                <span
                  key={i}
                  className="inline-flex px-2 py-0.5 rounded bg-lia-bg-secondary border border-lia-border-subtle text-xs text-lia-text-primary font-['Open_Sans',sans-serif]"
                >
                  {s.skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {behavSkills.length > 0 && (
          <div>
            <p className="text-xs font-medium text-lia-text-secondary font-['Open_Sans',sans-serif] mb-1.5">
              Comportamentais ({behavSkills.length})
            </p>
            <div className="space-y-1">
              {behavSkills.map((s, i) => (
                <div key={i} className="flex items-center gap-2 text-xs font-['Open_Sans',sans-serif]">
                  <span className="text-lia-text-primary">{s.skill}</span>
                  {s.trait && (
                    <span className="px-1.5 py-0.5 rounded bg-wedo-cyan/10 text-wedo-cyan text-[10px] font-medium">
                      {s.trait}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
