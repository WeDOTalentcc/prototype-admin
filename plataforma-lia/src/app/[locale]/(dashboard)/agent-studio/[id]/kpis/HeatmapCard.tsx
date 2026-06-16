// C5.4 (2026-05-29) — Recharts heatmap extracted from AgentKpisClient for lazy load.
//
// Recharts is a heavy dependency (~bundle weight). By isolating the only chart
// in the KPIs page into its own module, AgentKpisClient can import it via
// next/dynamic({ ssr: false }) so recharts is code-split out of the main bundle
// and only fetched when the KPI page actually renders the heatmap.
//
// Design tokens: zero hex hardcoded; cyan = var(--wedo-cyan) (canonical wedo-cyan).
// Sensor check_cyan_token_for_agents BLOCKING — no hex fallback.
"use client"

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { AgentKpiResponse } from "@/types/agents/kpi"

const CYAN_TOKEN = "var(--wedo-cyan)"
const NEUTRAL_TOKEN = "var(--lia-border-default)"

export interface HeatmapCardProps {
  title: string
  ariaLabel: string
  data: AgentKpiResponse["hour_heatmap"]
}

export function HeatmapCard({ title, ariaLabel, data }: HeatmapCardProps) {
  const chartData = data.map((entry) => ({
    hour: `${String(entry.hour_of_day).padStart(2, "0")}h`,
    executions: entry.executions_count,
  }))
  return (
    <Card className="border border-lia-border-subtle shadow-none">
      <CardHeader className="pb-2 pt-4">
        <CardTitle className="text-xs font-medium text-lia-text-tertiary">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="pb-4">
        <div aria-label={ariaLabel} role="img" data-testid="kpi-heatmap">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart
              data={chartData}
              margin={{ top: 4, right: 4, bottom: 0, left: 0 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--lia-border-subtle)"
                vertical={false}
              />
              <XAxis
                dataKey="hour"
                tick={{
                  fontSize: 10,
                  fill: "var(--lia-text-tertiary)",
                }}
                tickLine={false}
                axisLine={false}
                interval={1}
              />
              <YAxis
                tick={{
                  fontSize: 10,
                  fill: "var(--lia-text-tertiary)",
                }}
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
              />
              <Tooltip
                contentStyle={{
                  fontSize: 11,
                  borderRadius: 6,
                  border: "1px solid var(--lia-border-subtle)",
                }}
              />
              <Bar dataKey="executions" radius={[2, 2, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={entry.executions > 0 ? CYAN_TOKEN : NEUTRAL_TOKEN}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}

export default HeatmapCard
