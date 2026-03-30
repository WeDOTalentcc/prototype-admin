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
        className={`text-2xl font-semibold text-gray-950 font-['Open_Sans',sans-serif] flex items-center gap-2.5 ${
 isAnimating ? 'animate-pulse' : ''
        }`}
      >
        <Brain className="w-7 h-7 text-wedo-cyan" strokeWidth={2} />
        {title}
      </h2>
    </div>
  )
}
