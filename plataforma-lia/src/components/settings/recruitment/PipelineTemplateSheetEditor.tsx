"use client"

import React, { useState, useCallback, useEffect } from "react"
import { ChevronDown, ChevronRight, Loader2, Pencil, Save, Trash2, Upload, X } from "lucide-react"
import { toast } from "sonner"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import {
  RecruitmentJourneyConfig,
} from "@/components/settings/RecruitmentJourneyConfig"
import type { RecruitmentStage, SubStatus } from "@/components/settings/recruitment-journey.types"
import { usePipelineTemplates } from "@/hooks/pipeline/use-pipeline-templates"
import { apiFetch } from "@/lib/api/api-fetch"

// ─── Conversores shape ────────────────────────────────────────────────────────

function richToRecruitmentStage(s: any, idx: number): RecruitmentStage {
  return {
    id: s.id || `tpl-stage-${idx}`,
    name: s.name,
    display_name: s.display_name || s.name,
    order: s.order ?? idx + 1,
    isActive: true,
    notes: s.description || "",
    sla: s.sla_hours ? Math.round(s.sla_hours / 24) : (s.sla_days ?? 3),
    type: (s.stage_category === "system"
      ? "system"
      : s.stage_category === "catalog"
      ? "default"
      : "custom") as RecruitmentStage["type"],
    color: s.color,
    icon: s.icon,
    action_behavior: s.action_behavior,
    default_channel: s.default_channel,
    stage_category: s.stage_category,
    sub_statuses: (s.sub_statuses || []).map((ss: any, si: number): SubStatus => ({
      id: ss.id || `ss-${idx}-${si}`,
      stage_id: s.id || `tpl-stage-${idx}`,
      name: ss.name,
      display_name: ss.display_name,
      sub_status_order: ss.order ?? si,
      color: ss.color,
      icon: ss.icon,
      is_default: ss.is_default ?? false,
      is_waiting: ss.is_waiting ?? false,
      waiting_for: ss.waiting_for || "",
      sla_hours: ss.sla_hours ?? null,
      is_active: true,
    })),
  }
}

function recruitmentToRichStage(s: RecruitmentStage, idx: number): Record<string, unknown> {
  const ab = s.action_behavior || ""
  return {
    name: s.name,
    display_name: s.display_name || s.name,
    order: (s as any).order ?? idx + 1,
    color: s.color ?? null,
    icon: s.icon ?? null,
    stage_category: (s as any).stageCategory || s.type || "custom",
    action_behavior: ab,
    default_channel: s.default_channel || "email",
    sla_hours: s.sla ? s.sla * 24 : null,
    sla_days: s.sla ?? 3,
    is_initial: false,
    is_final: ["hired", "rejected"].includes(s.name),
    is_rejection: s.name === "rejected",
    is_hired: s.name === "hired",
    description: s.notes || "",
    type:
      ab === "screening" || ab === "intake" || ab === "trigger"
        ? "automatic"
        : ab === "proactive"
        ? "hybrid"
        : "manual",
    sub_statuses: (s.sub_statuses || []).map((ss: SubStatus) => ({
      name: ss.name,
      display_name: ss.display_name,
      order: ss.sub_status_order ?? 0,
      color: ss.color ?? null,
      icon: ss.icon ?? null,
      is_default: ss.is_default ?? false,
      is_waiting: ss.is_waiting ?? false,
      waiting_for: ss.waiting_for || null,
      sla_hours: ss.sla_hours ?? null,
    })),
  }
}

// ─── Componente principal ─────────────────────────────────────────────────────

interface PipelineTemplateSheetEditorProps {
  templateId: string | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onSaved?: () => void
}

export function PipelineTemplateSheetEditor({
  templateId,
  open,
  onOpenChange,
  onSaved,
}: PipelineTemplateSheetEditorProps) {
  const { templates, updateTemplate, deleteTemplate } = usePipelineTemplates()
  const template = templates.find((t) => t.id === templateId) ?? null

  const [localStages, setLocalStages] = useState<RecruitmentStage[]>([])
  const [localName, setLocalName] = useState<string>("")
  const [editingName, setEditingName] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)

  // Saturação: extraída do template ou vazia
  const [saturation, setSaturation] = useState<{
    threshold_web: number
    threshold_sourcing: number
    unlock_increment: number
    unlock_hours: number
    enabled: boolean
  } | null>(null)
  const [showSaturation, setShowSaturation] = useState(false)
  const [saving, setSaving] = useState(false)
  const [applyingPadrao, setApplyingPadrao] = useState(false)

  // Fase D Opcao 2: aplica template como Padrao da empresa
  // Usa PUT /api/backend-proxy/company-pipeline com os stages do template
  const handleApplyAsPadrao = async () => {
    if (!template) return
    const confirmed = window.confirm(
      `Aplicar "${template.name}" como pipeline padr\u00e3o da empresa?\n\n` +
      `Isso substituir\u00e1 as etapas do Pipeline > Padr\u00e3o.\n` +
      `Os sub-statuses existentes ser\u00e3o preservados nas etapas mantidas.`
    )
    if (!confirmed) return
    setApplyingPadrao(true)
    try {
      // Converte stages do template -> payload do PUT /company-pipeline
      const stagesPayload = localStages.map((s: any, idx: number) => ({
        id: undefined,  // criacao/match por nome
        name: s.name,
        display_name: s.display_name || s.name,
        stage_order: idx + 1,
        color: s.color || undefined,
        icon: s.icon || undefined,
        sla_hours: s.sla ? s.sla * 24 : null,
        is_active: s.isActive !== false,
        description: s.notes || s.description || '',
        action_behavior: (s as any).action_behavior || 'passive',
        default_channel: (s as any).default_channel || 'email',
      }))
      const res = await apiFetch('/api/backend-proxy/company-pipeline', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stages: stagesPayload }),
      })
      if (res.ok) {
        // 1. Sincroniza sub-statuses canonicos nas stages novas/recriadas
        try {
          await apiFetch('/api/backend-proxy/recruitment-stages/sync-canonical', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}),
          })
        } catch {
          // nao bloqueia
        }
        // 2. Upsert sub-statuses customizados do template nas stages da empresa
        try {
          const templateSubStatuses = localStages
            .filter((st: any) => (st.sub_statuses || []).length > 0)
            .map((st: any) => ({
              stage_name: st.name,
              sub_statuses: (st.sub_statuses || []).map((ss: any) => ({
                name: ss.name,
                display_name: ss.display_name,
                order: ss.sub_status_order ?? ss.order ?? 0,
                color: ss.color || null,
                icon: ss.icon || null,
                is_default: ss.is_default ?? false,
                is_waiting: ss.is_waiting ?? false,
                waiting_for: ss.waiting_for || null,
                sla_hours: ss.sla_hours || null,
              })),
            }))
          if (templateSubStatuses.length > 0) {
            await apiFetch('/api/backend-proxy/recruitment-stages/apply-template-sub-statuses', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ stages: templateSubStatuses }),
            })
          }
        } catch {
          // nao bloqueia — sub-statuses customizados podem ser adicionados manualmente
        }
        toast.success(`Pipeline Padr\u00e3o atualizado com o template "${template.name}"!`)
        onOpenChange(false)
      } else {
        toast.error('Erro ao aplicar template. Tente novamente.')
      }
    } catch {
      toast.error('Erro ao aplicar template. Tente novamente.')
    } finally {
      setApplyingPadrao(false)
    }
  }

  // Sincroniza stages e nome locais quando o template muda
  useEffect(() => {
    if (template) {
      setLocalStages((template.stages || []).map(richToRecruitmentStage))
      setLocalName(template.name || "")
      const sc = (template as any).saturation_config
      setSaturation(sc ? {
        threshold_web: sc.threshold_web ?? 50,
        threshold_sourcing: sc.threshold_sourcing ?? 200,
        unlock_increment: sc.unlock_increment ?? 10,
        unlock_hours: sc.unlock_hours ?? 24,
        enabled: true,
      } : null)
    } else {
      setLocalStages([])
      setLocalName("")
      setSaturation(null)
    }
  }, [template?.id])

  // Sub-status toggle: atualiza estado local (nao faz PATCH na empresa)
  const handleToggleSubStatus = useCallback(
    async (subStatusId: string, updates: { is_active?: boolean; is_default?: boolean }) => {
      setLocalStages((prev) =>
        prev.map((stage) => ({
          ...stage,
          sub_statuses: (stage.sub_statuses || []).map((ss) =>
            ss.id === subStatusId ? { ...ss, ...updates } : ss
          ),
        }))
      )
    },
    []
  )

  const handleSave = async () => {
    if (!templateId) return
    setSaving(true)
    try {
      const richStages = localStages.map(recruitmentToRichStage)
      await updateTemplate(templateId, {
        stages: richStages as any,
        name: localName.trim() || template?.name || "Template",
        ...(saturation?.enabled ? { saturation_config: {
          threshold_web: saturation.threshold_web,
          threshold_sourcing: saturation.threshold_sourcing,
          unlock_increment: saturation.unlock_increment,
          unlock_hours: saturation.unlock_hours,
        } } : { saturation_config: null }),
      })
      toast.success("Template salvo com sucesso!")
      onSaved?.()
      onOpenChange(false)
    } catch {
      toast.error("Erro ao salvar template. Tente novamente.")
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!templateId) return
    setDeleting(true)
    try {
      await deleteTemplate(templateId)
      toast.success("Template excluído.")
      onOpenChange(false)
    } catch {
      toast.error("Erro ao excluir template.")
    } finally {
      setDeleting(false)
      setConfirmDelete(false)
    }
  }

  return (
    <>
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-full max-w-none sm:max-w-none md:w-[90vw] lg:w-[80vw] xl:w-[72vw] overflow-hidden p-0 flex flex-col"
        data-testid="pipeline-template-sheet-editor"
      >
        {/* Header fixo */}
        <SheetHeader className="px-6 py-4 border-b border-lia-border-subtle flex-none">
          <div className="flex items-center justify-between gap-4">
            <div className="min-w-0">
              {editingName ? (
                <input
                  value={localName}
                  onChange={(e) => setLocalName(e.target.value)}
                  onBlur={() => setEditingName(false)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") setEditingName(false)
                    if (e.key === "Escape") { setLocalName(template?.name || ""); setEditingName(false) }
                  }}
                  autoFocus
                  aria-label="Nome do template"
                  className="text-lg font-semibold bg-transparent border-b border-lia-btn-primary-bg outline-none text-lia-text-primary w-full max-w-xs"
                />
              ) : (
                <SheetTitle
                  className="text-lg font-semibold text-lia-text-primary truncate cursor-text group flex items-center gap-1.5"
                  onClick={() => setEditingName(true)}
                  title="Clique para renomear"
                >
                  {(localName || template?.name) ?? "Template"}
                  <Pencil className="w-3 h-3 opacity-0 group-hover:opacity-40 transition-opacity" />
                </SheetTitle>
              )}
              <SheetDescription className="text-sm text-lia-text-secondary mt-0.5">
                {localStages.length} etapa{localStages.length !== 1 ? "s" : ""} —
                arraste para reordenar, edite SLA e sub-statuses
              </SheetDescription>
            </div>
            <div className="flex items-center gap-2 flex-none">
              <Button
                variant="outline"
                size="sm"
                onClick={handleApplyAsPadrao}
                disabled={saving || applyingPadrao || !template}
                title="Substituir o Pipeline Padr\u00e3o da empresa pelas etapas deste template"
              >
                {applyingPadrao ? (
                  <Loader2 className="w-4 h-4 mr-1 animate-spin" aria-hidden />
                ) : (
                  <Upload className="w-4 h-4 mr-1" aria-hidden />
                )}
                Aplicar como Padr\u00e3o
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setConfirmDelete(true)}
                disabled={saving || applyingPadrao || deleting || !template}
                title="Excluir este template"
                className="text-status-error hover:bg-status-error/10 mr-1"
              >
                <Trash2 className="w-4 h-4" aria-hidden />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onOpenChange(false)}
                disabled={saving}
              >
                <X className="w-4 h-4 mr-1" aria-hidden />
                Cancelar
              </Button>
              <Button size="sm" onClick={handleSave} disabled={saving}>
                {saving ? (
                  <Loader2 className="w-4 h-4 mr-1 animate-spin motion-reduce:animate-none" aria-hidden />
                ) : (
                  <Save className="w-4 h-4 mr-1" aria-hidden />
                )}
                Salvar template
              </Button>
            </div>
          </div>
        </SheetHeader>

        {/* Corpo rolavel */}
        <div className="flex-1 overflow-y-auto p-6">
          {!template ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-6 h-6 animate-spin text-lia-text-tertiary" />
            </div>
          ) : (
            {/* Card de configuração de saturação (opcional) */}
            <div className="mb-6 border border-lia-border-subtle rounded-xl overflow-hidden">
              <button
                className="w-full flex items-center justify-between px-4 py-3 bg-lia-bg-secondary/50 hover:bg-lia-bg-secondary text-sm font-medium text-lia-text-primary transition-colors"
                onClick={() => setShowSaturation(!showSaturation)}
                type="button"
              >
                <span className="flex items-center gap-2">
                  Configuração de Volume (Saturação)
                  {saturation?.enabled && (
                    <span className="text-xs text-wedo-cyan font-normal">incluída no template</span>
                  )}
                </span>
                {showSaturation
                  ? <ChevronDown className="w-4 h-4 text-lia-text-secondary" />
                  : <ChevronRight className="w-4 h-4 text-lia-text-secondary" />}
              </button>
              {showSaturation && (
                <div className="px-4 py-4 space-y-4 bg-lia-bg-primary">
                  <p className="text-xs text-lia-text-secondary">
                    Quando ativada, esta configuração é aplicada junto com o template no Pipeline Padrão.
                  </p>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={saturation?.enabled ?? false}
                      onChange={e => {
                        if (e.target.checked) {
                          setSaturation({ threshold_web: 50, threshold_sourcing: 200, unlock_increment: 10, unlock_hours: 24, enabled: true })
                        } else {
                          setSaturation(null)
                        }
                      }}
                      className="w-4 h-4 rounded accent-wedo-cyan"
                    />
                    <span className="text-sm text-lia-text-primary">Incluir no template</span>
                  </label>
                  {saturation?.enabled && (
                    <div className="grid grid-cols-2 gap-3">
                      {([
                        { key: 'threshold_web' as const, label: 'Máx. candidatos web', hint: 'Bloqueia sourcing web após este número' },
                        { key: 'threshold_sourcing' as const, label: 'Máx. em sourcing', hint: 'Bloqueia sourcing ativo após este número' },
                        { key: 'unlock_increment' as const, label: 'Desbloquear por vez', hint: '+N candidatos por desbloqueio' },
                        { key: 'unlock_hours' as const, label: 'Horas entre desbloqueios', hint: 'Intervalo de desbloqueio' },
                      ] as const).map(({ key, label, hint }) => (
                        <div key={key} className="space-y-1">
                          <label className="text-xs font-medium text-lia-text-primary">{label}</label>
                          <input
                            type="number"
                            min={1}
                            value={saturation[key]}
                            onChange={e => setSaturation(prev => prev ? { ...prev, [key]: Number(e.target.value) } : prev)}
                            className="w-full px-2.5 py-1.5 text-sm rounded-lg border border-lia-border-subtle bg-lia-bg-primary text-lia-text-primary focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20"
                          />
                          <p className="text-xs text-lia-text-tertiary">{hint}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            <RecruitmentJourneyConfig
              stages={localStages}
              onChange={setLocalStages}
              isEditMode
              hideHeader
              onToggleSubStatus={handleToggleSubStatus}
            />
          )}
        </div>
      </SheetContent>
    </Sheet>

    {/* Dialog de confirmação de exclusão */}
    {confirmDelete && (
      <div
        className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40"
        onClick={() => setConfirmDelete(false)}
      >
        <div
          className="bg-lia-bg-primary rounded-xl shadow-lg p-6 max-w-sm w-full mx-4 space-y-4"
          onClick={(e) => e.stopPropagation()}
        >
          <h2 className="text-base font-semibold text-lia-text-primary">Excluir template?</h2>
          <p className="text-sm text-lia-text-secondary">
            O template <strong>{localName || template?.name}</strong> será excluído permanentemente.
            Vagas que já usaram este template mantêm seus pipelines.
          </p>
          <div className="flex items-center justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => setConfirmDelete(false)} disabled={deleting}>
              Cancelar
            </Button>
            <Button
              size="sm"
              onClick={handleDelete}
              disabled={deleting}
              className="bg-status-error hover:bg-status-error/90 text-white"
            >
              {deleting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Excluir"}
            </Button>
          </div>
        </div>
      </div>
    )}
    </>
  )
}
