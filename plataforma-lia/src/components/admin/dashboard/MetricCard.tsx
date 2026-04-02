"use client"

import React, { memo } from "react"
import { TrendingUp, TrendingDown } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const ACCENT_BG_MAP: Record<string, string> = {
  "var(--gray-400)": "var(--gray-bg-10)",
  "var(--status-success)": "var(--status-success-bg)",
  "var(--status-error)": "var(--status-error-bg)",
  "var(--wedo-orange)": "var(--wedo-orange-bg-15)",
  "var(--wedo-purple)": "var(--wedo-purple-bg-10)",
  "var(--wedo-cyan)": "var(--wedo-cyan-bg-10)",
}

export interface MetricCardProps {
  title: string
  value: React.ReactNode
  /** Accept both LucideIcon and any React element type */
  icon: React.ElementType
  /** Numeric trend value (positive = up, negative = down). Shows TrendingUp/Down icon. */
  trend?: number | string
  trendLabel?: string
  /** Used when trend is a string direction */
  trendDirection?: "up" | "down" | "neutral"
  subtitle?: string
  /** CSS variable string (e.g. "var(--wedo-cyan)"). Colors the icon and its background. */
  accentColor?: string
}

const MetricCard = memo(function MetricCard({
  title,
  value,
  icon: Icon,
  trend,
  trendLabel,
  trendDirection,
  subtitle,
  accentColor,
}: MetricCardProps) {
  const bgColor = accentColor
    ? (ACCENT_BG_MAP[accentColor] ?? "var(--gray-bg-10)")
    : undefined

  // Determine trend display
  const isNumericTrend = typeof trend === "number"
  const isPositive = isNumericTrend ? trend >= 0 : trendDirection === "up"
  const trendColorClass = isNumericTrend || trendDirection
    ? isPositive ? "text-status-success" : "text-status-error"
    : "lia-text-secondary"

  return (
    <Card className="relative overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium lia-text-500 dark:text-lia-text-tertiary">
          {title}
        </CardTitle>
        <div
          className="p-2 rounded-md"
          style={bgColor ? { backgroundColor: bgColor } : undefined}
        >
          <Icon
            className="w-4 h-4"
            style={accentColor ? { color: accentColor } : undefined}
          />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold lia-text-800 dark:text-lia-text-primary">
          {value}
        </div>
        {(trend !== undefined || subtitle || trendLabel) && (
          <div className="flex items-center gap-2 mt-1">
            {isNumericTrend ? (
              <span className={`flex items-center text-xs font-medium ${trendColorClass}`}>
                {isPositive
                  ? <TrendingUp className="w-3 h-3 mr-1" />
                  : <TrendingDown className="w-3 h-3 mr-1" />
                }
                {isPositive ? "+" : ""}{trend}%
              </span>
            ) : typeof trend === "string" ? (
              <span className={`text-xs font-medium ${trendColorClass}`}>{trend}</span>
            ) : null}
            {trendLabel && (
              <span className="text-xs text-lia-text-disabled">{trendLabel}</span>
            )}
            {!trend && subtitle && (
              <span className="text-xs text-lia-text-disabled">{subtitle}</span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
})
MetricCard.displayName = "MetricCard"

export { MetricCard }
export { ACCENT_BG_MAP }
