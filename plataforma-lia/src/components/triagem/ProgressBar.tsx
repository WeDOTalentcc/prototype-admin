"use client"

import React from "react"
import { cn } from "@/lib/utils"
import type { WSIProgress } from "@/components/triagem/types"

interface ProgressBarProps {
  progress: WSIProgress
  className?: string
}

export function ProgressBar({ progress, className }: ProgressBarProps) {
  const percentage = Math.round((progress.currentBlock / progress.totalBlocks) * 100)

  return (
    <div
      className={cn(
 "sticky top-0 z-20 bg-white dark:bg-lia-bg-secondary border-b border-lia-border-subtle dark:border-lia-border-subtle px-4 py-3",
        className
      )}
      role="progressbar"
      aria-valuenow={progress.currentBlock}
      aria-valuemin={0}
      aria-valuemax={progress.totalBlocks}
      aria-label={`Etapa ${progress.currentBlock} de ${progress.totalBlocks}: ${progress.currentBlockName}`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium font-['Open_Sans',sans-serif] text-lia-text-secondary dark:text-lia-text-secondary">
          Etapa{" "}
          <span className="font-['Inter',sans-serif]">{progress.currentBlock}</span>
          {" "}de{" "}
          <span className="font-['Inter',sans-serif]">{progress.totalBlocks}</span>
          {" · "}
          {progress.currentBlockName}
        </span>
        <span className="text-micro font-['Inter',sans-serif] text-lia-text-disabled">
          {percentage}%
        </span>
      </div>
      <div className="w-full h-1.5 bg-gray-200 dark:bg-lia-bg-elevated rounded-full overflow-hidden">
        <div
          className="h-full bg-gray-900 rounded-full transition-[width,height] duration-500 ease-out"
          style={{width: `${percentage}%`}}
        />
      </div>
    </div>
  )
}
