"use client"

/**
 * WebhookEventTypesManager — P0.G #4 (audit 2026-05-21).
 *
 * UI Settings dedicada para CRUD de webhook event types per-tenant.
 * Pareado com Sprint 5 (catalogo dinamico ``webhook_event_types`` + hook
 * canonical ``useWebhookEventTypes``).
 *
 * Pattern canonical: monolithic Manager. Adaptado para WebhookEventTypeData
 * (event_type slug, label, category, description, deprecated flag).
 *
 * Decisoes Paulo (canonical 2026-05-20): A1 + B1 + C.
 *
 * Subscoping: ``payload_schema`` (JSON Schema arbitrário) NAO editavel
 * via este Manager inicial — fica para Manager dedicado JSON Schema editor
 * em sprint futura.
 *
 * i18n (Wave 3 followup 2026-05-21): strings PT-BR migradas para
 * `settings.catalogs.webhook` + `settings.catalogs.common`.
 */

import React, { useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import {
  Webhook,
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
  useWebhookEventTypes,
  type WebhookEventType,
  type WebhookEventTypeData,
  type EventCategory,
} from "@/hooks/webhooks/use-webhook-event-types"

interface WebhookEventTypesManagerProps {
  isAdmin: boolean
  currentUserId: string | null
}

interface FormState {
  event_type: string
  label: string
  category: EventCategory
  description: string
  deprecated: boolean
}

const EMPTY_FORM: FormState = {
  event_type: "",
  label: "",
  category: "candidates",
  description: "",
  deprecated: false,
}

const CATEGORIES: { value: EventCategory; label: string; icon: string }[] = [
  { value: "candidates", label: "Candidatos", icon: "👤" },
  { value: "jobs", label: "Vagas", icon: "💼" },
  { value: "interviews", label: "Entrevistas", icon: "🎙️" },
  { value: "offers", label: "Ofertas", icon: "📄" },
  { value: "ats", label: "ATS", icon: "🔗" },
  { value: "agents", label: "Agentes LIA", icon: "🤖" },
  { value: "system", label: "Sistema", icon: "⚙️" },
]

export function WebhookEventTypesManager({
  isAdmin,
  currentUserId,
}: WebhookEventTypesManagerProps) {
  const t = useTranslations("settings.catalogs.webhook")
  const tc = useTranslations("settings.catalogs.common")
  const {
    eventTypes,
    masterCount,
    customCount,
    total,
    isLoading,
    error,
    refetch,
    createCustom,
    updateEventType,
    deleteEventType,
    customizeMaster,
  } = useWebhookEventTypes({ includeMaster: true })

  const [filter, setFilter] = useState<"all" | "master" | "custom">("all")
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [isSaving, setIsSaving] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const filteredTemplates = useMemo(() => {
    if (filter === "master") return eventTypes.filter((t) => t.is_master_template)
    if (filter === "custom") return eventTypes.filter((t) => !t.is_master_template)
    return eventTypes
  }, [eventTypes, filter])

  function flashSuccess(msg: string) {
    setSuccessMsg(msg)
    setTimeout(() => setSuccessMsg(null), 2500)
  }

  function startCreate() {
    setEditingId("__new__")
    setForm(EMPTY_FORM)
    setFormError(null)
  }

  function startEdit(template: WebhookEventType) {
    const d = template.data
    setEditingId(template.id)
    setForm({
      event_type: d.event_type || "",
      label: d.label || "",
      category: (d.category as EventCategory) || "candidates",
      description: d.description || "",
      deprecated: !!d.deprecated,
    })
    setFormError(null)
  }

  function cancelEdit() {
    setEditingId(null)
    setForm(EMPTY_FORM)
    setFormError(null)
  }

  function buildData(): WebhookEventTypeData {
    return {
      event_type: form.event_type.trim(),
      label: form.label.trim(),
      category: form.category,
      description: form.description.trim() || undefined,
      deprecated: form.deprecated || undefined,
    }
  }

  async function handleSave() {
    if (!form.label.trim() || form.label.trim().length < 3) {
      setFormError(t("validationLabel"))
      return
    }
    if (!form.event_type.trim() || !/^[a-z0-9_]+\.[a-z0-9_]+$/.test(form.event_type.trim())) {
      setFormError(t("validationEventType"))
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
        } else setFormError(error || t("failCreate"))
      } else if (editingId) {
        const updated = await updateEventType(editingId, buildData())
        if (updated) {
          flashSuccess(t("successUpdate"))
          cancelEdit()
        } else setFormError(error || t("failUpdate"))
      }
    } finally {
      setIsSaving(false)
    }
  }

  async function handleCustomize(template: WebhookEventType) {
    const ok = await customizeMaster(template.id)
    if (ok) flashSuccess(tc("customizedMasterFlash", { label: template.data.label }))
  }

  async function handleDelete(template: WebhookEventType) {
    if (!confirm(t("confirmDelete", { label: template.data.label }))) return
    const ok = await deleteEventType(template.id)
    if (ok) flashSuccess(t("successDelete"))
  }

  function canEdit(template: WebhookEventType): boolean {
    if (template.is_master_template) return false
    if (isAdmin) return true
    return template.created_by === currentUserId
  }

  function canDelete(template: WebhookEventType): boolean {
    if (template.is_master_template) return false
    return isAdmin
  }

  if (isLoading) {
    return <HubLoadingState />
  }

  return (
    <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-lia-bg-primary/80 dark:bg-lia-bg-secondary/80 rounded-xl" data-testid="webhook-event-types-manager">
      <CardHeader className="pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
            <Webhook className="w-4 h-4 text-wedo-cyan" />
            {t("title")}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Chip variant="neutral" className="text-micro">
              {tc("countSummary", { master: masterCount, custom: customCount, total })}
            </Chip>
            <Button size="sm" onClick={startCreate} disabled={!!editingId} data-testid="webhook-event-types-new-button">
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

        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-lia-text-secondary">{tc("filters")}</span>
          {(["all", "master", "custom"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-2 py-0.5 rounded-full text-micro ${
                filter === f
                  ? "bg-wedo-cyan/15 text-wedo-cyan-dark border border-wedo-cyan/30"
                  : "bg-lia-bg-secondary text-lia-text-secondary border border-transparent"
              }`}
            >
              {f === "all" ? tc("filterAll") : f === "master" ? tc("filterMaster") : tc("filterCustom")}
            </button>
          ))}
        </div>

        {editingId && (
          <Card className="border border-wedo-cyan/30 bg-wedo-cyan/5 rounded-xl" data-testid="webhook-event-types-form">
            <CardContent className="p-3 space-y-3">
              <div className="flex items-center justify-between">
                <h5 className={textStyles.h4}>
                  {editingId === "__new__" ? t("formTitleCreate") : t("formTitleEdit")}
                </h5>
                <Button variant="ghost" size="sm" onClick={cancelEdit} data-testid="webhook-event-types-form-close">
                  <X className="w-3 h-3" />
                </Button>
              </div>
              <Input
                placeholder={t("placeholderLabel")}
                value={form.label}
                onChange={(e) => setForm({ ...form, label: e.target.value })}
                data-field="label"
              />
              <Input
                placeholder={t("placeholderEventType")}
                value={form.event_type}
                onChange={(e) => setForm({ ...form, event_type: e.target.value })}
                data-field="event_type"
              />
              <Select
                value={form.category}
                onValueChange={(v) => setForm({ ...form, category: v as EventCategory })}
              >
                <SelectTrigger data-field="category"><SelectValue placeholder={t("placeholderCategory")} /></SelectTrigger>
                <SelectContent>
                  {CATEGORIES.map((c) => (
                    <SelectItem key={c.value} value={c.value}>
                      {c.icon} {c.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <textarea
                placeholder={t("placeholderDescription")}
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                rows={2}
                className="w-full px-3 py-1.5 text-sm rounded-md border border-lia-border-subtle bg-lia-bg-primary"
                data-field="description"
              />
              <label className="flex items-center gap-1 text-xs">
                <input
                  type="checkbox"
                  checked={form.deprecated}
                  onChange={(e) => setForm({ ...form, deprecated: e.target.checked })}
                  data-toggle="deprecated"
                />
                {t("labelDeprecated")}
              </label>
              {formError && (
                <div className="text-xs text-status-error flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> {formError}
                </div>
              )}
              <div className="flex justify-end gap-2">
                <Button variant="outline" size="sm" onClick={cancelEdit} data-testid="webhook-event-types-form-cancel">{tc("cancel")}</Button>
                <Button size="sm" onClick={handleSave} disabled={isSaving} data-testid="webhook-event-types-form-save">
                  {isSaving ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : null}
                  {tc("save")}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="space-y-2 max-h-content-lg overflow-y-auto" data-testid="webhook-event-types-list">
          {filteredTemplates.length === 0 && (
            <p className="text-xs text-lia-text-secondary text-center py-4">
              {t("emptyList")}
            </p>
          )}
          {filteredTemplates.map((template) => {
            const d = template.data
            const catInfo = CATEGORIES.find((c) => c.value === d.category)
            return (
              <div
                key={template.id}
                className="flex items-start justify-between gap-2 p-3 bg-lia-bg-secondary/50 rounded-xl border border-lia-border-subtle"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className="text-sm text-lia-text-primary font-medium">{d.label}</span>
                    <Chip variant="neutral" className="text-micro font-mono">{d.event_type}</Chip>
                    {catInfo && (
                      <Chip variant="neutral" className="text-micro">
                        {catInfo.icon} {catInfo.label}
                      </Chip>
                    )}
                    {template.is_master_template && (
                      <Chip variant="neutral" className="text-micro bg-wedo-purple/15 text-wedo-purple">
                        {tc("masterChip")}
                      </Chip>
                    )}
                    {d.deprecated && (
                      <Chip variant="neutral" className="text-micro bg-status-error/10 text-status-error">
                        {tc("deprecatedChip")}
                      </Chip>
                    )}
                  </div>
                  {d.description && (
                    <p className="text-xs text-lia-text-secondary">{d.description}</p>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  {template.is_master_template && (
                    <Button variant="ghost" size="sm" onClick={() => handleCustomize(template)} title={tc("customize")}>
                      <Copy className="w-3 h-3" />
                    </Button>
                  )}
                  {canEdit(template) && (
                    <Button variant="ghost" size="sm" onClick={() => startEdit(template)} title={tc("edit")}>
                      <Pencil className="w-3 h-3" />
                    </Button>
                  )}
                  {canDelete(template) && (
                    <Button variant="ghost" size="sm" onClick={() => handleDelete(template)} title={tc("delete")}>
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
