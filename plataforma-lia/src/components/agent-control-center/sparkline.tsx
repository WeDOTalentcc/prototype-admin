"use client"

import React, { useMemo } from 'react'

interface SparklineProps {
  data: number[]
  color?: string
  height?: number
  showArea?: boolean
}

export function Sparkline({ data, color = 'var(--lia-text-secondary)', height = 32, showArea = true }: SparklineProps) {
  const pathData = useMemo(() => {
    if (!data.length) return { line: '', area: '' }

    const width = 100
    const padding = 2
    const min = Math.min(...data)
    const max = Math.max(...data)
    const range = max - min || 1

    const points = data.map((value, index) => {
      const x = padding + (index / (data.length - 1)) * (width - 2 * padding)
      const y = height - padding - ((value - min) / range) * (height - 2 * padding)
      return { x, y }
    })

    const line = points
      .map((point, i) => `${i === 0 ? 'M' : 'L'} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
      .join(' ')

    const area = `${line} L ${points[points.length - 1].x.toFixed(2)} ${height} L ${points[0].x.toFixed(2)} ${height} Z`

    return { line, area }
  }, [data, height])

  if (!data.length) {
    return (
      <div
        className="w-full flex items-center justify-center text-xs text-lia-text-muted"
        style={{height}}
      >
        Sem dados
      </div>
    )
  }

  return (
    <svg 
      width="100%" 
      height={height} 
      viewBox={`0 0 100 ${height}`}
      preserveAspectRatio="none"
      className="overflow-visible"
    >
      {showArea && (
        <path
          d={pathData.area}
          fill={color}
          fillOpacity={0.1}
        />
      )}
      <path
        d={pathData.line}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {data.length > 0 && (
        <circle
          cx={100 - 2}
          cy={(() => {
            const min = Math.min(...data)
            const max = Math.max(...data)
            const range = max - min || 1
            const lastValue = data[data.length - 1]
            return height - 2 - ((lastValue - min) / range) * (height - 4)
          })()}
          r={2.5}
          fill={color}
        />
      )}
    </svg>
  )
}

export default Sparkline
