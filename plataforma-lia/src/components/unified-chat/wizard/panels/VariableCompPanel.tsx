"use client"

import React from "react"
import { TrendingUp, X } from "lucide-react"

export interface VariableCompItem {
  name: string
  kind?: string
  target_pct?: number
  min_pct?: number
  max_pct?: number
  min_amount?: number
  max_amount?: number
  currency?: string
  frequency?: string
  matches_vaga?: boolean
}

interface Props {
  items: VariableCompItem[]
  onRemove?: (index: number) => void
  currency?: string
}

const KIND_LABELS: Record<string, string> = {
  PLR: "PLR",
  bonus: "Bônus",
  comissao: "Comissão",
  participacao: "Participação",
  stock: "Stock Options",
  outras: "Outros",
}

const FREQ_LABELS: Record<string, string> = {
  mensal: "mensal",
  trimestral: "trim.",
  semestral: "sem.",
  anual: "anual",
  monthly: "mensal",
  quarterly: "trim.",
  annually: "anual",
}

function formatPct(item: VariableCompItem): string | null {
  if (item.target_pct != null) return `${item.target_pct}%`
  if (item.min_pct != null && item.max_pct != null)
    return `${item.min_pct}–${item.max_pct}%`
  if (item.min_pct != null) return `a partir de ${item.min_pct}%`
  return null
}

function formatAmount(item: VariableCompItem, currency: string): string | null {
  const fmt = (v: number) => `${currency} ${v.toLocaleString("pt-BR")}`
  if (item.min_amount != null && item.max_amount != null)
    return `${fmt(item.min_amount)}–${fmt(item.max_amount)}`
  if (item.min_amount != null) return `a partir de ${fmt(item.min_amount)}`
  return null
}

export function VariableCompPanel({ items, onRemove, currency = "BRL" }: Props) {
  if (!items || items.length === 0) {
    return (
      <div className="px-4 py-3">
        <div className="flex items-center gap-1.5 mb-2">
          <TrendingUp className="w-4 h-4 text-wedo-cyan" />
          <span className="text-xs font-medium text-lia-text-secondary">Remuneração Variável</span>
        </div>
        <p className="text-xs text-lia-text-muted italic">
          Nenhuma remuneração variável adicionada.
        </p>
      </div>
    )
  }

  return (
    <div className="px-4 py-3 space-y-3">
      <div className="flex items-center gap-1.5">
        <TrendingUp className="w-4 h-4 text-wedo-cyan" />
        <span className="text-xs font-medium text-lia-text-secondary">
          Remuneração Variável ({items.length})
        </span>
      </div>

      <div className="space-y-1.5">
        {items.map((vc, i) => {
          const pct = formatPct(vc)
          const amount = formatAmount(vc, currency)
          const kindLabel = vc.kind ? (KIND_LABELS[vc.kind] ?? vc.kind) : null
          const freqLabel = vc.frequency ? (FREQ_LABELS[vc.frequency] ?? vc.frequency) : null

          return (
            <div
              key={i}
              className={[
                "flex items-start justify-between px-2.5 py-2 rounded-md border",
                vc.matches_vaga
                  ? "bg-wedo-cyan/5 border-wedo-cyan/30"
                  : "bg-lia-bg-secondary border-lia-border-subtle",
              ].join(" ")}
            >
              <div className="flex flex-col gap-0.5 min-w-0">
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="text-xs text-lia-text-primary font-medium">
                    {vc.name}
                  </span>
                  {kindLabel && (
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-medium bg-lia-bg-tertiary text-lia-text-secondary border border-lia-border-subtle">
                      {kindLabel}
                    </span>
                  )}
                  {vc.matches_vaga && (
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-medium bg-wedo-cyan/10 text-wedo-cyan border border-wedo-cyan/30">
                      recomendado
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  {pct && (
                    <span className="text-micro text-lia-text-secondary font-medium">
                      {pct}
                    </span>
                  )}
                  {amount && (
                    <span className="text-micro text-lia-text-muted">
                      {amount}
                    </span>
                  )}
                  {freqLabel && (
                    <span className="text-micro text-lia-text-tertiary">
                      · {freqLabel}
                    </span>
                  )}
                </div>
              </div>

              {onRemove && (
                <button
                  onClick={() => onRemove(i)}
                  className="text-lia-text-disabled hover:text-status-error transition-colors ml-2 mt-0.5 shrink-0"
                  aria-label={`Remover ${vc.name}`}
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
