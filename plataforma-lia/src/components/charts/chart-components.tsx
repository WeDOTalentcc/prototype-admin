"use client"

import { ReactNode } from "react"

interface ChartContainerProps {
  title: string
  description?: string
  children: ReactNode
  className?: string
}

export function ChartContainer({ title, description, children, className = "" }: ChartContainerProps) {
  return (
    <div className={`bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle p-6 transition-colors motion-reduce:transition-none duration-200 ${className}`}>
      <div className="mb-4">
        <h3 className="text-sm font-semibold font-sans text-lia-text-primary">{title}</h3>
        {description && (
          <p className="text-xs text-lia-text-primary mt-1">{description}</p>
        )}
      </div>
      {children}
    </div>
  )
}

interface BarChartProps {
  data: { label: string; value: number; color?: string }[]
  maxValue?: number
}

export function BarChart({ data, maxValue }: BarChartProps) {
  const max = maxValue || Math.max(...data.map(d => d.value))

  return (
    <div className="space-y-3">
      {data.map((item) => (
        // @ts-ignore TODO: fix type — Property 'name' does not exist on type '{ label: string; value: number; color?: 
        <div key={item.label || item.name} className="flex items-center gap-3">
          <div className="w-20 text-xs text-lia-text-secondary font-medium">
            {item.label}
          </div>
          <div className="flex-1 bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-[width,height] duration-500 ${
 item.color || 'bg-lia-border-medium'
              }`}
              style={{width: `${(item.value / max) * 100}%`}}
            />
          </div>
          <div className="w-12 text-xs text-lia-text-primary font-semibold text-right">
            {item.value}
          </div>
        </div>
      ))}
    </div>
  )
}


interface DonutChartProps {
  data: { label: string; value: number; color: string }[]
  centerText?: string
}

export function DonutChart({ data, centerText }: DonutChartProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0)
  let currentAngle = 0

  return (
    <div className="flex items-center gap-6">
      <div className="relative w-32 h-32">
        <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 36 36">
          <circle
            cx="18"
            cy="18"
            r="15.5"
            fill="transparent"
            stroke="var(--lia-border-subtle)"
            strokeWidth="3"
            className="dark:stroke-lia-border-medium"
          />
          {data.map((item, index) => {
            const strokeDasharray = `${(item.value / total) * 97.4} 97.4`
            const strokeDashoffset = -currentAngle
            currentAngle += (item.value / total) * 97.4

            return (
              <circle
                key={`arc-${index}`}
                cx="18"
                cy="18"
                r="15.5"
                fill="transparent"
                stroke={item.color}
                strokeWidth="3"
                strokeDasharray={strokeDasharray}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                className="transition-colors motion-reduce:transition-none duration-500"
              />
            )
          })}
        </svg>
        {centerText && (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-lg font-semibold text-lia-text-primary">
              {centerText}
            </span>
          </div>
        )}
      </div>

      <div className="space-y-2">
        {data.map((item) => (
          // @ts-ignore TODO: fix type — Property 'name' does not exist on type '{ label: string; value: number; color: s
          <div key={item.label || item.name} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{backgroundColor: item.color}}
            />
            <span className="text-xs text-lia-text-secondary">
              {item.label}
            </span>
            <span className="text-xs font-semibold text-lia-text-primary">
              {item.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

interface LineChartProps {
  data: { label: string; value: number }[]
  color?: string
}

export function LineChart({ data, color = "var(--lia-text-secondary)" }: LineChartProps) {
  const maxValue = Math.max(...data.map(d => d.value))
  const minValue = Math.min(...data.map(d => d.value))
  const range = maxValue - minValue || 1

  const points = data.map((item, index) => {
    const x = (index / (data.length - 1)) * 200
    const y = 40 - ((item.value - minValue) / range) * 40
    return `${x},${y}`
  }).join(' ')

  return (
    <div>
      <svg className="w-full h-16" viewBox="0 0 200 40">
        <polyline
          fill="none"
          stroke={color}
          strokeWidth="2"
          points={points}
          className="transition-colors motion-reduce:transition-none duration-500"
        />
        {data.map((item, index) => {
          const x = (index / (data.length - 1)) * 200
          const y = 40 - ((item.value - minValue) / range) * 40
          return (
            <circle
              key={`pt-${index}`}
              cx={x}
              cy={y}
              r="3"
              fill={color}
              className="transition-colors motion-reduce:transition-none duration-500"
            />
          )
        })}
      </svg>
      <div className="flex justify-between mt-2">
        {data.map((item) => (
          // @ts-ignore TODO: fix type — Property 'name' does not exist on type '{ label: string; value: number; }'.
          // @ts-ignore TODO: fix type — Property 'month' does not exist on type '{ label: string; value: number; }'.
          <div key={item.label || item.month || item.name} className="text-center">
            <div className="text-xs text-lia-text-primary">
              {item.label}
            </div>
            <div className="text-xs font-semibold text-lia-text-primary">
              {item.value}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
