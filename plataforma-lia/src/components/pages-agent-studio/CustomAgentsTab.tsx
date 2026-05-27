"use client"

import React, { useState, useEffect, useCallback } from "react"
import { useTranslations } from "next-intl"
import { Bot, ChevronRight, Copy, Edit3, ExternalLink, Loader2, MoreVertical, Pause, Play, Plus, Settings, Store, TestTube2, Trash2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { ConfirmAlertDialog } from "@/components/agent-studio/confirm-alert-dialog"
import { getCustomAgentStatusConfig } from "@/lib/agent-studio/status-config"
import { Button } from "@/components/ui/button"
import { TabSectionHeader } from "@/components/pages-agent-studio/TabSectionHeader"
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

// UX-Sprint-A QW#18 Batch 3 (audit 2026-05-21): STATUS_CONFIG extraído para
// lib/agent-studio/status-config.ts canonical (3 duplicações eliminadas).
// Label keys mantidas locais para i18n namespace customAgents.
const STATUS_LABELS = {
  draft: "statusDraft",
  active: "statusActive",
  paused: "statusPaused",
  archived: "statusArchived",
}

export default function CustomAgentsTab() {
  const t = useTranslations('agents.customAgents')
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

  // Sprint B QW#4 audit 2026-05-22: state-driven confirm via shadcn AlertDialog
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null)

  const handleDelete = (agentId: string) => {
    setDeleteTargetId(agentId)
  }

  const confirmDelete = async () => {
    if (!deleteTargetId) return
    try {
      await fetch(`/api/backend-proxy/custom-agents/${deleteTargetId}`, { method: "DELETE" })
      loadAgents()
    } catch (err) {
      console.error("Failed to delete agent:", err)
    } finally {
      setDeleteTargetId(null)
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
          <span className="text-xs">{t('loadingCustomAgents')}</span>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <TabSectionHeader
        title={t('customAgentsTitle')}
        subtitle={t('customAgentsSubtitle')}
        count={total}
        actions={
          <Button
            size="sm"
            onClick={() => { setEditingAgent(null); setShowCreateModal(true) }}
            className="gap-2 bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
          >
            <Plus className="w-4 h-4" />
            {t('newCustomAgent')}
          </Button>
        }
      />

      {agents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 rounded-md border border-dashed border-lia-border-subtle bg-lia-bg-secondary/50">
          <div className="w-14 h-14 rounded-2xl bg-lia-bg-tertiary flex items-center justify-center mb-3">
            <Bot className="w-7 h-7 text-lia-text-disabled" />
          </div>
          <p className="text-sm font-medium text-lia-text-secondary">{t('noCustomAgents')}</p>
          <p className="text-xs text-lia-text-disabled mt-1 mb-4">
            {t('createCustomHint')}
          </p>
          <Button
            size="sm"
            onClick={() => setShowCreateModal(true)}
            className="gap-2 bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
          >
            <Plus className="w-3.5 h-3.5" />
            {t('createFirstAgent')}
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map(agent => {
            const statusConf = getCustomAgentStatusConfig(agent.status)
            return (
              <div
                key={agent.id}
                className={cn(
                  "group relative rounded-md border border-lia-border-subtle bg-lia-bg-secondary",
                  "hover:border-lia-border-medium hover:shadow-md transition-colors duration-200"
                )}
              >
                <div className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-powder border border-mist flex items-center justify-center text-lg">
                        {agent.icon || "🤖"}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-lia-text-primary">{agent.name}</p>
                        <p className="text-[10px] text-lia-text-secondary">{agent.role}</p>
                      </div>
                    </div>
                    <div className={cn("flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold", statusConf.bg, statusConf.text)}>
                      <div className={cn("w-1.5 h-1.5 rounded-full", statusConf.dot)} />
                      {t(STATUS_LABELS[agent.status as keyof typeof STATUS_LABELS])}
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
                      <span className="text-[9px] text-lia-text-disabled uppercase">{t('executions')}</span>
                    </div>
                    <div className="flex flex-col items-center p-2 rounded-lg bg-lia-bg-primary">
                      <span className="text-xs font-bold text-lia-text-primary">v{agent.version}</span>
                      <span className="text-[9px] text-lia-text-disabled uppercase">{t('version')}</span>
                    </div>
                    <div className="flex flex-col items-center p-2 rounded-lg bg-lia-bg-primary">
                      <span className="text-xs font-bold text-lia-text-primary">{agent.domain}</span>
                      <span className="text-[9px] text-lia-text-disabled uppercase">{t('domain')}</span>
                    </div>
                  </div>

                  {agent.is_marketplace_published && (
                    <div className="flex items-center gap-1.5 mb-3 px-2.5 py-1.5 rounded-lg bg-violet-50 dark:bg-violet-950/20 border border-violet-200 dark:border-violet-800">
                      <Store className="w-3 h-3 text-violet-500" />
                      <span className="text-[10px] text-violet-700 dark:text-violet-400 font-medium">{t('publishedMarketplace')}</span>
                    </div>
                  )}

                  <div className="flex items-center gap-2 pt-3 border-t border-lia-border-subtle">
                    <button
                      onClick={() => setTestingAgent(agent)}
                      className="flex items-center justify-center gap-1.5 h-8 px-3 rounded-lg border border-lia-border-subtle text-xs font-medium text-lia-text-secondary hover:bg-lia-bg-tertiary transition-colors"
                    >
                      <TestTube2 className="w-3.5 h-3.5" />
                      {t('test')}
                    </button>
                    <button
                      onClick={() => { setEditingAgent(agent); setShowCreateModal(true) }}
                      className="flex items-center justify-center gap-1.5 h-8 px-3 rounded-lg border border-lia-border-subtle text-xs font-medium text-lia-text-secondary hover:bg-lia-bg-tertiary transition-colors"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                      {t('edit')}
                    </button>
                    {agent.status === "active" ? (
                      <button
                        onClick={() => handleStatusChange(agent.id, "paused")}
                        className="flex items-center justify-center w-8 h-8 rounded-lg border border-lia-border-subtle hover:bg-lia-bg-tertiary transition-colors"
                        title={t('pause')}
                      >
                        <Pause className="w-3.5 h-3.5 text-amber-500" />
                      </button>
                    ) : agent.status !== "archived" ? (
                      <button
                        onClick={() => handleStatusChange(agent.id, "active")}
                        className="flex items-center justify-center w-8 h-8 rounded-lg border border-lia-border-subtle hover:bg-lia-bg-tertiary transition-colors"
                        title={t('activate')}
                      >
                        <Play className="w-3.5 h-3.5 text-emerald-500" />
                      </button>
                    ) : null}
                    <button
                      onClick={() => handleDelete(agent.id)}
                      className="flex items-center justify-center w-8 h-8 rounded-lg border border-lia-border-subtle hover:bg-red-50 dark:hover:bg-red-950/20 transition-colors ml-auto"
                      title={t('deleteAgent')}
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
          {/* Sprint B QW#4 audit 2026-05-22: ConfirmAlertDialog canonical (era native confirm) */}
      <ConfirmAlertDialog
        open={deleteTargetId !== null}
        onOpenChange={(open) => !open && setDeleteTargetId(null)}
        title={t('confirmDeleteTitle') || 'Excluir agente?'}
        description={t('confirmDeleteAgent')}
        onConfirm={confirmDelete}
        confirmLabel={t('delete') || 'Excluir'}
        destructive
      />

      </div>
  )
}

export function CreateCustomAgentModal({
  agent, onClose, onSaved,
}: {
  agent: CustomAgent | null
  onClose: () => void
  onSaved: () => void
}) {
  const t = useTranslations('agents.customAgents')
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
        throw new Error(errData?.detail || `Error ${res.status}`)
      }

      onSaved()
    } catch (err) {
      setError(err instanceof Error ? err.message : t('errors.errorSaving'))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-2xl bg-lia-bg-primary border-lia-border-subtle max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-base font-semibold text-lia-text-primary flex items-center gap-2">
            <Bot className="w-4 h-4 text-graphite" />
            {isEditing ? t('editCustomAgent') : t('createCustomAgent')}
          </DialogTitle>
          <DialogDescription className="sr-only">{t('configureAgent')}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-lia-text-primary mb-1 block">{t('name')}</label>
              <input
                type="text" value={name} onChange={e => setName(e.target.value)}
                placeholder={t('namePlaceholder')}
                className="w-full border border-lia-border-subtle rounded-lg px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-lia-text-primary mb-1 block">{t('role')}</label>
              <input
                type="text" value={role} onChange={e => setRole(e.target.value)}
                placeholder={t('rolePlaceholder')}
                className="w-full border border-lia-border-subtle rounded-lg px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-lia-text-primary mb-1 block">{t('description')}</label>
            <input
              type="text" value={description} onChange={e => setDescription(e.target.value)}
              placeholder={t('descriptionPlaceholder')}
              className="w-full border border-lia-border-subtle rounded-lg px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-lia-text-primary mb-1 block">{t('systemPrompt')}</label>
            <textarea
              value={systemPrompt} onChange={e => setSystemPrompt(e.target.value)}
              rows={6}
              placeholder={t('systemPromptPlaceholder') as string}
              className="w-full border border-lia-border-subtle rounded-lg px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30 resize-none font-mono"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-lia-text-primary mb-1 block">
              {t('allowedTools')}
              {availableTools.length > 0 && (
                <span className="font-normal text-lia-text-disabled ml-1">({availableTools.length} {t('available')})</span>
              )}
            </label>
            <input
              type="text" value={toolsInput} onChange={e => setToolsInput(e.target.value)}
              placeholder="search_candidates, list_jobs, get_candidate_details"
              className="w-full border border-lia-border-subtle rounded-lg px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30"
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
              <label className="text-xs font-semibold text-lia-text-primary mb-1 block">{t('domainLabel')}</label>
              <select
                value={domain} onChange={e => setDomain(e.target.value)}
                className="w-full border border-lia-border-subtle rounded-lg px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30"
              >
                <option value="general">{t('domainGeneral')}</option>
                <option value="sourcing">{t('domainSourcing')}</option>
                <option value="pipeline">{t('domainPipeline')}</option>
                <option value="analytics">{t('domainAnalytics')}</option>
                <option value="communication">{t('domainCommunication')}</option>
                <option value="screening">{t('domainScreening')}</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-lia-text-primary mb-1 block">{t('maxSteps')}</label>
              <input
                type="number" value={maxSteps} onChange={e => setMaxSteps(Number(e.target.value))}
                min={1} max={20}
                className="w-full border border-lia-border-subtle rounded-lg px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-lia-text-primary mb-1 block">{t('temperature')}</label>
              <input
                type="number" value={temperature} onChange={e => setTemperature(Number(e.target.value))}
                min={0} max={2} step={0.1}
                className="w-full border border-lia-border-subtle rounded-lg px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30"
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
          <Button variant="ghost" onClick={onClose} disabled={isSaving}>{t('cancel')}</Button>
          <Button
            onClick={handleSave}
            disabled={isSaving || !name || !role || !systemPrompt}
            className="bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
          >
            {isSaving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
            {isEditing ? t('saveChanges') : t('createAgent')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function TestAgentModal({ agent, onClose }: { agent: CustomAgent; onClose: () => void }) {
  const t = useTranslations('agents.customAgents')
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
        setResponse(data.response || t('noResponse'))
      } else {
        setResponse(t('errorTestAgent'))
      }
    } catch {
      setResponse(t('connectionError'))
    } finally {
      setIsRunning(false)
    }
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-xl bg-lia-bg-primary border-lia-border-subtle">
        <DialogHeader>
          <DialogTitle className="text-base font-semibold text-lia-text-primary flex items-center gap-2">
            <TestTube2 className="w-4 h-4 text-graphite" />
            {t('testAgent')}: {agent.name}
          </DialogTitle>
          <DialogDescription className="sr-only">{t('testAgent')}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div>
            <label className="text-xs font-semibold text-lia-text-primary mb-1 block">{t('testMessage')}</label>
            <textarea
              value={message} onChange={e => setMessage(e.target.value)}
              rows={3}
              placeholder={t('typeMessage') as string}
              className="w-full border border-lia-border-subtle rounded-lg px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30 resize-none"
              onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleTest() } }}
            />
          </div>

          <Button
            onClick={handleTest}
            disabled={isRunning || !message.trim()}
            className="w-full bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
          >
            {isRunning ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Play className="w-4 h-4 mr-2" />}
            {t('runTest')}
          </Button>

          {response && (
            <div className="rounded-lg border border-lia-border-subtle bg-lia-bg-secondary p-4">
              <div className="flex items-center gap-1.5 mb-2">
                <Bot className="w-3.5 h-3.5 text-graphite" />
                <span className="text-[10px] font-semibold text-lia-text-secondary uppercase">{t('agentResponse')}</span>
              </div>
              <p className="text-sm text-lia-text-primary whitespace-pre-wrap">{response}</p>
            </div>
          )}
      </div>
      </DialogContent>
    </Dialog>
  )
}
