"use client"

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

/**
 * StatusPill — pílula de status canônica (Fundação DS).
 *
 * `rounded-full` + tokens semânticos `status-*` (e `wedo-cyan` para info/IA).
 * Resolve o desvio recorrente nos hubs: chips de status com cores cruas do
 * Tailwind (`bg-emerald-50 text-emerald-700`, `bg-amber-100`, `bg-red-200`…) e
 * raios inconsistentes.
 *
 * Acessibilidade (daltonismo): use SEMPRE ícone + cor + texto. Passe um ícone
 * via prop `icon`, ou ative o ponto indicador com `withDot`.
 *
 * Uso:
 *   <StatusPill status="success" withDot>Ativo</StatusPill>
 *   <StatusPill status="warning" icon={<Clock className="h-3 w-3" />}>Pendente</StatusPill>
 */
const statusPillVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-micro font-medium whitespace-nowrap",
  {
    variants: {
      status: {
        success:
          "bg-status-success/10 text-status-success border-status-success/20 dark:bg-status-success/20",
        error:
          "bg-status-error/10 text-status-error border-status-error/20 dark:bg-status-error/20",
        warning:
          "bg-status-warning/10 text-status-warning border-status-warning/20 dark:bg-status-warning/20",
        info: "bg-wedo-cyan/10 text-lia-text-secondary border-wedo-cyan/20",
        neutral:
          "bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-subtle dark:bg-lia-bg-elevated dark:text-lia-text-secondary",
      },
    },
    defaultVariants: {
      status: "neutral",
    },
  },
)

const dotColors: Record<NonNullable<VariantProps<typeof statusPillVariants>["status"]>, string> = {
  success: "bg-status-success",
  error: "bg-status-error",
  warning: "bg-status-warning",
  info: "bg-wedo-cyan",
  neutral: "bg-lia-text-tertiary",
}

export interface StatusPillProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof statusPillVariants> {
  /** Ícone à esquerda do texto (recomendado para acessibilidade). */
  icon?: React.ReactNode
  /** Mostra um ponto colorido como indicador de status. */
  withDot?: boolean
}

export const StatusPill = React.forwardRef<HTMLSpanElement, StatusPillProps>(
  function StatusPill(
    { status = "neutral", icon, withDot, className, children, ...rest },
    ref,
  ) {
    return (
      <span
        ref={ref}
        className={cn(statusPillVariants({ status }), className)}
        {...rest}
      >
        {withDot ? (
          <span
            aria-hidden="true"
            className={cn(
              "h-1.5 w-1.5 shrink-0 rounded-full",
              dotColors[status ?? "neutral"],
            )}
          />
        ) : null}
        {icon ? (
          <span aria-hidden="true" className="inline-flex shrink-0">
            {icon}
          </span>
        ) : null}
        {children}
      </span>
    )
  },
)

StatusPill.displayName = "StatusPill"

export { statusPillVariants }
export default StatusPill
