"use client"

import React from "react"

interface DataPoint {
  date: string
  value: number
}

interface LiaMetricsChartProps {
  data: DataPoint[]
  title: string
  color?: string
  targetValue?: number
}

export function LiaMetricsChart({ data, title, color = "var(--lia-text-secondary)", targetValue }: LiaMetricsChartProps) {
  const width = 400
  const height = 150
  const padding = { top: 20, right: 20, bottom: 30, left: 40 }

  const chartWidth = width - padding.left - padding.right
  const chartHeight = height - padding.top - padding.bottom

  // Find min/max values
  const values = data.map(d => d.value)
  const minValue = Math.min(...values, targetValue || 0)
  const maxValue = Math.max(...values, targetValue || 100)

  // Scale functions
  const xScale = (index: number) => {
    return (index / (data.length - 1)) * chartWidth + padding.left
  }

  const yScale = (value: number) => {
    const range = maxValue - minValue
    const normalizedValue = (value - minValue) / range
    return chartHeight - (normalizedValue * chartHeight) + padding.top
  }

  // Create path for line
  const linePath = data.map((point, index) => {
    const x = xScale(index)
    const y = yScale(point.value)
    return index === 0 ? `M ${x} ${y}` : `L ${x} ${y}`
  }).join(' ')

  // Create path for area under line
  const areaPath = `${linePath} L ${xScale(data.length - 1)} ${height - padding.bottom} L ${xScale(0)} ${height - padding.bottom} Z`

  // Target line path
  const targetLinePath = targetValue ? `M ${padding.left} ${yScale(targetValue)} L ${width - padding.right} ${yScale(targetValue)}` : ''

  return (
    <div className="w-full">
      <h4 className="text-xs font-semibold font-sans text-lia-text-primary mb-2">{title}</h4>
      <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} className="overflow-visible">
        {/* Grid lines */}
        {[0, 25, 50, 75, 100].map(value => (
          <g key={value}>
            <line
              x1={padding.left}
              y1={yScale(value)}
              x2={width - padding.right}
              y2={yScale(value)}
              stroke="currentColor"
              strokeWidth="1"
              strokeDasharray="2,2"
              className="text-lia-text-inverse"
              opacity="0.5"
            />
            <text
              x={padding.left - 5}
              y={yScale(value)}
              textAnchor="end"
              alignmentBaseline="middle"
              className="text-lia-text-secondary"
             
            >
              {value}%
            </text>
          </g>
        ))}

        {/* Target line */}
        {targetValue && (
          <g>
            <path
              d={targetLinePath}
              stroke="var(--status-error)"
              strokeWidth="1.5"
              strokeDasharray="4,4"
              fill="none"
            />
            <text
              x={width - padding.right + 5}
              y={yScale(targetValue)}
              className="text-status-error dark:text-status-error"
             
              alignmentBaseline="middle"
            >
              Meta: {targetValue}%
            </text>
          </g>
        )}

        {/* Area under line */}
        <path
          d={areaPath}
          fill={color}
          opacity="0.1"
        />

        {/* Line */}
        <path
          d={linePath}
          stroke={color}
          strokeWidth="2"
          fill="none"
        />

        {/* Data points */}
        {data.map((point, index) => (
          <g key={`point-${index}`}>
            <circle
              cx={xScale(index)}
              cy={yScale(point.value)}
              r="3"
              fill={color}
              stroke="white"
              strokeWidth="2"
            />
            {/* Tooltip on hover */}
            <title>{`${point.date}: ${point.value}%`}</title>
          </g>
        ))}

        {/* X-axis labels */}
        {data.map((point, index) => {
          // Show every other label to avoid crowding
          if (index % Math.ceil(data.length / 4) === 0 || index === data.length - 1) {
            return (
              <text
                key={`label-${index}`}
                x={xScale(index)}
                y={height - padding.bottom + 15}
                textAnchor="middle"
                className="text-lia-text-secondary"
               
              >
                {point.date}
              </text>
            )
          }
          return null
        })}

        {/* Latest value badge */}
        <g>
          <rect
            x={xScale(data.length - 1) - 20}
            y={yScale(data[data.length - 1].value) - 20}
            width="40"
            height="16"
            rx="8"
            fill={color}
          />
          <text
            x={xScale(data.length - 1)}
            y={yScale(data[data.length - 1].value) - 12}
            textAnchor="middle"
            className="text-white"
           
          >
            {data[data.length - 1].value}%
          </text>
        </g>
      </svg>
    </div>
  )
}
