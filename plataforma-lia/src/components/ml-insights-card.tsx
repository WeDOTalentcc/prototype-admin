"use client"

/**
 * MLInsightsCard — card compacto de previsões ML para uma vaga (P4).
 *
 * Exibe 3 métricas ao expandir:
 *  - Tempo estimado de preenchimento (time-to-fill)
 *  - Faixa salarial ótima
 *  - Percentil de mercado
 *
 * Portabilidade Vue: props tipadas, onToggle callback, sem padrões React-only.
 */
import { useState, useCallback } from "react"
import { TrendingUp, Clock, DollarSign, ChevronDown, ChevronUp, Loader2, AlertCircle, RefreshCw } from "lucide-react"
import { useMLPredictions } from "@/hooks/use-ml-predictions"

// ── Types ──────────────────────────────────────────────────────────────────

interface MLInsightsCardProps {
  companyId: string
  jobData: {
    title?: string
    department?: string
    seniority?: string
    location?: string
    work_model?: string
    employment_type?: string
  }
  className?: string
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 0,
  }).format(value)
}

function confidenceColor(level: string): string {
  if (level === "high") return "text-emerald-700 dark:text-emerald-400"
  if (level === "medium") return "text-amber-600 dark:text-amber-400"
  return "text-gray-500 dark:text-gray-400"
}

// ── Component ─────────────────────────────────────────────────────────────

export function MLInsightsCard({ companyId, jobData, className = "" }: MLInsightsCardProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [hasFetched, setHasFetched] = useState(false)
  const { timeToFill, salary, loading, error, fetchTimeToFill, fetchSalary } = useMLPredictions()

  const loadPredictions = useCallback(async () => {
    if (hasFetched) return
    setHasFetched(true)
    await Promise.all([
      fetchTimeToFill(companyId, jobData),
      fetchSalary(companyId, jobData),
    ])
  }, [hasFetched, companyId, jobData, fetchTimeToFill, fetchSalary])

  const handleToggle = useCallback(() => {
    const next = !isOpen
    setIsOpen(next)
    if (next) loadPredictions()
  }, [isOpen, loadPredictions])

  const handleRefresh = useCallback(async (e: React.MouseEvent) => {
    e.stopPropagation()
    setHasFetched(false)
    setIsOpen(true)
    await Promise.all([
      fetchTimeToFill(companyId, jobData),
      fetchSalary(companyId, jobData),
    ])
    setHasFetched(true)
  }, [companyId, jobData, fetchTimeToFill, fetchSalary])

  return (
    <div className={`border border-gray-200 dark:border-gray-700 rounded-md bg-white dark:bg-gray-900 overflow-hidden ${className}`}>
      {/* Header — sempre visível */}
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between px-3 py-2 text-xs font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
        style={{ fontFamily: "Open Sans, sans-serif" }}
      >
        <span className="flex items-center gap-1.5">
          <TrendingUp className="w-3.5 h-3.5 text-gray-500" />
          Previsões IA
        </span>
        <span className="flex items-center gap-1">
          {loading && <Loader2 className="w-3 h-3 animate-spin text-gray-400" />}
          {isOpen ? <ChevronUp className="w-3.5 h-3.5 text-gray-400" /> : <ChevronDown className="w-3.5 h-3.5 text-gray-400" />}
        </span>
      </button>

      {/* Body — expandível */}
      {isOpen && (
        <div className="border-t border-gray-200 dark:border-gray-700 px-3 py-2.5 space-y-2.5">
          {error && (
            <div className="flex items-center gap-1.5 text-xs text-red-600 dark:text-red-400">
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
              <span>{error}</span>
              <button
                onClick={handleRefresh}
                className="ml-auto text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                title="Tentar novamente"
              >
                <RefreshCw className="w-3 h-3" />
              </button>
            </div>
          )}

          {loading && !timeToFill && !salary && (
            <div className="flex items-center justify-center py-3">
              <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
              <span className="ml-2 text-xs text-gray-500" style={{ fontFamily: "Open Sans, sans-serif" }}>
                Calculando previsões...
              </span>
            </div>
          )}

          {/* Time to Fill */}
          {timeToFill && (
            <div className="flex items-start gap-2">
              <Clock className="w-3.5 h-3.5 text-gray-500 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-xs text-gray-500 dark:text-gray-400" style={{ fontFamily: "Open Sans, sans-serif" }}>
                  Tempo estimado de preenchimento
                </p>
                <p className="text-sm font-semibold text-gray-900 dark:text-gray-50" style={{ fontFamily: "Inter, sans-serif" }}>
                  {timeToFill.predicted_days} dias
                  <span className="text-micro font-normal text-gray-500 ml-1">
                    ({timeToFill.range_min}–{timeToFill.range_max})
                  </span>
                </p>
                <p className={`text-micro ${confidenceColor(timeToFill.confidence_level)}`} style={{ fontFamily: "Open Sans, sans-serif" }}>
                  {timeToFill.comparison_to_market}
                </p>
              </div>
            </div>
          )}

          {/* Salary Range */}
          {salary && (
            <div className="flex items-start gap-2">
              <DollarSign className="w-3.5 h-3.5 text-gray-500 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-xs text-gray-500 dark:text-gray-400" style={{ fontFamily: "Open Sans, sans-serif" }}>
                  Faixa salarial sugerida
                </p>
                <p className="text-sm font-semibold text-gray-900 dark:text-gray-50" style={{ fontFamily: "Inter, sans-serif" }}>
                  {formatCurrency(salary.suggested_min)} – {formatCurrency(salary.suggested_max)}
                </p>
                <p className={`text-micro ${confidenceColor(salary.confidence_level)}`} style={{ fontFamily: "Open Sans, sans-serif" }}>
                  {salary.competitive_analysis} · P{salary.market_percentile}
                </p>
              </div>
            </div>
          )}

          {/* Refresh footer */}
          {(timeToFill || salary) && !loading && (
            <div className="flex justify-end pt-0.5">
              <button
                onClick={handleRefresh}
                className="flex items-center gap-1 text-micro text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                style={{ fontFamily: "Open Sans, sans-serif" }}
              >
                <RefreshCw className="w-2.5 h-2.5" />
                Atualizar
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
