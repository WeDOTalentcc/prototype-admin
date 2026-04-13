"use client"

import React from "react"
import { cn } from "@/lib/utils"
import { cardStyles } from "@/lib/design-tokens"

export function AgentCardSkeleton() {
  return (
    <div className={cn(cardStyles.default, "p-4 animate-pulse")}>
      <div className="flex items-start gap-2.5 mb-3">
        <div className="w-8 h-8 rounded-md bg-lia-bg-tertiary" />
        <div className="flex-1">
          <div className="h-4 w-24 bg-lia-bg-tertiary rounded mb-1.5" />
          <div className="flex gap-1">
            <div className="h-3 w-12 bg-lia-bg-tertiary rounded-full" />
            <div className="h-3 w-10 bg-lia-bg-tertiary rounded-full" />
          </div>
        </div>
      </div>
      <div className="h-3 w-full bg-lia-bg-tertiary rounded mb-2" />
      <div className="h-3 w-2/3 bg-lia-bg-tertiary rounded mb-3" />
      <div className="flex gap-4">
        <div className="h-3 w-16 bg-lia-bg-tertiary rounded" />
        <div className="h-3 w-16 bg-lia-bg-tertiary rounded" />
      </div>
    </div>
  )
}
