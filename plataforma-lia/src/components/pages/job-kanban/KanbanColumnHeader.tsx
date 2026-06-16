"use client"

import React from "react"
import { kanbanColumnHeaderStyles } from "@/lib/design-tokens"

export type KanbanColumnHeaderWidth = "sm" | "md"

export interface KanbanColumnHeaderProps {
  title: string
  count: number
  subtitle?: string
  /** Tailwind class for the accent dot (preferred, DS token). */
  accentClass?: string
  /** Legacy fallback when only a hex/rgb color is available. */
  accentColor?: string
  /**
   * Visual density:
   * - `md` (default): roomier, used by the jobs kanban (vagas).
   * - `sm`: denser, used by the candidates kanban inside a job.
   */
  width?: KanbanColumnHeaderWidth
  /** Extras rendered inline next to the count (menu, saturation badge, etc.). */
  inlineExtras?: React.ReactNode
  /** Trailing slot rendered on the right (icon buttons, checkbox, etc.). */
  actions?: React.ReactNode
  /** Optional ring/scale effect on the dot when the column is being targeted by drag. */
  isDropping?: boolean
  className?: string
}

export function KanbanColumnHeader({
  title,
  count,
  subtitle,
  accentClass,
  accentColor,
  width = "md",
  inlineExtras,
  actions,
  isDropping = false,
  className = "",
}: KanbanColumnHeaderProps) {
  const s = kanbanColumnHeaderStyles
  const dotSize = s.dotSize[width]
  const titleClass = s.title[width]
  const padding = s.padding[width]
  const gap = s.titleGap[width]

  return (
    <div
      className={`flex-shrink-0 ${padding} ${className}`}
      data-testid="kanban-column-header"
    >
      <div className="flex items-center justify-between gap-2">
        <div className={`flex items-center ${gap} min-w-0`}>
          <span
            className={`${dotSize} rounded-full transition-transform motion-reduce:transition-none duration-300 ${
              accentClass ?? ""
            } ${isDropping ? "scale-150" : ""}`}
            style={accentClass ? undefined : { backgroundColor: accentColor }}
            aria-hidden="true"
          />
          <h3 className={`${titleClass} truncate`}>{title}</h3>
          <span className={s.count[width]}>{count}</span>
          {inlineExtras}
        </div>
        {actions && (
          <div className="flex items-center gap-1 flex-shrink-0">{actions}</div>
        )}
      </div>
      {subtitle && (
        <p className={s.subtitle}>{subtitle}</p>
      )}
    </div>
  )
}
