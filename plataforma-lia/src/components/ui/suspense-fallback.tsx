"use client"

import React from "react"
import { Loader2 } from "lucide-react"

interface SuspenseFallbackProps {
  size?: "sm" | "md" | "lg"
  message?: string
}

const sizeMap = {
  sm: { icon: "w-4 h-4", text: "text-xs", padding: "py-4" },
  md: { icon: "w-6 h-6", text: "text-sm", padding: "py-8" },
  lg: { icon: "w-8 h-8", text: "text-base", padding: "py-12" },
}

export function SuspenseFallback({ size = "md", message }: SuspenseFallbackProps) {
  const s = sizeMap[size]
  return (
    <div className={`flex flex-col items-center justify-center ${s.padding}`}>
      <Loader2 className={`${s.icon} animate-spin motion-reduce:animate-none text-lia-text-secondary`} />
      {message && (
        <p className={`${s.text} text-lia-text-tertiary mt-2`}>{message}</p>
      )}
    </div>
  )
}
