"use client"

import * as React from "react"
import { kanbanColumnShellStyles } from "@/lib/design-tokens"
import { cn } from "@/lib/utils"

export type KanbanColumnDensity = "comfortable" | "compact"

export interface KanbanColumnShellProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, "children"> {
  density: KanbanColumnDensity
  /** Header node (typically a <KanbanColumnHeader />). */
  header: React.ReactNode
  /** Body node (list of cards, scroll area, drop target). */
  children: React.ReactNode
  /** Visual ring/tint while a drag-and-drop is targeting this column. */
  isDropping?: boolean
}

/**
 * Canonical kanban column container shared by jobs (`comfortable`) and
 * candidates (`compact`).
 *
 * Owns: width per density, surface (background + border + radius +
 * dark mode), preferred height, and the drop-state ring/tint. Header
 * and body are passed as slots so callers can keep their existing
 * scroll/drop semantics inside.
 */
export const KanbanColumnShell = React.forwardRef<HTMLDivElement, KanbanColumnShellProps>(
  function KanbanColumnShell(
    { density, header, children, isDropping = false, className, ...rest },
    ref,
  ) {
    return (
      <div
        ref={ref}
        className={cn(
          kanbanColumnShellStyles.base,
          kanbanColumnShellStyles.width[density],
          kanbanColumnShellStyles.height[density],
          isDropping && kanbanColumnShellStyles.dropping,
          className,
        )}
        {...rest}
      >
        {header}
        {children}
      </div>
    )
  },
)
