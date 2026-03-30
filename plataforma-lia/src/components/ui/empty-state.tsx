"use client"

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

export function EmptyState({
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
        <div className="mb-4 text-gray-300 [&>svg]:w-10 [&>svg]:h-10">
          {icon}
        </div>
      )}
      <p className="text-sm font-medium text-gray-700 dark:text-lia-text-secondary mb-1">
        {title}
      </p>
      {description && (
        <p className="text-xs text-gray-500 dark:text-lia-text-tertiary max-w-xs mb-4">
          {description}
        </p>
      )}
      {action && (
        <Button
          variant="outline"
          size="sm"
          onClick={action.onClick}
          className="mt-2 rounded-md text-xs"
        >
          {action.label}
        </Button>
      )}
    </div>
  )
}
