"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { FlaskConical } from "lucide-react"

export interface BetaBadgeProps {
  label?: string
  size?: "sm" | "md"
  className?: string
}

export const BetaBadge = React.memo(function BetaBadge({
  label = "BETA",
  size = "sm",
  className,
}: BetaBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full font-semibold border border-transparent",
        "bg-wedo-purple/15 text-wedo-purple dark:bg-wedo-purple/20 dark:text-wedo-purple",
        size === "sm" && "px-1.5 py-0.5 text-[9px]",
        size === "md" && "px-2 py-0.5 text-[10px]",
        className,
      )}
    >
      <FlaskConical
        className={cn(
          "flex-shrink-0",
          size === "sm" ? "w-2 h-2" : "w-2.5 h-2.5",
        )}
      />
      {label}
    </span>
  )
})
BetaBadge.displayName = "BetaBadge"
