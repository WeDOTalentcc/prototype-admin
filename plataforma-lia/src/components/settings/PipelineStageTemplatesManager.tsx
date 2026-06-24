"use client"

/**
 * PipelineStageTemplatesManager — P0.G #1 (audit 2026-05-21).
 *
 * UI Settings dedicada para CRUD de templates de pipeline stages
 * per-tenant. Pareado com Sprint 2 (catalogo dinamico
 * ``pipeline_stage_templates`` + hook canonical ``usePipelineStageTemplates``).
 *
 * Pattern canonical: monolithic Manager mesma estrutura de
 * ``EligibilityTemplatesManager.tsx`` (Sprint 1). Adaptado para
 * PipelineStageData shape.
 *
 * Decisoes Paulo (canonical 2026-05-20):
 * - A1: customize cria copia total (snapshot canonical, nao live link)
 * - B1: custom NAO sincroniza com master apos customizacao
 * - C: admin full CRUD; recrutador create-novos OK + edita proprios; NAO delete
 *
 * Subscoping: substatuses (array complexo) NAO editavel via este Manager
 * inicial — fica para Manager dedicado em sprint futura. Apenas exibe
 * count quando presente.
 *
 * i18n (Wave 3 followup 2026-05-21): strings PT-BR migradas para
 * `settings.catalogs.pipeline` + `settings.catalogs.common` em
 * messages/{pt-BR,en}.json via next-intl `useTranslations`.
 */

import React, { useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import {
  Workflow,
  Plus,
  Pencil,
  Trash2,
  Copy,
  Loader2,
  AlertCircle,
  CheckCircle,
  X,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Input } from "@/components/ui/input"
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select"
import { textStyles } from "@/lib/design-tokens"
import { HubLoadingState } from "./_shared"
import {
  usePipelineStageTemplates,
  type PipelineStageTemplate,
  type PipelineStageData,
  type ActionBehavior,
  type DefaultChannel,
} from "@/hooks/pipeline/use-pipeline-stage-templates"

interface PipelineStageTemplatesManagerProps {
  /** Whether the current user is admin (decisão Paulo C). */
  isAdmin: boolean
  /** Current user id — para owner check (recrutador edita só os seus). */
  currentUserId: string | null
}

interface FormState {
  label: string
  key: string
  color: string
  icon: string
  order: string  // string for input parsing
  is_default_in_pipeline: boolean
  action_behavior: ActionBehavior | ""
  default_channel: DefaultChannel | ""
  sla_hours: string  // string for input parsing
}

const EMPTY_FORM: FormState = {
  label: "",
  key: "",
  color: "",
  icon: "",
  order: "",
  is_default_in_pipeline: false,
  action_behavior: "",
  default_channel: "",
  sla_hours: "",
}

const ACTION_BEHAVIORS: { value: ActionBehavior; label: string }[] = [
  { value: "intake", label: "Intake (Triagem inicial)" },
  { value: "screening", label: "Screening (Avaliação CV)" },
  { value: "passive", label: "Passive (Pool passivo)" },
  { value: "scheduling", label: "Scheduling (Agendamento)" },
  { value: "evaluation", label: "Evaluation (Avaliação)" },
  { value: "verification", label: "Verification (Verificação)" },
  { value: "offer", label: "Offer (Oferta)" },
  { value: "conclusion_hired", label: "Conclusion Hired (Contratado)" },
  { value: "conclusion_declined", label: "Conclusion Declined (Declinou)" },
  { value: "conclusion_rejected", label: "Conclusion Rejected (Rejeitado)" },
]

const DEFAULT_CHANNELS: { value: DefaultChannel; label: string }[] = [
  { value: "email", label: "Email" },
  { value: "email_whatsapp", label: "Email + WhatsApp" },
  { value: "whatsapp", label: "WhatsApp" },
  { value: "none", label: "Sem comunicação" },
]

export function PipelineStageTemplatesManager({
  isAdmin,
  currentUserId,
}: PipelineStageTemplatesManagerProps) {
  const t = useTranslations("settings.catalogs.pipeline")
  const tc = useTranslations("settings.catalogs.common")
  const {
    templates,
    masterCount,
    customCount,
    total,
    isLoading,
    error,
    refetch,
    createCustom,
    updateTemplate,
    deleteTemplate,
    customizeMaster,
  } = usePipelineStageTemplates({ includeMaster: true })

  const [filter, setFilter] = useState<"all" | "master" | "custom">("all")
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [isSaving, setIsSaving] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const filteredTemplates = useMemo(() => {
    if (filter === "master") return templates.filter((t) => t.is_master_template)
    if (filter === "custom") return templates.filter((t) => !t.is_master_template)
    return templates
  }, [templates, filter])

  function flashSuccess(msg: string) {
    setSuccessMsg(msg)
    setTimeout(() => setSuccessMsg(null), 2500)
  }

  function startCreate() {
    setEditingId("__new__")
    setForm(EMPTY_FORM)
    setFormError(null)
  }

  function startEdit(template: PipelineStageTemplate) {
    const d = template.data
    setEditingId(template.id)
    setForm({
      label: d.label || "",
      key: d.key || "",
      color: d.color || "",
      icon: d.icon || "",
      order: d.order != null ? String(d.order) : "",
      is_default_in_pipeline: !!d.is_default_in_pipeline,
      action_behavior: (d.action_behavior as ActionBehavior) || "",
      default_channel: (d.default_channel as DefaultChannel) || "",
      sla_hours: d.sla_hours != null ? String(d.sla_hours) : "",
    })
    setFormError(null)
  }

  function cancelEdit() {
    setEditingId(null)
    setForm(EMPTY_FORM)
    setFormError(null)
  }

  function buildData(): PipelineStageData {
    return {
      label: form.label.trim(),
      key: form.key.trim(),
      color: form.color.trim() || undefined,
      icon: form.icon.trim() || undefined,
      order: form.order.trim() ? Number(form.order) : 0,
      is_default_in_pipeline: form.is_default_in_pipeline,
      action_behavior: form.action_behavior || undefined,
      default_channel: form.default_channel || undefined,
      sla_hours: form.sla_hours.trim() ? Number(form.sla_hours) : undefined,
    }
  }

  async function handleSave() {
    if (!form.label.trim() || form.label.trim().length < 2) {
      setFormError(t("validationLabel"))
      return
    }
    if (!form.key.trim() || !/^[a-z0-9_]+$/.test(form.key.trim())) {
      setFormError(t("validationKey"))
      return
    }
    setIsSaving(true)
    setFormError(null)
    try {
      if (editingId === "__new__") {
        const created = await createCustom(buildData())
        if (created) {
          flashSuccess(t("successCreate"))
          cancelEdit()
        } else {
          setFormError(error || t("failCreate"))
        }
      } else if (editingId) {
        const updated = await updateTemplate(editingId, buildData())
        if (updated) {
          flashSuccess(t("successUpdate"))
          cancelEdit()
        } else {
          setFormError(error || t("failUpdate"))
        }
      }
    } finally {
      setIsSaving(false)
    }
  }

  async function handleCustomize(template: PipelineStageTemplate) {
    const ok = await customizeMaster(template.id)
    if (ok) {
      flashSuccess(tc("customizedMasterFlash", { label: template.data.label }))
    }
  }

  async function handleDelete(template: PipelineStageTemplate) {
    if (!confirm(t("confirmDelete", { label: template.data.label }))) return
    const ok = await deleteTemplate(template.id)
    if (ok) {
      flashSuccess(t("successDelete"))
    }
  }

  function canEdit(template: PipelineStageTemplate): boolean {
    if (template.is_master_template) return false
    if (isAdmin) return true
    return template.created_by === currentUserId
  }

  function canDelete(template: PipelineStageTemplate): boolean {
    if (template.is_master_template) return false
    return isAdmin
  }

  if (isLoading) {
    return <HubLoadingState />
  }

  return (
    <Card data-testid="pipeline-stage-templates-manager" className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-lia-bg-primary/80 dark:bg-lia-bg-secondary/80 rounded-xl">
      <CardHeader className="pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
            <Workflow className="w-4 h-4 text-wedo-cyan" />
            {t("title")}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Chip variant="neutral" className="text-micro">
              {tc("countSummary", { master: masterCount, custom: customCount, total })}
            </Chip>
            <Button data-testid="pipeline-stage-template-create" size="sm" onClick={startCreate} disabled={!!editingId}>
              <Plus className="w-3 h-3 mr-1" /> {t("newButton")}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <div className="flex items-center gap-2 p-2 bg-status-error/10 rounded-md text-xs text-status-error">
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
            <Button variant="ghost" size="sm" onClick={refetch}>{tc("tryAgain")}</Button>
          </div>
        )}
        {successMsg && (
          <div className="flex items-center gap-2 p-2 bg-status-success/10 rounded-md text-xs text-status-success">
            <CheckCircle className="w-4 h-4" />
            {successMsg}
          </div>
        )}

        {/* Filter chips */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-lia-text-secondary">{tc("filters")}</span>
          {(["all", "master", "custom"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-2 py-0.5 rounded-full text-micro ${
                filter === f
                  ? "bg-wedo-cyan/15 text-wedo-cyan-text border border-wedo-cyan/30"
                  : "bg-lia-bg-secondary text-lia-text-secondary border border-transparent"
              }`}
            >
              {f === "all" ? tc("filterAll") : f === "master" ? tc("filterMaster") : tc("filterCustom")}
            </button>
          ))}
        </div>

        {/* Form */}
        {editingId && (
          <Card data-testid="pipeline-stage-template-form" className="border border-wedo-cyan/30 bg-wedo-cyan/5 rounded-xl">
            <CardContent className="p-3 space-y-3">
              <div className="flex items-center justify-between">
                <h5 className={textStyles.h4}>
                  {editingId === "__new__" ? t("formTitleCreate") : t("formTitleEdit")}
                </h5>
                <Button data-testid="pipeline-stage-template-form-close" variant="ghost" size="sm" onClick={cancelEdit}>
                  <X className="w-3 h-3" />
                </Button>
              </div>
              <Input
                data-field="label"
                data-testid="pipeline-stage-template-field-label"
                placeholder={t("placeholderLabel")}
                value={form.label}
                onChange={(e) => setForm({ ...form, label: e.target.value })}
              />
              <Input
                data-field="key"
                data-testid="pipeline-stage-template-field-key"
                placeholder={t("placeholderKey")}
                value={form.key}
                onChange={(e) => setForm({ ...form, key: e.target.value })}
              />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <Input
                  data-field="color"
                  data-testid="pipeline-stage-template-field-color"
                  placeholder={t("placeholderColor")}
                  value={form.color}
                  onChange={(e) => setForm({ ...form, color: e.target.value })}
                />
                <Input
                  data-field="icon"
                  data-testid="pipeline-stage-template-field-icon"
                  placeholder={t("placeholderIcon")}
                  value={form.icon}
                  onChange={(e) => setForm({ ...form, icon: e.target.value })}
                />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <Input
                  type="number"
                  data-field="order"
                  data-testid="pipeline-stage-template-field-order"
                  placeholder={t("placeholderOrder")}
                  value={form.order}
                  onChange={(e) => setForm({ ...form, order: e.target.value })}
                />
                <Input
                  type="number"
                  data-field="sla_hours"
                  data-testid="pipeline-stage-template-field-sla-hours"
                  placeholder={t("placeholderSlaHours")}
                  value={form.sla_hours}
                  onChange={(e) => setForm({ ...form, sla_hours: e.target.value })}
                />
              </div>
              <Select
                value={form.action_behavior}
                onValueChange={(v) => setForm({ ...form, action_behavior: v as ActionBehavior })}
              >
                <SelectTrigger data-field="action_behavior" data-testid="pipeline-stage-template-field-action-behavior"><SelectValue placeholder={t("placeholderActionBehavior")} /></SelectTrigger>
                <SelectContent>
                  {ACTION_BEHAVIORS.map((b) => (
                    <SelectItem key={b.value} value={b.value}>{b.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select
                value={form.default_channel}
                onValueChange={(v) => setForm({ ...form, default_channel: v as DefaultChannel })}
              >
                <SelectTrigger data-field="default_channel" data-testid="pipeline-stage-template-field-default-channel"><SelectValue placeholder={t("placeholderDefaultChannel")} /></SelectTrigger>
                <SelectContent>
                  {DEFAULT_CHANNELS.map((c) => (
                    <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <label className="flex items-center gap-1 text-xs">
                <input
                  type="checkbox"
                  data-toggle="is_default_in_pipeline"
                  data-testid="pipeline-stage-template-toggle-is-default"
                  checked={form.is_default_in_pipeline}
                  onChange={(e) => setForm({ ...form, is_default_in_pipeline: e.target.checked })}
                />
                {t("labelIsDefault")}
              </label>
              {formError && (
                <div className="text-xs text-status-error flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> {formError}
                </div>
              )}
              <div className="flex justify-end gap-2">
                <Button data-testid="pipeline-stage-template-cancel" variant="outline" size="sm" onClick={cancelEdit}>{tc("cancel")}</Button>
                <Button data-testid="pipeline-stage-template-save" size="sm" onClick={handleSave} disabled={isSaving}>
                  {isSaving ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : null}
                  {tc("save")}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* List */}
        <div data-testid="pipeline-stage-templates-list" className="space-y-2 max-h-content-lg overflow-y-auto">
          {filteredTemplates.length === 0 && (
            <p className="text-xs text-lia-text-secondary text-center py-4">
              {t("emptyList")}
            </p>
          )}
          {filteredTemplates.map((template) => {
            const d = template.data
            return (
              <div
                key={template.id}
                data-testid={`pipeline-stage-template-row-${template.id}`}
                className="flex items-start justify-between gap-2 p-3 bg-lia-bg-secondary/50 rounded-xl border border-lia-border-subtle"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    {d.icon && <span className="text-base">{d.icon}</span>}
                    <span className="text-sm text-lia-text-primary font-medium">{d.label}</span>
                    <Chip variant="neutral" className="text-micro font-mono">
                      {d.key}
                    </Chip>
                    {template.is_master_template && (
                      <Chip variant="neutral" className="text-micro bg-wedo-purple/15 text-wedo-purple-text">
                        {tc("masterChip")}
                      </Chip>
                    )}
                    {d.is_default_in_pipeline && (
                      <Chip variant="neutral" className="text-micro bg-wedo-cyan/15 text-wedo-cyan-text">
                        {tc("defaultChip")}
                      </Chip>
                    )}
                  </div>
                  <p className="text-xs text-lia-text-secondary">
                    {d.action_behavior && <span>{t("labelBehavior")} {d.action_behavior} · </span>}
                    {d.default_channel && <span>{t("labelChannel")} {d.default_channel} · </span>}
                    {d.sla_hours != null && <span>{t("labelSla")} {d.sla_hours}h · </span>}
                    {t("labelOrder")} {d.order}
                    {d.substatuses && d.substatuses.length > 0 && (
                      <span> · {t("labelSubstatusesCount", { count: d.substatuses.length })}</span>
                    )}
                  </p>
                </div>
                <div className="flex items-center gap-1">
                  {template.is_master_template && (
                    <Button
                      data-testid={`pipeline-stage-template-customize-${template.id}`}
                      variant="ghost" size="sm"
                      onClick={() => handleCustomize(template)}
                      title={tc("customizeHint")}
                    >
                      <Copy className="w-3 h-3" />
                    </Button>
                  )}
                  {canEdit(template) && (
                    <Button data-testid={`pipeline-stage-template-edit-${template.id}`} variant="ghost" size="sm" onClick={() => startEdit(template)} title={tc("edit")}>
                      <Pencil className="w-3 h-3" />
                    </Button>
                  )}
                  {canDelete(template) && (
                    <Button
                      data-testid={`pipeline-stage-template-delete-${template.id}`}
                      variant="ghost" size="sm"
                      onClick={() => handleDelete(template)}
                      title={tc("deleteAdminOnly")}
                    >
                      <Trash2 className="w-3 h-3 text-status-error" />
                    </Button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
