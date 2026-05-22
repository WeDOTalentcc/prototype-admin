"use client"

import * as React from "react"
import { kanbanChipStyles } from "@/lib/design-tokens"
import { cn } from "@/lib/utils"

export type ChipDensity = "comfortable" | "compact" | "relaxed"

export type ChipVariant =
  | "neutral"
  | "success"
  | "warning"
  | "danger"
  | "info"

export interface ChipProps extends React.HTMLAttributes<HTMLSpanElement> {
  density?: ChipDensity
  variant?: ChipVariant
  muted?: boolean
}

/**
 * Canonical pill/badge used across the platform. Wraps `kanbanChipStyles`
 * so the chip visual language stays in sync with the kanban canonical chip.
 *
 * Densities:
 * - `comfortable` (default): tables, modals, summary cards (10px).
 * - `compact`: dense lists, kanban candidate cards (10px tight leading).
 * - `relaxed`: modals, previews, detail cards onde 10px era apertado (12px).
 *
 * Variants follow the semantic palette (neutral/success/warning/danger/info)
 * and respect light/dark tokens automatically.
 */
export const Chip = React.forwardRef<HTMLSpanElement, ChipProps>(function Chip(
  { density = "comfortable", variant = "neutral", muted = false, className, children, ...rest },
  ref,
) {
  return (
    <span
      ref={ref}
      className={cn(
        kanbanChipStyles.base,
        kanbanChipStyles.size[density],
        kanbanChipStyles.variant[variant],
        muted && kanbanChipStyles.muted,
        className,
      )}
      {...rest}
    >
      {children}
    </span>
  )
})

Chip.displayName = "Chip"

export default Chip
