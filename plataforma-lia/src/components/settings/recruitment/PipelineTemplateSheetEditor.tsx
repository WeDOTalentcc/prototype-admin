"use client"

import React, { useState, useCallback, useEffect } from "react"
import { Loader2, Save, X } from "lucide-react"
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
    stageCategory: s.stage_category,
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
  const { templates, updateTemplate } = usePipelineTemplates()
  const template = templates.find((t) => t.id === templateId) ?? null

  const [localStages, setLocalStages] = useState<RecruitmentStage[]>([])
  const [saving, setSaving] = useState(false)

  // Sincroniza stages locais quando o template muda
  useEffect(() => {
    if (template) {
      setLocalStages((template.stages || []).map(richToRecruitmentStage))
    } else {
      setLocalStages([])
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
      await updateTemplate(templateId, { stages: richStages as any, name: template?.name ?? "Template" })
      toast.success("Template salvo com sucesso!")
      onSaved?.()
      onOpenChange(false)
    } catch {
      toast.error("Erro ao salvar template. Tente novamente.")
    } finally {
      setSaving(false)
    }
  }

  return (
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
              <SheetTitle className="text-lg font-semibold text-lia-text-primary truncate">
                {template?.name ?? "Template"}
              </SheetTitle>
              <SheetDescription className="text-sm text-lia-text-secondary mt-0.5">
                {localStages.length} etapa{localStages.length !== 1 ? "s" : ""} —
                arraste para reordenar, edite SLA e sub-statuses
              </SheetDescription>
            </div>
            <div className="flex items-center gap-2 flex-none">
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
  )
}
