"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import { useState } from "react"
import { useTranslations } from "next-intl"
import { Archive, Copy, Layers, Loader2, Maximize2, Plus, Sparkles, Trash2 } from "lucide-react"

import { cn } from "@/lib/utils"
import { textStyles } from "@/lib/design-tokens"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog"

import { usePipelineTemplates } from "@/hooks/pipeline/use-pipeline-templates"
import { useCompanyPipeline } from "@/hooks/company/use-company-pipeline"
import { PipelineTemplateSheetEditor } from "./PipelineTemplateSheetEditor"

// ─── ConfirmDialog ────────────────────────────────────────────────────────────

interface ConfirmDialogProps {
  open: boolean
  title: string
  description: string
  confirmLabel: string
  cancelLabel: string
  destructive?: boolean
  onConfirm: () => void
  onCancel: () => void
}

function ConfirmDialog({ open, title, description, confirmLabel, cancelLabel, destructive, onConfirm, onCancel }: ConfirmDialogProps) {
  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onCancel() }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>{cancelLabel}</Button>
          <Button variant={destructive ? "destructive" : "primary"} onClick={onConfirm}>{confirmLabel}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─── PipelineTemplatesTab ─────────────────────────────────────────────────────

export function PipelineTemplatesTab({ onSettingsChange }: { onSettingsChange?: (changed: boolean) => void }) {
  const t       = useTranslations("settings.recruitment.pipelineTemplates")
  const tEmpty  = useTranslations("settings.recruitment.pipelineTemplates.empty")
  const tHints  = useTranslations("settings.recruitment.pipelineTemplates.hints")
  const tStates = useTranslations("settings.recruitment.pipelineTemplates.states")
  const tActions = useTranslations("settings.recruitment.pipelineTemplates.actions")

  const {
    templates,
    isLoading,
    error: loadError,
    createTemplate,
    cloneTemplate,
    archiveTemplate,
    deleteTemplate,
    seedDefaults,
  } = usePipelineTemplates()

  const { pipeline: companyPipeline } = useCompanyPipeline()

  // ── estado ──────────────────────────────────────────────────────────────────
  const [busy, setBusy] = useState(false)
  const [confirmArchive, setConfirmArchive] = useState<string | null>(null)
  const [confirmDelete, setConfirmDelete]   = useState<string | null>(null)
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('pipeline-template-confirm-archive', !!confirmArchive)
  useLiaModalTracking('pipeline-template-confirm-delete', !!confirmDelete)

  // Sheet editor
  const [sheetOpen, setSheetOpen]           = useState(false)
  const [sheetTemplateId, setSheetTemplateId] = useState<string | null>(null)

  // Inline form para novo template
  const [showNewForm, setShowNewForm]       = useState(false)
  const [newTemplateName, setNewTemplateName] = useState("")
  const [creatingNew, setCreatingNew]       = useState(false)

  // ── handlers ────────────────────────────────────────────────────────────────

  function openSheetEditor(id: string) {
    setSheetTemplateId(id)
    setSheetOpen(true)
  }

  function handleNew() {
    setShowNewForm(true)
    setNewTemplateName("")
  }

  async function handleCreateNew(name: string) {
    const trimmed = name.trim()
    if (!trimmed) return
    setCreatingNew(true)
    try {
      const created = await createTemplate({ name: trimmed, stages: [] })
      if (created) {
        setShowNewForm(false)
        setNewTemplateName("")
        openSheetEditor(created.id)
        onSettingsChange?.(true)
      }
    } finally {
      setCreatingNew(false)
    }
  }

  async function handleNewFromPadrao() {
    if (!companyPipeline || companyPipeline.length === 0) {
      handleNew()
      return
    }
    const stages = (companyPipeline as any[])
      .filter((s) => s.stageCategory !== "system")
      .map((s, idx) => ({
        name: s.name || s.stageName,
        display_name: s.display_name || s.stageName,
        order: idx + 1,
        type: (s.liaAssisted ? "hybrid" : "manual") as "automatic" | "manual" | "hybrid",
        sla_days: s.slaDays ?? s.defaultSlaDays ?? 3,
        instructions: "",
      }))
    setBusy(true)
    try {
      const created = await createTemplate({ name: t("newTemplateDefaultName"), stages })
      if (created) {
        openSheetEditor(created.id)
        onSettingsChange?.(true)
      }
    } finally {
      setBusy(false)
    }
  }

  async function handleClone(id: string) {
    setBusy(true)
    try {
      const cloned = await cloneTemplate(id)
      if (cloned) openSheetEditor(cloned.id)
    } finally {
      setBusy(false)
    }
  }

  async function handleArchive(id: string) {
    setBusy(true)
    try {
      await archiveTemplate(id)
      onSettingsChange?.(true)
    } finally {
      setBusy(false)
      setConfirmArchive(null)
    }
  }

  async function handleDelete(id: string) {
    setBusy(true)
    try {
      await deleteTemplate(id)
      onSettingsChange?.(true)
    } finally {
      setBusy(false)
      setConfirmDelete(null)
    }
  }

  async function handleSeedDefaults() {
    try {
      setBusy(true)
      await seedDefaults()
    } finally {
      setBusy(false)
    }
  }

  // ── render ──────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-4">
      {/* Cabeçalho */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className={textStyles.titleLarge}>{t("title")}</h2>
          <p className="text-sm text-lia-text-secondary mt-1 max-w-2xl">{t("subtitle")}</p>
        </div>

        <div className="flex items-center gap-2">
          {showNewForm ? (
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={newTemplateName}
                onChange={(e) => setNewTemplateName(e.target.value)}
                placeholder="Nome do template..."
                autoFocus
                className="text-xs px-2.5 py-1.5 rounded-md border border-lia-border-subtle bg-lia-bg-primary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 w-44"
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleCreateNew(newTemplateName)
                  if (e.key === "Escape") { setShowNewForm(false); setNewTemplateName("") }
                }}
              />
              <Button size="sm" onClick={() => handleCreateNew(newTemplateName)} disabled={!newTemplateName.trim() || creatingNew} className="h-8">
                {creatingNew ? <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" /> : "Criar"}
              </Button>
              <Button variant="outline" size="sm" onClick={() => { setShowNewForm(false); setNewTemplateName("") }} className="h-8">
                Cancelar
              </Button>
            </div>
          ) : (
            <>
              <Button
                variant="outline"
                className="gap-2 text-xs h-9"
                onClick={handleNewFromPadrao}
                disabled={busy || !companyPipeline || companyPipeline.length === 0}
                title="Criar template pré-preenchido com as etapas do Pipeline Padrão da empresa"
              >
                <Copy className="w-3.5 h-3.5" />
                A partir do Padrão
              </Button>
              <Button onClick={handleNew} className="gap-2" disabled={busy}>
                <Plus className="w-4 h-4" />
                {t("newTemplate")}
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Banner de erro */}
      {loadError && (
        <Card className="border-status-error/30 bg-status-error/5">
          <CardContent className="p-4 text-sm text-status-error">{t("loadError")}</CardContent>
        </Card>
      )}

      {/* Estado vazio */}
      {!isLoading && templates.length === 0 && !loadError ? (
        <Card>
          <CardContent className="p-10 text-center space-y-4">
            <Layers className="w-12 h-12 mx-auto opacity-30" />
            <div>
              <h3 className={textStyles.titleLarge}>{tEmpty("title")}</h3>
              <p className="text-sm text-lia-text-secondary mt-1">{tEmpty("description")}</p>
            </div>
            <div className="flex items-center justify-center gap-3">
              <Button onClick={handleNew} className="gap-2">
                <Plus className="w-4 h-4" />
                {tEmpty("cta")}
              </Button>
              <Button variant="outline" disabled={busy} onClick={handleSeedDefaults} className="gap-2">
                <Sparkles className="w-4 h-4" />
                {tEmpty("seedCta")}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        /* Lista full-width (sem dual-card) */
        <div className="space-y-3">
          {isLoading && (
            <Card>
              <CardContent className="p-4 text-sm text-lia-text-secondary flex items-center gap-2">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                {t("loading")}
              </CardContent>
            </Card>
          )}

          {templates.map((tpl) => {
            const hintBadges = [
              ...(tpl.department_hint ?? []),
              ...(tpl.seniority_hint ?? []),
              ...(tpl.job_family_hint ?? []),
            ].slice(0, 4)
            const stageCount = (tpl.stages ?? []).length
            const usage = tpl.usage_count ?? 0
            const isActive = sheetTemplateId === tpl.id && sheetOpen

            return (
              <Card
                key={tpl.id}
                className={cn(
                  "transition-colors cursor-pointer",
                  isActive ? "border-lia-btn-primary-bg ring-1 ring-lia-btn-primary-bg" : "hover:border-lia-border-strong"
                )}
                onClick={() => openSheetEditor(tpl.id)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    {/* Info */}
                    <div className="flex-1 min-w-0 space-y-1.5">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className={cn(textStyles.h4, "truncate")}>{tpl.name}</h3>
                        <Chip variant={tpl.is_archived ? "neutral" : "success"}>
                          {tpl.is_archived ? tStates("archived") : tStates("active")}
                        </Chip>
                        {tpl.is_default && (
                          <Chip variant="neutral" className="text-xs">Padrão</Chip>
                        )}
                      </div>
                      {tpl.description && (
                        <p className="text-sm text-lia-text-secondary line-clamp-1">{tpl.description}</p>
                      )}
                      <div className="flex items-center gap-3 flex-wrap">
                        <span className="text-xs text-lia-text-tertiary">
                          {stageCount === 1
                            ? tHints("stagesCount_one", { count: stageCount })
                            : tHints("stagesCount_other", { count: stageCount })}
                          {" · "}
                          {usage === 1
                            ? tHints("usageCount_one", { count: usage })
                            : tHints("usageCount_other", { count: usage })}
                        </span>
                        {hintBadges.map((h, i) => (
                          <Chip key={`${h}-${i}`} variant="neutral" className="text-xs">{h}</Chip>
                        ))}
                      </div>
                    </div>

                    {/* Acões */}
                    <div className="flex items-center gap-1 flex-none" onClick={(e) => e.stopPropagation()}>
                      <Button
                        variant="ghost" size="sm"
                        onClick={() => openSheetEditor(tpl.id)}
                        aria-label="Editar pipeline completo"
                        title="Editar etapas, sub-statuses, SLA e comportamento"
                        className="h-8 w-8 p-0"
                      >
                        <Maximize2 className="w-3.5 h-3.5" />
                      </Button>
                      <Button
                        variant="ghost" size="sm"
                        disabled={busy}
                        onClick={() => handleClone(tpl.id)}
                        aria-label={tActions("clone")}
                        title={tActions("clone")}
                        className="h-8 w-8 p-0"
                      >
                        <Copy className="w-3.5 h-3.5" />
                      </Button>
                      {!tpl.is_archived && (
                        <Button
                          variant="ghost" size="sm"
                          disabled={busy}
                          onClick={() => setConfirmArchive(tpl.id)}
                          aria-label={tActions("archive")}
                          title={tActions("archive")}
                          className="h-8 w-8 p-0"
                        >
                          <Archive className="w-3.5 h-3.5" />
                        </Button>
                      )}
                      {!tpl.is_default && (
                        <Button
                          variant="ghost" size="sm"
                          disabled={busy}
                          onClick={() => setConfirmDelete(tpl.id)}
                          aria-label={tActions("delete")}
                          title={tActions("delete")}
                          className="h-8 w-8 p-0 text-status-error hover:bg-status-error/10"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {/* Diálogos de confirmação */}
      <ConfirmDialog
        open={!!confirmArchive}
        title={t("confirmArchiveTitle")}
        description={t("confirmArchive")}
        confirmLabel={tActions("archive")}
        cancelLabel={tActions("cancel")}
        onConfirm={() => confirmArchive && handleArchive(confirmArchive)}
        onCancel={() => setConfirmArchive(null)}
      />
      <ConfirmDialog
        open={!!confirmDelete}
        title={t("confirmDeleteTitle")}
        description={t("confirmDelete")}
        confirmLabel={tActions("delete")}
        cancelLabel={tActions("cancel")}
        destructive
        onConfirm={() => confirmDelete && handleDelete(confirmDelete)}
        onCancel={() => setConfirmDelete(null)}
      />

      {/* Sheet editor full-screen */}
      <PipelineTemplateSheetEditor
        templateId={sheetTemplateId}
        open={sheetOpen}
        onOpenChange={setSheetOpen}
      />
    </div>
  )
}
