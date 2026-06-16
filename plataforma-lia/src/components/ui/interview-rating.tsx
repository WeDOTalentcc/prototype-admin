"use client"

import * as React from "react"
import { Star } from "lucide-react"
import { cn } from "@/lib/utils"

type LikertValue =
  | "insatisfatorio"
  | "abaixo_esperado"
  | "esperado"
  | "acima_esperado"
  | "excelente"

interface StarRatingProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, "onChange"> {
  value: number | null
  onChange: (value: number) => void
  disabled?: boolean
  size?: "sm" | "md" | "lg"
}

interface LikertRatingProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, "onChange"> {
  value: LikertValue | null
  onChange: (value: LikertValue) => void
  disabled?: boolean
  size?: "sm" | "md" | "lg"
}

// StarRating Component
const StarRating = React.forwardRef<HTMLDivElement, StarRatingProps>(
  (
    { className, value, onChange, disabled = false, size = "md", ...props },
    ref
  ) => {
    const sizeClasses = {
      sm: "gap-1",
      md: "gap-2",
      lg: "gap-3",
    }

    const starSizeClasses = {
      sm: "h-4 w-4",
      md: "h-6 w-6",
      lg: "h-8 w-8",
    }

    return (
      <div
        ref={ref}
        className={cn("flex", sizeClasses[size], className)}
        role="group"
        aria-label="Star rating"
        {...props}
      >
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            onClick={() => !disabled && onChange(star)}
            disabled={disabled}
            aria-label={`${star} stars`}
            type="button"
            className={cn(
 "transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-lia-btn-primary-bg/20 rounded-sm disabled:pointer-events-none disabled:opacity-50",
              value !== null && star <= value
                ? "text-status-warning dark:text-status-warning"
                : "text-lia-text-disabled hover:text-status-warning dark:hover:text-status-warning"
            )}
          >
            <Star
              className={cn(
 "pointer-events-none shrink-0",
                starSizeClasses[size]
              )}
              fill={value !== null && star <= value ? "currentColor" : "none"}
              strokeWidth={2}
            />
          </button>
        ))}
      </div>
    )
  }
)
StarRating.displayName = "StarRating"

// LikertRating Component
const likertOptions = [
  { value: "insatisfatorio" as const, label: "Insatisfatório" },
  { value: "abaixo_esperado" as const, label: "Abaixo do Esperado" },
  { value: "esperado" as const, label: "Esperado" },
  { value: "acima_esperado" as const, label: "Acima do Esperado" },
  { value: "excelente" as const, label: "Excelente" },
]

const LikertRating = React.forwardRef<HTMLDivElement, LikertRatingProps>(
  (
    { className, value, onChange, disabled = false, size = "md", ...props },
    ref
  ) => {
    const sizeClasses = {
      sm: "gap-1",
      md: "gap-2",
      lg: "gap-3",
    }

    const buttonSizeClasses = {
      sm: "px-2 py-1 text-xs",
      md: "px-3 py-2 text-sm",
      lg: "px-4 py-3 text-base",
    }

    return (
      <div
        ref={ref}
        className={cn("flex flex-wrap", sizeClasses[size], className)}
        role="group"
        aria-label="Likert scale rating"
        {...props}
      >
        {likertOptions.map((option) => (
          <button
            key={option.value}
            onClick={() => !disabled && onChange(option.value)}
            disabled={disabled}
            type="button"
            className={cn(
 "rounded-md font-medium transition-opacity duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-lia-btn-primary-bg/20 disabled:pointer-events-none disabled:opacity-50 border whitespace-nowrap",
              buttonSizeClasses[size],
              value === option.value
                ? "bg-lia-btn-primary-bg text-lia-btn-primary-text border-lia-btn-primary-bg"
                : "border-lia-border-default bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary hover:border-lia-text-primary"
            )}
          >
            {option.label}
          </button>
        ))}
      </div>
    )
  }
)
LikertRating.displayName = "LikertRating"

export { StarRating, LikertRating }
