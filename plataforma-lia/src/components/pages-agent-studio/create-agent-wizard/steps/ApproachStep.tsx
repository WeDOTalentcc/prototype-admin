"use client"

import { FileText, Lightbulb, MessagesSquare, Settings2, Brain } from "lucide-react"
import * as Icons from "lucide-react"
import { useTranslations } from "next-intl"

import { useAiPersona } from "@/hooks/company/use-ai-persona"

import { Card, CardContent } from "@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Textarea } from "@/components/ui/textarea"
import { useLegacyAgentTemplates } from "@/hooks/agents/use-legacy-agent-templates"
import { cn } from "@/lib/utils"
import { AgentConversationPreview } from "../../AgentConversationPreview"

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
  const tStudio = useTranslations("agents.studio")
  const { persona: aiPersona } = useAiPersona()
  const aiAssistantName = aiPersona?.name ?? "assistente"
  const { templates: AGENT_TEMPLATES } = useLegacyAgentTemplates()
  const relevantTemplates = filterTemplatesByGoal(AGENT_TEMPLATES, goal).slice(0, 4)
  const selectedTemplate =
    approach === "template"
      ? relevantTemplates.find((tmpl) => tmpl.id === config.templateId) ?? null
      : null

  return (
    <div className="space-y-5" role="radiogroup" aria-label={t("approachGroupAriaLabel")}>
      {/* Linha de tranquilidade — remove o medo de errar. Tom Quiet Operator:
          icone lucide sutil (sem emoji), cyan leve porque a IA monta o agente. */}
      <div className="flex items-start gap-2 rounded-md bg-wedo-cyan/5 px-3 py-2">
        <Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0 text-wedo-cyan" aria-hidden="true" />
        <p className="text-xs leading-relaxed text-lia-text-secondary">
          {t("approachReassurance")}
        </p>
      </div>

      {/* Hero "Criar com IA" — opcao recomendada, acento cyan (regra LIA Cyan
          Exclusivity: cyan = IA presente). */}
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
          "cursor-pointer border-wedo-cyan/30 bg-wedo-cyan/5 transition-shadow duration-200 hover:shadow-lia-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/40",
          approach === "ai" && "border-wedo-cyan ring-2 ring-wedo-cyan/30",
        )}
      >
        <CardContent className="space-y-3 p-5">
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-wedo-cyan" aria-hidden="true" />
            {/* Nao usamos <TabSectionHeader> aqui (sentinela Task #1050) porque o
                titulo eh interno a um card de option do wizard, nao header de tab.
                Usamos <p> com role="heading" + aria-level pra manter semantica. */}
            <p
              role="heading"
              aria-level={3}
              className="text-sm font-semibold text-lia-text-primary"
            >
              {t("aiOptionTitle")}
            </p>
            <Chip variant="info" density="compact">
              {t("aiOptionRecommended")}
            </Chip>
          </div>

          <p className="text-xs leading-relaxed text-lia-text-secondary">
            {t("aiOptionDescription", { assistantName: aiAssistantName })}
          </p>

          {/* Exemplo SEMPRE visivel — ensina o que escrever mesmo antes de
              selecionar (antes, o exemplo so vivia no placeholder do textarea,
              que so aparecia pos-selecao: circular). */}
          <div className="rounded-md bg-lia-bg-tertiary/60 px-3 py-2">
            <p className="mb-0.5 text-[10px] font-semibold uppercase tracking-wider text-lia-text-disabled">
              {t("aiOptionExampleLabel")}
            </p>
            <p className="text-xs italic leading-relaxed text-lia-text-secondary">
              {t("aiOptionExample")}
            </p>
          </div>

          {approach === "ai" && (
            <div className="space-y-1.5">
              <Textarea
                value={config.aiDescription}
                onChange={(e) => setConfig({ ...config, aiDescription: e.target.value })}
                placeholder={t("aiDescriptionPlaceholder")}
                rows={4}
                aria-label={t("aiDescriptionAriaLabel")}
                data-testid="ai-description-textarea"
                className="resize-none"
              />
              <p className="text-[11px] leading-relaxed text-lia-text-disabled">
                {t("aiDescriptionHelper")}
              </p>
            </div>
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
                {t("orFromTemplate")}
              </span>
            </div>
          </div>

          <p className="-mt-1 text-center text-[11px] text-lia-text-disabled">
            {t("templateSectionHint")}
          </p>

          {/* items-stretch + h-full: cards de alturas naturais (texto completo,
              sem line-clamp) alinham no topo do grid. */}
          <div className="grid grid-cols-1 items-stretch gap-2 md:grid-cols-2">
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
                    "h-full cursor-pointer transition-shadow duration-200 hover:shadow-lia-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30",
                    isSelected && "border-pebble ring-2 ring-graphite/20",
                  )}
                >
                  <CardContent className="flex h-full items-start gap-3 p-4">
                    <div
                      className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-powder text-graphite"
                      aria-hidden="true"
                    >
                      <TmplIcon className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-semibold text-lia-text-primary">{tmpl.name}</div>
                      <div className="mt-0.5 text-xs leading-relaxed text-lia-text-secondary">
                        {tmpl.description}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>

          {/* Veja em ação — conversa-exemplo do template selecionado
              (Fase 3 Sprint 2). "Veja como ela trabalha": só aparece quando há
              template escolhido, full-width abaixo do grid. */}
          {selectedTemplate && (
            <div
              className="rounded-lg border border-lia-border-subtle bg-lia-bg-secondary p-4"
              data-testid="approach-template-conversation"
            >
              <div className="mb-2 flex items-center gap-2">
                <MessagesSquare
                  className="h-4 w-4 text-lia-text-secondary"
                  aria-hidden="true"
                />
                <p className="text-sm font-semibold text-lia-text-primary">
                  {tStudio("seeInActionLabel")}
                </p>
              </div>
              <p className="mb-3 text-xs text-lia-text-secondary">
                {tStudio("seeInActionHint")}
              </p>
              <AgentConversationPreview
                slug={selectedTemplate.slug}
                category={selectedTemplate.category}
              />
            </div>
          )}
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
            <div className="mt-0.5 text-xs leading-relaxed text-lia-text-secondary">
              {t("createManualDescription")}
            </div>
          </div>
          <FileText className="mt-1 h-4 w-4 shrink-0 text-lia-text-disabled" aria-hidden="true" />
        </CardContent>
      </Card>
    </div>
  )
}
