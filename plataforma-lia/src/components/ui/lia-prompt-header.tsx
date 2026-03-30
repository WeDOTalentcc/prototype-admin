"use client"

import { Brain } from "lucide-react"

interface LiaPromptHeaderProps {
  title: string
  isAnimating?: boolean
}

export function LiaPromptHeader({ title, isAnimating = false }: LiaPromptHeaderProps) {
  return (
    <div className="mb-4 flex flex-col items-center justify-center">
      <h2
        className={`text-2xl font-semibold text-lia-text-primary font-['Open_Sans',sans-serif] flex items-center gap-2.5 ${
 isAnimating ? 'animate-pulse motion-reduce:animate-none' : ''
        }`}
      >
        <Brain className="w-7 h-7 text-wedo-cyan" strokeWidth={2} />
        {title}
      </h2>
    </div>
  )
}
