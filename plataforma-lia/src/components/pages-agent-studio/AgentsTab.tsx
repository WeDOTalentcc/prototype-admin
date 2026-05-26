"use client"

import React, { useState, useEffect } from "react"
import { useTranslations } from "next-intl"
import { Bot, RefreshCw, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { textStyles, buttonStyles } from "@/lib/design-tokens"
import { extractErrorMessage } from "@/lib/api/extract-error-message"
import { AgentPanel } from "./AgentPanel"
import type { TimelineEvent } from "./AgentPanel"
import type { CustomAgent } from "./custom-agents/types"

// SOURCING-LEGACY-EXEMPT: migration comment header (Sprint 7B-3b Part 2 v2 swap concluido)
// Sprint 7B-3b Part 2 v2 (2026-05-26): swap canonical SourcingAgent -> CustomAgent.
// Endpoint /sourcing-agents -> /custom-agents?category=sourcing&talent_pool_id=X&job_id=Y
// (backend filter B1 estendido). Timeline /custom-agents/{id}/timeline (Part 1 shim).
// Snapshot SHA pre-edit: bb7bde407bc646709ee3e6ff5bdd40211be76146.

interface AgentsTabProps {
  jobId?: string
  talentPoolId?: string
  onStartCalibration: (agentId: string) => void
  onCreateAgent: () => void
}

export default function AgentsTab({
  jobId, talentPoolId, onStartCalibration, onCreateAgent,
}: AgentsTabProps) {
  const t = useTranslations('agents.agentsTab')
  const [agents, setAgents] = useState<CustomAgent[]>([])
  const [timelines, setTimelines] = useState<Record<string, TimelineEvent[]>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => { loadAgents() }, [jobId, talentPoolId])

  const loadAgents = async () => {
    setIsLoading(true)
    setLoadError(null)
    try {
      const params = new URLSearchParams()
      params.set("category", "sourcing")
      if (jobId) params.set("job_id", jobId)
      if (talentPoolId) params.set("talent_pool_id", talentPoolId)
      const res = await fetch(`/api/backend-proxy/custom-agents?${params}`)

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}))
        throw new Error(extractErrorMessage(errBody, res.status))
      }
      const data = await res.json()
      const agentList: CustomAgent[] = data?.agents || []
      setAgents(agentList)

      const tl: Record<string, TimelineEvent[]> = {}
      await Promise.all(agentList.map(async (a: CustomAgent) => {
        try {
          const tlRes = await fetch(`/api/backend-proxy/custom-agents/${a.id}/timeline?limit=10`)
          if (!tlRes.ok) { tl[a.id] = []; return }
          const tlData = await tlRes.json()
          tl[a.id] = tlData?.timeline || []
        } catch {
          tl[a.id] = []
        }
      }))
      setTimelines(tl)
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Erro desconhecido"
      setLoadError(msg)
      setAgents([])
      console.error("Failed to load agents:", err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleToggle = async (agentId: string, currentStatus: string) => {
    const action = currentStatus === "active" ? "pause" : "resume"
    await fetch(`/api/backend-proxy/custom-agents/${agentId}/${action}`, { method: "PATCH" })
    loadAgents()
  }

  if (isLoading) {
    return <div className="flex items-center justify-center h-32"><p className={textStyles.caption}>{t('loadingAgents')}</p></div>
  }

  if (loadError) {
    return (
      <div className="flex flex-col items-center justify-center h-48 gap-3 text-center px-4">
        <AlertCircle className="w-10 h-10 text-status-error" />
        <p className={textStyles.body}>Nao foi possivel carregar os agentes</p>
        <p className={`${textStyles.caption} max-w-md`}>{loadError}</p>
        <Button variant="outline" onClick={loadAgents} className="mt-2">
          <RefreshCw className="w-4 h-4 mr-2" />
          Tentar novamente
        </Button>
      </div>
    )
  }

  if (agents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48">
        <Bot className="w-10 h-10 text-lia-text-disabled mb-3" />
        <p className={textStyles.body}>{t('noAgentsConfigured')}</p>
        <p className={textStyles.caption}>{t('createAgentHint')}</p>
        <Button className={`${buttonStyles.primary} mt-4`} onClick={onCreateAgent}>
          {t('createSourcingAgent')}
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {agents.map(agent => (
        <AgentPanel
          key={agent.id}
          agent={agent}
          timeline={timelines[agent.id] || []}
          onToggle={() => handleToggle(agent.id, agent.status)}
          onRecalibrate={() => onStartCalibration(agent.id)}
        />
      ))}
    </div>
  )
}
