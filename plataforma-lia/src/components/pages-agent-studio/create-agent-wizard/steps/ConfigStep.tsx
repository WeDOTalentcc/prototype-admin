"use client"

import { Loader2, Zap } from "lucide-react"
import * as Icons from "lucide-react"
import { useTranslations } from "next-intl"

import { useAiPersona } from "@/hooks/company/use-ai-persona"

import { Button } from "@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Textarea } from "@/components/ui/textarea"
import { useLegacyAgentTemplates } from "@/hooks/agents/use-legacy-agent-templates"

import type { AgentApproach, AgentGoal, GeneratedConfigPreview, WizardConfig } from "../types"

interface ConfigStepProps {
  approach: AgentApproach
  goal: AgentGoal
  config: WizardConfig
  setConfig: (next: WizardConfig) => void
  aiPreview: GeneratedConfigPreview | null
  isGeneratingAI: boolean
  aiError: string | null
  onGenerateAI: () => void
}

export function ConfigStep({
  approach,
  goal,
  config,
  setConfig,
  aiPreview,
  isGeneratingAI,
  aiError,
  onGenerateAI,
}: ConfigStepProps) {
  const t = useTranslations("agents.studio.wizard")
  const { persona: aiPersona } = useAiPersona()
  const aiAssistantName = aiPersona?.name ?? "assistente"
  const { templates: AGENT_TEMPLATES } = useLegacyAgentTemplates()
  if (approach === "ai") {
    return (
      <div className="space-y-4" data-testid="config-step-ai">
        <div className="rounded-lg border border-lia-border-subtle bg-lia-bg-secondary p-4">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="h-4 w-4 text-graphite" aria-hidden="true" />
            <span className="text-sm font-semibold text-lia-text-primary">{t("yourDescription")}</span>
          </div>
          <p className="text-xs text-lia-text-secondary italic">"{config.aiDescription}"</p>
        </div>

        {!aiPreview && !isGeneratingAI && (
          <div className="flex flex-col items-center gap-3 py-6 text-center">
            <p className="text-sm text-lia-text-secondary">
              {aiAssistantName} vai analisar sua descrição e gerar a configuração do agente.
            </p>
            <Button
              type="button"
              onClick={onGenerateAI}
              disabled={!config.aiDescription || config.aiDescription.trim().length < 10}
              data-testid="ai-generate-button"
              className="gap-2"
            >
              <Zap className="h-4 w-4" aria-hidden="true" />
              Gerar configuração com {aiAssistantName}
            </Button>
            <p className="text-[11px] text-lia-text-disabled">
              Minimo 10 caracteres. Quanto mais detalhe, melhor o resultado.
            </p>
          </div>
        )}

        {isGeneratingAI && (
          <div className="flex flex-col items-center gap-3 py-8 text-center" data-testid="ai-loading">
            <Loader2 className="h-6 w-6 animate-spin text-graphite" aria-hidden="true" />
            <p className="text-sm text-lia-text-secondary">{aiAssistantName} está configurando o agente...</p>
          </div>
        )}

        {aiError && (
          <div className="rounded-lg border border-red-200 bg-red-50 dark:bg-red-950/20 p-3" role="alert">
            <p className="text-xs text-red-700 dark:text-red-400">{aiError}</p>
          </div>
        )}

        {aiPreview && !isGeneratingAI && (
          <div className="space-y-3" data-testid="ai-preview">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-lia-text-primary">{t("suggestedConfig")}</span>
              <Chip variant="neutral" density="compact" muted>Editavel</Chip>
            </div>

            <div className="rounded-lg border border-lia-border-subtle bg-lia-bg-secondary p-4 space-y-3">
              <div>
                <label htmlFor="wizard-ai-name" className="text-xs font-semibold text-lia-text-primary block mb-1">
                  Nome do agente
                </label>
                <input
                  id="wizard-ai-name"
                  type="text"
                  value={config.name}
                  onChange={(e) => setConfig({ ...config, name: e.target.value })}
                  className="w-full rounded-lg border border-lia-border-subtle bg-lia-bg-primary px-3 py-2 text-sm text-lia-text-primary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30"
                  data-testid="wizard-ai-name-input"
                />
              </div>

              <div className="flex flex-wrap gap-1">
                {(aiPreview.suggested_tools ?? []).map((tool) => (
                  <span
                    key={tool}
                    className="rounded-md bg-lia-bg-tertiary px-2 py-0.5 text-[10px] text-lia-text-secondary"
                  >
                    {tool}
                  </span>
                ))}
              </div>

              <div className="flex flex-wrap items-center gap-3 text-[10px] text-lia-text-disabled">
                <span>contexto: {aiPreview.suggested_context_level ?? "standard"}</span>
                <span>passos: {aiPreview.suggested_max_steps ?? 8}</span>
                <span>temp: {aiPreview.suggested_temperature ?? 0.5}</span>
              </div>

              {aiPreview.reasoning && (
                <p className="text-[11px] italic text-graphite border-t border-lia-border-subtle pt-2">
                  {aiAssistantName}: {aiPreview.reasoning}
                </p>
              )}
            </div>

            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={onGenerateAI}
              className="text-xs gap-1"
              data-testid="ai-regenerate-button"
            >
              <Zap className="h-3 w-3" aria-hidden="true" />
              Gerar novamente
            </Button>
          </div>
        )}
      </div>
    )
  }

  if (approach === "template") {
    const tmpl = AGENT_TEMPLATES.find((t) => t.id === config.templateId)
    if (!tmpl) {
      return (
        <p className="text-sm text-lia-text-secondary text-center py-6">
          Nenhum template selecionado. Volte ao passo anterior.
        </p>
      )
    }
    const TmplIcon = ((Icons as unknown as Record<string, React.ComponentType<{ className?: string }>>)[tmpl.icon] || Icons.Bot)
    return (
      <div className="space-y-4" data-testid="config-step-template">
        <div className="flex items-start gap-3 rounded-lg border border-lia-border-subtle bg-lia-bg-secondary p-4">
          <div
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-powder text-graphite"
            aria-hidden="true"
          >
            <TmplIcon className="h-5 w-5" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-lia-text-primary">{tmpl.name}</p>
            <p className="text-xs text-lia-text-secondary">{tmpl.description}</p>
          </div>
        </div>

        <div>
          <label htmlFor="wizard-template-name" className="text-xs font-semibold text-lia-text-primary block mb-1">
            Nome do agente
          </label>
          <input
            id="wizard-template-name"
            type="text"
            value={config.name}
            onChange={(e) => setConfig({ ...config, name: e.target.value })}
            placeholder="Ex: Triagem Tech - Vagas Eng"
            className="w-full rounded-lg border border-lia-border-subtle bg-lia-bg-primary px-3 py-2 text-sm text-lia-text-primary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30"
            data-testid="wizard-template-name-input"
          />
        </div>

        <div className="flex flex-wrap gap-1">
          {tmpl.allowed_tools.map((tool) => (
            <span
              key={tool}
              className="rounded-md bg-lia-bg-tertiary px-2 py-0.5 text-[10px] text-lia-text-secondary"
            >
              {tool}
            </span>
          ))}
        </div>
      </div>
    )
  }

  // approach === "manual"
  return (
    <div className="space-y-4" data-testid="config-step-manual">
      <p className="text-sm text-lia-text-secondary">
        Configure os campos basicos. Apos criar, voce podera ajustar system prompt, ferramentas e
        persona em detalhe no editor avancado.
      </p>

      <div>
        <label htmlFor="wizard-manual-name" className="text-xs font-semibold text-lia-text-primary block mb-1">
          Nome do agente
          <span className="ml-1 text-red-500" aria-hidden="true">*</span>
        </label>
        <input
          id="wizard-manual-name"
          type="text"
          value={config.name}
          onChange={(e) => setConfig({ ...config, name: e.target.value })}
          placeholder={t("namePlaceholder")}
          className="w-full rounded-lg border border-lia-border-subtle bg-lia-bg-primary px-3 py-2 text-sm text-lia-text-primary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30"
          data-testid="wizard-manual-name-input"
        />
      </div>

      <div>
        <label htmlFor="wizard-manual-desc" className="text-xs font-semibold text-lia-text-primary block mb-1">
          Descricao curta
        </label>
        <Textarea
          id="wizard-manual-desc"
          value={config.description}
          onChange={(e) => setConfig({ ...config, description: e.target.value })}
          placeholder="O que esse agente faz?"
          rows={3}
          className="resize-none"
          data-testid="wizard-manual-desc-input"
        />
      </div>
    </div>
  )
}
