import React from "react"
import { cn } from "@/lib/utils"

export interface TabSectionHeaderProps {
  title: React.ReactNode
  subtitle?: React.ReactNode
  icon?: React.ReactNode
  count?: number
  actions?: React.ReactNode
  className?: string
  /**
   * id aplicado ao <h2> do cabeçalho. Permite que um container externo o
   * referencie via aria-labelledby (ex.: <section aria-labelledby={id}>).
   */
  headingId?: string
}

export function TabSectionHeader({
  title,
  subtitle,
  icon,
  count,
  actions,
  className,
  headingId,
}: TabSectionHeaderProps) {
  const hasActions = actions !== undefined && actions !== null && actions !== false
  return (
    <div
      className={cn(
        hasActions ? "flex items-center justify-between" : undefined,
        className,
      )}
    >
      <div>
        <h2 id={headingId} className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
          {icon}
          <span>{title}</span>
          {typeof count === "number" && count > 0 && (
            <span className="ml-2 px-2 py-0.5 rounded-full text-[10px] font-bold bg-lia-interactive-active text-lia-text-primary">
              {count}
            </span>
          )}
        </h2>
        {subtitle && (
          <p className="text-xs text-lia-text-secondary mt-0.5">{subtitle}</p>
        )}
      </div>
      {hasActions && <div>{actions}</div>}
    </div>
  )
}

export default TabSectionHeader
