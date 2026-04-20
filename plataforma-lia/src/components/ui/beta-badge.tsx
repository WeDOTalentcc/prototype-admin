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
        "inline-flex items-center gap-0.5 rounded-full font-semibold tracking-wide leading-none",
        "bg-wedo-purple text-white",
        size === "sm" && "px-1.5 py-[1px] text-[8px]",
        size === "md" && "px-2 py-0.5 text-[10px]",
        className,
      )}
    >
      {size === "md" && (
        <FlaskConical className="w-2.5 h-2.5 flex-shrink-0" />
      )}
      {label}
    </span>
  )
})
BetaBadge.displayName = "BetaBadge"
