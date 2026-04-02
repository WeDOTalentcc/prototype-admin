"use client"

import React, { memo } from "react"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"
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
  icon: React.ElementType | React.ReactNode
  trend?: number | string
  trendLabel?: string
  trendDirection?: "up" | "down" | "neutral"
  subtitle?: string
  accentColor?: string
  variant?: "default" | "compact"
}

function TrendIndicator({ trend, trendLabel, trendDirection, subtitle }: Pick<MetricCardProps, "trend" | "trendLabel" | "trendDirection" | "subtitle">) {
  if (trend === undefined && !subtitle && !trendLabel) return null

  const isNumericTrend = typeof trend === "number"
  const isPositive = isNumericTrend ? trend >= 0 : trendDirection === "up"
  const trendColorClass = isNumericTrend || trendDirection
    ? isPositive ? "text-status-success" : "text-status-error"
    : "lia-text-secondary"

  return (
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
  )
}

function CompactDelta({ value }: { value: number }) {
  if (value === 0) {
    return (
      <div className="flex items-center gap-0.5 text-xs text-lia-text-disabled">
        <Minus className="w-2.5 h-2.5" />
        <span>0%</span>
      </div>
    )
  }
  if (value > 0) {
    return (
      <div className="flex items-center gap-0.5 text-xs text-wedo-green-bright">
        <TrendingUp className="w-2.5 h-2.5" />
        <span>+{value}%</span>
      </div>
    )
  }
  return (
    <div className="flex items-center gap-0.5 text-xs" style={{ color: 'var(--status-error)' }}>
      <TrendingDown className="w-2.5 h-2.5" />
      <span>{value}%</span>
    </div>
  )
}

const MetricCard = memo(function MetricCard({
  title,
  value,
  icon,
  trend,
  trendLabel,
  trendDirection,
  subtitle,
  accentColor,
  variant = "default",
}: MetricCardProps) {
  if (variant === "compact") {
    const numericTrend = typeof trend === "number" ? trend : undefined
    return (
      <div className="p-3 rounded-md border bg-white border-lia-border-subtle dark:border-lia-border-subtle">
        <div className="flex items-center gap-2 mb-1.5">
          <div style={accentColor ? { color: accentColor } : undefined}>
            {typeof icon === "function" ? React.createElement(icon, { className: "w-4 h-4" }) : icon}
          </div>
          <span className="text-xs text-lia-text-disabled">{title}</span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-xl font-bold" style={accentColor ? { color: accentColor } : undefined}>{value}</span>
          {numericTrend !== undefined && <CompactDelta value={numericTrend} />}
        </div>
      </div>
    )
  }

  const bgColor = accentColor
    ? (ACCENT_BG_MAP[accentColor] ?? "var(--gray-bg-10)")
    : undefined

  const renderIcon = () => {
    if (typeof icon === "function") {
      const Icon = icon as React.ElementType
      return <Icon className="w-4 h-4" style={accentColor ? { color: accentColor } : undefined} />
    }
    return icon
  }

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
          {renderIcon()}
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold lia-text-800 dark:text-lia-text-primary">
          {value}
        </div>
        <TrendIndicator trend={trend} trendLabel={trendLabel} trendDirection={trendDirection} subtitle={subtitle} />
      </CardContent>
    </Card>
  )
})
MetricCard.displayName = "MetricCard"

export { MetricCard, CompactDelta }
export { ACCENT_BG_MAP }
