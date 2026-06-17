"use client"

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

/**
 * Metric — KPI numérico canônico (Fundação DS).
 *
 * Padrão ÚNICO para qualquer número/KPI exibido na plataforma:
 * fonte de dados Inter (`font-data`) + `tabular-nums` (alinhamento de dígitos).
 * Resolve a divergência recorrente em Consumo/Compliance, onde KPIs usavam
 * `font-sans` (Open Sans) ou nenhuma fonte numérica padrão.
 *
 * Use também `textStyles.metric*`/`textStyles.kpi*` quando precisar só da
 * className (ex.: aplicar em um <span> existente).
 *
 * Uso:
 *   <Metric value="1.284" label="Candidatos" size="lg" />
 *   <Metric value={`${pct}%`} label="Taxa de conversão" hint="últimos 30 dias" />
 */
const metricValueVariants = cva(
  "font-data tabular-nums text-lia-text-primary leading-none",
  {
    variants: {
      size: {
        sm: "text-sm font-medium",
        md: "text-lg font-semibold",
        lg: "text-2xl font-semibold",
        xl: "text-4xl font-bold",
      },
    },
    defaultVariants: {
      size: "md",
    },
  },
)

export interface MetricProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, "children">,
    VariantProps<typeof metricValueVariants> {
  /** O valor numérico já formatado (string ou número). */
  value: React.ReactNode
  /** Rótulo descritivo abaixo do valor. */
  label?: React.ReactNode
  /** Texto auxiliar abaixo do rótulo (cinza secundário). */
  hint?: React.ReactNode
  /** Slot opcional à direita do valor (ex.: badge de variação). */
  trailing?: React.ReactNode
}

export const Metric = React.forwardRef<HTMLDivElement, MetricProps>(
  function Metric(
    { value, label, hint, trailing, size = "md", className, ...rest },
    ref,
  ) {
    return (
      <div ref={ref} className={cn("space-y-0.5", className)} {...rest}>
        <div className="flex items-baseline gap-1.5">
          <span className={cn(metricValueVariants({ size }))}>{value}</span>
          {trailing ? <span className="shrink-0">{trailing}</span> : null}
        </div>
        {label ? (
          <p className="text-xs font-medium text-lia-text-secondary">{label}</p>
        ) : null}
        {hint ? (
          <p className="text-micro text-lia-text-tertiary">{hint}</p>
        ) : null}
      </div>
    )
  },
)

Metric.displayName = "Metric"

export { metricValueVariants }
export default Metric
