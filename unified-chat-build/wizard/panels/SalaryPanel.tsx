"use client"

import React, { useState } from "react"
import { DollarSign, Gift } from "lucide-react"
import type { SalaryData } from "../wizard-types"

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
      <div>
        <div className="flex items-center gap-1.5 mb-2">
          <DollarSign className="w-4 h-4 text-wedo-cyan" />
          <span className="text-xs font-medium text-lia-text-secondary font-['Open_Sans',sans-serif]">Faixa salarial</span>
        </div>

        {/* Range display */}
        <div className="flex items-center gap-3 text-sm font-['Open_Sans',sans-serif] mb-3">
          <span className="text-lia-text-primary">{fmt(min || d.salary_min)}</span>
          <span className="text-lia-text-disabled">—</span>
          <span className="text-lia-text-primary">{fmt(max || d.salary_max)}</span>
        </div>

        {/* Range sliders */}
        <div className="space-y-3">
          <div>
            <label className="text-[10px] text-lia-text-tertiary font-['Open_Sans',sans-serif]">Minimo</label>
            <input
              type="range"
              min={0}
              max={50000}
              step={500}
              value={min || d.salary_min || 0}
              onChange={(e) => handleMinChange(Number(e.target.value))}
              className="w-full h-1.5 rounded-full appearance-none bg-lia-bg-tertiary accent-wedo-cyan cursor-pointer"
            />
          </div>
          <div>
            <label className="text-[10px] text-lia-text-tertiary font-['Open_Sans',sans-serif]">Maximo</label>
            <input
              type="range"
              min={0}
              max={50000}
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
          <p className="text-[10px] font-medium text-wedo-cyan font-['Open_Sans',sans-serif]">Benchmark de mercado</p>
          <p className="text-xs text-lia-text-primary font-['Open_Sans',sans-serif] mt-0.5">
            {JSON.stringify(d.benchmark)}
          </p>
        </div>
      )}

      {d.benefits?.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 mb-1.5">
            <Gift className="w-4 h-4 text-wedo-cyan" />
            <span className="text-xs font-medium text-lia-text-secondary font-['Open_Sans',sans-serif]">Beneficios</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {d.benefits.map((b, i) => (
              <span key={i} className="px-2 py-0.5 rounded bg-lia-bg-secondary border border-lia-border-subtle text-xs text-lia-text-primary font-['Open_Sans',sans-serif]">
                {b}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
