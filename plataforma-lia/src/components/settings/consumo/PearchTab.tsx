"use client"

import { useState } from "react"
import useSWR from "swr"
import { Search, CheckCircle2, DollarSign, BarChart3 } from "lucide-react"
import { cn } from "@/lib/utils"

const jsonFetcher = (url: string) => fetch(url).then(r => r.json())

interface PearchConsumption {
  company_id: string
  period_start: string
  period_end: string
  period_days: number
  total_searches: number
  successful_searches: number
  total_credits_consumed: number
  estimated_cost_brl: number
}

const PERIOD_OPTIONS = [
  { label: "7d", value: 7 },
  { label: "30d", value: 30 },
  { label: "90d", value: 90 },
] as const

export function PearchTab() {
  const [days, setDays] = useState<7 | 30 | 90>(30)

  const { data, isLoading, error } =
    useSWR<PearchConsumption>(, jsonFetcher)

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-lia-text-tertiary">
        Carregando dados do Pearch...
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-status-error">
        Erro ao carregar dados. Tente novamente.
      </div>
    )
  }

  const totalSearches = data?.total_searches ?? 0
  const creditsUsed = data?.total_credits_consumed ?? 0
  const successfulSearches = data?.successful_searches ?? 0
  const costBrl = data?.estimated_cost_brl ?? 0
  const successRate = totalSearches > 0 ? Math.round((successfulSearches / totalSearches) * 100) : null

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <p className="text-sm text-lia-text-tertiary">
          Buscas globais de candidatos via Pearch.
        </p>
        <div className="flex items-center gap-1 rounded-md border border-lia-border-subtle bg-lia-bg-primary p-0.5">
          {PERIOD_OPTIONS.map(({ label, value }) => (
            <button
              key={value}
              onClick={() => setDays(value)}
              className={cn(
                "rounded px-2.5 py-1 text-xs font-medium transition-colors",
                days === value
                  ? "bg-lia-bg-elevated text-lia-text-primary shadow-sm"
                  : "text-lia-text-tertiary hover:text-lia-text-secondary"
              )}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {totalSearches === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <Search className="w-8 h-8 text-lia-text-tertiary mb-3" />
          <p className="text-sm font-medium text-lia-text-secondary">Nenhuma busca registrada</p>
          <p className="text-xs text-lia-text-tertiary mt-1">
            Nenhuma busca Pearch nos últimos {days} dias.
          </p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 max-w-xl">
            <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-primary p-4">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs text-lia-text-tertiary">Buscas realizadas</p>
                <Search className="w-3.5 h-3.5 text-lia-text-disabled" />
              </div>
              <p className="text-2xl font-semibold text-lia-text-primary tabular-nums">
                {totalSearches.toLocaleString("pt-BR")}
              </p>
              <p className="text-xs text-lia-text-disabled mt-1">Últimos {days} dias</p>
            </div>

            <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-primary p-4">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs text-lia-text-tertiary">Créditos utilizados</p>
                <BarChart3 className="w-3.5 h-3.5 text-lia-text-disabled" />
              </div>
              <p className="text-2xl font-semibold text-lia-text-primary tabular-nums">
                {creditsUsed.toLocaleString("pt-BR")}
              </p>
              <p className="text-xs text-lia-text-disabled mt-1">créditos</p>
            </div>

            <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-primary p-4">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs text-lia-text-tertiary">Taxa de sucesso</p>
                <CheckCircle2 className="w-3.5 h-3.5 text-lia-text-disabled" />
              </div>
              {successRate !== null ? (
                <>
                  <p className="text-2xl font-semibold text-lia-text-primary tabular-nums">
                    {successRate}%
                  </p>
                  <div className="mt-2 h-1.5 rounded-full bg-lia-bg-tertiary overflow-hidden">
                    <div
                      className="h-full rounded-full bg-forest-green transition-all duration-500"
                      style={{ width:  }}
                    />
                  </div>
                </>
              ) : (
                <p className="text-2xl font-semibold text-lia-text-disabled">—</p>
              )}
            </div>

            {costBrl > 0 && (
              <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-primary p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs text-lia-text-tertiary">Custo estimado</p>
                  <DollarSign className="w-3.5 h-3.5 text-lia-text-disabled" />
                </div>
                <p className="text-2xl font-semibold text-lia-text-primary tabular-nums">
                  {costBrl.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}
                </p>
                <p className="text-xs text-lia-text-disabled mt-1">no período</p>
              </div>
            )}
          </div>

          {successRate !== null && (
            <p className="text-xs text-lia-text-tertiary">
              {successfulSearches.toLocaleString("pt-BR")} de {totalSearches.toLocaleString("pt-BR")} buscas retornaram candidatos.
            </p>
          )}
        </>
      )}
    </div>
  )
}
