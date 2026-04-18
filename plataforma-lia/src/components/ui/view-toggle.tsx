"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

export interface ViewToggleOption<T extends string = string> {
  value: T
  label: string
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
  ariaLabel?: string
}

const SIZE_CLASSES = {
  sm: {
    container: "p-0.5 gap-0.5",
    button: "h-6 px-2 text-xs gap-1",
    icon: "w-3 h-3",
  },
  md: {
    container: "p-0.5 gap-0.5",
    button: "h-7 px-2.5 text-xs gap-1.5",
    icon: "w-3.5 h-3.5",
  },
} as const

export function ViewToggle<T extends string = string>({
  value,
  onChange,
  options,
  size = "md",
  ariaLabel,
  className,
  ...rest
}: ViewToggleProps<T>) {
  const sz = SIZE_CLASSES[size]
  return (
    <div
      role="group"
      aria-label={ariaLabel}
      className={cn(
        "inline-flex items-center bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-lg",
        sz.container,
        className,
      )}
      {...rest}
    >
      {options.map((opt) => {
        const Icon = opt.icon
        const isActive = opt.value === value
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            aria-pressed={isActive}
            aria-label={opt.ariaLabel ?? opt.label}
            title={opt.title ?? opt.label}
            className={cn(
              "inline-flex items-center justify-center rounded-md font-medium transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/20 dark:focus-visible:ring-lia-border-subtle/20",
              sz.button,
              isActive
                ? "bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary shadow-sm"
                : "text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse",
            )}
          >
            {Icon ? <Icon className={sz.icon} aria-hidden="true" /> : null}
            <span>{opt.label}</span>
          </button>
        )
      })}
    </div>
  )
}
