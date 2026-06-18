"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import React, { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Bot, Loader2, Wrench, Zap } from "lucide-react"
import { useTranslations } from "next-intl"
import { textStyles, badgeStyles, inputStyles, formStyles } from "@/lib/design-tokens"
import { cn } from "@/lib/utils"
import type { AgentTemplate } from "./types"

interface TemplatePreviewModalProps {
  template: AgentTemplate | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: (customizedTemplate: AgentTemplate) => Promise<void>
}

/**
 * UX Sprint B QW#5 audit 2026-05-22: confirma preview ANTES de criar agente
 * (era POST direto silencioso). WCAG 3.3.4 + Nielsen H#5 error prevention.
 *
 * Permite editar nome + revisa system_prompt + allowed_tools + config antes
 * de confirmar criação.
 */
export function TemplatePreviewModal({
  template,
  open,
  onOpenChange,
  onConfirm,
}: TemplatePreviewModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('template-preview', open)

  const t = useTranslations("agents.customAgents")
  const [customName, setCustomName] = useState("")
  const [isCreating, setIsCreating] = useState(false)

  // Reset name quando template muda
  useEffect(() => {
    if (template) {
      setCustomName(template.name)
    }
  }, [template])

  if (!template) return null

  const handleConfirm = async () => {
    const finalName = customName.trim() || template.name
    setIsCreating(true)
    try {
      await onConfirm({ ...template, name: finalName })
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className={cn(textStyles.h3, "flex items-center gap-2")}>
            <Zap className="w-5 h-5 text-graphite" aria-hidden="true" />
            {t("templatePreviewTitle") || "Confirmar criação do agente"}
          </DialogTitle>
          <DialogDescription className="text-sm text-lia-text-secondary">
            {t("templatePreviewDesc") || "Revise a configuração do template antes de criar o agente. Você pode personalizar o nome."}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Nome editável */}
          <div className={formStyles.fieldGroup}>
            <label htmlFor="template-preview-name" className={formStyles.labelRequired}>
              {t("nameLabel") || "Nome do agente"}
            </label>
            <input
              id="template-preview-name"
              className={cn(inputStyles.default, "w-full")}
              value={customName}
              onChange={(e) => setCustomName(e.target.value)}
              placeholder={template.name}
              aria-label={t("nameLabel") || "Nome do agente"}
              maxLength={80}
            />
            <p className={formStyles.helperText}>
              {t("templatePreviewNameHelp") || "Use um nome descritivo. Você pode editar depois."}
            </p>
          </div>

          {/* Description (readonly) */}
          {template.description && (
            <div className="rounded-lg bg-lia-bg-secondary p-3">
              <p className="text-xs font-semibold text-lia-text-secondary uppercase mb-1">
                {t("descLabel") || "Descrição"}
              </p>
              <p className="text-sm text-lia-text-primary">{template.description}</p>
            </div>
          )}

          {/* System Prompt preview */}
          <div className="rounded-lg border border-lia-border-subtle p-3">
            <div className="flex items-center gap-2 mb-2">
              <Bot className="w-3.5 h-3.5 text-graphite" aria-hidden="true" />
              <p className="text-xs font-semibold text-lia-text-secondary uppercase">
                {t("systemPromptLabel") || "Instruções do agente (LLM)"}
              </p>
            </div>
            <p className="text-xs text-lia-text-primary whitespace-pre-wrap leading-relaxed font-mono bg-lia-bg-tertiary p-2 rounded max-h-32 overflow-y-auto">
              {template.system_prompt}
            </p>
          </div>

          {/* Allowed tools chips */}
          {template.allowed_tools && template.allowed_tools.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Wrench className="w-3.5 h-3.5 text-lia-text-secondary" aria-hidden="true" />
                <p className="text-xs font-semibold text-lia-text-secondary uppercase">
                  {t("allowedToolsLabel") || "Ferramentas habilitadas"} ({template.allowed_tools.length})
                </p>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {template.allowed_tools.map((tool: string) => (
                  <span key={tool} className={cn(badgeStyles.default, "text-xs font-mono")}>
                    {tool}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Config grid */}
          <div className="grid grid-cols-3 gap-3 pt-2 border-t border-lia-border-subtle">
            <div>
              <p className="text-xs text-lia-text-secondary">{t("maxStepsLabel") || "Max steps"}</p>
              <p className="text-sm font-semibold text-lia-text-primary">{template.max_steps}</p>
            </div>
            <div>
              <p className="text-xs text-lia-text-secondary">{t("temperatureLabel") || "Temperature"}</p>
              <p className="text-sm font-semibold text-lia-text-primary">{template.temperature}</p>
            </div>
            <div>
              <p className="text-xs text-lia-text-secondary">{t("contextLevelLabel") || "Context"}</p>
              <p className="text-sm font-semibold text-lia-text-primary">{template.context_level}</p>
            </div>
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isCreating}>
            {t("cancel") || "Cancelar"}
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={isCreating || !customName.trim()}
            className="bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
          >
            {isCreating ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" aria-hidden="true" />
                {t("creating") || "Criando..."}
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 mr-2" aria-hidden="true" />
                {t("createAgent") || "Criar agente"}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
