"use client"

import React from "react"
import { History, Clock, Users, RotateCcw, Sparkles } from "lucide-react"

export interface JdSimilarItem {
  id: string
  title: string
  department?: string | null
  seniorityLevel?: string | null
  wasFilled: boolean
  timeToFillDays?: number | null
  candidatesCount: number
  similarity?: number | null
}

interface Props {
  items: JdSimilarItem[]
  onReuse: (id: string) => void
  onCreateFresh: () => void
  loading?: boolean
}

/**
 * JdSimilarCard — Sprint B Phase 1.
 *
 * Aparece no inicio do wizard quando a empresa tem >= 10 JDs em historico
 * e existe ao menos uma vaga similar (similarity >= 0.7) para o titulo digitado.
 *
 * Outcome-aware: prioriza visualmente JDs que preencheram bem (`wasFilled` + `timeToFillDays`).
 *
 * Fail-graceful: se `items` esta vazio, retorna null (nao polui UI sem dado).
 */
export function JdSimilarCard({ items, onReuse, onCreateFresh, loading }: Props) {
  if (loading) {
    return (
      <div className="rounded-lg border border-lia-border-default bg-lia-bg-secondary p-4">
        <div className="flex items-center gap-2 text-sm text-lia-text-secondary">
          <History className="w-4 h-4 animate-pulse" />
          <span>Buscando vagas similares no historico...</span>
        </div>
      </div>
    )
  }

  if (!items || items.length === 0) {
    return null
  }

  return (
    <div className="rounded-lg border border-wedo-cyan/30 bg-lia-bg-secondary p-4 space-y-3">
      <div className="flex items-center gap-2">
        <History className="w-4 h-4 text-wedo-cyan" />
        <h3 className="text-sm font-medium text-lia-text-primary">
          Vaga similar encontrada no historico
        </h3>
      </div>

      <p className="text-xs text-lia-text-secondary">
        Voce ja criou {items.length === 1 ? "uma vaga parecida" : `${items.length} vagas parecidas`} antes.
        Reusar pode economizar tempo e manter consistencia.
      </p>

      <div className="space-y-2">
        {items.map((item) => (
          <button
            key={item.id}
            onClick={() => onReuse(item.id)}
            className="w-full text-left rounded-md border border-lia-border-default bg-lia-bg-primary p-3 hover:border-wedo-cyan hover:bg-lia-interactive-hover transition-colors group"
            aria-label={`Reusar JD: ${item.title}`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-lia-text-primary truncate">
                  {item.title}
                </div>
                {(item.department || item.seniorityLevel) && (
                  <div className="text-xs text-lia-text-secondary mt-0.5 flex items-center gap-1.5">
                    {item.department && <span>{item.department}</span>}
                    {item.department && item.seniorityLevel && <span>·</span>}
                    {item.seniorityLevel && <span className="capitalize">{item.seniorityLevel}</span>}
                  </div>
                )}
              </div>
              {item.similarity != null && (
                <span className="text-xs text-wedo-cyan-text font-mono shrink-0">
                  {Math.round(item.similarity * 100)}%
                </span>
              )}
            </div>

            <div className="mt-2 flex items-center gap-3 text-xs text-lia-text-secondary">
              {item.wasFilled && item.timeToFillDays != null && (
                <span className="flex items-center gap-1 text-status-success">
                  <Clock className="w-3 h-3" />
                  Preenchida em {item.timeToFillDays}d
                </span>
              )}
              {!item.wasFilled && (
                <span className="flex items-center gap-1 text-lia-text-disabled">
                  <Clock className="w-3 h-3" />
                  Em aberto
                </span>
              )}
              <span className="flex items-center gap-1">
                <Users className="w-3 h-3" />
                {item.candidatesCount} candidato{item.candidatesCount === 1 ? "" : "s"}
              </span>
            </div>
          </button>
        ))}
      </div>

      <div className="flex justify-end pt-1">
        <button
          onClick={onCreateFresh}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-lia-text-secondary hover:text-lia-text-primary hover:bg-lia-interactive-hover rounded transition-colors"
          aria-label="Criar vaga do zero"
        >
          <Sparkles className="w-3 h-3" />
          Criar do zero
        </button>
      </div>
    </div>
  )
}

export default JdSimilarCard
