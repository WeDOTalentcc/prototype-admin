"use client"

/**
 * WT-2022 P1.APIFY: STATUS = ORPHAN COMPONENT (verificado 2026-05-21).
 *
 * Componente funcional, com backend real (/api/backend-proxy/consumption?path=budget-status
 * via app/api/v1/consumption.py :: get_budget_status), mas atualmente sem call-site no
 * frontend (zero imports).
 *
 * NAO deletar: backend live + valor real para tenants que usam sourcing Apify.
 * NAO montar adivinhando: integration-data.ts nao tem entry "apify" (Apify roda do
 * lado WeDOTalent, nao e integracao cliente-configuravel via UI).
 *
 * TODO produto: decidir lugar canonical de mount:
 *   (a) painel sourcing / dashboard de consumo (provavel correto)
 *   (b) hub MCPs & APIs com novo entry apify em integration-data.ts
 *   (c) tab dedicada em "Minha Empresa > Consumo"
 *
 * Ate decisao, fica como dead-but-preserved code com referencia explicita aqui.
 *
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
import { useTranslations } from "next-intl"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Chip } from "@/components/ui/chip"
import { Zap, AlertCircle, RefreshCw } from "lucide-react"
import { cn } from "@/lib/utils"
import { apiFetch } from "@/lib/api/api-fetch"

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
  const t = useTranslations("settings.apifyWidget")
  const [data, setData] = useState<BudgetStatus | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStatus = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await apiFetch("/api/backend-proxy/consumption?path=budget-status", {
        headers: { "Content-Type": "application/json" },
      })
      if (!res.ok) {
        setError(t("loadError", { status: res.status }))
        setData(null)
      } else {
        const body = (await res.json()) as BudgetStatus
        setData(body)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t("loadFailed"))
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [t])

  useEffect(() => {
    fetchStatus()
    if (!autoRefreshMs || autoRefreshMs < 5000) return
    const id = setInterval(fetchStatus, autoRefreshMs)
    return () => clearInterval(id)
  }, [autoRefreshMs, fetchStatus])

  const severity = data ? severityForUsage(data.usage_percentage) : "success"

  return (
    <Card className={cn("border-lia-border-subtle", className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Zap className="w-4 h-4 text-wedo-cyan" />
            {t("title")}
          </CardTitle>
          <button
            type="button"
            onClick={fetchStatus}
            aria-label={t("refresh")}
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
          <p className="text-xs text-lia-text-tertiary">{t("loading")}</p>
        ) : error ? (
          <div className="flex items-start gap-2 text-xs text-status-danger">
            <AlertCircle className="w-3.5 h-3.5 mt-0.5" />
            <span>{error}</span>
          </div>
        ) : data ? (
          <>
            <div className="flex items-baseline justify-between">
              <div>
                <p className="text-xs text-lia-text-tertiary">{t("spent")}</p>
                <p className="text-sm font-medium text-lia-text-primary">
                  ${data.current_spend_usd.toFixed(2)}{" "}
                  <span className="text-xs text-lia-text-tertiary">USD</span>
                </p>
                <p className="text-xs text-lia-text-tertiary">
                  ≈ {formatBRL(data.current_spend_usd, data.exchange_rate)}
                </p>
              </div>
              <div className="text-right">
                <p className="text-xs text-lia-text-tertiary">{t("limit")}</p>
                <p className="text-sm font-medium text-lia-text-primary">
                  ${data.monthly_budget_usd.toFixed(2)}
                </p>
                <p className="text-xs text-lia-text-tertiary">
                  {t("remaining", { amount: `$${data.remaining_usd.toFixed(2)}` })}
                </p>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-lia-text-tertiary">
                  {t("usagePct", { pct: data.usage_percentage.toFixed(1) })}
                </span>
                <Chip
                  variant={
                    severity === "danger" ? "danger"
                    : severity === "warning" ? "warning"
                    : "success"
                  }
                >
                  {severity === "danger" ? t("nearLimit")
                    : severity === "warning" ? t("highUse")
                    : t("healthy")}
                </Chip>
              </div>
              <Progress value={Math.min(data.usage_percentage, 100)} />
            </div>

            {severity === "danger" && (
              <div className="flex items-start gap-2 text-xs text-status-danger">
                <AlertCircle className="w-3.5 h-3.5 mt-0.5" />
                <span>
                  {t("nearLimitWarning")}
                </span>
              </div>
            )}
          </>
        ) : null}
      </CardContent>
    </Card>
  )
}
