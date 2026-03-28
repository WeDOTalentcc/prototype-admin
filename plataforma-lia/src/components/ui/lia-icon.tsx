import { Brain } from "lucide-react"
import { cn } from "@/lib/utils"

interface LIAIconProps {
  className?: string
  size?: "xs" | "sm" | "md" | "lg" | "xl"
  animate?: boolean
  speaking?: boolean
  useChatCyan?: boolean
}

function SoundWaveBars({ size }: { size: string }) {
  const barHeight = size === "xs" ? "h-2" : size === "sm" ? "h-3" : "h-4"
  return (
    <div className="absolute inset-0 flex items-center justify-center gap-0.5">
      {[0, 1, 2, 3].map((i) => (
        <span
          key={i}
          className={cn(
            "inline-block w-0.5 rounded-full bg-chat-cyan lia-sound-wave-bar",
            barHeight
          )}
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  )
}

export function LIAIcon({ className, size = "md", animate = false, speaking = false, useChatCyan = false }: LIAIconProps) {
  const sizeClasses = {
    xs: "w-3.5 h-3.5",
    sm: "w-7 h-7",
    md: "w-9 h-9",
    lg: "w-10 h-10",
    xl: "w-12 h-12"
  }

  return (
    <div className={cn(
      "relative inline-flex items-center justify-center rounded-full",
      animate && "animate-pulse",
      speaking && "lia-speaking-glow",
      sizeClasses[size],
      className
    )}>
      <Brain 
        className={cn(
          "transition-opacity duration-200",
          useChatCyan ? "text-chat-cyan" : "text-wedo-cyan",
          speaking && "opacity-30",
          size === "xs" && "w-3.5 h-3.5",
          size === "sm" && "w-4 h-4",
          size === "md" && "w-5.5 h-5.5",
          size === "lg" && "w-6 h-6",
          size === "xl" && "w-7 h-7"
        )}
        strokeWidth={2.5}
      />
      {speaking && <SoundWaveBars size={size} />}
    </div>
  )
}
