"use client"

import React, { useState } from "react"
import { Wand2, Loader2, Check, ChevronDown, ChevronUp } from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { cardStyles, buttonStyles, textStyles, inputStyles, badgeStyles } from "@/lib/design-tokens"
import { toast } from "@/lib/toast"
import { BetaBadge } from "@/components/ui/beta-badge"
import type { AgentCategory } from "./types"

/**
 * Shape of the config returned by POST /api/backend-proxy/custom-agents/generate.
 *
 * All fields are optional because the backend may return null/missing values
 * when the LLM fails to produce a complete JSON. Defenders below (`config?.field ?? default`)
 * guarantee the UI never crashes regardless of backend shape.
 *
 * Backend contract (defensive): app/api/v1/custom_agents.py uses _coalesce()
 * to convert null → defaults before responding, so in practice fields should
 * always be populated. This optional typing is belt-and-suspenders.
 */
interface GeneratedConfig {
  suggested_name?: string
  suggested_role?: string
  suggested_domain?: string
  suggested_tools?: string[]
  suggested_prompt?: string
  suggested_context_level?: string
  suggested_max_steps?: number
  suggested_temperature?: number
  reasoning?: string
}

interface ConversationalCreatorProps {
  onAgentCreated: () => void
}

export function ConversationalCreator({ onAgentCreated }: ConversationalCreatorProps) {
  const t = useTranslations('agents.customAgents')
  const tToast = useTranslations('agents.toast')
  const [description, setDescription] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)
  const [config, setConfig] = useState<GeneratedConfig | null>(null)
  const [showPrompt, setShowPrompt] = useState(false)
  const [isCreating, setIsCreating] = useState(false)

  const handleGenerate = async () => {
    if (!description.trim() || description.length < 10) return
    setIsGenerating(true)
    setConfig(null)
    try {
      const res = await fetch("/api/backend-proxy/custom-agents/generate", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Error" }))
        throw new Error(err.detail || tToast('errorGenerating'))
      }
      const data = await res.json()
      // Validate response shape — backend should never return non-object,
      // but defend against proxy/network corruption.
      if (!data || typeof data !== "object") {
        throw new Error(tToast('errorGenerating'))
      }
      setConfig(data)
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : tToast('errorGenerating'))
    } finally {
      setIsGenerating(false)
    }
  }

  const handleCreate = async () => {
    if (!config) return
    setIsCreating(true)
    try {
      // Apply same defaults the UI uses when the backend response is partial,
      // so created agents are never persisted with null/empty critical fields.
      const safeName = config.suggested_name ?? "Novo Agente"
      const safeRole = config.suggested_role ?? description.slice(0, 200)
      const safeDomain = config.suggested_domain ?? "general"
      const safeTools = config.suggested_tools ?? ["search_candidates", "get_candidate_details"]
      const safeContextLevel = config.suggested_context_level ?? "standard"
      const safeMaxSteps = config.suggested_max_steps ?? 8
      const safeTemperature = config.suggested_temperature ?? 0.5

      const res = await fetch("/api/backend-proxy/custom-agents", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: safeName,
          role: safeRole,
          description: safeRole,
          system_prompt: config.suggested_prompt ?? "",
          allowed_tools: safeTools,
          domain: safeDomain,
          context_level: safeContextLevel,
          max_steps: safeMaxSteps,
          temperature: safeTemperature,
        }),
      })
      if (!res.ok) throw new Error(tToast('errorCreatingAgent'))
      toast.success(tToast('agentCreated', { name: safeName }), tToast('agentCreatedDesc'))
      setConfig(null)
      setDescription("")
      onAgentCreated()
    } catch {
      toast.error(tToast('errorCreatingAgent'))
    } finally {
      setIsCreating(false)
    }
  }

  // Defensive: backend should always populate suggested_domain via _coalesce(),
  // but if the LLM emits null and the helper is not deployed yet, fall back
  // to "general" instead of resolving categories.undefined (i18n MISSING_MESSAGE).
  const domainKey = config?.suggested_domain ?? "general"
  const domainLabel = config
    ? (t('categories.' + (domainKey as AgentCategory)) || domainKey)
    : ""

  return (
    <div className={cn(cardStyles.default, "p-5")}>
      <div className="flex items-center gap-2 mb-3">
        <Wand2 className="w-4 h-4 text-wedo-cyan-dark" />
        <h3 className={cn(textStyles.subtitle, "text-sm font-semibold")}>{t('createWithAI')}</h3>
        <BetaBadge size="sm" />
      </div>

      <p className={cn(textStyles.caption, "mb-3 text-xs")}>
        {t('describeNeed')}
      </p>

      {/* Input */}
      <div className="flex gap-2">
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder={t('aiPlaceholder')}
          rows={2}
          className={cn(inputStyles.default, "flex-1 text-sm resize-none")}
        />
        <button
          type="button"
          onClick={handleGenerate}
          disabled={isGenerating || description.length < 10}
          className={cn(buttonStyles.primary, "px-4 py-2 text-xs self-end shrink-0")}
        >
          {isGenerating ? <Loader2 className="w-4 h-4 animate-spin" /> : t('generate')}
        </button>
      </div>

      {/* Generated Config Preview */}
      {config && (
        <div className="mt-4 space-y-3">
          <div className="flex items-center gap-2">
            <Check className="w-4 h-4 text-emerald-500" />
            <span className={cn(textStyles.subtitle, "text-sm font-semibold")}>
              {t('suggestedConfig')}
            </span>
          </div>

          <div className={cn(cardStyles.flat, "p-4 space-y-2")}>
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-lia-text-primary">
                {config.suggested_name ?? t('defaultAgentName') ?? "Novo Agente"}
              </span>
              <span className={badgeStyles.cyan}>{domainLabel}</span>
            </div>
            <p className="text-xs text-lia-text-secondary">{config.suggested_role ?? ""}</p>

            <div className="flex flex-wrap gap-1 pt-1">
              {(config.suggested_tools ?? []).map((tool) => (
                <span key={tool} className={cn(badgeStyles.default, "text-[10px]")}>
                  {t('tools.' + tool) || tool}
                </span>
              ))}
            </div>

            <div className="flex items-center gap-3 pt-1 text-[10px] text-lia-text-muted">
              <span>{t('context')}: {config.suggested_context_level ?? "standard"}</span>
              <span>{t('steps')}: {config.suggested_max_steps ?? 8}</span>
              <span>{t('temp')}: {config.suggested_temperature ?? 0.5}</span>
            </div>

            {config.reasoning && (
              <p className="text-[11px] text-wedo-cyan-text italic pt-1">
                LIA: {config.reasoning}
              </p>
            )}

            {/* Collapsible prompt */}
            <button
              type="button"
              onClick={() => setShowPrompt(!showPrompt)}
              className="flex items-center gap-1 text-[10px] text-lia-text-muted hover:text-lia-text-secondary pt-1"
            >
              {showPrompt ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              {showPrompt ? t('hidePrompt') : t('viewFullPrompt')}
            </button>
            {showPrompt && (
              <pre className="text-[10px] text-lia-text-secondary bg-lia-bg-tertiary rounded-md p-3 overflow-auto max-h-32 whitespace-pre-wrap font-mono">
                {config.suggested_prompt ?? ""}
              </pre>
            )}
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleCreate}
              disabled={isCreating}
              className={cn(buttonStyles.primary, "text-xs px-4 py-1.5")}
            >
              {isCreating ? t('creatingAgent') : t('createAgentBtn')}
            </button>
            <button
              type="button"
              onClick={() => { setConfig(null); setDescription("") }}
              className={cn(buttonStyles.ghost, "text-xs px-3 py-1.5")}
            >
              {t('startOver')}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
