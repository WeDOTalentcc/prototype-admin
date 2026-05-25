"use client"

import React, { useState } from "react"
import { DollarSign, Gift } from "lucide-react"
import type { SalaryData } from "../wizard-types"
import { FallbackBanner } from "./FallbackBanner"
import { AiDegradedModeBanner } from "./AiDegradedModeBanner"

interface Props {
  data: Record<string, unknown>
  onUpdate?: (updates: Record<string, unknown>) => void
}

export function SalaryPanel({ data, onUpdate }: Props) {
  const d = data as unknown as SalaryData
  const currency = d.salary_currency || "BRL"
  const fmt = (v: number | null) => v ? `${currency} ${v.toLocaleString("pt-BR")}` : "-"

  const [min, setMin] = useState(d.salary_min ?? 0)
  const [max, setMax] = useState(d.salary_max ?? 0)

  // Dynamic slider range based on data or benchmark
  const benchmarkMax = d.benchmark ? Number((d.benchmark as Record<string, unknown>).p90 || (d.benchmark as Record<string, unknown>).max || 50000) : null
  const sliderMax = Math.max(50000, benchmarkMax ?? 0, (d.salary_max ?? 0) * 1.5)

  const handleMinChange = (val: number) => {
    setMin(val)
    onUpdate?.({ salary_min: val })
  }

  const handleMaxChange = (val: number) => {
    setMax(val)
    onUpdate?.({ salary_max: val })
  }

  return (
    <div className="px-4 py-3 space-y-4">
      {/* Task #1070 — banner de modo degradado agregado (sessao/tenant). */}
      <AiDegradedModeBanner state={d.ai_degraded_mode ?? null} />
      {/* Task #1065 — banner de fallback (timeout do benchmark fetch). */}
      {d.salary_used_fallback && (
        <div className="-mx-4 -mt-3 [&>div]:mx-0 [&>div]:mt-0 [&>div]:rounded-none [&>div]:border-x-0 [&>div]:border-t-0">
          <FallbackBanner
            reason={d.salary_fallback_reason ?? "timeout"}
            message={
              d.salary_fallback_reason
                ? undefined
                : "Benchmark de mercado indisponível agora — preencha a faixa manualmente."
            }
            onRetry={() =>
              window.dispatchEvent(
                new CustomEvent("lia:wizard-retry-stage", {
                  detail: { stage: "salary" },
                }),
              )
            }
          />
        </div>
      )}
      <div>
        <div className="flex items-center gap-1.5 mb-2">
          <DollarSign className="w-4 h-4 text-wedo-cyan" />
          <span className="text-xs font-medium text-lia-text-secondary">Faixa salarial</span>
        </div>

        {/* Range display */}
        <div className="flex items-center gap-3 text-sm mb-3">
          <span className="text-lia-text-primary">{fmt(min || d.salary_min)}</span>
          <span className="text-lia-text-disabled">—</span>
          <span className="text-lia-text-primary">{fmt(max || d.salary_max)}</span>
        </div>

        {/* Range sliders */}
        <div className="space-y-3">
          <div>
            <label className="text-[10px] text-lia-text-tertiary">Minimo</label>
            <input
              type="range"
              min={0}
              max={sliderMax}
              step={500}
              value={min || d.salary_min || 0}
              onChange={(e) => handleMinChange(Number(e.target.value))}
              className="w-full h-1.5 rounded-full appearance-none bg-lia-bg-tertiary accent-wedo-cyan cursor-pointer"
            />
          </div>
          <div>
            <label className="text-[10px] text-lia-text-tertiary">Maximo</label>
            <input
              type="range"
              min={0}
              max={sliderMax}
              step={500}
              value={max || d.salary_max || 0}
              onChange={(e) => handleMaxChange(Number(e.target.value))}
              className="w-full h-1.5 rounded-full appearance-none bg-lia-bg-tertiary accent-wedo-cyan cursor-pointer"
            />
          </div>
        </div>
      </div>

      {/* Benchmark */}
      {d.benchmark && (
        <div className="p-2.5 rounded-md bg-wedo-cyan/5 border border-wedo-cyan/20">
          <p className="text-[10px] font-medium text-wedo-cyan">Benchmark de mercado</p>
          <div className="mt-1 space-y-0.5">
            {Object.entries(d.benchmark).map(([key, val]) => (
              <div key={key} className="flex items-center justify-between text-xs">
                <span className="text-lia-text-secondary capitalize">{key.replace(/_/g, " ")}</span>
                <span className="text-lia-text-primary font-medium">
                  {typeof val === "number" ? `${currency} ${val.toLocaleString("pt-BR")}` : String(val)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {d.benefits?.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 mb-1.5">
            <Gift className="w-4 h-4 text-wedo-cyan" />
            <span className="text-xs font-medium text-lia-text-secondary">Beneficios</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {d.benefits.map((b, i) => (
              <span key={i} className="px-2 py-0.5 rounded bg-lia-bg-secondary border border-lia-border-subtle text-micro text-lia-text-primary">
                {b}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
