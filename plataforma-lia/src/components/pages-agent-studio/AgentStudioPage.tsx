"use client"

import React, { useState, useEffect } from "react"
import {
  Bot, Plus, Settings, Play, Pause, Briefcase, Database,
  Factory, HeartPulse, ShoppingCart, Code, Truck, Sparkles,
  ChevronRight
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import {
  textStyles, cardStyles, badgeStyles, buttonStyles, tabStyles
} from "@/lib/design-tokens"

// ---------- Types ----------

interface SourcingAgent {
  id: string
  agent_name: string
  status: "active" | "paused" | "completed"
  calibration_v: number
  job_id: string | null
  talent_pool_id: string | null
  search_strategy: Record<string, unknown>
  preferences: Record<string, unknown>
  profiles_viewed: number
  profiles_approved: number
  profiles_rejected: number
  created_at: string
}

interface SectorTemplate {
  id: string
  display_name: string
  description: string
  icon: string
}

// ---------- Icon map ----------

const SECTOR_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  factory: Factory,
  heart_pulse: HeartPulse,
  shopping_cart: ShoppingCart,
  code: Code,
  truck: Truck,
}

const STATUS_CONFIG = {
  active: { label: "Ativo", style: badgeStyles.success },
  paused: { label: "Pausado", style: badgeStyles.warning },
  completed: { label: "Concluído", style: badgeStyles.error },
}

// ---------- Main Page ----------

interface AgentStudioPageProps {
  onNavigateToPool?: (poolId: string) => void
  onNavigateToJob?: (jobId: string) => void
  onStartCalibration?: (agentId: string) => void
}

export default function AgentStudioPage({
  onNavigateToPool,
  onNavigateToJob,
  onStartCalibration,
}: AgentStudioPageProps) {
  const [agents, setAgents] = useState<SourcingAgent[]>([])
  const [templates, setTemplates] = useState<SectorTemplate[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<SectorTemplate | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setIsLoading(true)
    try {
      const [agentsRes, templatesRes] = await Promise.all([
        fetch("/api/backend-proxy/sourcing-agents"),
        fetch("/api/backend-proxy/agent-templates/sectors"),
      ])
      const agentsData = await agentsRes.json()
      const templatesData = await templatesRes.json()
      setAgents(agentsData?.agents || [])
      setTemplates(templatesData || [])
    } catch (err) {
      console.error("Failed to load agent studio data:", err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleToggleStatus = async (agentId: string, currentStatus: string) => {
    const action = currentStatus === "active" ? "pause" : "resume"
    try {
      await fetch(`/api/backend-proxy/sourcing-agents/${agentId}/${action}`, { method: "PATCH" })
      loadData()
    } catch (err) {
      console.error("Failed to toggle agent:", err)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex-shrink-0 px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h1 className={textStyles.titleLarge}>Agent Studio</h1>
            <p className={textStyles.description}>
              Crie e gerencie agentes de sourcing a partir de templates por setor.
            </p>
          </div>
          <Button className={buttonStyles.primary} onClick={() => setShowCreateModal(true)}>
            <Plus className="w-4 h-4 mr-1" />
            Criar Agente
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-auto px-6 py-6 space-y-8">
        {/* Active Agents */}
        <section>
          <h2 className={textStyles.h3}>Meus Agentes ({agents.length})</h2>
          {isLoading ? (
            <p className={`${textStyles.caption} mt-2`}>Carregando...</p>
          ) : agents.length === 0 ? (
            <Card className={`${cardStyles.flat} mt-3`}>
              <CardContent className="flex flex-col items-center py-8">
                <Bot className="w-10 h-10 text-gray-300 mb-2" />
                <p className={textStyles.body}>Nenhum agente criado</p>
                <p className={textStyles.caption}>Escolha um template abaixo para começar.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-3">
              {agents.map(agent => (
                <AgentCard
                  key={agent.id}
                  agent={agent}
                  onToggleStatus={() => handleToggleStatus(agent.id, agent.status)}
                  onCalibrate={() => onStartCalibration?.(agent.id)}
                  onNavigate={() => {
                    if (agent.talent_pool_id) onNavigateToPool?.(agent.talent_pool_id)
                    else if (agent.job_id) onNavigateToJob?.(agent.job_id)
                  }}
                />
              ))}
            </div>
          )}
        </section>

        {/* Sector Templates Gallery */}
        <section>
          <h2 className={textStyles.h3}>Templates por Setor</h2>
          <p className={textStyles.description}>
            Templates pré-configurados com prompts, perguntas de triagem e critérios de avaliação.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mt-3">
            {templates.map(t => {
              const Icon = SECTOR_ICONS[t.icon] || Sparkles
              return (
                <Card
                  key={t.id}
                  className={`${cardStyles.default} cursor-pointer hover:shadow-md transition-shadow`}
                  onClick={() => { setSelectedTemplate(t); setShowCreateModal(true) }}
                >
                  <CardContent className="flex flex-col items-center py-6 px-4 text-center">
                    <Icon className="w-8 h-8 text-gray-600 mb-2" />
                    <p className={`${textStyles.subtitle} mb-1`}>{t.display_name}</p>
                    <p className={textStyles.caption}>{t.description}</p>
                  </CardContent>
                </Card>
              )
            })}
            <Card
              className={`${cardStyles.flat} cursor-pointer hover:shadow-md transition-shadow border-dashed`}
              onClick={() => { setSelectedTemplate(null); setShowCreateModal(true) }}
            >
              <CardContent className="flex flex-col items-center py-6 px-4 text-center">
                <Sparkles className="w-8 h-8 text-gray-400 mb-2" />
                <p className={`${textStyles.subtitle} mb-1`}>Personalizado</p>
                <p className={textStyles.caption}>Criar do zero</p>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* How it works */}
        <section>
          <h2 className={textStyles.h3}>Como funciona</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-3">
            {[
              { step: "1", title: "Escolha template", desc: "Selecione o setor ou crie personalizado" },
              { step: "2", title: "Configure", desc: "Ajuste preferências e vincule a vaga/pool" },
              { step: "3", title: "Calibre", desc: "Avalie 3+ perfis para o agente aprender" },
              { step: "4", title: "Aguarde", desc: "O agente busca candidatos automaticamente" },
            ].map(s => (
              <Card key={s.step} className={cardStyles.flat}>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="w-6 h-6 rounded-full bg-gray-900 text-white text-xs flex items-center justify-center">{s.step}</span>
                    <p className={textStyles.subtitle}>{s.title}</p>
                  </div>
                  <p className={textStyles.caption}>{s.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      </div>

      {/* Create Agent Modal */}
      {showCreateModal && (
        <CreateAgentModal
          initialTemplate={selectedTemplate}
          onClose={() => { setShowCreateModal(false); setSelectedTemplate(null) }}
          onCreated={(agentId) => {
            setShowCreateModal(false)
            setSelectedTemplate(null)
            loadData()
            onStartCalibration?.(agentId)
          }}
        />
      )}
    </div>
  )
}

// ---------- Agent Card ----------

function AgentCard({
  agent, onToggleStatus, onCalibrate, onNavigate,
}: {
  agent: SourcingAgent
  onToggleStatus: () => void
  onCalibrate: () => void
  onNavigate: () => void
}) {
  const status = STATUS_CONFIG[agent.status]
  const strategy = agent.search_strategy as { required_skills?: string[]; exclusions?: string[] }

  return (
    <Card className={cardStyles.default}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-gray-600" />
            <div>
              <p className={textStyles.subtitle}>{agent.agent_name}</p>
              <p className={textStyles.caption}>
                v{agent.calibration_v} · {agent.profiles_viewed} perfis analisados
              </p>
            </div>
          </div>
          <Badge className={status.style}>{status.label}</Badge>
        </div>

        {/* Strategy summary */}
        <div className="space-y-1 mb-3">
          {strategy.required_skills?.length ? (
            <p className={textStyles.caption}>
              ✅ {strategy.required_skills.slice(0, 3).join(", ")}
            </p>
          ) : null}
          {strategy.exclusions?.length ? (
            <p className={textStyles.caption}>
              ❌ Excluir: {strategy.exclusions.slice(0, 2).join(", ")}
            </p>
          ) : null}
        </div>

        {/* Stats */}
        <div className="flex items-center gap-4 text-xs text-gray-500 mb-3">
          <span>✅ {agent.profiles_approved}</span>
          <span>❌ {agent.profiles_rejected}</span>
          {agent.talent_pool_id && <span title="Vinculado a pool"><Database className="w-3 h-3 inline" /> Pool</span>}
          {agent.job_id && <span title="Vinculado a vaga"><Briefcase className="w-3 h-3 inline" /> Vaga</span>}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 pt-2 border-t border-gray-100">
          <Button
            className={buttonStyles.outline}
            onClick={onToggleStatus}
            title={agent.status === "active" ? "Pausar" : "Retomar"}
          >
            {agent.status === "active" ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
          </Button>
          <Button className={buttonStyles.outline} onClick={onCalibrate}>
            Recalibrar
          </Button>
          <Button className={buttonStyles.secondary} onClick={onNavigate}>
            Ver <ChevronRight className="w-3.5 h-3.5" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

// ---------- Create Agent Modal ----------

interface CreateAgentModalProps {
  initialTemplate: SectorTemplate | null
  onClose: () => void
  onCreated: (agentId: string) => void
}

function CreateAgentModal({ initialTemplate, onClose, onCreated }: CreateAgentModalProps) {
  const [step, setStep] = useState<"config" | "linking">(initialTemplate ? "config" : "config")
  const [agentName, setAgentName] = useState(initialTemplate ? `Agente ${initialTemplate.display_name}` : "")
  const [sectorId, setSectorId] = useState(initialTemplate?.id || "")
  const [linkType, setLinkType] = useState<"job" | "pool" | "none">("none")
  const [linkId, setLinkId] = useState("")
  const [candidatesPerDay, setCandidatesPerDay] = useState(20)
  const [notifyFrequency, setNotifyFrequency] = useState("daily")
  const [isCreating, setIsCreating] = useState(false)

  const handleCreate = async () => {
    setIsCreating(true)
    try {
      // 1. Apply sector template if selected
      let templateId: string | undefined
      if (sectorId) {
        const templateRes = await fetch(`/api/backend-proxy/agent-templates/sectors/${sectorId}/apply`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ agent_name: agentName }),
        })
        const templateData = await templateRes.json()
        templateId = templateData?.template_id
      }

      // 2. Create sourcing agent
      const res = await fetch("/api/backend-proxy/sourcing-agents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          agent_name: agentName,
          job_id: linkType === "job" ? linkId : null,
          talent_pool_id: linkType === "pool" ? linkId : null,
          agent_template_id: templateId || null,
          preferences: {
            candidates_per_day: candidatesPerDay,
            notify_frequency: notifyFrequency,
            channels: ["internal", "linkedin"],
          },
        }),
      })
      const data = await res.json()
      if (data?.agent_id) onCreated(data.agent_id)
    } catch (err) {
      console.error("Failed to create agent:", err)
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className={textStyles.h3}>
            {initialTemplate ? `Criar Agente — ${initialTemplate.display_name}` : "Criar Agente"}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Name */}
          <div>
            <label className={textStyles.label}>Nome do agente *</label>
            <input
              type="text"
              value={agentName}
              onChange={e => setAgentName(e.target.value)}
              placeholder="Ex: Agente Backend Sênior SP"
              className="mt-1 w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-gray-400"
            />
          </div>

          {/* Link to job or pool */}
          <div>
            <label className={textStyles.label}>Vincular a</label>
            <div className="flex gap-2 mt-1">
              {[
                { id: "none", label: "Nenhum", icon: Sparkles },
                { id: "job", label: "Vaga", icon: Briefcase },
                { id: "pool", label: "Banco de Talentos", icon: Database },
              ].map(opt => (
                <button
                  key={opt.id}
                  onClick={() => setLinkType(opt.id as "job" | "pool" | "none")}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-sm border transition-colors ${
                    linkType === opt.id
                      ? "border-gray-900 bg-gray-50 text-gray-900"
                      : "border-gray-200 text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  <opt.icon className="w-4 h-4" />
                  {opt.label}
                </button>
              ))}
            </div>
            {linkType !== "none" && (
              <input
                type="text"
                value={linkId}
                onChange={e => setLinkId(e.target.value)}
                placeholder={linkType === "job" ? "ID da vaga" : "ID do banco de talentos"}
                className="mt-2 w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-gray-400"
              />
            )}
          </div>

          {/* Preferences */}
          <div>
            <label className={textStyles.label}>Candidatos por dia</label>
            <div className="flex gap-2 mt-1">
              {[10, 20, 30, 50].map(n => (
                <button
                  key={n}
                  onClick={() => setCandidatesPerDay(n)}
                  className={`px-3 py-1.5 rounded-md text-sm border transition-colors ${
                    candidatesPerDay === n
                      ? "border-gray-900 bg-gray-50 text-gray-900"
                      : "border-gray-200 text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className={textStyles.label}>Notificar</label>
            <div className="flex gap-2 mt-1">
              {[
                { id: "realtime", label: "A cada candidato" },
                { id: "daily", label: "Resumo diário" },
                { id: "weekly", label: "Resumo semanal" },
              ].map(opt => (
                <button
                  key={opt.id}
                  onClick={() => setNotifyFrequency(opt.id)}
                  className={`px-3 py-1.5 rounded-md text-sm border transition-colors ${
                    notifyFrequency === opt.id
                      ? "border-gray-900 bg-gray-50 text-gray-900"
                      : "border-gray-200 text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button className={buttonStyles.secondary} onClick={onClose}>Cancelar</Button>
          <Button
            className={buttonStyles.primary}
            onClick={handleCreate}
            disabled={!agentName.trim() || isCreating}
          >
            {isCreating ? "Criando..." : "Criar e Calibrar"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
