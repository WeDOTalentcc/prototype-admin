"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Users, TrendingUp, MessageSquare, FileText, Search, Brain, LucideIcon } from "lucide-react"
import type { AgentUsage } from "@/hooks/use-ai-consumption"

export interface AgentBreakdownProps {
  title?: string
  agents: AgentUsage[]
}

const agentIcons: Record<string, LucideIcon> = {
  screening: Users,
  scoring: TrendingUp,
  interview: MessageSquare,
  cv_parsing: FileText,
  search: Search,
  default: Brain,
}

function getAgentIcon(agent: string): LucideIcon {
  return agentIcons[agent] || agentIcons.default
}

export function AgentBreakdown({
  title = "Consumo por Agente",
  agents,
}: AgentBreakdownProps) {
  return (
    <Card className="border-gray-200 dark:border-gray-700">
      <CardHeader>
        <CardTitle className="text-base font-semibold text-gray-800 dark:text-gray-100">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {agents.map((agent) => {
            const Icon = getAgentIcon(agent.agent)
            return (
              <div key={agent.agent}>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <Icon className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                    <span className="text-sm font-medium text-gray-800 dark:text-gray-100">
                      {agent.label}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-medium text-gray-800 dark:text-gray-100">
                      {(agent.tokens / 1000).toFixed(0)}K
                    </span>
                    <span className="text-xs ml-2 text-gray-400 dark:text-gray-500">
                      ({agent.percentage}%)
                    </span>
                  </div>
                </div>
                <Progress value={agent.percentage} className="h-2" />
                <p className="text-xs mt-1 text-gray-400 dark:text-gray-500">
                  {agent.calls.toLocaleString('pt-BR')} chamadas
                </p>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

export default AgentBreakdown
