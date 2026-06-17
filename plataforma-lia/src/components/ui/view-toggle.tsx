"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { toolbarStyles } from "@/lib/design-tokens"

export interface ViewToggleOption<T extends string = string> {
  value: T
  label?: string
  icon?: React.ComponentType<{ className?: string }>
  ariaLabel?: string
  title?: string
}

export interface ViewToggleProps<T extends string = string>
  extends Omit<React.HTMLAttributes<HTMLDivElement>, "onChange"> {
  value: T
  onChange: (value: T) => void
  options: ReadonlyArray<ViewToggleOption<T>>
  size?: "sm" | "md"
  iconOnly?: boolean
  ariaLabel?: string
}

export function ViewToggle<T extends string = string>({
  value,
  onChange,
  options,
  size = "md",
  iconOnly = false,
  ariaLabel,
  className,
  ...rest
}: ViewToggleProps<T>) {
  return (
    <div
      role="group"
      aria-label={ariaLabel}
      className={cn(
        toolbarStyles.viewToggleContainer,
        toolbarStyles.viewToggleContainerPad[size],
        className,
      )}
      {...rest}
    >
      {options.map((opt) => {
        const Icon = opt.icon
        const isActive = opt.value === value
        const hasLabel = !iconOnly && Boolean(opt.label)
        const sizeClass = iconOnly
          ? toolbarStyles.viewToggleItemSize[size === "sm" ? "iconSm" : "iconMd"]
          : toolbarStyles.viewToggleItemSize[size]
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            aria-pressed={isActive}
            aria-label={opt.ariaLabel ?? opt.label}
            title={opt.title ?? opt.label}
            className={cn(
              toolbarStyles.viewToggleItemBase,
              sizeClass,
              isActive ? toolbarStyles.viewToggleItemActive : toolbarStyles.viewToggleItemInactive,
            )}
          >
            {Icon ? (
              <Icon className={toolbarStyles.viewToggleIcon[size]} aria-hidden="true" />
            ) : null}
            {hasLabel ? <span>{opt.label}</span> : null}
          </button>
        )
      })}
    </div>
  )
}
