"use client"

import React, { useState, useEffect } from "react"
import {
  Bot, Play, Pause, Settings, RefreshCw, Search as SearchIcon,
  ThumbsUp, ThumbsDown, AlertCircle
} from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  textStyles, cardStyles, badgeStyles, buttonStyles
} from "@/lib/design-tokens"

// ---------- Types ----------

interface SourcingAgent {
  id: string
  agent_name: string
  status: "active" | "paused" | "completed"
  calibration_v: number
  search_strategy: {
    required_skills?: string[]
    exclusions?: string[]
    positive_signals?: string[]
    seniority?: string
    location?: string
  }
  preferences: Record<string, unknown>
  profiles_viewed: number
  profiles_approved: number
  profiles_rejected: number
  created_at: string
}

interface TimelineEvent {
  id: string
  icon: string
  type: "positive" | "negative"
  reason: string
  criteria: string[]
  candidate_id: string | null
  created_at: string
}

// ---------- Constants ----------

const STATUS_CONFIG = {
  active: { label: "Ativo", style: badgeStyles.success },
  paused: { label: "Pausado", style: badgeStyles.warning },
  completed: { label: "Concluído", style: badgeStyles.error },
}

// ---------- Main Component ----------

interface AgentsTabProps {
  jobId?: string
  talentPoolId?: string
  onStartCalibration: (agentId: string) => void
  onCreateAgent: () => void
}

export default function AgentsTab({
  jobId, talentPoolId, onStartCalibration, onCreateAgent,
}: AgentsTabProps) {
  const [agents, setAgents] = useState<SourcingAgent[]>([])
  const [timelines, setTimelines] = useState<Record<string, TimelineEvent[]>>({})
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => { loadAgents() }, [jobId, talentPoolId])

  const loadAgents = async () => {
    setIsLoading(true)
    try {
      const params = new URLSearchParams()
      if (jobId) params.set("job_id", jobId)
      if (talentPoolId) params.set("talent_pool_id", talentPoolId)
      const res = await fetch(`/api/backend-proxy/sourcing-agents?${params}`)
      const data = await res.json()
      const agentList = data?.agents || []
      setAgents(agentList)

      // Load timelines for each agent
      const tl: Record<string, TimelineEvent[]> = {}
      await Promise.all(agentList.map(async (a: SourcingAgent) => {
        try {
          const tlRes = await fetch(`/api/backend-proxy/sourcing-agents/${a.id}/timeline?limit=10`)
          const tlData = await tlRes.json()
          tl[a.id] = tlData?.timeline || []
        } catch {
          tl[a.id] = []
        }
      }))
      setTimelines(tl)
    } catch (err) {
      console.error("Failed to load agents:", err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleToggle = async (agentId: string, currentStatus: string) => {
    const action = currentStatus === "active" ? "pause" : "resume"
    await fetch(`/api/backend-proxy/sourcing-agents/${agentId}/${action}`, { method: "PATCH" })
    loadAgents()
  }

  if (isLoading) {
    return <div className="flex items-center justify-center h-32"><p className={textStyles.caption}>Carregando agentes...</p></div>
  }

  if (agents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48">
        <Bot className="w-10 h-10 text-lia-text-disabled mb-3" />
        <p className={textStyles.body}>Nenhum agente configurado</p>
        <p className={textStyles.caption}>Crie um agente para buscar candidatos automaticamente.</p>
        <Button className={`${buttonStyles.primary} mt-4`} onClick={onCreateAgent}>
          Criar Agente de Sourcing
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

// ---------- Agent Panel ----------

function AgentPanel({
  agent, timeline, onToggle, onRecalibrate,
}: {
  agent: SourcingAgent
  timeline: TimelineEvent[]
  onToggle: () => void
  onRecalibrate: () => void
}) {
  const status = STATUS_CONFIG[agent.status]
  const strategy = agent.search_strategy

  return (
    <Card className={cardStyles.default}>
      <CardContent className="p-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-lia-text-secondary" />
            <span className={textStyles.subtitle}>{agent.agent_name}</span>
            <Badge className={status.style}>{status.label}</Badge>
            <span className={textStyles.caption}>v{agent.calibration_v}</span>
          </div>
          <div className="flex items-center gap-2">
            <Button className={buttonStyles.outline} onClick={onToggle} title={agent.status === "active" ? "Pausar" : "Retomar"}>
              {agent.status === "active" ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            </Button>
            <Button className={buttonStyles.outline} onClick={onRecalibrate}>
              <RefreshCw className="w-3.5 h-3.5 mr-1" /> Recalibrar
            </Button>
          </div>
        </div>

        {/* Strategy summary */}
        <div className="flex flex-wrap gap-1.5 mb-3">
          {strategy.required_skills?.map(s => (
            <Badge key={s} className="bg-green-50 text-green-700 text-xs">✅ {s}</Badge>
          ))}
          {strategy.exclusions?.map(e => (
            <Badge key={e} className="bg-red-50 text-red-700 text-xs">❌ {e}</Badge>
          ))}
          {strategy.seniority && <Badge className="bg-blue-50 text-blue-700 text-xs">{strategy.seniority}</Badge>}
          {strategy.location && <Badge className="bg-lia-bg-tertiary text-lia-text-secondary text-xs">{strategy.location}</Badge>}
        </div>

        {/* Stats */}
        <div className="flex items-center gap-6 text-sm text-lia-text-secondary mb-3 py-2 border-y border-lia-border-subtle">
          <span title="Perfis analisados"><SearchIcon className="w-3.5 h-3.5 inline mr-1" />{agent.profiles_viewed}</span>
          <span title="Aprovados"><ThumbsUp className="w-3.5 h-3.5 inline mr-1" />{agent.profiles_approved}</span>
          <span title="Rejeitados"><ThumbsDown className="w-3.5 h-3.5 inline mr-1" />{agent.profiles_rejected}</span>
        </div>

        {/* Timeline */}
        {timeline.length > 0 && (
          <div>
            <h4 className={`${textStyles.label} mb-2`}>Atividade recente</h4>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {timeline.map(event => (
                <div key={event.id} className="flex items-start gap-2 text-sm">
                  <span className="flex-shrink-0 mt-0.5">{event.icon}</span>
                  <div className="min-w-0">
                    <p className={textStyles.bodySmall}>{event.reason}</p>
                    {event.criteria.length > 0 && (
                      <p className={textStyles.caption}>
                        Critérios: {event.criteria.join(", ")}
                      </p>
                    )}
                    {event.created_at && (
                      <p className={textStyles.caption}>
                        {new Date(event.created_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
