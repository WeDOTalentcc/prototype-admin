"use client"

import React from "react"
import { DollarSign, Gift } from "lucide-react"
import type { SalaryData } from "../wizard-types"

interface Props {
  data: Record<string, unknown>
  onUpdate?: (updates: Record<string, unknown>) => void
}

export function SalaryPanel({ data }: Props) {
  const d = data as unknown as SalaryData
  const currency = d.salary_currency || "BRL"
  const fmt = (v: number | null) => v ? `${currency} ${v.toLocaleString("pt-BR")}` : "-"

  return (
    <div className="px-4 py-3 space-y-4">
      <div>
        <div className="flex items-center gap-1.5 mb-2">
          <DollarSign className="w-4 h-4 text-wedo-cyan" />
          <span className="text-xs font-medium text-lia-text-secondary font-['Open_Sans',sans-serif]">Faixa salarial</span>
        </div>
        <div className="flex items-center gap-3 text-sm font-['Open_Sans',sans-serif]">
          <span className="text-lia-text-primary">{fmt(d.salary_min)}</span>
          <span className="text-lia-text-disabled">—</span>
          <span className="text-lia-text-primary">{fmt(d.salary_max)}</span>
        </div>
      </div>

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
