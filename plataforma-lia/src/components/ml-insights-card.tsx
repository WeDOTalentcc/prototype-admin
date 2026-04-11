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
import { useMLPredictions } from "@/hooks/ai/use-ml-predictions"

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
  if (level === "high") return "text-status-success dark:text-status-success"
  if (level === "medium") return "text-status-warning dark:text-status-warning"
  return "text-lia-text-tertiary"
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
    <div className={`border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-lia-bg-primary dark:bg-lia-bg-primary overflow-hidden ${className}`}>
      {/* Header — sempre visível */}
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between px-3 py-2 text-xs font-medium text-lia-text-secondary hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none"
       
      >
        <span className="flex items-center gap-1.5">
          <TrendingUp className="w-3.5 h-3.5 text-lia-text-secondary" />
          Previsões IA
        </span>
        <span className="flex items-center gap-1">
          {loading && <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none text-lia-text-secondary" />}
          {isOpen ? <ChevronUp className="w-3.5 h-3.5 text-lia-text-secondary" /> : <ChevronDown className="w-3.5 h-3.5 text-lia-text-secondary" />}
        </span>
      </button>

      {/* Body — expandível */}
      {isOpen && (
        <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle px-3 py-2.5 space-y-2.5">
          {error && (
            <div className="flex items-center gap-1.5 text-xs text-status-error dark:text-status-error">
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
              <span>{error}</span>
              <button
                onClick={handleRefresh}
                className="ml-auto text-lia-text-secondary hover:text-lia-text-secondary dark:hover:text-lia-text-tertiary"
                title="Tentar novamente"
              >
                <RefreshCw className="w-3 h-3" />
              </button>
            </div>
          )}

          {loading && !timeToFill && !salary && (
            <div className="flex items-center justify-center py-3" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
              <span className="ml-2 text-xs text-lia-text-secondary">
                Calculando previsões...
              </span>
            </div>
          )}

          {/* Time to Fill */}
          {timeToFill && (
            <div className="flex items-start gap-2">
              <Clock className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-xs text-lia-text-tertiary">
                  Tempo estimado de preenchimento
                </p>
                <p className="text-sm font-semibold text-lia-text-primary" >
                  {timeToFill.predicted_days} dias
                  <span className="text-micro font-normal text-lia-text-secondary ml-1">
                    ({timeToFill.range_min}–{timeToFill.range_max})
                  </span>
                </p>
                <p className={`text-micro ${confidenceColor(timeToFill.confidence_level)}`}>
                  {timeToFill.comparison_to_market}
                </p>
              </div>
            </div>
          )}

          {/* Salary Range */}
          {salary && (
            <div className="flex items-start gap-2">
              <DollarSign className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-xs text-lia-text-tertiary">
                  Faixa salarial sugerida
                </p>
                <p className="text-sm font-semibold text-lia-text-primary" >
                  {formatCurrency(salary.suggested_min)} – {formatCurrency(salary.suggested_max)}
                </p>
                <p className={`text-micro ${confidenceColor(salary.confidence_level)}`}>
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
                className="flex items-center gap-1 text-micro text-lia-text-secondary hover:text-lia-text-secondary dark:hover:text-lia-text-tertiary transition-colors motion-reduce:transition-none"
               
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
