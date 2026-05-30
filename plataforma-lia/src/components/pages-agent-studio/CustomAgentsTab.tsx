"use client"

import React, { useState, useEffect, useCallback, useMemo } from "react"
import { useTranslations } from "next-intl"
import { Bot, ChevronRight, Copy, Edit3, ExternalLink, Loader2, MoreVertical, Pause, Play, Plus, Settings, Sliders, Store, TestTube2, Trash2 } from "lucide-react"
import { cn } from "@/lib/utils"
// Sprint 4 Fase 3 (Studio Experience) — config humana `/edit`. Ferramentas como
// checkboxes agrupados em PT (TOOL_GROUP/CAPABILITY_GROUP_ORDER), nunca slug cru.
import { TOOL_GROUP, CAPABILITY_GROUP_ORDER, type CapabilityGroup } from "@/lib/agents/tool-capabilities"
import { ConfirmAlertDialog } from "@/components/agent-studio/confirm-alert-dialog"
import { getCustomAgentStatusConfig } from "@/lib/agent-studio/status-config"
import { Button } from "@/components/ui/button"
import { TabSectionHeader } from "@/components/pages-agent-studio/TabSectionHeader"
// Onda 4 F6.1 — empty state persona-aware canonical
import { StudioEmptyState } from "@/components/pages-agent-studio/StudioEmptyState"
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogDescription, DialogFooter,
} from "@/components/ui/dialog"
// White-label canonical 2026-05-29: persona do cliente como fallback do nome
// quando agent.name está vazio (edge case durante criação/erro).
import { useAiPersona } from "@/hooks/company/use-ai-persona"

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
  // White-label canonical: fallback do nome do agente no card list.
  const { persona: aiPersona } = useAiPersona()
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
        // Onda 4 F6.1 — empty state persona-aware com 2 CTAs (marketplace + chat).
        // Original "createFirstAgent" inline state substituído pelo canonical.
        <StudioEmptyState
          onExploreMarketplace={() => {
            // Switch para tab Marketplace dentro do Studio.
            // Default fallback do componente já navega via ?tab=marketplace, mas
            // como o CustomAgentsTab é um sub-tab, prefer keeping in same surface.
            if (typeof window !== "undefined") {
              window.dispatchEvent(new CustomEvent("studio:open-marketplace"))
            }
          }}
        />
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
                        <p className="text-sm font-semibold text-lia-text-primary">{agent.name || aiPersona?.name || t('untitledAgent')}</p>
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

// Sprint 4 Fase 3 — "Estilo de resposta" amigável mapeia para valores de
// temperatura que o backend espera. O recrutador NUNCA vê o número; a UI fala
// "Consistente / Equilibrado / Criativo". Mapeamento bidirecional canonical.
type ResponseStyle = "consistent" | "balanced" | "creative"

const RESPONSE_STYLE_TO_TEMPERATURE: Record<ResponseStyle, number> = {
  consistent: 0.2,
  balanced: 0.5,
  creative: 0.8,
}

const RESPONSE_STYLE_ORDER: readonly ResponseStyle[] = ["consistent", "balanced", "creative"] as const

/** Inverte um valor de temperatura numérico no preset mais próximo. */
function temperatureToResponseStyle(value: number | undefined): ResponseStyle {
  if (value == null) return "balanced"
  let closest: ResponseStyle = "balanced"
  let smallestDelta = Number.POSITIVE_INFINITY
  for (const style of RESPONSE_STYLE_ORDER) {
    const delta = Math.abs(RESPONSE_STYLE_TO_TEMPERATURE[style] - value)
    if (delta < smallestDelta) {
      smallestDelta = delta
      closest = style
    }
  }
  return closest
}

/** i18n key suffix por preset (responseStyleLabel/Desc + ícone semântico). */
const RESPONSE_STYLE_I18N: Record<ResponseStyle, { label: string; desc: string }> = {
  consistent: { label: "styleConsistent", desc: "styleConsistentDesc" },
  balanced: { label: "styleBalanced", desc: "styleBalancedDesc" },
  creative: { label: "styleCreative", desc: "styleCreativeDesc" },
}

/** i18n key suffix por grupo de capacidade (cabeçalho do bloco de checkboxes). */
const CAPABILITY_GROUP_I18N: Record<CapabilityGroup, string> = {
  find: "groupFind",
  analyze: "groupAnalyze",
  act: "groupAct",
  communicate: "groupCommunicate",
  report: "groupReport",
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
  // Estilo de resposta (preset amigável) deriva da temperatura existente ao
  // editar; no submit volta a número via RESPONSE_STYLE_TO_TEMPERATURE.
  const [responseStyle, setResponseStyle] = useState<ResponseStyle>(
    () => temperatureToResponseStyle(agent?.temperature)
  )
  // Ferramentas como Set de slugs canonical (checkbox marcado = slug presente).
  const [selectedTools, setSelectedTools] = useState<Set<string>>(
    () => new Set(agent?.allowed_tools || [])
  )
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState("")
  const [availableTools, setAvailableTools] = useState<string[]>([])

  useEffect(() => {
    fetch("/api/backend-proxy/custom-agents/available-tools")
      .then(r => r.ok ? r.json() : { tools: [] })
      .then(d => setAvailableTools(d.tools || []))
      .catch(() => {})
  }, [])

  const toggleTool = useCallback((slug: string) => {
    setSelectedTools(prev => {
      const next = new Set(prev)
      if (next.has(slug)) next.delete(slug)
      else next.add(slug)
      return next
    })
  }, [])

  // Universo de tools a oferecer como checkbox: o que o backend expõe (filtrado
  // ao que tem grupo/rótulo PT conhecido) + tools já marcadas no agente sendo
  // editado (garante que nada selecionado some). Fallback: catálogo canonical.
  const toolUniverse = useMemo(() => {
    const fromBackend = availableTools.filter(slug => TOOL_GROUP[slug])
    const base = fromBackend.length > 0 ? fromBackend : Object.keys(TOOL_GROUP)
    const universe = new Set(base)
    // Preserva tools já atribuídas ao agente mesmo que o backend não as liste.
    for (const slug of selectedTools) {
      if (TOOL_GROUP[slug]) universe.add(slug)
    }
    return Array.from(universe)
  }, [availableTools, selectedTools])

  const handleSave = async () => {
    setIsSaving(true)
    setError("")
    try {
      // Contrato backend preservado: slug array + número de temperatura, exatos.
      const allowedTools = Array.from(selectedTools)
      const body = {
        name,
        role,
        description: description || undefined,
        system_prompt: systemPrompt,
        allowed_tools: allowedTools,
        domain,
        max_steps: maxSteps,
        temperature: RESPONSE_STYLE_TO_TEMPERATURE[responseStyle],
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
              <label htmlFor="agent-name" className="text-xs font-semibold text-lia-text-primary mb-1 block">{t('name')}</label>
              <input
                id="agent-name"
                type="text" value={name} onChange={e => setName(e.target.value)}
                placeholder={t('namePlaceholder')}
                className="w-full border border-lia-border-subtle rounded-md px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30"
              />
            </div>
            <div>
              <label htmlFor="agent-role" className="text-xs font-semibold text-lia-text-primary mb-1 block">{t('role')}</label>
              <input
                id="agent-role"
                type="text" value={role} onChange={e => setRole(e.target.value)}
                placeholder={t('rolePlaceholder')}
                className="w-full border border-lia-border-subtle rounded-md px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30"
              />
            </div>
          </div>

          <div>
            <label htmlFor="agent-description" className="text-xs font-semibold text-lia-text-primary mb-1 block">{t('description')}</label>
            <input
              id="agent-description"
              type="text" value={description} onChange={e => setDescription(e.target.value)}
              placeholder={t('descriptionPlaceholder')}
              className="w-full border border-lia-border-subtle rounded-md px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30"
            />
          </div>

          {/* Instruções do agente — antes "System prompt" mono. Humanizado:
              label + placeholder didáticos, sem fonte mono. Mesmo campo, só UI. */}
          <div>
            <label htmlFor="agent-instructions" className="text-xs font-semibold text-lia-text-primary mb-1 block">{t('instructionsLabel')}</label>
            <textarea
              id="agent-instructions"
              value={systemPrompt} onChange={e => setSystemPrompt(e.target.value)}
              rows={5}
              placeholder={t('instructionsPlaceholder') as string}
              className="w-full border border-lia-border-subtle rounded-md px-3 py-2 text-sm leading-relaxed bg-lia-bg-secondary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30 resize-none"
            />
            <p className="text-[11px] text-lia-text-secondary mt-1.5">{t('instructionsHelp')}</p>
          </div>

          {/* Ferramentas — checkboxes agrupados em PT (read/analyze/act/communicate/report).
              Slug interno preservado; só o rótulo é PT (tools.<slug> + groupX). */}
          <fieldset>
            <legend className="text-xs font-semibold text-lia-text-primary mb-1 block">{t('toolsLabel')}</legend>
            <p className="text-[11px] text-lia-text-secondary mb-2.5">{t('toolsHelp')}</p>
            <div className="space-y-3">
              {CAPABILITY_GROUP_ORDER.map(group => {
                const groupTools = toolUniverse.filter(slug => TOOL_GROUP[slug] === group)
                if (groupTools.length === 0) return null
                return (
                  <div key={group}>
                    <p className="text-[10px] font-semibold uppercase tracking-wide text-lia-text-disabled mb-1.5">
                      {t(CAPABILITY_GROUP_I18N[group])}
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                      {groupTools.map(slug => {
                        const checked = selectedTools.has(slug)
                        return (
                          <label
                            key={slug}
                            className={cn(
                              "flex items-center gap-2 rounded-md border px-3 py-2 text-sm cursor-pointer transition-colors",
                              checked
                                ? "border-lia-btn-primary-bg bg-lia-bg-tertiary text-lia-text-primary"
                                : "border-lia-border-subtle bg-lia-bg-secondary text-lia-text-secondary hover:bg-lia-bg-tertiary"
                            )}
                          >
                            <input
                              type="checkbox"
                              checked={checked}
                              onChange={() => toggleTool(slug)}
                              className="h-4 w-4 shrink-0 rounded border-lia-border-medium accent-lia-btn-primary-bg"
                            />
                            <span>{t(`tools.${slug}`)}</span>
                          </label>
                        )
                      })}
                    </div>
                  </div>
                )
              })}
            </div>
          </fieldset>

          {/* Estilo de resposta — segmented Consistente/Equilibrado/Criativo.
              Mapeia pra temperatura no submit. Recrutador não vê o número. */}
          <div>
            <span className="text-xs font-semibold text-lia-text-primary mb-1 block">{t('responseStyleLabel')}</span>
            <div role="radiogroup" aria-label={t('responseStyleLabel')} className="grid grid-cols-3 gap-2">
              {RESPONSE_STYLE_ORDER.map(style => {
                const active = responseStyle === style
                return (
                  <button
                    key={style}
                    type="button"
                    role="radio"
                    aria-checked={active}
                    onClick={() => setResponseStyle(style)}
                    title={t(RESPONSE_STYLE_I18N[style].desc)}
                    className={cn(
                      "rounded-md border px-3 py-2 text-xs font-medium text-center transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30",
                      active
                        ? "border-lia-btn-primary-bg bg-lia-bg-tertiary text-lia-text-primary"
                        : "border-lia-border-subtle bg-lia-bg-secondary text-lia-text-secondary hover:bg-lia-bg-tertiary"
                    )}
                  >
                    {t(RESPONSE_STYLE_I18N[style].label)}
                  </button>
                )
              })}
            </div>
            <p className="text-[11px] text-lia-text-secondary mt-1.5">{t(RESPONSE_STYLE_I18N[responseStyle].desc)}</p>
          </div>

          {/* Configuração avançada — disclosure recolhido por default. Ajustes
              que o recrutador raramente toca: área (domain) + limite de ações. */}
          <details className="rounded-md border border-lia-border-subtle bg-lia-bg-secondary">
            <summary className="flex items-center gap-2 px-3 py-2.5 text-xs font-semibold text-lia-text-primary cursor-pointer select-none list-none">
              <Sliders className="w-3.5 h-3.5 text-graphite" />
              {t('advancedConfig')}
            </summary>
            <div className="px-3 pb-3 pt-1 space-y-3 border-t border-lia-border-subtle">
              <p className="text-[11px] text-lia-text-secondary pt-2">{t('advancedConfigHelp')}</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="agent-domain" className="text-xs font-semibold text-lia-text-primary mb-1 block">{t('domainLabel')}</label>
                  <select
                    id="agent-domain"
                    value={domain} onChange={e => setDomain(e.target.value)}
                    className="w-full border border-lia-border-subtle rounded-md px-3 py-2 text-sm bg-lia-bg-primary text-lia-text-primary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30"
                  >
                    <option value="general">{t('domainGeneral')}</option>
                    <option value="sourcing">{t('domainSourcing')}</option>
                    <option value="pipeline">{t('domainPipeline')}</option>
                    <option value="analytics">{t('domainAnalytics')}</option>
                    <option value="communication">{t('domainCommunication')}</option>
                    <option value="screening">{t('domainScreening')}</option>
                  </select>
                  <p className="text-[11px] text-lia-text-secondary mt-1">{t('domainHelp')}</p>
                </div>
                <div>
                  <label htmlFor="agent-max-steps" className="text-xs font-semibold text-lia-text-primary mb-1 block">{t('maxStepsLabel')}</label>
                  <input
                    id="agent-max-steps"
                    type="number" value={maxSteps} onChange={e => setMaxSteps(Number(e.target.value))}
                    min={1} max={20}
                    className="w-full border border-lia-border-subtle rounded-md px-3 py-2 text-sm bg-lia-bg-primary text-lia-text-primary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30"
                  />
                  <p className="text-[11px] text-lia-text-secondary mt-1">{t('maxStepsHelp')}</p>
                </div>
              </div>
            </div>
          </details>

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
  // White-label canonical: fallback do nome no título do modal de teste.
  const { persona: aiPersona } = useAiPersona()
  const agentDisplayName = agent.name || aiPersona?.name || t('untitledAgent')
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
            {t('testAgent')}: {agentDisplayName}
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
