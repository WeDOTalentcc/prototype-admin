import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-gray-100 dark:bg-gray-700 text-gray-950 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600",
        secondary:
          "border-transparent bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600",
        destructive:
          "border-transparent bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200 hover:bg-red-200 dark:hover:bg-red-900/50",
        outline: "border-gray-300 dark:border-gray-600 text-gray-800 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700",
        success: "border-transparent bg-[rgba(123,194,154,0.15)] text-[#5aa078]",
        warning: "border-transparent bg-[rgba(232,168,124,0.15)] text-[#c58a5e]",
        info: "border-transparent bg-wedo-cyan/15 text-[#50a3b8]",
        danger: "border-transparent bg-[rgba(232,168,124,0.15)] text-[#c58a5e]",
        lilac: "border-transparent bg-[rgba(201,160,220,0.15)] text-[#a078b0]",
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
