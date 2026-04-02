import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md !text-xs font-medium transition-opacity duration-200 focus-visible:outline-none focus:outline-none disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        primary: "bg-gray-900 text-white hover:bg-gray-800 dark:hover:bg-gray-200 focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20",
        destructive:
          "bg-status-error text-white hover:bg-status-error dark:bg-status-error dark:hover:bg-status-error focus:ring-2 focus:ring-red-600/20",
        outline:
          "border border-lia-border-default bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary hover:bg-lia-interactive-hover hover:text-lia-text-primary focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20",
        secondary:
          "bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary hover:bg-lia-interactive-active focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20",
        ghost: "text-lia-text-primary hover:bg-lia-interactive-hover hover:text-lia-text-primary focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20",
        link: "text-lia-text-secondary dark:text-lia-text-secondary underline-offset-4 hover:underline hover:text-lia-text-primary dark:hover:lia-text-subtle focus:text-lia-text-primary dark:focus:text-lia-text-inverse",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
