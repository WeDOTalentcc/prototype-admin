"use client"

import React from "react"
import { cn } from "@/lib/utils"
import { CheckCircle, AlertCircle, HelpCircle } from "lucide-react"

export interface ConfidenceIndicatorProps {
  confidence: number
  showLabel?: boolean
  showPercentage?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const sizeStyles = {
  sm: {
    container: 'w-4 h-4',
    dot: 'w-2 h-2',
    text: 'text-micro ml-1'
  },
  md: {
    container: 'w-5 h-5',
    dot: 'w-2.5 h-2.5',
    text: 'text-xs ml-1.5'
  },
  lg: {
    container: 'w-6 h-6',
    dot: 'w-3 h-3',
    text: 'text-sm ml-2'
  }
}

type ConfidenceLevel = 'high' | 'medium' | 'low'

function getConfidenceLevel(confidence: number): ConfidenceLevel {
  if (confidence >= 0.85) return 'high'
  if (confidence >= 0.70) return 'medium'
  return 'low'
}

const levelStyles: Record<ConfidenceLevel, {
  icon: React.ElementType
  color: string
  bgColor: string
  label: string
}> = {
  high: {
    icon: CheckCircle,
    color: 'text-status-success',
    bgColor: 'bg-status-success/15 dark:bg-status-success/30',
    label: 'Alta confiança'
  },
  medium: {
    icon: AlertCircle,
    color: 'text-status-warning',
    bgColor: 'bg-status-warning/15',
    label: 'Média confiança'
  },
  low: {
    icon: HelpCircle,
    color: 'text-status-error dark:text-status-error',
    bgColor: 'bg-status-error/15 dark:bg-status-error/30',
    label: 'Baixa confiança'
  }
}

export function ConfidenceIndicator({ 
  confidence, 
  showLabel = false,
  showPercentage = false,
  size = 'sm', 
  className 
}: ConfidenceIndicatorProps) {
  const level = getConfidenceLevel(confidence)
  const styles = levelStyles[level]
  const sizeStyle = sizeStyles[size]
  const percentage = Math.round(confidence * 100)
  const Icon = styles.icon
  
  // For backward compatibility, support the old size='sm' behavior
  const displaySize = size === 'sm' ? 'h-4 w-4' : size === 'md' ? 'h-5 w-5' : 'h-6 w-6'

  return (
    <div className={cn('flex items-center', className)}>
      <div className={cn('rounded-full p-0.5', styles.bgColor)}>
        <Icon className={cn(displaySize, styles.color)} />
      </div>
      {(showLabel || showPercentage) && (
        <span className={cn(sizeStyle.text, styles.color, "font-medium tabular-nums")}>
          {showPercentage && `${percentage}%`}
          {showLabel && !showPercentage && styles.label}
        </span>
      )}
    </div>
  )
}

export function ConfidenceLabel({ 
  confidence, 
  size = 'md',
  className 
}: { 
  confidence: number
  size?: 'sm' | 'md' | 'lg'
  className?: string 
}) {
  const level = getConfidenceLevel(confidence)
  const styles = levelStyles[level]
  const percentage = Math.round(confidence * 100)
  const Icon = styles.icon

  return (
    <span 
      className={cn(
 "inline-flex items-center gap-1",
        size === 'sm' ? 'text-micro' : size === 'md' ? 'text-xs' : 'text-sm',
        styles.color,
        className
      )}
      title={`Confiança: ${percentage}%`}
    >
      <Icon className={size === 'sm' ? 'h-3 w-3' : size === 'md' ? 'h-4 w-4' : 'h-5 w-5'} />
      <span>{percentage}%</span>
    </span>
  )
}

export default ConfidenceIndicator
