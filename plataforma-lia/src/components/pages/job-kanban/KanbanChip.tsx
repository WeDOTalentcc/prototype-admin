"use client"

import * as React from "react"
import { kanbanChipStyles } from "@/lib/design-tokens"
import { cn } from "@/lib/utils"
import type { KanbanCardDensity } from "./KanbanCardShell"

export interface KanbanChipProps
  extends React.HTMLAttributes<HTMLSpanElement> {
  density: KanbanCardDensity
  /** Renders the chip with the muted text token. */
  muted?: boolean
}

/**
 * Canonical chip used inside <KanbanCardShell />. Matches the `comfortable`
 * (jobs) and `compact` (candidates) densities so chips visually align with
 * the card around them. Composition: pill, outlined, secondary text.
 */
export const KanbanChip = React.forwardRef<HTMLSpanElement, KanbanChipProps>(
  function KanbanChip(
    { density, muted = false, className, children, ...rest },
    ref,
  ) {
    return (
      <span
        ref={ref}
        className={cn(
          kanbanChipStyles.base,
          kanbanChipStyles.size[density],
          muted && kanbanChipStyles.muted,
          className,
        )}
        {...rest}
      >
        {children}
      </span>
    )
  },
)
