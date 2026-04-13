"use client"

import React, { useState, useEffect, useCallback } from "react"
import {
  Bot, Plus, Play, Pause, Trash2, Edit3, TestTube2,
  Loader2, Settings, Wand2, Copy, ExternalLink,
  ChevronRight, MoreVertical, Store
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogDescription, DialogFooter,
} from "@/components/ui/dialog"

interface CustomAgent {
  id: string
  name: string
  role: string
  description: string | null
  system_prompt: string
  allowed_tools: string[]
  domain: string
  icon: string
  status: string
  version: number
  total_executions: number
  avg_confidence: number
  is_marketplace_published: boolean
  created_at: string | null
  updated_at: string | null
  max_steps?: number
  temperature?: number
}

const STATUS_CONFIG: Record<string, { label: string; dot: string; bg: string; text: string }> = {
  draft: { label: "Rascunho", dot: "bg-lia-text-disabled", bg: "bg-lia-bg-secondary dark:bg-lia-bg-inverse/30", text: "text-lia-text-secondary dark:text-lia-text-tertiary" },
  active: { label: "Ativo", dot: "bg-emerald-500", bg: "bg-emerald-50 dark:bg-emerald-950/30", text: "text-emerald-700 dark:text-emerald-400" },
  paused: { label: "Pausado", dot: "bg-amber-500", bg: "bg-amber-50 dark:bg-amber-950/30", text: "text-amber-700 dark:text-amber-400" },
  archived: { label: "Arquivado", dot: "bg-red-400", bg: "bg-red-50 dark:bg-red-950/30", text: "text-red-600 dark:text-red-400" },
}

export default function CustomAgentsTab() {
  const [agents, setAgents] = useState<CustomAgent[]>([])
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingAgent, setEditingAgent] = useState<CustomAgent | null>(null)
  const [testingAgent, setTestingAgent] = useState<CustomAgent | null>(null)

  const loadAgents = useCallback(async () => {
    setIsLoading(true)
    try {
      const res = await fetch("/api/backend-proxy/custom-agents")
      if (res.ok) {
        const data = await res.json()
        setAgents(data.agents || [])
        setTotal(data.total || 0)
      }
    } catch (err) {
      console.error("Failed to load custom agents:", err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => { loadAgents() }, [loadAgents])

  const handleDelete = async (agentId: string) => {
    if (!confirm("Tem certeza que deseja excluir este agente?")) return
    try {
      await fetch(`/api/backend-proxy/custom-agents/${agentId}`, { method: "DELETE" })
      loadAgents()
    } catch (err) {
      console.error("Failed to delete agent:", err)
    }
  }

  const handleStatusChange = async (agentId: string, newStatus: string) => {
    try {
      await fetch(`/api/backend-proxy/custom-agents/${agentId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      })
      loadAgents()
    } catch (err) {
      console.error("Failed to update status:", err)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="flex flex-col items-center gap-3 text-lia-text-secondary">
          <Loader2 className="w-6 h-6 animate-spin" />
          <span className="text-xs">Carregando agentes custom...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-lia-text-primary">
            Agentes Customizados
            {total > 0 && (
              <span className="ml-2 px-2 py-0.5 rounded-full text-[10px] font-bold bg-lia-interactive-active text-lia-text-primary">
                {total}
              </span>
            )}
          </h2>
          <p className="text-xs text-lia-text-secondary mt-0.5">
            Crie agentes com prompt, tools e comportamento personalizado
          </p>
        </div>
        <Button
          size="sm"
          onClick={() => { setEditingAgent(null); setShowCreateModal(true) }}
          className="gap-2 bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
        >
          <Plus className="w-4 h-4" />
          Novo Agente Custom
        </Button>
      </div>

      {agents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 rounded-xl border border-dashed border-lia-border-subtle bg-lia-bg-secondary/50">
          <div className="w-14 h-14 rounded-2xl bg-lia-bg-tertiary flex items-center justify-center mb-3">
            <Wand2 className="w-7 h-7 text-lia-text-disabled" />
          </div>
          <p className="text-sm font-medium text-lia-text-secondary">Nenhum agente custom criado</p>
          <p className="text-xs text-lia-text-disabled mt-1 mb-4">
            Crie um agente personalizado com prompt, tools e domínio de atuação
          </p>
          <Button
            size="sm"
            onClick={() => setShowCreateModal(true)}
            className="gap-2 bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
          >
            <Plus className="w-3.5 h-3.5" />
            Criar primeiro agente
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map(agent => {
            const statusConf = STATUS_CONFIG[agent.status] || STATUS_CONFIG.draft
            return (
              <div
                key={agent.id}
                className={cn(
                  "group relative rounded-xl border border-lia-border-subtle bg-lia-bg-secondary",
                  "hover:border-lia-border-medium hover:shadow-md transition-all duration-200"
                )}
              >
                <div className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500/10 to-cyan-500/10 flex items-center justify-center text-lg">
                        {agent.icon || "🤖"}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-lia-text-primary">{agent.name}</p>
                        <p className="text-[10px] text-lia-text-secondary">{agent.role}</p>
                      </div>
                    </div>
                    <div className={cn("flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold", statusConf.bg, statusConf.text)}>
                      <div className={cn("w-1.5 h-1.5 rounded-full", statusConf.dot)} />
                      {statusConf.label}
                    </div>
                  </div>

                  {agent.description && (
                    <p className="text-xs text-lia-text-secondary mb-3 line-clamp-2">{agent.description}</p>
                  )}

                  {agent.allowed_tools.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {agent.allowed_tools.slice(0, 3).map((tool, i) => (
                        <span key={i} className="px-2 py-0.5 rounded-xl bg-lia-bg-tertiary text-[10px] font-medium text-lia-text-secondary">
                          {tool}
                        </span>
                      ))}
                      {agent.allowed_tools.length > 3 && (
                        <span className="px-2 py-0.5 rounded-xl bg-lia-bg-tertiary text-[10px] text-lia-text-disabled">
                          +{agent.allowed_tools.length - 3}
                        </span>
                      )}
                    </div>
                  )}

                  <div className="grid grid-cols-3 gap-2 mb-3">
                    <div className="flex flex-col items-center p-2 rounded-lg bg-lia-bg-primary">
                      <span className="text-xs font-bold text-lia-text-primary">{agent.total_executions}</span>
                      <span className="text-[9px] text-lia-text-disabled uppercase">Execuções</span>
                    </div>
                    <div className="flex flex-col items-center p-2 rounded-lg bg-lia-bg-primary">
                      <span className="text-xs font-bold text-lia-text-primary">v{agent.version}</span>
                      <span className="text-[9px] text-lia-text-disabled uppercase">Versão</span>
                    </div>
                    <div className="flex flex-col items-center p-2 rounded-lg bg-lia-bg-primary">
                      <span className="text-xs font-bold text-lia-text-primary">{agent.domain}</span>
                      <span className="text-[9px] text-lia-text-disabled uppercase">Domínio</span>
                    </div>
                  </div>

                  {agent.is_marketplace_published && (
                    <div className="flex items-center gap-1.5 mb-3 px-2.5 py-1.5 rounded-lg bg-violet-50 dark:bg-violet-950/20 border border-violet-200 dark:border-violet-800">
                      <Store className="w-3 h-3 text-violet-500" />
                      <span className="text-[10px] text-violet-700 dark:text-violet-400 font-medium">Publicado no Marketplace</span>
                    </div>
                  )}

                  <div className="flex items-center gap-2 pt-3 border-t border-lia-border-subtle">
                    <button
                      onClick={() => setTestingAgent(agent)}
                      className="flex items-center justify-center gap-1.5 h-8 px-3 rounded-lg border border-lia-border-subtle text-xs font-medium text-lia-text-secondary hover:bg-lia-bg-tertiary transition-colors"
                    >
                      <TestTube2 className="w-3.5 h-3.5" />
                      Testar
                    </button>
                    <button
                      onClick={() => { setEditingAgent(agent); setShowCreateModal(true) }}
                      className="flex items-center justify-center gap-1.5 h-8 px-3 rounded-lg border border-lia-border-subtle text-xs font-medium text-lia-text-secondary hover:bg-lia-bg-tertiary transition-colors"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                      Editar
                    </button>
                    {agent.status === "active" ? (
                      <button
                        onClick={() => handleStatusChange(agent.id, "paused")}
                        className="flex items-center justify-center w-8 h-8 rounded-lg border border-lia-border-subtle hover:bg-lia-bg-tertiary transition-colors"
                        title="Pausar"
                      >
                        <Pause className="w-3.5 h-3.5 text-amber-500" />
                      </button>
                    ) : agent.status !== "archived" ? (
                      <button
                        onClick={() => handleStatusChange(agent.id, "active")}
                        className="flex items-center justify-center w-8 h-8 rounded-lg border border-lia-border-subtle hover:bg-lia-bg-tertiary transition-colors"
                        title="Ativar"
                      >
                        <Play className="w-3.5 h-3.5 text-emerald-500" />
                      </button>
                    ) : null}
                    <button
                      onClick={() => handleDelete(agent.id)}
                      className="flex items-center justify-center w-8 h-8 rounded-lg border border-lia-border-subtle hover:bg-red-50 dark:hover:bg-red-950/20 transition-colors ml-auto"
                      title="Excluir"
                    >
                      <Trash2 className="w-3.5 h-3.5 text-red-400" />
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {showCreateModal && (
        <CreateCustomAgentModal
          agent={editingAgent}
          onClose={() => { setShowCreateModal(false); setEditingAgent(null) }}
          onSaved={() => { setShowCreateModal(false); setEditingAgent(null); loadAgents() }}
        />
      )}

      {testingAgent && (
        <TestAgentModal
          agent={testingAgent}
          onClose={() => setTestingAgent(null)}
        />
      )}
    </div>
  )
}

function CreateCustomAgentModal({
  agent, onClose, onSaved,
}: {
  agent: CustomAgent | null
  onClose: () => void
  onSaved: () => void
}) {
  const isEditing = !!agent
  const [name, setName] = useState(agent?.name || "")
  const [role, setRole] = useState(agent?.role || "")
  const [description, setDescription] = useState(agent?.description || "")
  const [systemPrompt, setSystemPrompt] = useState(agent?.system_prompt || "")
  const [domain, setDomain] = useState(agent?.domain || "general")
  const [maxSteps, setMaxSteps] = useState(agent?.max_steps || 8)
  const [temperature, setTemperature] = useState(agent?.temperature || 0.7)
  const [toolsInput, setToolsInput] = useState((agent?.allowed_tools || []).join(", "))
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState("")
  const [availableTools, setAvailableTools] = useState<string[]>([])

  useEffect(() => {
    fetch("/api/backend-proxy/custom-agents/available-tools")
      .then(r => r.ok ? r.json() : { tools: [] })
      .then(d => setAvailableTools(d.tools || []))
      .catch(() => {})
  }, [])

  const handleSave = async () => {
    setIsSaving(true)
    setError("")
    try {
      const allowedTools = toolsInput.split(",").map(t => t.trim()).filter(Boolean)
      const body = {
        name,
        role,
        description: description || undefined,
        system_prompt: systemPrompt,
        allowed_tools: allowedTools,
        domain,
        max_steps: maxSteps,
        temperature,
      }

      const url = isEditing
        ? `/api/backend-proxy/custom-agents/${agent!.id}`
        : "/api/backend-proxy/custom-agents"
      const method = isEditing ? "PATCH" : "POST"

      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(errData?.detail || `Erro ${res.status}`)
      }

      onSaved()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar")
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-2xl bg-lia-bg-primary border-lia-border-subtle max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-base font-semibold text-lia-text-primary flex items-center gap-2">
            <Wand2 className="w-4 h-4 text-wedo-cyan" />
            {isEditing ? "Editar Agente Custom" : "Criar Agente Custom"}
          </DialogTitle>
          <DialogDescription className="sr-only">Configure o agente customizado</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-lia-text-primary mb-1 block">Nome</label>
              <input
                type="text" value={name} onChange={e => setName(e.target.value)}
                placeholder="Ex: Agente Triagem Cultural"
                className="w-full border border-lia-border-subtle rounded-lg px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-wedo-cyan/30"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-lia-text-primary mb-1 block">Role</label>
              <input
                type="text" value={role} onChange={e => setRole(e.target.value)}
                placeholder="Ex: Analista de Fit Cultural"
                className="w-full border border-lia-border-subtle rounded-lg px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-wedo-cyan/30"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-lia-text-primary mb-1 block">Descrição</label>
            <input
              type="text" value={description} onChange={e => setDescription(e.target.value)}
              placeholder="Breve descrição do que o agente faz"
              className="w-full border border-lia-border-subtle rounded-lg px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-wedo-cyan/30"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-lia-text-primary mb-1 block">System Prompt</label>
            <textarea
              value={systemPrompt} onChange={e => setSystemPrompt(e.target.value)}
              rows={6}
              placeholder="Instruções de comportamento do agente..."
              className="w-full border border-lia-border-subtle rounded-lg px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-wedo-cyan/30 resize-none font-mono"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-lia-text-primary mb-1 block">
              Tools permitidas
              {availableTools.length > 0 && (
                <span className="font-normal text-lia-text-disabled ml-1">({availableTools.length} disponíveis)</span>
              )}
            </label>
            <input
              type="text" value={toolsInput} onChange={e => setToolsInput(e.target.value)}
              placeholder="search_candidates, list_jobs, get_candidate_details"
              className="w-full border border-lia-border-subtle rounded-lg px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-wedo-cyan/30"
            />
            {availableTools.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {availableTools.slice(0, 10).map(t => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => {
                      const current = toolsInput.split(",").map(s => s.trim()).filter(Boolean)
                      if (!current.includes(t)) {
                        setToolsInput([...current, t].join(", "))
                      }
                    }}
                    className="px-2 py-0.5 rounded text-[10px] bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active transition-colors cursor-pointer"
                  >
                    + {t}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="text-xs font-semibold text-lia-text-primary mb-1 block">Domínio</label>
              <select
                value={domain} onChange={e => setDomain(e.target.value)}
                className="w-full border border-lia-border-subtle rounded-lg px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary focus:outline-none focus:ring-2 focus:ring-wedo-cyan/30"
              >
                <option value="general">Geral</option>
                <option value="sourcing">Sourcing</option>
                <option value="pipeline">Pipeline</option>
                <option value="analytics">Análises</option>
                <option value="communication">Comunicação</option>
                <option value="screening">Triagem</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-lia-text-primary mb-1 block">Max Steps</label>
              <input
                type="number" value={maxSteps} onChange={e => setMaxSteps(Number(e.target.value))}
                min={1} max={20}
                className="w-full border border-lia-border-subtle rounded-lg px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary focus:outline-none focus:ring-2 focus:ring-wedo-cyan/30"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-lia-text-primary mb-1 block">Temperatura</label>
              <input
                type="number" value={temperature} onChange={e => setTemperature(Number(e.target.value))}
                min={0} max={2} step={0.1}
                className="w-full border border-lia-border-subtle rounded-lg px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary focus:outline-none focus:ring-2 focus:ring-wedo-cyan/30"
              />
            </div>
          </div>

          {error && (
            <div className="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/20 rounded-lg px-3 py-2">
              {error}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={onClose} disabled={isSaving}>Cancelar</Button>
          <Button
            onClick={handleSave}
            disabled={isSaving || !name || !role || !systemPrompt}
            className="bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
          >
            {isSaving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
            {isEditing ? "Salvar Alterações" : "Criar Agente"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function TestAgentModal({ agent, onClose }: { agent: CustomAgent; onClose: () => void }) {
  const [message, setMessage] = useState("")
  const [response, setResponse] = useState("")
  const [isRunning, setIsRunning] = useState(false)

  const handleTest = async () => {
    if (!message.trim()) return
    setIsRunning(true)
    setResponse("")
    try {
      const res = await fetch(`/api/backend-proxy/custom-agents/${agent.id}/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      })
      if (res.ok) {
        const data = await res.json()
        setResponse(data.response || "Sem resposta")
      } else {
        setResponse("Erro ao testar o agente")
      }
    } catch {
      setResponse("Erro de conexão")
    } finally {
      setIsRunning(false)
    }
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-xl bg-lia-bg-primary border-lia-border-subtle">
        <DialogHeader>
          <DialogTitle className="text-base font-semibold text-lia-text-primary flex items-center gap-2">
            <TestTube2 className="w-4 h-4 text-wedo-cyan" />
            Testar: {agent.name}
          </DialogTitle>
          <DialogDescription className="sr-only">Teste o agente com uma mensagem</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div>
            <label className="text-xs font-semibold text-lia-text-primary mb-1 block">Mensagem de teste</label>
            <textarea
              value={message} onChange={e => setMessage(e.target.value)}
              rows={3}
              placeholder="Digite uma mensagem para testar o agente..."
              className="w-full border border-lia-border-subtle rounded-lg px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-wedo-cyan/30 resize-none"
              onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleTest() } }}
            />
          </div>

          <Button
            onClick={handleTest}
            disabled={isRunning || !message.trim()}
            className="w-full bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
          >
            {isRunning ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Play className="w-4 h-4 mr-2" />}
            Executar Teste
          </Button>

          {response && (
            <div className="rounded-lg border border-lia-border-subtle bg-lia-bg-secondary p-4">
              <div className="flex items-center gap-1.5 mb-2">
                <Bot className="w-3.5 h-3.5 text-wedo-cyan" />
                <span className="text-[10px] font-semibold text-lia-text-secondary uppercase">Resposta do agente</span>
              </div>
              <p className="text-sm text-lia-text-primary whitespace-pre-wrap">{response}</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
