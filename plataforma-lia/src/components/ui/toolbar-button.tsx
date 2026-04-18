"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

export interface ToolbarButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  size?: "sm" | "md"
  active?: boolean
  icon?: React.ReactNode
  trailing?: React.ReactNode
}

const SIZE_CLASSES = {
  sm: "h-7 px-3 text-xs gap-1.5",
  md: "h-8 px-4 text-xs gap-2",
} as const

export const ToolbarButton = React.forwardRef<HTMLButtonElement, ToolbarButtonProps>(
  ({ className, size = "md", active = false, icon, trailing, children, type, ...rest }, ref) => {
    return (
      <button
        ref={ref}
        type={type ?? "button"}
        aria-pressed={active}
        className={cn(
          "inline-flex items-center justify-center font-medium rounded-full transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/20 dark:focus-visible:ring-lia-border-subtle/20 disabled:opacity-50 disabled:cursor-not-allowed",
          SIZE_CLASSES[size],
          active
            ? "bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:bg-lia-bg-secondary dark:hover:bg-lia-interactive-active"
            : "bg-lia-bg-primary text-lia-text-primary border border-lia-border-subtle dark:bg-lia-bg-secondary dark:border-lia-border-default hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse",
          className,
        )}
        {...rest}
      >
        {icon ? <span className="inline-flex items-center [&>svg]:w-3.5 [&>svg]:h-3.5" aria-hidden="true">{icon}</span> : null}
        <span>{children}</span>
        {trailing ? <span className="inline-flex items-center" aria-hidden="true">{trailing}</span> : null}
      </button>
    )
  },
)
ToolbarButton.displayName = "ToolbarButton"
