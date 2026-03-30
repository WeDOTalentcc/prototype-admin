import * as React from "react"
import { cn } from "@/lib/utils"

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
 "flex h-10 w-full rounded-md border border-lia-border-default dark:border-lia-border-default bg-white dark:bg-lia-bg-elevated px-3 py-2 text-xs text-lia-text-primary placeholder:text-lia-text-secondary dark:placeholder:text-lia-text-disabled focus:outline-none focus:border-gray-500 focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }
