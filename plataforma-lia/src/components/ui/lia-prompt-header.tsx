"use client"

import React from "react"
import { Brain } from "lucide-react"

interface LiaPromptHeaderProps {
  title: string
  isAnimating?: boolean
}

export const LiaPromptHeader = React.memo(function LiaPromptHeader({ title, isAnimating = false }: LiaPromptHeaderProps) {
  return (
    <div className="mb-4 flex flex-col items-center justify-center">
      <h2
        className={`text-xl font-semibold flex items-center gap-2 ${isAnimating ? 'animate-pulse' : ''}`}
      >
        <Brain className="w-7 h-7 text-wedo-cyan" strokeWidth={2} />
        {title}
      </h2>
    </div>
  )
})
LiaPromptHeader.displayName = 'LiaPromptHeader'
