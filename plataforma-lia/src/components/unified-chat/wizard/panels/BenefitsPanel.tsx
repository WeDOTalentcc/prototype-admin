"use client"

import React from "react"
import { Gift, Star, X } from "lucide-react"

export interface BenefitItem {
  name: string
  source?: string
  category?: string
  icon?: string
  value?: string
  value_type?: string
  is_highlighted?: boolean
}

interface Props {
  benefits: Array<string | BenefitItem>
  onRemove?: (index: number) => void
}

function normalize(b: string | BenefitItem): BenefitItem {
  return typeof b === "string" ? { name: b } : b
}

const CATEGORY_LABELS: Record<string, string> = {
  alimentacao: "Alimentação",
  transporte: "Transporte",
  saude: "Saúde",
  educacao: "Educação",
  lazer: "Lazer & Bem-estar",
  financeiro: "Financeiro",
  flexibilidade: "Flexibilidade",
  outros: "Outros",
}

export function BenefitsPanel({ benefits, onRemove }: Props) {
  if (!benefits || benefits.length === 0) {
    return (
      <div className="px-4 py-3">
        <div className="flex items-center gap-1.5 mb-2">
          <Gift className="w-4 h-4 text-wedo-cyan" />
          <span className="text-xs font-medium text-lia-text-secondary">Benefícios</span>
        </div>
        <p className="text-xs text-lia-text-muted italic">
          Nenhum benefício adicionado ainda.
        </p>
      </div>
    )
  }

  // Group by category
  const groups: Record<string, Array<{ item: BenefitItem; index: number }>> = {}
  const ungrouped: Array<{ item: BenefitItem; index: number }> = []

  benefits.forEach((raw, index) => {
    const item = normalize(raw)
    const cat = item.category?.toLowerCase() || ""
    if (cat) {
      if (!groups[cat]) groups[cat] = []
      groups[cat].push({ item, index })
    } else {
      ungrouped.push({ item, index })
    }
  })

  const hasGroups = Object.keys(groups).length > 0

  const renderItem = (item: BenefitItem, index: number) => (
    <div
      key={index}
      className="flex items-center justify-between px-2.5 py-1.5 rounded-md bg-lia-bg-secondary border border-lia-border-subtle"
    >
      <div className="flex items-center gap-1.5 min-w-0">
        {item.is_highlighted && (
          <Star className="w-3 h-3 text-wedo-cyan shrink-0" />
        )}
        <span className="text-xs text-lia-text-primary font-medium truncate">
          {item.name}
        </span>
        {item.value && (
          <span className="text-micro text-lia-text-muted shrink-0">
            {item.value}
            {item.value_type === "monthly" ? "/mês" : item.value_type === "daily" ? "/dia" : ""}
          </span>
        )}
      </div>
      {onRemove && (
        <button
          onClick={() => onRemove(index)}
          className="text-lia-text-disabled hover:text-status-error transition-colors ml-2 shrink-0"
          aria-label={`Remover ${item.name}`}
        >
          <X className="w-3 h-3" />
        </button>
      )}
    </div>
  )

  return (
    <div className="px-4 py-3 space-y-3">
      <div className="flex items-center gap-1.5">
        <Gift className="w-4 h-4 text-wedo-cyan" />
        <span className="text-xs font-medium text-lia-text-secondary">
          Benefícios ({benefits.length})
        </span>
      </div>

      {hasGroups ? (
        <div className="space-y-3">
          {Object.entries(groups).map(([cat, entries]) => (
            <div key={cat}>
              <p className="text-[10px] font-medium text-lia-text-tertiary uppercase tracking-wider mb-1.5">
                {CATEGORY_LABELS[cat] ?? cat}
              </p>
              <div className="space-y-1">
                {entries.map(({ item, index }) => renderItem(item, index))}
              </div>
            </div>
          ))}
          {ungrouped.length > 0 && (
            <div>
              <p className="text-[10px] font-medium text-lia-text-tertiary uppercase tracking-wider mb-1.5">
                Outros
              </p>
              <div className="space-y-1">
                {ungrouped.map(({ item, index }) => renderItem(item, index))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="flex flex-wrap gap-1.5">
          {ungrouped.map(({ item, index }) => (
            <span
              key={index}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-lia-bg-secondary border border-lia-border-subtle text-micro text-lia-text-primary"
            >
              {item.is_highlighted && <Star className="w-2.5 h-2.5 text-wedo-cyan" />}
              {item.name}
              {onRemove && (
                <button
                  onClick={() => onRemove(index)}
                  className="text-lia-text-disabled hover:text-status-error transition-colors ml-0.5"
                  aria-label={`Remover ${item.name}`}
                >
                  <X className="w-2.5 h-2.5" />
                </button>
              )}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
