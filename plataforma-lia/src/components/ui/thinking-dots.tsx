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
export function ThinkingDots({ dotClassName = "bg-lia-text-tertiary", size = "md", className }: ThinkingDotsProps) {
  const sizeClass = size === "sm" ? "w-1 h-1" : size === "lg" ? "w-2 h-2" : "w-1.5 h-1.5"
  return (
    <div className={cn("flex items-center gap-1", className)}>
      {[0, 150, 300].map((delay, i) => (
        <span
          key={i}
          className={cn("rounded-full animate-bounce motion-reduce:animate-none", sizeClass, dotClassName)}
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </div>
  )
}
