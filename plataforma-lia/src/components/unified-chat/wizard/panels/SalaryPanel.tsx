"use client"

import React, { useState } from "react"
import { DollarSign, Gift, CheckCircle2, Edit2, TrendingUp, X } from "lucide-react"
import type { SalaryData } from "../wizard-types"
import { FallbackBanner } from "./FallbackBanner"
import { AiDegradedModeBanner } from "./AiDegradedModeBanner"

interface Props {
  data: Record<string, unknown>
  onUpdate?: (updates: Record<string, unknown>) => void
}

export function SalaryPanel({ data, onUpdate }: Props) {
  const d = data as unknown as SalaryData
  const currency = d.salary_currency || "BRL"
  const fmt = (v: number | null | undefined) =>
    v ? `${currency} ${v.toLocaleString("pt-BR")}` : "-"

  // Fase 5: se salary_confirmed=true (recrutador confirmou via painel ou
  // right_panel_form), mostra a faixa como confirmada com ajuste como ação secundária.
  const isConfirmed = Boolean(d.salary_confirmed)
  const [isAdjusting, setIsAdjusting] = useState(false)

  const [min, setMin] = useState(d.salary_min ?? 0)
  const [max, setMax] = useState(d.salary_max ?? 0)

  const benchmarkMax = d.benchmark
    ? Number(
        (d.benchmark as Record<string, unknown>).p90 ||
        (d.benchmark as Record<string, unknown>).max ||
        50000,
      )
    : null
  const sliderMax = Math.max(50000, benchmarkMax ?? 0, (d.salary_max ?? 0) * 1.5)

  const handleMinChange = (val: number) => {
    setMin(val)
    onUpdate?.({ salary_min: val })
  }
  const handleMaxChange = (val: number) => {
    setMax(val)
    onUpdate?.({ salary_max: val })
  }
  const handleConfirmAdjust = () => {
    onUpdate?.({ salary_min: min, salary_max: max })
    setIsAdjusting(false)
  }

  const showSliders = !isConfirmed || isAdjusting

  return (
    <div className="px-4 py-3 space-y-4">
      <AiDegradedModeBanner state={d.ai_degraded_mode ?? null} />

      {d.salary_used_fallback && (
        <div className="-mx-4 -mt-3 [&>div]:mx-0 [&>div]:mt-0 [&>div]:rounded-none [&>div]:border-x-0 [&>div]:border-t-0">
          <FallbackBanner
            reason={d.salary_fallback_reason ?? "timeout"}
            message={
              d.salary_fallback_reason
                ? undefined
                : "Benchmark de mercado indisponível agora — preencha a faixa manualmente."
            }
            onRetry={() =>
              window.dispatchEvent(
                new CustomEvent("lia:wizard-retry-stage", {
                  detail: { stage: "salary" },
                }),
              )
            }
          />
        </div>
      )}

      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5">
            <DollarSign className="w-4 h-4 text-wedo-cyan" />
            <span className="text-xs font-medium text-lia-text-secondary">Faixa salarial</span>
          </div>
          {/* Fase 5: modo confirmado mostra badge + botão de ajuste secundário */}
          {isConfirmed && !isAdjusting && (
            <button
              data-testid="salary-adjust-btn"
              onClick={() => setIsAdjusting(true)}
              className="flex items-center gap-1 text-[10px] text-lia-text-muted hover:text-wedo-cyan transition-colors"
            >
              <Edit2 className="w-3 h-3" />
              Ajustar
            </button>
          )}
        </div>

        {/* Faixa confirmada — exibe como badge verde */}
        {isConfirmed && !isAdjusting ? (
          <div
            data-testid="salary-confirmed-display"
            className="flex items-center gap-2 p-2.5 rounded-md bg-status-success/10 border border-status-success/30"
          >
            <CheckCircle2 className="w-4 h-4 text-status-success shrink-0" />
            <div>
              <p className="text-xs font-medium text-status-success">Faixa confirmada</p>
              <p className="text-sm text-lia-text-primary mt-0.5">
                {fmt(d.salary_min)} — {fmt(d.salary_max)}
              </p>
            </div>
          </div>
        ) : (
          <>
            {/* Faixa não-confirmada ou em ajuste: display + sliders */}
            <div className="flex items-center gap-3 text-sm mb-3">
              <span className="text-lia-text-primary">{fmt(min || d.salary_min)}</span>
              <span className="text-lia-text-disabled">—</span>
              <span className="text-lia-text-primary">{fmt(max || d.salary_max)}</span>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-[10px] text-lia-text-tertiary">Mínimo</label>
                <input
                  data-testid="salary-slider-min"
                  type="range"
                  min={0}
                  max={sliderMax}
                  step={500}
                  value={min || d.salary_min || 0}
                  onChange={(e) => handleMinChange(Number(e.target.value))}
                  className="w-full h-1.5 rounded-full appearance-none bg-lia-bg-tertiary accent-wedo-cyan cursor-pointer"
                />
              </div>
              <div>
                <label className="text-[10px] text-lia-text-tertiary">Máximo</label>
                <input
                  data-testid="salary-slider-max"
                  type="range"
                  min={0}
                  max={sliderMax}
                  step={500}
                  value={max || d.salary_max || 0}
                  onChange={(e) => handleMaxChange(Number(e.target.value))}
                  className="w-full h-1.5 rounded-full appearance-none bg-lia-bg-tertiary accent-wedo-cyan cursor-pointer"
                />
              </div>
            </div>

            {isAdjusting && (
              <div className="flex justify-end gap-2 mt-2">
                <button
                  onClick={() => setIsAdjusting(false)}
                  className="px-2 py-1 text-xs text-lia-text-secondary hover:bg-lia-interactive-hover rounded"
                >
                  Cancelar
                </button>
                <button
                  data-testid="salary-confirm-adjust-btn"
                  onClick={handleConfirmAdjust}
                  className="px-2 py-1 text-xs text-white bg-wedo-cyan rounded hover:bg-wedo-cyan/90"
                >
                  Confirmar ajuste
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Benchmark */}
      {d.benchmark && (
        <div className="p-2.5 rounded-md bg-wedo-cyan/5 border border-wedo-cyan/20">
          <p className="text-[10px] font-medium text-wedo-cyan-text">Benchmark de mercado</p>
          <div className="mt-1 space-y-0.5">
            {Object.entries(d.benchmark).map(([key, val]) => (
              <div key={key} className="flex items-center justify-between text-xs">
                <span className="text-lia-text-secondary capitalize">{key.replace(/_/g, " ")}</span>
                <span className="text-lia-text-primary font-medium">
                  {typeof val === "number"
                    ? `${currency} ${val.toLocaleString("pt-BR")}`
                    : String(val)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {d.benefits?.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 mb-1.5">
            <Gift className="w-4 h-4 text-wedo-cyan" />
            <span className="text-xs font-medium text-lia-text-secondary">Benefícios</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {d.benefits.map((b, i) => {
              const label = typeof b === "string" ? b : (b as Record<string, unknown>).name as string
              return (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-lia-bg-secondary border border-lia-border-subtle text-micro text-lia-text-primary"
                >
                  {label}
                  <button
                    onClick={() => {
                      const next = d.benefits.filter((_, j) => j !== i)
                      onUpdate?.({ benefits: next })
                    }}
                    className="text-lia-text-disabled hover:text-status-error transition-colors ml-0.5"
                    aria-label={`Remover ${label}`}
                  >
                    <X className="w-2.5 h-2.5" />
                  </button>
                </span>
              )
            })}
          </div>
        </div>
      )}

      {d.variable_compensation && d.variable_compensation.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 mb-1.5">
            <TrendingUp className="w-4 h-4 text-wedo-cyan" />
            <span className="text-xs font-medium text-lia-text-secondary">Remuneração Variável</span>
          </div>
          <div className="space-y-1">
            {d.variable_compensation.map((vc, i) => (
              <div
                key={i}
                className="flex items-center justify-between px-2.5 py-1.5 rounded-md bg-lia-bg-secondary border border-lia-border-subtle"
              >
                <span className="text-xs text-lia-text-primary font-medium">{vc.name}</span>
                <div className="flex items-center gap-1.5 ml-2">
                  {(vc.target_pct || vc.min_pct) && (
                    <span className="text-micro text-wedo-cyan-text">
                      {vc.target_pct ? `${vc.target_pct}%` : `${vc.min_pct}–${vc.max_pct}%`}
                    </span>
                  )}
                  {vc.min_amount && (
                    <span className="text-micro text-wedo-cyan-text">
                      {`R$ ${vc.min_amount.toLocaleString("pt-BR")}`}
                      {vc.max_amount ? `–${vc.max_amount.toLocaleString("pt-BR")}` : ""}
                    </span>
                  )}
                  <button
                    onClick={() => {
                      const next = d.variable_compensation!.filter((_, j) => j !== i)
                      onUpdate?.({ variable_compensation: next })
                    }}
                    className="text-lia-text-disabled hover:text-status-error transition-colors"
                    aria-label={`Remover ${vc.name}`}
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
