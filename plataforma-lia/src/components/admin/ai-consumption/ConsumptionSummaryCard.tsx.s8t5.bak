"use client"

import React from "react"
import { LucideIcon } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"

export interface ConsumptionSummaryCardProps {
  title: string
  value: React.ReactNode
  subtitle?: string
  icon: LucideIcon
  progress?: number
  progressLabel?: string
  valueColor?: string
}

export function ConsumptionSummaryCard({
  title,
  value,
  subtitle,
  icon: Icon,
  progress,
  progressLabel,
  valueColor,
}: ConsumptionSummaryCardProps) {
  return (
    <Card className="border-gray-200 dark:border-gray-700">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2 text-gray-400 dark:text-gray-500">
          <Icon className="w-4 h-4" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div
          className={`text-2xl font-bold ${!valueColor ? 'text-gray-800 dark:text-gray-100' : ''}`}
          style={valueColor ? { color: valueColor } : undefined}
        >
          {value}
        </div>
        {progress !== undefined && (
          <div className="mt-2">
            <Progress value={progress} className="h-2" />
            {progressLabel && (
              <p className="text-xs mt-1 text-gray-400 dark:text-gray-500">
                {progressLabel}
              </p>
            )}
          </div>
        )}
        {subtitle && progress === undefined && (
          <p className="text-xs mt-2 text-gray-400 dark:text-gray-500">
            {subtitle}
          </p>
        )}
      </CardContent>
    </Card>
  )
}

export default ConsumptionSummaryCard
