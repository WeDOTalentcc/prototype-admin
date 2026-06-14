"use client"

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import {
  AlertTriangle,
  CheckCircle2,
  Info,
  XCircle,
  type LucideIcon,
} from "lucide-react"
import { cn } from "@/lib/utils"

/**
 * Callout — bloco de alerta/aviso de status canônico (Fundação DS).
 *
 * Container `rounded-md` com fundo/borda/ícone derivados dos tokens `status-*`
 * (e `wedo-cyan` para info). Resolve o desvio recorrente nos hubs: blocos de
 * aviso com cores cruas do Tailwind (`bg-amber-50 border-amber-200`,
 * `bg-blue-50`, `bg-red-50`…) e ícones sem cor semântica.
 *
 * Uso:
 *   <Callout variant="warning" title="Configuração incompleta">
 *     Preencha os benefícios antes de publicar a vaga.
 *   </Callout>
 *
 *   <Callout variant="success">Política salva com sucesso.</Callout>
 */
const calloutVariants = cva(
  "flex gap-2.5 rounded-md border p-3 text-xs text-lia-text-primary",
  {
    variants: {
      variant: {
        success: "bg-status-success/10 border-status-success/20",
        warning: "bg-status-warning/10 border-status-warning/20",
        error: "bg-status-error/10 border-status-error/20",
        info: "bg-wedo-cyan/10 border-wedo-cyan/20",
        neutral: "bg-lia-bg-tertiary border-lia-border-subtle dark:bg-lia-bg-elevated",
      },
    },
    defaultVariants: {
      variant: "neutral",
    },
  },
)

type CalloutVariant = NonNullable<VariantProps<typeof calloutVariants>["variant"]>

const variantIcon: Record<CalloutVariant, LucideIcon> = {
  success: CheckCircle2,
  warning: AlertTriangle,
  error: XCircle,
  info: Info,
  neutral: Info,
}

const variantIconColor: Record<CalloutVariant, string> = {
  success: "text-status-success",
  warning: "text-status-warning",
  error: "text-status-error",
  info: "text-lia-text-secondary dark:text-wedo-cyan",
  neutral: "text-lia-text-secondary",
}

export interface CalloutProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, "title">,
    VariantProps<typeof calloutVariants> {
  /** Título opcional em negrito acima do conteúdo. */
  title?: React.ReactNode
  /** Substitui o ícone padrão da variante. Passe `null` para ocultar. */
  icon?: React.ReactNode
}

export const Callout = React.forwardRef<HTMLDivElement, CalloutProps>(
  function Callout(
    { variant = "neutral", title, icon, className, children, ...rest },
    ref,
  ) {
    const resolved = variant ?? "neutral"
    const Icon = variantIcon[resolved]
    const showIcon = icon !== null
    return (
      <div
        ref={ref}
        role="status"
        className={cn(calloutVariants({ variant }), className)}
        {...rest}
      >
        {showIcon ? (
          <span aria-hidden="true" className="mt-0.5 shrink-0">
            {icon ?? <Icon className={cn("h-4 w-4", variantIconColor[resolved])} />}
          </span>
        ) : null}
        <div className="min-w-0 space-y-0.5">
          {title ? (
            <p className="font-semibold text-lia-text-primary">{title}</p>
          ) : null}
          {children ? (
            <div className="text-lia-text-secondary">{children}</div>
          ) : null}
        </div>
      </div>
    )
  },
)

Callout.displayName = "Callout"

export { calloutVariants }
export default Callout
