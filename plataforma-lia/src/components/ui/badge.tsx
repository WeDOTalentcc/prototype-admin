import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-gray-100 dark:bg-lia-bg-elevated text-lia-text-primary dark:text-lia-text-primary hover:bg-gray-200 dark:hover:bg-gray-600",
        secondary:
          "border-transparent bg-gray-100 dark:bg-lia-bg-elevated text-lia-text-secondary dark:text-lia-text-secondary hover:bg-gray-200 dark:hover:bg-gray-600",
        destructive:
          "border-transparent bg-status-error/15 dark:bg-status-error/20 text-status-error hover:bg-status-error/25",
        outline: "border-lia-border-default dark:border-lia-border-default text-lia-text-primary dark:text-lia-text-primary hover:bg-gray-50 dark:hover:bg-gray-700",
        success: "border-transparent bg-wedo-green/15 text-wedo-green dark:bg-wedo-green/20 dark:text-wedo-green",
        warning: "border-transparent bg-wedo-orange/15 text-wedo-orange dark:bg-wedo-orange/20 dark:text-wedo-orange",
        info: "border-transparent bg-wedo-cyan/15 text-wedo-cyan-dark dark:bg-wedo-cyan/20 dark:text-wedo-cyan",
        danger: "border-transparent bg-status-error/15 text-status-error dark:bg-status-error/20 dark:text-status-error",
        lilac: "border-transparent bg-wedo-purple/15 text-wedo-purple dark:bg-wedo-purple/20 dark:text-wedo-purple",
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

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
