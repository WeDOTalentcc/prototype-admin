"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { toolbarStyles } from "@/lib/design-tokens"

export interface ToolbarButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  size?: "sm" | "md"
  active?: boolean
  icon?: React.ReactNode
  trailing?: React.ReactNode
}

export const ToolbarButton = React.forwardRef<HTMLButtonElement, ToolbarButtonProps>(
  ({ className, size = "md", active = false, icon, trailing, children, type, ...rest }, ref) => {
    return (
      <button
        ref={ref}
        type={type ?? "button"}
        aria-pressed={active}
        className={cn(
          toolbarStyles.toolbarBtnBase,
          toolbarStyles.toolbarBtnSize[size],
          active ? toolbarStyles.toolbarBtnActive : toolbarStyles.toolbarBtnDefault,
          className,
        )}
        {...rest}
      >
        {icon ? (
          <span
            className="inline-flex items-center [&>svg]:w-3.5 [&>svg]:h-3.5"
            aria-hidden="true"
          >
            {icon}
          </span>
        ) : null}
        <span>{children}</span>
        {trailing ? (
          <span className="inline-flex items-center" aria-hidden="true">
            {trailing}
          </span>
        ) : null}
      </button>
    )
  },
)
ToolbarButton.displayName = "ToolbarButton"
