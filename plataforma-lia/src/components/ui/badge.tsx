import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2 py-0.5 text-micro font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary hover:bg-lia-interactive-active",
        secondary:
          "border-transparent bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-secondary hover:bg-lia-interactive-active",
        destructive:
          "border-transparent bg-status-error/15 dark:bg-status-error/20 text-status-error hover:bg-status-error/25",
        outline: "border-lia-border-default text-lia-text-primary hover:bg-lia-interactive-hover",
        success: "border-transparent bg-wedo-green/15 text-lia-text-secondary dark:bg-wedo-green/20 dark:text-lia-text-secondary",
        warning: "border-transparent bg-wedo-orange/15 text-lia-text-secondary dark:bg-wedo-orange/20 dark:text-lia-text-secondary",
        info: "border-transparent bg-wedo-cyan/15 text-lia-text-secondary dark:bg-wedo-cyan/20 dark:text-lia-text-secondary",
        danger: "border-transparent bg-status-error/15 text-status-error dark:bg-status-error/20 dark:text-status-error",
        lilac: "border-transparent bg-wedo-purple/15 text-lia-text-secondary dark:bg-wedo-purple/20 dark:text-lia-text-secondary",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

const Badge = React.memo(function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
})
Badge.displayName = 'Badge'

export { Badge, badgeVariants }
