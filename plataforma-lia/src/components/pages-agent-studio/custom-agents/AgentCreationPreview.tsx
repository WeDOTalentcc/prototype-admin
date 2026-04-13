"use client"

import React, { useState, useEffect } from "react"
import { Wand2, Check, X, Loader2, ChevronDown, ChevronUp } from "lucide-react"
import { cn } from "@/lib/utils"
import { cardStyles, badgeStyles, textStyles, buttonStyles } from "@/lib/design-tokens"
import { BetaBadge } from "@/components/ui/beta-badge"
import { toast } from "@/lib/toast"
import { CATEGORY_LABELS, TOOL_LABELS } from "./types"
import type { AgentCategory } from "./types"

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

interface AgentCreationPreviewProps {
  description: string
  onClose: () => void
  onCreated?: (agentId: string) => void
}

export function AgentCreationPreview({ description, onClose, onCreated }: AgentCreationPreviewProps) {
  const [config, setConfig] = useState<GeneratedConfig | null>(null)
  const [isGenerating, setIsGenerating] = useState(true)
  const [isCreating, setIsCreating] = useState(false)
  const [showPrompt, setShowPrompt] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const generate = async () => {
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
          const err = await res.json().catch(() => ({ detail: "Erro" }))
          throw new Error(err.detail || "Erro ao gerar")
        }
        const data = await res.json()
        if (!cancelled) setConfig(data)
      } catch (e: unknown) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Erro ao gerar configuracao")
      } finally {
        if (!cancelled) setIsGenerating(false)
      }
    }
    generate()
    return () => { cancelled = true }
  }, [description])

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
      if (!res.ok) throw new Error("Erro ao criar")
      const agent = await res.json()
      toast.success(`Agente "${config.suggested_name}" criado!`, "Agora vincule a uma vaga ou pool.")
      onCreated?.(agent.id)
      onClose()
    } catch {
      toast.error("Erro ao criar agente")
    } finally {
      setIsCreating(false)
    }
  }

  const domainLabel = config ? (CATEGORY_LABELS[config.suggested_domain as AgentCategory] || config.suggested_domain) : ""

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-lia-border-subtle">
        <div className="flex items-center gap-2">
          <Wand2 className="w-4 h-4 text-wedo-cyan-dark" />
          <h3 className={cn(textStyles.subtitle, "text-sm font-semibold")}>Novo Agente</h3>
          <BetaBadge size="sm" />
        </div>
        <button type="button" onClick={onClose} className="text-lia-text-disabled hover:text-lia-text-secondary">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-auto p-4 space-y-3">
        <div className={cn(cardStyles.flat, "p-3")}>
          <p className="text-[10px] text-lia-text-disabled uppercase font-semibold">Sua solicitacao</p>
          <p className="text-xs text-lia-text-secondary mt-1">{description}</p>
        </div>

        {isGenerating && (
          <div className="flex items-center gap-2 py-8 justify-center">
            <Loader2 className="w-4 h-4 animate-spin text-wedo-cyan-dark" />
            <span className="text-xs text-lia-text-secondary">LIA esta configurando o agente...</span>
          </div>
        )}

        {error && (
          <div className={cn(cardStyles.default, "p-3 border-red-200")}>
            <p className="text-xs text-red-600">{error}</p>
          </div>
        )}

        {config && (
          <>
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-500" />
              <span className={cn(textStyles.subtitle, "text-sm font-semibold")}>Configuracao sugerida</span>
            </div>

            <div className={cn(cardStyles.default, "p-4 space-y-2")}>
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-lia-text-primary">{config.suggested_name}</span>
                <span className={badgeStyles.cyan}>{domainLabel}</span>
              </div>
              <p className="text-xs text-lia-text-secondary">{config.suggested_role}</p>

              <div className="flex flex-wrap gap-1 pt-1">
                {config.suggested_tools.map((tool) => (
                  <span key={tool} className={cn(badgeStyles.default, "text-[10px]")}>
                    {TOOL_LABELS[tool] || tool}
                  </span>
                ))}
              </div>

              <div className="flex items-center gap-3 pt-1 text-[10px] text-lia-text-disabled">
                <span>Contexto: {config.suggested_context_level}</span>
                <span>Steps: {config.suggested_max_steps}</span>
                <span>Temp: {config.suggested_temperature}</span>
              </div>

              {config.reasoning && (
                <p className="text-[11px] text-wedo-cyan-dark italic pt-1">
                  LIA: {config.reasoning}
                </p>
              )}

              <button
                type="button"
                onClick={() => setShowPrompt(!showPrompt)}
                className="flex items-center gap-1 text-[10px] text-lia-text-disabled hover:text-lia-text-secondary pt-1"
              >
                {showPrompt ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                {showPrompt ? "Ocultar prompt" : "Ver prompt completo"}
              </button>
              {showPrompt && (
                <pre className="text-[10px] text-lia-text-secondary bg-lia-bg-tertiary rounded-md p-3 overflow-auto max-h-32 whitespace-pre-wrap font-mono">
                  {config.suggested_prompt}
                </pre>
              )}
            </div>
          </>
        )}
      </div>

      {/* Footer */}
      {config && (
        <div className="p-4 border-t border-lia-border-subtle flex gap-2">
          <button
            type="button"
            onClick={handleCreate}
            disabled={isCreating}
            className={cn(buttonStyles.primary, "flex-1 text-xs px-4 py-2")}
          >
            {isCreating ? "Criando..." : "Criar agente"}
          </button>
          <button
            type="button"
            onClick={onClose}
            className={cn(buttonStyles.ghost, "text-xs px-3 py-2")}
          >
            Cancelar
          </button>
        </div>
      )}
    </div>
  )
}
