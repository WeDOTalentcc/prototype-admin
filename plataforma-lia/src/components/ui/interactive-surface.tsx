import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const interactiveSurfaceVariants = cva(
  "transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-text-primary/20 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        accordion:
          "w-full flex items-center justify-between text-left bg-lia-bg-primary hover:bg-lia-bg-secondary",
        "card-toggle": "text-left",
      },
    },
    defaultVariants: {
      variant: "accordion",
    },
  }
)

export interface InteractiveSurfaceProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof interactiveSurfaceVariants> {}

const InteractiveSurface = React.forwardRef<HTMLButtonElement, InteractiveSurfaceProps>(
  ({ className, variant, type = "button", ...props }, ref) => {
    return (
      <button
        ref={ref}
        type={type}
        data-ds-surface={variant ?? "accordion"}
        className={cn(interactiveSurfaceVariants({ variant }), className)}
        {...props}
      />
    )
  }
)
InteractiveSurface.displayName = "InteractiveSurface"

export { InteractiveSurface, interactiveSurfaceVariants }
