"use client"

import { Bot, CheckCircle2, Heart, Phone, Search, Settings2, Brain } from "lucide-react"
import * as Icons from "lucide-react"
import { useTranslations } from "next-intl"

import { useLegacyAgentTemplates } from "@/hooks/agents/use-legacy-agent-templates"
import { summarizeCapabilities } from "@/lib/agents/tool-capabilities"

import type { AgentApproach, AgentGoal, GeneratedConfigPreview, WizardConfig } from "../types"

// Ícone por objetivo (o rótulo agora vem do i18n, não hardcoded).
const GOAL_ICONS: Record<AgentGoal, typeof Brain> = {
  triagem_inicial: Brain,
  sourcing_ativo: Search,
  screening_cultural: Heart,
  voz_whatsapp: Phone,
  outro: Settings2,
}

interface PreviewStepProps {
  goal: AgentGoal
  approach: AgentApproach
  config: WizardConfig
  aiPreview: GeneratedConfigPreview | null
}

/**
 * PreviewStep — etapa final "Pronto pra criar?" do wizard.
 *
 * Redesign 2026-05-30 (Paulo, crítica do recrutador, P2+P3):
 *  - P2: a nota de rodapé "editor avançado" (jargão) vira "Você pode ajustar
 *    tudo depois, quando quiser." (i18n).
 *  - P3: o objetivo reflete o template escolhido (quando há um) ou o objetivo
 *    real em PT — nunca "Outro / criar do zero". As ferramentas viram
 *    capacidades de alto nível em PT (summarizeCapabilities), não slugs crus.
 */
export function PreviewStep({ goal, approach, config, aiPreview }: PreviewStepProps) {
  const t = useTranslations("agents.customAgents")
  const { templates: AGENT_TEMPLATES } = useLegacyAgentTemplates()

  const GoalIcon = GOAL_ICONS[goal]
  const tmpl = approach === "template" ? AGENT_TEMPLATES.find((tpl) => tpl.id === config.templateId) : null
  const TmplIcon = tmpl
    ? ((Icons as unknown as Record<string, React.ComponentType<{ className?: string }>>)[tmpl.icon] || Bot)
    : null

  const finalName = config.name || aiPreview?.suggested_name || tmpl?.name || t("preview.objectiveLabel")

  // Objetivo legível: quando o usuário escolheu um modelo, o objetivo é o
  // próprio modelo; senão usa o rótulo PT do objetivo. Nunca "Outro / criar do zero".
  const objectiveText = tmpl ? tmpl.name : t(`goalLabels.${goal}`)

  const tools: string[] =
    approach === "ai"
      ? aiPreview?.suggested_tools ?? []
      : approach === "template"
        ? tmpl?.allowed_tools ?? []
        : []
  const capabilities = summarizeCapabilities(tools)

  return (
    <div className="space-y-4" data-testid="preview-step">
      <div className="flex items-center justify-center py-2">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-status-success/10 text-status-success" aria-hidden="true">
          <CheckCircle2 className="h-6 w-6" />
        </div>
      </div>

      <p className="text-center text-sm text-lia-text-secondary">
        {t("preview.intro")}
      </p>

      <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-secondary p-5 space-y-3">
        <div className="flex items-center gap-3 pb-3 border-b border-lia-border-subtle">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-powder text-graphite dark:bg-lia-bg-tertiary dark:text-lia-text-primary" aria-hidden="true">
            {TmplIcon ? <TmplIcon className="h-5 w-5" /> : <Bot className="h-5 w-5" />}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-lia-text-primary">{finalName}</p>
            <p className="text-[11px] text-lia-text-muted">{t(`approachLabels.${approach}`)}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-2 text-xs">
          <div className="flex items-start gap-2">
            <GoalIcon className="h-3.5 w-3.5 text-lia-text-muted mt-0.5 shrink-0" aria-hidden="true" />
            <div className="min-w-0">
              <span className="text-lia-text-disabled">{t("preview.objectiveLabel")}:</span>{" "}
              <span className="text-lia-text-primary">{objectiveText}</span>
            </div>
          </div>

          {approach === "ai" && config.aiDescription && (
            <p className="text-lia-text-secondary italic text-[11px] mt-1">
              {config.aiDescription.slice(0, 160)}
              {config.aiDescription.length > 160 ? "..." : ""}
            </p>
          )}

          {capabilities.length > 0 && (
            <div className="mt-1">
              <p className="text-[10px] uppercase tracking-wide font-semibold text-lia-text-tertiary">
                {t("preview.whatItDoesLabel")}
              </p>
              <ul className="mt-1.5 space-y-1">
                {capabilities.map((cap) => (
                  <li
                    key={cap}
                    className="flex items-start gap-2 text-xs text-lia-text-secondary"
                  >
                    <span
                      className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-lia-text-disabled"
                      aria-hidden="true"
                    />
                    <span>{cap}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      <p className="text-center text-[11px] text-lia-text-muted">
        {t("preview.adjustLaterNote")}
      </p>
    </div>
  )
}
