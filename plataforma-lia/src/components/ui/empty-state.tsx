"use client"

import React from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import type { ReactNode } from "react"

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
  className?: string
}

export const EmptyState = React.memo(function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-12 px-6 text-center",
        className
      )}
    >
      {icon && (
        <div className="mb-4 text-lia-text-tertiary [&>svg]:w-10 [&>svg]:h-10">
          {icon}
        </div>
      )}
      <p className="text-sm font-medium text-lia-text-secondary mb-1">
        {title}
      </p>
      {description && (
        <p className="text-xs text-lia-text-tertiary max-w-xs mb-4">
          {description}
        </p>
      )}
      {action && (
        <Button
          variant="outline"
          size="sm"
          onClick={action.onClick}
          className="mt-2 rounded-lg text-xs hover:bg-lia-interactive-hover transition-colors cursor-pointer"
        >
          {action.label}
        </Button>
      )}
    </div>
  )
})
EmptyState.displayName = 'EmptyState'
