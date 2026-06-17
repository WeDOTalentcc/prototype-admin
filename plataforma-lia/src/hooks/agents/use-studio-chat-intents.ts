"use client"

import { useCallback } from "react"
import type { CustomAgent } from "@/components/pages-agent-studio/custom-agents/types"

interface StudioMetricsSummary {
  period_days: number
  total_executions: number
  total_tokens_input: number
  total_tokens_output: number
  total_tokens: number
  total_credits: number
  estimated_cost_brl: number
  avg_confidence: number
  avg_latency_ms: number
  active_agents: number
  top_agents: Array<{ agent_id: string; agent_name: string; execution_count: number; total_tokens: number }>
}

export function useStudioChatIntents() {
  const searchAgentByName = useCallback(async (name: string): Promise<CustomAgent[]> => {
    const token = localStorage.getItem("auth_token")
    const res = await fetch(`/api/backend-proxy/custom-agents/search?name=${encodeURIComponent(name)}&limit=5`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!res.ok) return []
    const data = await res.json()
    return data.agents || []
  }, [])

  const getMetricsSummary = useCallback(async (periodDays = 7): Promise<StudioMetricsSummary | null> => {
    const token = localStorage.getItem("auth_token")
    const res = await fetch(`/api/backend-proxy/custom-agents/studio-metrics-summary?period_days=${periodDays}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!res.ok) return null
    return await res.json()
  }, [])

  /** Extract agent name from user message like "como esta o agente Triagem Tech" */
  const extractAgentName = useCallback((message: string): string | null => {
    const patterns = [
      /(?:agente|agent)\s+([A-Z][\w\s]{2,40})/i,
      /(?:do|da|sobre|o)\s+agente\s+([\w\s]{2,40})/i,
    ]
    for (const p of patterns) {
      const match = message.match(p)
      if (match?.[1]) {
        return match[1].trim().replace(/[?!.,]$/, "")
      }
    }
    return null
  }, [])

  return { searchAgentByName, getMetricsSummary, extractAgentName }
}
