"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { DailyUsage } from "@/hooks/use-ai-consumption"

export interface ConsumptionChartProps {
  title?: string
  data: DailyUsage[]
  height?: number
}

export function ConsumptionChart({
  title = "Consumo Diário (Últimos 30 dias)",
  data,
  height = 160,
}: ConsumptionChartProps) {
  const maxTokens = Math.max(...data.map(d => d.tokens), 1)

  return (
    <Card className="" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
      <CardHeader>
        <CardTitle className="text-base font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-end gap-1" style={{ height }}>
          {data.map((day) => (
            <div
              key={day.date}
              className="flex-1 bg-gray-200 dark:bg-gray-700 hover:bg-gray-800 dark:hover:bg-gray-200/40 transition-colors rounded-t cursor-pointer group relative"
              style={{ height: `${(day.tokens / maxTokens) * 100}%`, minHeight: '2px' }}
            >
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                <div className="font-medium">{day.date}</div>
                <div>{day.tokens.toLocaleString('pt-BR')} tokens</div>
              </div>
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-2 text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
          <span>30 dias atrás</span>
          <span>Hoje</span>
        </div>
      </CardContent>
    </Card>
  )
}

export default ConsumptionChart
