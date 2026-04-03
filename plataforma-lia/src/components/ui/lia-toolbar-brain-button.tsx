"use client"

import { Brain } from "lucide-react"
import { cn } from "@/lib/utils"

interface LIAToolbarBrainButtonProps {
  isOpen: boolean
  onClick: () => void
  isThinking?: boolean
  className?: string
}

export function LIAToolbarBrainButton({
  isOpen,
  onClick,
  isThinking = false,
  className,
}: LIAToolbarBrainButtonProps) {
  return (
    <button
      onClick={onClick}
      aria-label="Conversar com LIA"
      aria-pressed={isOpen}
      title="Conversar com LIA"
      className={cn(
        "relative flex items-center justify-center w-9 h-9 rounded-lg",
        "transition-all duration-200 motion-reduce:transition-none",
        "hover:bg-lia-bg-tertiary",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/30",
        isOpen && "bg-lia-bg-tertiary",
        className
      )}
    >
      <Brain
        className={cn(
          "w-5 h-5 transition-all duration-200 motion-reduce:transition-none",
          isOpen
            ? "text-wedo-cyan drop-shadow-lia-md scale-110"
            : "text-wedo-cyan hover:drop-shadow-lia-sm"
        )}
        strokeWidth={2}
      />
      {isThinking && (
        <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-wedo-cyan animate-pulse motion-reduce:animate-none" />
      )}
    </button>
  )
}
