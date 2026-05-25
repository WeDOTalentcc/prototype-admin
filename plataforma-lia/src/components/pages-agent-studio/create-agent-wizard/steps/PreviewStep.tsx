"use client"

import { Bot, CheckCircle2, Heart, Phone, Search, Settings2, Sparkles } from "lucide-react"
import * as Icons from "lucide-react"

import { useLegacyAgentTemplates } from "@/hooks/agents/use-legacy-agent-templates"

import type { AgentApproach, AgentGoal, GeneratedConfigPreview, WizardConfig } from "../types"

const GOAL_LABELS: Record<AgentGoal, { icon: typeof Sparkles; label: string }> = {
  triagem_inicial: { icon: Sparkles, label: "Triagem inicial automatizada" },
  sourcing_ativo: { icon: Search, label: "Sourcing ativo" },
  screening_cultural: { icon: Heart, label: "Screening cultural / fit" },
  voz_whatsapp: { icon: Phone, label: "Triagem por voz ou WhatsApp" },
  outro: { icon: Settings2, label: "Outro / criar do zero" },
}

const APPROACH_LABELS: Record<AgentApproach, string> = {
  ai: "Criar com IA",
  template: "Template pre-configurado",
  manual: "Criar custom manual",
}

interface PreviewStepProps {
  goal: AgentGoal
  approach: AgentApproach
  config: WizardConfig
  aiPreview: GeneratedConfigPreview | null
}

export function PreviewStep({ goal, approach, config, aiPreview }: PreviewStepProps) {
  const { templates: AGENT_TEMPLATES } = useLegacyAgentTemplates()
  const goalInfo = GOAL_LABELS[goal]
  const GoalIcon = goalInfo.icon
  const tmpl = approach === "template" ? AGENT_TEMPLATES.find((t) => t.id === config.templateId) : null
  const TmplIcon = tmpl
    ? ((Icons as unknown as Record<string, React.ComponentType<{ className?: string }>>)[tmpl.icon] || Bot)
    : null

  const finalName = config.name || aiPreview?.suggested_name || tmpl?.name || "Novo Agente"
  const tools: string[] =
    approach === "ai"
      ? aiPreview?.suggested_tools ?? []
      : approach === "template"
        ? tmpl?.allowed_tools ?? []
        : []

  return (
    <div className="space-y-4" data-testid="preview-step">
      <div className="flex items-center justify-center py-2">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-500" aria-hidden="true">
          <CheckCircle2 className="h-6 w-6" />
        </div>
      </div>

      <p className="text-center text-sm text-lia-text-secondary">
        Confira o resumo antes de criar o agente.
      </p>

      <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-secondary p-5 space-y-3">
        <div className="flex items-center gap-3 pb-3 border-b border-lia-border-subtle">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-powder text-graphite" aria-hidden="true">
            {TmplIcon ? <TmplIcon className="h-5 w-5" /> : <Bot className="h-5 w-5" />}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-lia-text-primary">{finalName}</p>
            <p className="text-[11px] text-lia-text-disabled">{APPROACH_LABELS[approach]}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-2 text-xs">
          <div className="flex items-start gap-2">
            <GoalIcon className="h-3.5 w-3.5 text-lia-text-disabled mt-0.5 shrink-0" aria-hidden="true" />
            <div className="min-w-0">
              <span className="text-lia-text-disabled">Objetivo:</span>{" "}
              <span className="text-lia-text-primary">{goalInfo.label}</span>
            </div>
          </div>

          {approach === "ai" && config.aiDescription && (
            <div className="text-lia-text-secondary italic text-[11px] mt-1">
              "{config.aiDescription.slice(0, 160)}{config.aiDescription.length > 160 ? "..." : ""}"
            </div>
          )}

          {tools.length > 0 && (
            <div className="mt-1">
              <span className="text-lia-text-disabled">Ferramentas:</span>{" "}
              <span className="text-lia-text-primary">{tools.length} habilitadas</span>
              <div className="mt-1 flex flex-wrap gap-1">
                {tools.slice(0, 6).map((tool) => (
                  <span
                    key={tool}
                    className="rounded-md bg-lia-bg-tertiary px-2 py-0.5 text-[10px] text-lia-text-secondary"
                  >
                    {tool}
                  </span>
                ))}
                {tools.length > 6 && (
                  <span className="text-[10px] text-lia-text-disabled self-center">
                    +{tools.length - 6} mais
                  </span>
                )}
              </div>
            </div>
          )}

          {approach === "ai" && aiPreview && (
            <div className="grid grid-cols-3 gap-2 pt-2 text-[10px] text-lia-text-disabled">
              <span>contexto: {aiPreview.suggested_context_level ?? "standard"}</span>
              <span>passos: {aiPreview.suggested_max_steps ?? 8}</span>
              <span>temp: {aiPreview.suggested_temperature ?? 0.5}</span>
            </div>
          )}
        </div>
      </div>

      <p className="text-center text-[11px] text-lia-text-disabled">
        Apos criar, voce podera ajustar todos os campos no editor avancado.
      </p>
    </div>
  )
}
