"use client"

import React from "react"
import { ClipboardCheck, Settings } from "lucide-react"
import type { ReviewData } from "../wizard-types"

interface Props {
  data: Record<string, unknown>
  onUpdate?: (updates: Record<string, unknown>) => void
}

export function ReviewPanel({ data, onUpdate }: Props) {
  const d = data as unknown as ReviewData
  const defaultsApplied = d.defaults_applied || []

  const handleApplyDefaults = () => {
    window.dispatchEvent(new CustomEvent("lia:prefill-message", {
      detail: { message: "Aplicar defaults da empresa nesta vaga" },
    }))
  }

  return (
    <div className="px-4 py-3 space-y-3">
      <div className="flex items-center gap-2">
        <ClipboardCheck className="w-4 h-4 text-wedo-cyan" />
        <span className="text-sm font-semibold text-lia-text-primary">
          Revisao da vaga
        </span>
      </div>

      {defaultsApplied.length > 0 && (
        <div className="text-[10px] text-lia-text-tertiary">
          Defaults aplicados: {defaultsApplied.join(", ")}
        </div>
      )}

      <button
        onClick={handleApplyDefaults}
        className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl border border-lia-border-subtle text-xs font-medium text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors"
      >
        <Settings className="w-3.5 h-3.5" />
        Aplicar defaults da empresa
      </button>
    </div>
  )
}
