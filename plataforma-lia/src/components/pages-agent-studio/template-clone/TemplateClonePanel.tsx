"use client"

/**
 * TemplateClonePanel — modal de detalhe didático do template (redesign 2026-05-30).
 *
 * CONTEXTO (Paulo, crítica do recrutador): o modal expunha jargão de engenharia
 * ("Prompt do sistema", lista de IDs de tools, "Persona / Domínio: screening").
 * Redesign deixa didático para recrutador, mantendo a info técnica acessível
 * sob demanda:
 *
 *  - "O que este agente faz": bullets de alto nível em PT (summarizeCapabilities),
 *    NÃO lista de IDs crus de tools.
 *  - "Como este agente trabalha": config traduzida + o system_prompt técnico
 *    recolhido em <details> "Ver instruções técnicas".
 *  - "Especialidade: <categoria PT> · Área: <vertical PT>" — sem Domínio/Categoria
 *    redundantes nem termos crus em inglês.
 *  - Config traduzida: "Profundidade da análise" + "Processa até N etapas".
 *  - CTA "Usar e ajustar" (coerente com o card).
 *
 * Histórico: UX_AUDIT T4 (clone-first HubSpot Breeze) + P1-1 (Dialog central).
 *
 * Acessibilidade (WCAG 2.2 AA): Dialog (Radix) provê focus trap + escape + ARIA
 * modal; DialogTitle/DialogDescription canonical; headings semânticos por seção.
 */

import * as Icons from "lucide-react"
import { Copy, Layers, ListChecks, MessagesSquare, Brain } from "lucide-react"
import { useTranslations } from "next-intl"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { textStyles } from "@/lib/design-tokens"
import { cn } from "@/lib/utils"
import { summarizeCapabilities } from "@/lib/agents/tool-capabilities"
import { AgentConversationPreview } from "../AgentConversationPreview"

import type { AgentTemplate, ContextLevel } from "../custom-agents/types"

interface TemplateClonePanelProps {
  template: AgentTemplate | null
  open: boolean
  onClose: () => void
  /** Called when user confirms — parent opens wizard with template pre-populated. */
  onClone: (template: AgentTemplate) => void
}

const DEPTH_VALUE_KEY: Record<ContextLevel, string> = {
  minimal: "depthValue.minimal",
  standard: "depthValue.standard",
  full: "depthValue.full",
}

export function TemplateClonePanel({
  template,
  open,
  onClose,
  onClone,
}: TemplateClonePanelProps) {
  const t = useTranslations("agents.customAgents")
  const tRich = useTranslations("agents.customAgents.template.rich")

  if (!template) return null

  // Lucide icon resolver — same pattern as TemplateCard.
  const IconComp =
    ((Icons as unknown as Record<string, React.ComponentType<{ className?: string }>>)[
      template.icon
    ] || Icons.Bot)

  const capabilities = summarizeCapabilities(template.allowed_tools)
  const verticalLabelKey = template.vertical
    ? `vertical${template.vertical.charAt(0).toUpperCase()}${template.vertical.slice(1)}`
    : null

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent
        className={cn(
          "max-w-2xl w-full p-0 flex flex-col max-h-[85vh]",
          "bg-lia-bg-primary border border-lia-border-medium shadow-lia-lg rounded-xl"
        )}
        data-testid="template-clone-panel"
      >
        {/* Header: avatar tonal + nome + descrição */}
        <DialogHeader className="px-6 pt-6 pb-4 border-b border-lia-border-subtle">
          <div className="flex items-start gap-3">
            <div
              className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-powder text-graphite dark:bg-lia-bg-tertiary dark:text-lia-text-primary"
              aria-hidden="true"
            >
              <IconComp className="h-6 w-6" />
            </div>
            <div className="min-w-0 flex-1 text-left">
              <DialogTitle className={cn(textStyles.h3, "leading-tight")}>
                {template.name}
              </DialogTitle>
              <DialogDescription className="mt-1 text-sm text-lia-text-secondary">
                {template.description}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {/* Body — seções didáticas.
            P4 (Paulo 2026-05-30): a conversa-exemplo NÃO é mais o herói do modal
            (era redundante com o teaser do card "Veja em ação"). O modal foca no
            que agrega: o que o agente faz (capacidades), especialidade/área, como
            trabalha. A conversa vira UMA seção secundária no fim, recolhida. */}
        <ScrollArea className="flex-1 min-h-0">
          <div className="px-6 py-5 space-y-5">
            {/* O que este agente faz — capacidades de alto nível (herói do modal) */}
            <section data-testid="template-clone-section-tools">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-lia-text-primary mb-2">
                <ListChecks className="h-4 w-4 text-lia-text-secondary" aria-hidden="true" />
                {t("whatItDoesLabel")}
              </h3>
              {capabilities.length > 0 ? (
                <ul className="space-y-1.5">
                  {capabilities.map((cap) => (
                    <li
                      key={cap}
                      className="flex items-start gap-2 text-sm text-lia-text-secondary"
                    >
                      <span
                        className="mt-2 h-1 w-1 shrink-0 rounded-full bg-lia-text-disabled"
                        aria-hidden="true"
                      />
                      <span>{cap}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-lia-text-disabled italic">
                  {t("noToolsConfigured") || "—"}
                </p>
              )}
            </section>

            <Separator />

            {/* Especialidade + área */}
            <section data-testid="template-clone-section-persona">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-lia-text-primary mb-2">
                <Brain className="h-4 w-4 text-lia-text-secondary" aria-hidden="true" />
                {t("specialtyLabel")}
              </h3>
              <p className="text-sm text-lia-text-secondary">
                {t("categories." + template.category) || template.category}
                {verticalLabelKey && (
                  <>
                    {" · "}
                    <span className="text-lia-text-secondary">
                      {t("areaLabel")}: {t(verticalLabelKey) || template.vertical}
                    </span>
                  </>
                )}
              </p>
            </section>

            <Separator />

            {/* Como este agente trabalha — config traduzida + instruções técnicas recolhidas */}
            <section data-testid="template-clone-section-config">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-lia-text-primary mb-2">
                <Layers className="h-4 w-4 text-lia-text-secondary" aria-hidden="true" />
                {t("howItWorksLabel")}
              </h3>
              <div className="grid grid-cols-2 gap-2">
                <div className="rounded-lg bg-lia-bg-tertiary p-3">
                  <p className="text-xs text-lia-text-secondary">
                    {t("depthAnalysisLabel")}
                  </p>
                  <p className="text-sm font-semibold text-lia-text-primary">
                    {tRich(DEPTH_VALUE_KEY[template.context_level])}
                  </p>
                </div>
                <div className="rounded-lg bg-lia-bg-tertiary p-3">
                  <p className="text-sm font-semibold text-lia-text-primary">
                    {tRich("stepsValue", { count: template.max_steps })}
                  </p>
                </div>
              </div>

              {/* Instruções técnicas (system prompt) — recolhidas por padrão */}
              <details
                className="mt-3 group"
                data-testid="template-clone-section-prompt"
              >
                <summary className="cursor-pointer list-none text-xs font-medium text-lia-text-secondary hover:text-lia-text-primary transition-colors flex items-center gap-1.5">
                  <Icons.ChevronRight
                    className="h-3.5 w-3.5 transition-transform group-open:rotate-90"
                    aria-hidden="true"
                  />
                  {t("technicalInstructionsToggle")}
                </summary>
                <pre
                  className="mt-2 text-xs whitespace-pre-wrap font-mono bg-lia-bg-tertiary p-3 rounded-md max-h-48 overflow-y-auto text-lia-text-secondary leading-relaxed border border-lia-border-subtle"
                  data-testid="template-clone-system-prompt"
                >
                  {template.system_prompt || "—"}
                </pre>
              </details>
            </section>

            <Separator />

            {/* Veja em ação — conversa-exemplo, agora SECUNDÁRIA e recolhida
                (P4). O teaser curto da conversa já vive no card; aqui ela é só
                um complemento opcional, não o destaque. */}
            <section data-testid="template-clone-section-conversation">
              <details className="group">
                <summary className="cursor-pointer list-none flex items-center gap-2 text-sm font-semibold text-lia-text-primary hover:text-lia-text-secondary transition-colors">
                  <Icons.ChevronRight
                    className="h-3.5 w-3.5 transition-transform group-open:rotate-90 text-lia-text-secondary"
                    aria-hidden="true"
                  />
                  <MessagesSquare className="h-4 w-4 text-lia-text-secondary" aria-hidden="true" />
                  {t("seeInActionLabel")}
                </summary>
                <p className="mt-1 mb-3 text-xs text-lia-text-secondary">
                  {t("seeInActionHint")}
                </p>
                <AgentConversationPreview
                  slug={template.slug}
                  category={template.category}
                />
              </details>
            </section>
          </div>
        </ScrollArea>

        {/* Footer: Cancelar + Usar e ajustar */}
        <DialogFooter className="px-6 py-4 border-t border-lia-border-subtle flex-row gap-2 sm:justify-between">
          <Button
            variant="outline"
            onClick={onClose}
            className="flex-1 sm:flex-initial"
            data-testid="template-clone-cancel"
          >
            {t("cancel") || "Cancelar"}
          </Button>
          <Button
            onClick={() => onClone(template)}
            className="flex-1 sm:flex-initial gap-2 bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
            data-testid="template-clone-confirm"
          >
            <Copy className="h-4 w-4" aria-hidden="true" />
            {t("useAndAdjust")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
