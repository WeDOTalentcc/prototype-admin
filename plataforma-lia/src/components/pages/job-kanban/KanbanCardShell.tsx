"use client"

import * as React from "react"
import { kanbanCardStyles } from "@/lib/design-tokens"
import { cn } from "@/lib/utils"

export type KanbanCardDensity = "comfortable" | "compact"

export interface KanbanCardShellProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, "children"> {
  density: KanbanCardDensity
  /**
   * Tailwind class for the colored 4px left accent (e.g.
   * `border-l-status-success`). When omitted, the card has a uniform border.
   */
  accentLeftClass?: string
  /** Optional ribbon rendered at the top before the body (e.g. "Action Required"). */
  ribbon?: React.ReactNode
  /** Optional footer rendered after the body. */
  footer?: React.ReactNode
  /**
   * Whether the shell adds the canonical top divider above the footer.
   * Set to `false` when the footer node already brings its own border/background.
   * @default true
   */
  footerDivider?: boolean
  /** Pulsing animation while a drop is in progress. */
  isDropping?: boolean
  /** Children rendered inside the body container. */
  children: React.ReactNode
  /** Whether the card surface should react to hover (border tint + cursor). */
  interactive?: boolean
}

/**
 * Canonical kanban card container shared by jobs (`comfortable`) and
 * candidates (`compact`).
 *
 * Owns: surface (background + border + radius + dark mode), hover tint,
 * left accent stripe, optional ribbon, body padding, footer divider and
 * the pulse-on-drop animation. Slots remain free for callers to compose
 * the card content.
 */
export const KanbanCardShell = React.forwardRef<HTMLDivElement, KanbanCardShellProps>(
  function KanbanCardShell(
    {
      density,
      accentLeftClass,
      ribbon,
      footer,
      footerDivider = true,
      isDropping,
      interactive = true,
      className,
      style,
      children,
      ...rest
    },
    ref,
  ) {
    const accentClass = accentLeftClass ? `border-l-4 ${accentLeftClass}` : ""

    return (
      <div
        ref={ref}
        className={cn(
          kanbanCardStyles.shell,
          interactive && kanbanCardStyles.shellInteractive,
          accentClass,
          isDropping && "animate-pulse motion-reduce:animate-none",
          className,
        )}
        style={style}
        {...rest}
      >
        {ribbon ? <div className={kanbanCardStyles.ribbon}>{ribbon}</div> : null}

        <div className={kanbanCardStyles.body[density]}>{children}</div>

        {footer ? (
          footerDivider ? (
            <div className={cn(kanbanCardStyles.divider)}>{footer}</div>
          ) : (
            footer
          )
        ) : null}
      </div>
    )
  },
)
