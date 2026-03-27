"use client"

import React from "react"
import { Progress } from "@/components/ui/progress"
import { AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"

interface AdjustmentCounterProps {
  current: number
  max: number
  className?: string
}

export function AdjustmentCounter({
  current,
  max,
  className
}: AdjustmentCounterProps) {
  const percentage = Math.min((current / max) * 100, 100)
  const isAtLimit = current >= max
  const isNearLimit = current >= max - 1

  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-gray-600">
          Ajuste {current} de {max}
        </span>
        {isAtLimit && (
          <div className="flex items-center gap-1">
            <AlertCircle className="h-3 w-3 text-amber-500" />
            <span className="text-[10px] text-amber-600 font-medium">Limite atingido</span>
          </div>
        )}
      </div>
      <Progress
        value={percentage}
        className="h-1.5"
      />
      {isNearLimit && !isAtLimit && (
        <p className="text-[10px] text-amber-600">
          Último ajuste disponível para este bloco
        </p>
      )}
      {isAtLimit && (
        <p className="text-[10px] text-gray-500">
          Você atingiu o limite de ajustes. Para recomeçar, gere novas perguntas.
        </p>
      )}
    </div>
  )
}

export default AdjustmentCounter
