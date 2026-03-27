"use client"

import React from "react"
import { cn } from "@/lib/utils"

interface ChatContainerProps {
  children: React.ReactNode
  className?: string
}

export function ChatContainer({ children, className }: ChatContainerProps) {
  return (
    <div
      className={cn(
        "max-w-[640px] mx-auto min-h-screen bg-gray-50 dark:bg-[#0F1113] flex flex-col font-['Open_Sans',sans-serif] rounded-2xl",
        className
      )}
      role="main"
      aria-label="Chat de triagem"
    >
      {children}
    </div>
  )
}
