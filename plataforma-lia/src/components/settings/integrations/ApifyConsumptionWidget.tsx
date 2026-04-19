"use client"

/**
 * ApifyConsumptionWidget — visual summary of Apify consumption for the tenant.
 *
 * Data source: GET /api/backend-proxy/consumption?path=budget-status
 * Backend: app/api/v1/consumption.py :: get_budget_status (already exists, D0).
 *
 * Design system v4.2.2:
 *   - Card base with monochromatic background + wedo-cyan accent.
 *   - Progress bar color: status-success (<70%), status-warning (70-90%), status-danger (>90%).
 *   - Typography: Open Sans, text-xs for labels, text-sm for values.
 */

import React, { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Chip } from "@/components/ui/chip"
import { Zap, AlertCircle, RefreshCw } from "lucide-react"
import { cn } from "@/lib/utils"

interface BudgetStatus {
  company_id: string
  monthly_budget_usd: number
  current_spend_usd: number
  remaining_usd: number
  usage_percentage: number
  exchange_rate: number
}

interface Props {
  className?: string
  autoRefreshMs?: number // optional polling interval
}

function severityForUsage(pct: number): "success" | "warning" | "danger" {
  if (pct >= 90) return "danger"
  if (pct >= 70) return "warning"
  return "success"
}

function formatBRL(usd: number, rate: number): string {
  const brl = usd * rate
  return brl.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2,
  })
}

export function ApifyConsumptionWidget({ className, autoRefreshMs }: Props) {
  const [data, setData] = useState<BudgetStatus | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStatus = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch("/api/backend-proxy/consumption?path=budget-status", {
        headers: { "Content-Type": "application/json" },
      })
      if (!res.ok) {
        setError(`Erro ${res.status} ao carregar consumo`)
        setData(null)
      } else {
        const body = (await res.json()) as BudgetStatus
        setData(body)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar consumo")
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
    if (!autoRefreshMs || autoRefreshMs < 5000) return
    const t = setInterval(fetchStatus, autoRefreshMs)
    return () => clearInterval(t)
  }, [autoRefreshMs])

  const severity = data ? severityForUsage(data.usage_percentage) : "success"

  return (
    <Card className={cn("border-lia-border-subtle", className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Zap className="w-4 h-4 text-wedo-cyan" />
            Consumo Apify (mês atual)
          </CardTitle>
          <button
            type="button"
            onClick={fetchStatus}
            aria-label="Atualizar"
            className={cn(
              "p-1 rounded-md text-lia-text-tertiary hover:text-lia-text-secondary",
              "hover:bg-black/5 dark:hover:bg-white/5",
              "transition-colors motion-reduce:transition-none",
              loading && "animate-spin",
            )}
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {loading && !data ? (
          <p className="text-xs text-lia-text-tertiary">Carregando...</p>
        ) : error ? (
          <div className="flex items-start gap-2 text-xs text-status-danger">
            <AlertCircle className="w-3.5 h-3.5 mt-0.5" />
            <span>{error}</span>
          </div>
        ) : data ? (
          <>
            <div className="flex items-baseline justify-between">
              <div>
                <p className="text-xs text-lia-text-tertiary">Gasto</p>
                <p className="text-sm font-medium text-lia-text-primary">
                  ${data.current_spend_usd.toFixed(2)}{" "}
                  <span className="text-xs text-lia-text-tertiary">USD</span>
                </p>
                <p className="text-xs text-lia-text-tertiary">
                  ≈ {formatBRL(data.current_spend_usd, data.exchange_rate)}
                </p>
              </div>
              <div className="text-right">
                <p className="text-xs text-lia-text-tertiary">Limite</p>
                <p className="text-sm font-medium text-lia-text-primary">
                  ${data.monthly_budget_usd.toFixed(2)}
                </p>
                <p className="text-xs text-lia-text-tertiary">
                  Restam ${data.remaining_usd.toFixed(2)}
                </p>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-lia-text-tertiary">
                  {data.usage_percentage.toFixed(1)}% usado
                </span>
                <Chip
                  variant={
                    severity === "danger" ? "status-danger"
                    : severity === "warning" ? "status-warning"
                    : "status-success"
                  }
                >
                  {severity === "danger" ? "Limite próximo"
                    : severity === "warning" ? "Uso alto"
                    : "Saudável"}
                </Chip>
              </div>
              <Progress value={Math.min(data.usage_percentage, 100)} />
            </div>

            {severity === "danger" && (
              <div className="flex items-start gap-2 text-xs text-status-danger">
                <AlertCircle className="w-3.5 h-3.5 mt-0.5" />
                <span>
                  Próximo do limite mensal. Novas chamadas Apify podem ser bloqueadas.
                </span>
              </div>
            )}
          </>
        ) : null}
      </CardContent>
    </Card>
  )
}
