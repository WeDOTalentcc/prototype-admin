"use client"

import { FileText, Settings2, Zap } from "lucide-react"
import * as Icons from "lucide-react"
import { useTranslations } from "next-intl"

import { useAiPersona } from "@/hooks/company/use-ai-persona"

import { Card, CardContent } from "@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Textarea } from "@/components/ui/textarea"
import { useLegacyAgentTemplates } from "@/hooks/agents/use-legacy-agent-templates"
import { cn } from "@/lib/utils"

import { filterTemplatesByGoal, type AgentApproach, type AgentGoal, type WizardConfig } from "../types"

interface ApproachStepProps {
  goal: AgentGoal
  approach: AgentApproach | null
  config: WizardConfig
  onSelect: (approach: AgentApproach) => void
  setConfig: (next: WizardConfig) => void
}

export function ApproachStep({ goal, approach, config, onSelect, setConfig }: ApproachStepProps) {
  const t = useTranslations("agents.studio.wizard")
  const { persona: aiPersona } = useAiPersona()
  const aiAssistantName = aiPersona?.name ?? "assistente"
  const { templates: AGENT_TEMPLATES } = useLegacyAgentTemplates()
  const relevantTemplates = filterTemplatesByGoal(AGENT_TEMPLATES, goal).slice(0, 4)

  return (
    <div className="space-y-5" role="radiogroup" aria-label="Como criar o agente">
      {/* T3 — Hero "Criar com IA" */}
      <Card
        role="radio"
        aria-checked={approach === "ai"}
        tabIndex={0}
        data-testid="approach-ai-hero"
        onClick={() => onSelect("ai")}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault()
            onSelect("ai")
          }
        }}
        className={cn(
          "cursor-pointer border-lia-border-default bg-lia-bg-secondary transition-shadow duration-200 hover:shadow-lia-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30",
          approach === "ai" && "border-pebble ring-2 ring-graphite/20",
        )}
      >
        <CardContent className="space-y-3 p-5">
          <div className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-graphite" aria-hidden="true" />
            {/* Nao usamos <TabSectionHeader> aqui (sentinela Task #1050) porque o
                titulo eh interno a um card de option do wizard, nao header de tab.
                Usamos <p> com role="heading" + aria-level pra manter semantica. */}
            <p
              role="heading"
              aria-level={3}
              className="text-sm font-semibold text-lia-text-primary"
            >
              Criar com IA
            </p>
            <Chip variant="info" density="compact">
              Recomendado
            </Chip>
          </div>
          <p className="text-xs text-lia-text-secondary">
            Descreva o que precisa em linguagem natural e {aiAssistantName} configura o agente automaticamente:
            nome, prompt, ferramentas, contexto e temperatura.
          </p>
          {approach === "ai" && (
            <Textarea
              value={config.aiDescription}
              onChange={(e) => setConfig({ ...config, aiDescription: e.target.value })}
              placeholder="Ex.: Preciso de um agente que faca triagem inicial de candidatos para vagas de Engenharia, focando em experiencia com Python e cloud..."
              rows={4}
              aria-label="Descricao do agente para gerar com IA"
              data-testid="ai-description-textarea"
              className="resize-none"
            />
          )}
        </CardContent>
      </Card>

      {relevantTemplates.length > 0 && (
        <>
          <div className="relative my-2">
            <div className="absolute inset-0 flex items-center" aria-hidden="true">
              <div className="w-full border-t border-lia-border-subtle" />
            </div>
            <div className="relative flex justify-center text-[10px] uppercase tracking-wider">
              <span className="bg-lia-bg-primary px-2 text-lia-text-disabled">
                ou escolha um template
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            {relevantTemplates.map((tmpl) => {
              const isSelected = approach === "template" && config.templateId === tmpl.id
              const TmplIcon = ((Icons as unknown as Record<string, React.ComponentType<{ className?: string }>>)[tmpl.icon] || Icons.Bot)
              return (
                <Card
                  key={tmpl.id}
                  role="radio"
                  aria-checked={isSelected}
                  tabIndex={0}
                  data-testid={`template-option-${tmpl.id}`}
                  onClick={() => {
                    onSelect("template")
                    setConfig({ ...config, templateId: tmpl.id, name: tmpl.name })
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault()
                      onSelect("template")
                      setConfig({ ...config, templateId: tmpl.id, name: tmpl.name })
                    }
                  }}
                  className={cn(
                    "cursor-pointer transition-shadow duration-200 hover:shadow-lia-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30",
                    isSelected && "border-pebble ring-2 ring-graphite/20",
                  )}
                >
                  <CardContent className="flex items-start gap-3 p-4">
                    <div
                      className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-powder text-graphite"
                      aria-hidden="true"
                    >
                      <TmplIcon className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-semibold text-lia-text-primary">{tmpl.name}</div>
                      <div className="text-xs text-lia-text-secondary mt-0.5 line-clamp-2">
                        {tmpl.description}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </>
      )}

      <div className="relative my-2">
        <div className="absolute inset-0 flex items-center" aria-hidden="true">
          <div className="w-full border-t border-lia-border-subtle" />
        </div>
        <div className="relative flex justify-center text-[10px] uppercase tracking-wider">
          <span className="bg-lia-bg-primary px-2 text-lia-text-disabled">{t("orCreateFromScratch")}</span>
        </div>
      </div>

      <Card
        role="radio"
        aria-checked={approach === "manual"}
        tabIndex={0}
        data-testid="approach-manual"
        onClick={() => onSelect("manual")}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault()
            onSelect("manual")
          }
        }}
        className={cn(
          "cursor-pointer transition-shadow duration-200 hover:shadow-lia-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30",
          approach === "manual" && "border-pebble ring-2 ring-graphite/20",
        )}
      >
        <CardContent className="flex items-start gap-3 p-4">
          <div
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-lia-bg-tertiary text-lia-text-secondary"
            aria-hidden="true"
          >
            <Settings2 className="h-4 w-4" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-sm font-semibold text-lia-text-primary">{t("createManual")}</div>
            <div className="text-xs text-lia-text-secondary mt-0.5">
              Configure tudo manualmente: nome, system prompt, ferramentas e persona. Para quem ja sabe
              exatamente o que quer.
            </div>
          </div>
          <FileText className="h-4 w-4 shrink-0 text-lia-text-disabled mt-1" aria-hidden="true" />
        </CardContent>
      </Card>
    </div>
  )
}
