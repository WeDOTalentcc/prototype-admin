"use client"

import React, { useState } from "react"
import { Wand2, Loader2, Check, ChevronDown, ChevronUp } from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { cardStyles, buttonStyles, textStyles, inputStyles, badgeStyles } from "@/lib/design-tokens"
import { toast } from "@/lib/toast"
import { BetaBadge } from "@/components/ui/beta-badge"
import { safeCategoryKey } from "./types"

interface GeneratedConfig {
  suggested_name: string
  suggested_role: string
  suggested_domain: string
  suggested_tools: string[]
  suggested_prompt: string
  suggested_context_level: string
  suggested_max_steps: number
  suggested_temperature: number
  reasoning: string
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
      const token = localStorage.getItem("auth_token")
      const res = await fetch("/api/backend-proxy/custom-agents/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ description }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Error" }))
        throw new Error(err.detail || tToast('errorGenerating'))
      }
      const data = await res.json()
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
      const token = localStorage.getItem("auth_token")
      const res = await fetch("/api/backend-proxy/custom-agents", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          name: config.suggested_name,
          role: config.suggested_role,
          description: config.suggested_role,
          system_prompt: config.suggested_prompt,
          allowed_tools: config.suggested_tools,
          domain: config.suggested_domain,
          context_level: config.suggested_context_level,
          max_steps: config.suggested_max_steps,
          temperature: config.suggested_temperature,
        }),
      })
      if (!res.ok) throw new Error(tToast('errorCreatingAgent'))
      toast.success(tToast('agentCreated', { name: config.suggested_name }), tToast('agentCreatedDesc'))
      setConfig(null)
      setDescription("")
      onAgentCreated()
    } catch {
      toast.error(tToast('errorCreatingAgent'))
    } finally {
      setIsCreating(false)
    }
  }

  const domainLabel = config ? (t('categories.' + safeCategoryKey(config.suggested_domain)) || config.suggested_domain || 'general') : ""

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
              <span className="text-sm font-semibold text-lia-text-primary">{config.suggested_name}</span>
              <span className={badgeStyles.cyan}>{domainLabel}</span>
            </div>
            <p className="text-xs text-lia-text-secondary">{config.suggested_role}</p>

            <div className="flex flex-wrap gap-1 pt-1">
              {config.suggested_tools.map((tool) => (
                <span key={tool} className={cn(badgeStyles.default, "text-[10px]")}>
                  {t('tools.' + tool) || tool}
                </span>
              ))}
            </div>

            <div className="flex items-center gap-3 pt-1 text-[10px] text-lia-text-disabled">
              <span>{t('context')}: {config.suggested_context_level}</span>
              <span>{t('steps')}: {config.suggested_max_steps}</span>
              <span>{t('temp')}: {config.suggested_temperature}</span>
            </div>

            {config.reasoning && (
              <p className="text-[11px] text-wedo-cyan-dark italic pt-1">
                LIA: {config.reasoning}
              </p>
            )}

            {/* Collapsible prompt */}
            <button
              type="button"
              onClick={() => setShowPrompt(!showPrompt)}
              className="flex items-center gap-1 text-[10px] text-lia-text-disabled hover:text-lia-text-secondary pt-1"
            >
              {showPrompt ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              {showPrompt ? t('hidePrompt') : t('viewFullPrompt')}
            </button>
            {showPrompt && (
              <pre className="text-[10px] text-lia-text-secondary bg-lia-bg-tertiary rounded-md p-3 overflow-auto max-h-32 whitespace-pre-wrap font-mono">
                {config.suggested_prompt}
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
