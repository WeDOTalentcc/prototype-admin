import { cn } from "@/lib/utils"

interface ThinkingDotsProps {
  dotClassName?: string
  size?: "sm" | "md" | "lg"
  className?: string
}

/**
 * Three-dot loading animation used across chat and AI-processing contexts.
 * Replaces inline animate-bounce patterns scattered across 11+ files.
 *
 * Usage:
 *   <ThinkingDots dotClassName="bg-wedo-cyan" />           // LIA chat contexts
 *   <ThinkingDots dotClassName="bg-lia-text-tertiary" />    // neutral contexts
 *   <ThinkingDots dotClassName="bg-lia-text-primary" size="sm" /> // settings
 */
export function ThinkingDots({ dotClassName, size, className }: ThinkingDotsProps) {
  return (
    <span className={cn("inline animate-pulse motion-reduce:animate-none text-inherit font-normal", className)}
      aria-hidden="true"
    >…</span>
  )
}
