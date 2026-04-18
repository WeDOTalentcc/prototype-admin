"use client"

import React, { useState, useEffect } from"react"
import { useTranslations } from "next-intl"
import {
  Bot, Play, Pause, Settings, RefreshCw, Search as SearchIcon,
  ThumbsUp, ThumbsDown, AlertCircle
} from"lucide-react"
import { Card, CardContent } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import {
  textStyles, cardStyles, badgeStyles, buttonStyles
} from"@/lib/design-tokens"
import { extractErrorMessage } from "@/lib/api/extract-error-message"

// ---------- Types ----------

interface SourcingAgent {
  id: string
  agent_name: string
  status:"active" |"paused" |"completed"
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
  type:"positive" |"negative"
  reason: string
  criteria: string[]
  candidate_id: string | null
  created_at: string
}

// ---------- Constants ----------

const STATUS_CONFIG_KEYS = {
  active: { labelKey: "statusActive" as const, style: badgeStyles.success },
  paused: { labelKey: "statusPaused" as const, style: badgeStyles.warning },
  completed: { labelKey: "statusCompleted" as const, style: badgeStyles.error },
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
  const t = useTranslations('agents.agentsTab')
  const [agents, setAgents] = useState<SourcingAgent[]>([])
  const [timelines, setTimelines] = useState<Record<string, TimelineEvent[]>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => { loadAgents() }, [jobId, talentPoolId])

  const loadAgents = async () => {
    setIsLoading(true)
    setLoadError(null)
    try {
      const params = new URLSearchParams()
      if (jobId) params.set("job_id", jobId)
      if (talentPoolId) params.set("talent_pool_id", talentPoolId)
      const res = await fetch(`/api/backend-proxy/sourcing-agents?${params}`)

      // Ao contrário do comportamento antigo (data?.agents || []), aqui
      // distinguimos lista vazia legítima (200 OK, zero agentes) de falha
      // de backend (500/4xx). Sem isso, 500 caía no empty state silenciosamente
      // mesmo com agentes cadastrados (bug QA BUG-02).
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}))
        throw new Error(extractErrorMessage(errBody, res.status))
      }
      const data = await res.json()
      const agentList = data?.agents || []
      setAgents(agentList)

      // Load timelines for each agent
      const tl: Record<string, TimelineEvent[]> = {}
      await Promise.all(agentList.map(async (a: SourcingAgent) => {
        try {
          const tlRes = await fetch(`/api/backend-proxy/sourcing-agents/${a.id}/timeline?limit=10`)
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
    const action = currentStatus ==="active" ?"pause" :"resume"
    await fetch(`/api/backend-proxy/sourcing-agents/${agentId}/${action}`, { method:"PATCH" })
    loadAgents()
  }

  if (isLoading) {
    return <div className="flex items-center justify-center h-32"><p className={textStyles.caption}>{t('loadingAgents')}</p></div>
  }

  if (loadError) {
    return (
      <div className="flex flex-col items-center justify-center h-48 gap-3 text-center px-4">
        <AlertCircle className="w-10 h-10 text-status-error" />
        <p className={textStyles.body}>Não foi possível carregar os agentes</p>
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

// ---------- Agent Panel ----------

function AgentPanel({
  agent, timeline, onToggle, onRecalibrate,
}: {
  agent: SourcingAgent
  timeline: TimelineEvent[]
  onToggle: () => void
  onRecalibrate: () => void
}) {
  const t = useTranslations('agents.agentsTab')
  const statusCfg = STATUS_CONFIG_KEYS[agent.status]
  const strategy = agent.search_strategy

  return (
    <Card className={cardStyles.default}>
      <CardContent className="p-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-lia-text-secondary" />
            <span className={textStyles.subtitle}>{agent.agent_name}</span>
            <Chip variant="neutral" muted className={statusCfg.style}>{t(statusCfg.labelKey)}</Chip>
            <span className={textStyles.caption}>v{agent.calibration_v}</span>
          </div>
          <div className="flex items-center gap-2">
            <Button className={buttonStyles.outline} onClick={onToggle} title={agent.status ==="active" ? t('pause') : t('resume')}>
              {agent.status ==="active" ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            </Button>
            <Button className={buttonStyles.outline} onClick={onRecalibrate}>
              <RefreshCw className="w-3.5 h-3.5 mr-1" /> {t('recalibrate')}
            </Button>
          </div>
        </div>

        {/* Strategy summary */}
        <div className="flex flex-wrap gap-1.5 mb-3">
          {strategy.required_skills?.map(s => (
            <Chip variant="neutral" muted key={s} className="bg-green-50 text-green-700 text-xs">✅ {s}</Chip>
          ))}
          {strategy.exclusions?.map(e => (
            <Chip variant="neutral" muted key={e} className="bg-red-50 text-red-700 text-xs">❌ {e}</Chip>
          ))}
          {strategy.seniority && <Chip variant="neutral" muted className="bg-blue-50 text-blue-700 text-xs">{strategy.seniority}</Chip>}
          {strategy.location && <Chip variant="neutral" muted className="bg-lia-bg-tertiary text-lia-text-secondary text-xs">{strategy.location}</Chip>}
        </div>

        {/* Stats */}
        <div className="flex items-center gap-6 text-sm text-lia-text-secondary mb-3 py-2 border-y border-lia-border-subtle">
          <span title={t('profilesAnalyzed')}><SearchIcon className="w-3.5 h-3.5 inline mr-1" />{agent.profiles_viewed}</span>
          <span title={t('approved')}><ThumbsUp className="w-3.5 h-3.5 inline mr-1" />{agent.profiles_approved}</span>
          <span title={t('rejected')}><ThumbsDown className="w-3.5 h-3.5 inline mr-1" />{agent.profiles_rejected}</span>
        </div>

        {/* Timeline */}
        {timeline.length > 0 && (
          <div>
            <h4 className={`${textStyles.label} mb-2`}>{t('recentActivity')}</h4>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {timeline.map(event => (
                <div key={event.id} className="flex items-start gap-2 text-sm">
                  <span className="flex-shrink-0 mt-0.5">{event.icon}</span>
                  <div className="min-w-0">
                    <p className={textStyles.bodySmall}>{event.reason}</p>
                    {event.criteria.length > 0 && (
                      <p className={textStyles.caption}>
                        {t('criteria')}: {event.criteria.join(",")}
                      </p>
                    )}
                    {event.created_at && (
                      <p className={textStyles.caption}>
                        {new Date(event.created_at).toLocaleDateString(undefined, { day:"2-digit", month:"2-digit", hour:"2-digit", minute:"2-digit" })}
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
