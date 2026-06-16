import * as React from "react"
import { cn } from "@/lib/utils"

export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
 "flex min-h-20 w-full rounded-md border border-lia-border-default bg-lia-bg-primary dark:bg-lia-bg-elevated px-3 py-2 text-xs text-lia-text-primary placeholder:text-lia-text-secondary dark:placeholder:text-lia-text-disabled focus:outline-none focus:border-lia-border-medium focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Textarea.displayName = "Textarea"

export { Textarea }
