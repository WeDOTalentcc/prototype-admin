"use client"

import React from "react"
import { LucideIcon } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export interface MetricCardProps {
  title: string
  value: React.ReactNode
  icon: LucideIcon
  trend?: string
  trendLabel?: string
  trendDirection?: "up" | "down" | "neutral"
  subtitle?: string
}

export function MetricCard({
  title,
  value,
  icon: Icon,
  trend,
  trendLabel,
  trendDirection = "neutral",
  subtitle,
}: MetricCardProps) {
  const getTrendColor = () => {
    switch (trendDirection) {
      case "up":
        return "text-status-success"
      case "down":
        return "text-status-error"
      default:
        return "text-gray-500"
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium" style={{ color: 'var(--eleven-text-secondary)' }}>
          {title}
        </CardTitle>
        <Icon className="w-4 h-4" style={{ color: 'var(--eleven-text-tertiary)' }} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold" style={{ color: 'var(--eleven-text-primary)' }}>
          {value}
        </div>
        {(trend || subtitle) && (
          <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
            {trend && <span className={getTrendColor()}>{trend}</span>}
            {trend && trendLabel && " "}
            {trendLabel || subtitle}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
