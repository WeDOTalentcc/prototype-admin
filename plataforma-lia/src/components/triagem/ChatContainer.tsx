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
 "max-w-[640px] mx-auto min-h-screen bg-lia-bg-secondary dark:bg-lia-bg-primary flex flex-col rounded-xl",
        className
      )}
      role="main"
      aria-label="Chat de triagem"
    >
      {children}
    </div>
  )
}
