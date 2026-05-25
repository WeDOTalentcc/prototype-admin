"use client"

/**
 * TemplateClonePanel — right-panel clone-first preview (UX T4).
 *
 * UX_AUDIT_ESTUDIO_AGENTES_2026-05-21 T4 (linha 281): adota o pattern
 * "clone-first" do HubSpot Breeze. Hoje o card de template (Sprint B
 * QW#5) abria um Dialog confirm rápido; aqui usamos um Sheet lateral
 * direito com preview RICO (system_prompt completo + tools + persona
 * + greeting + tags + config grid) e CTA "Clonar e customizar" que
 * abre o CreateAgentWizard (T1) já populado com a config do template.
 *
 * O TemplatePreviewModal (Sprint B QW#5) é preservado em
 * `custom-agents/template-preview-modal.tsx` para fluxos rápidos de
 * confirmação — TemplateClonePanel é o novo entry-point primário a
 * partir do TemplateGallery.
 *
 * Acessibilidade (WCAG 2.2 AA):
 * - Sheet (Radix Dialog wrapper) já provê focus trap + escape key + ARIA
 * - SheetTitle/SheetDescription canonical (não silenciamos para sr-only)
 * - Region landmarks com headings semânticos por seção
 * - ScrollArea com keyboard scroll natural
 */

import * as Icons from "lucide-react"
import { Copy, MessageSquare, Settings, User, Wrench } from "lucide-react"
import { useTranslations } from "next-intl"

import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { badgeStyles, textStyles } from "@/lib/design-tokens"
import { cn } from "@/lib/utils"

import type { AgentTemplate } from "../custom-agents/types"

interface TemplateClonePanelProps {
  template: AgentTemplate | null
  open: boolean
  onClose: () => void
  /** Called when user confirms clone — parent opens wizard with template pre-populated. */
  onClone: (template: AgentTemplate) => void
}

export function TemplateClonePanel({
  template,
  open,
  onClose,
  onClone,
}: TemplateClonePanelProps) {
  const t = useTranslations("agents.customAgents")

  if (!template) return null

  // Lucide icon resolver — same pattern as TemplateCard
  const IconComp =
    ((Icons as unknown as Record<string, React.ComponentType<{ className?: string }>>)[
      template.icon
    ] || Icons.Bot)

  return (
    <Sheet open={open} onOpenChange={(o) => !o && onClose()}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-xl flex flex-col p-0"
        data-testid="template-clone-panel"
      >
        {/* Header: icon + name + description + tags */}
        <SheetHeader className="px-6 pt-6 pb-4 border-b border-lia-border-subtle">
          <div className="flex items-start gap-3">
            <div
              className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-powder text-graphite"
              aria-hidden="true"
            >
              <IconComp className="h-6 w-6" />
            </div>
            <div className="min-w-0 flex-1 text-left">
              <SheetTitle className={cn(textStyles.h3, "leading-tight")}>
                {template.name}
              </SheetTitle>
              <SheetDescription className="mt-1 text-sm text-lia-text-secondary">
                {template.description}
              </SheetDescription>
              {template.tags && template.tags.length > 0 && (
                <div
                  className="mt-2 flex flex-wrap gap-1.5"
                  data-testid="template-clone-tags"
                >
                  {template.tags.map((tag) => (
                    <span
                      key={tag}
                      className={cn(badgeStyles.default, "text-[10px] font-mono")}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </SheetHeader>

        {/* Scrollable body — rich preview sections */}
        <ScrollArea className="flex-1">
          <div className="px-6 py-5 space-y-5">
            {/* System prompt */}
            <section data-testid="template-clone-section-prompt">
              <h3 className="flex items-center gap-2 text-xs font-semibold text-lia-text-secondary uppercase mb-2">
                <Settings className="h-3.5 w-3.5" aria-hidden="true" />
                {t("systemPromptLabel") || "Instruções do agente (LLM)"}
              </h3>
              <pre
                className="text-xs whitespace-pre-wrap font-mono bg-lia-bg-tertiary p-3 rounded-md max-h-48 overflow-y-auto text-lia-text-primary leading-relaxed border border-lia-border-subtle"
                data-testid="template-clone-system-prompt"
              >
                {template.system_prompt || "—"}
              </pre>
            </section>

            <Separator />

            {/* Allowed tools */}
            <section data-testid="template-clone-section-tools">
              <h3 className="flex items-center gap-2 text-xs font-semibold text-lia-text-secondary uppercase mb-2">
                <Wrench className="h-3.5 w-3.5" aria-hidden="true" />
                {t("allowedToolsLabel") || "Ferramentas habilitadas"}
                {template.allowed_tools && (
                  <span className="ml-1 text-lia-text-disabled normal-case font-normal">
                    ({template.allowed_tools.length})
                  </span>
                )}
              </h3>
              {template.allowed_tools && template.allowed_tools.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {template.allowed_tools.map((tool) => (
                    <span
                      key={tool}
                      className={cn(badgeStyles.default, "text-[10px] font-mono")}
                    >
                      {tool}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-lia-text-disabled italic">
                  {t("noToolsConfigured") || "Nenhuma ferramenta configurada"}
                </p>
              )}
            </section>

            <Separator />

            {/* Persona / domain */}
            <section data-testid="template-clone-section-persona">
              <h3 className="flex items-center gap-2 text-xs font-semibold text-lia-text-secondary uppercase mb-2">
                <User className="h-3.5 w-3.5" aria-hidden="true" />
                {t("personaLabel") || "Persona / Domínio"}
              </h3>
              <p className="text-sm text-lia-text-primary">
                <span className="font-medium">{t("domainLabel") || "Domínio"}:</span>{" "}
                {template.domain || "—"}
              </p>
              <p className="mt-0.5 text-sm text-lia-text-primary">
                <span className="font-medium">{t("categoryLabel") || "Categoria"}:</span>{" "}
                {template.category}
              </p>
              {template.vertical && (
                <p
                  className="mt-0.5 text-sm text-lia-text-primary"
                  data-testid="template-clone-vertical"
                >
                  <span className="font-medium">{t("verticalLabel") || "Vertical"}:</span>{" "}
                  <span className="inline-flex items-center gap-1 rounded-full bg-powder px-2 py-0.5 text-micro font-medium text-graphite">
                    {t(`vertical${template.vertical.charAt(0).toUpperCase()}${template.vertical.slice(1)}`) || template.vertical}
                  </span>
                </p>
              )}
            </section>

            <Separator />

            {/* Initial greeting (placeholder — not present on AgentTemplate yet) */}
            <section data-testid="template-clone-section-config">
              <h3 className="flex items-center gap-2 text-xs font-semibold text-lia-text-secondary uppercase mb-2">
                <MessageSquare className="h-3.5 w-3.5" aria-hidden="true" />
                {t("configLabel") || "Configuração"}
              </h3>
              <div className="grid grid-cols-3 gap-2">
                <div className="rounded-lg bg-lia-bg-tertiary p-2 text-center">
                  <p className="text-xs text-lia-text-secondary">
                    {t("maxStepsLabel") || "Max steps"}
                  </p>
                  <p className="text-sm font-semibold text-lia-text-primary">
                    {template.max_steps}
                  </p>
                </div>
                <div className="rounded-lg bg-lia-bg-tertiary p-2 text-center">
                  <p className="text-xs text-lia-text-secondary">
                    {t("temperatureLabel") || "Temperature"}
                  </p>
                  <p className="text-sm font-semibold text-lia-text-primary">
                    {template.temperature}
                  </p>
                </div>
                <div className="rounded-lg bg-lia-bg-tertiary p-2 text-center">
                  <p className="text-xs text-lia-text-secondary">
                    {t("contextLevelLabel") || "Context"}
                  </p>
                  <p className="text-sm font-semibold text-lia-text-primary">
                    {template.context_level}
                  </p>
                </div>
              </div>
              <p className="mt-2 text-[11px] text-lia-text-disabled">
                {t("memoryLabel") || "Memória habilitada"}:{" "}
                <span className="font-medium">
                  {template.enable_memory
                    ? t("memoryYes") || "Sim"
                    : t("memoryNo") || "Não"}
                </span>
              </p>
            </section>
          </div>
        </ScrollArea>

        {/* Footer: Cancel + Clone CTA */}
        <SheetFooter className="px-6 py-4 border-t border-lia-border-subtle flex-row gap-2 sm:justify-between">
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
            {t("cloneAndCustomize") || "Clonar e customizar"}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}
