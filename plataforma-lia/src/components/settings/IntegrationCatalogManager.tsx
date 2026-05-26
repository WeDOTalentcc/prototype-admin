"use client"

/**
 * IntegrationCatalogManager — P0.G #3 (audit 2026-05-21).
 *
 * UI Settings dedicada para CRUD de integration catalog per-tenant.
 * Pareado com Sprint 4 (catalogo dinamico ``integration_catalog_entries``
 * + hook canonical ``useIntegrationCatalog``).
 *
 * Pattern canonical: monolithic Manager. Adaptado para IntegrationCatalogData
 * (provider, label, category, status, description).
 *
 * Decisoes Paulo (canonical 2026-05-20): A1 + B1 + C.
 *
 * Subscoping: ``metadata.capabilities`` array NAO editavel via este Manager
 * inicial (form complexo) — fica para Manager dedicado em sprint futura.
 *
 * i18n (Wave 3 followup 2026-05-21): strings PT-BR migradas para
 * `settings.catalogs.integration` + `settings.catalogs.common`.
 */

import React, { useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import {
  Plug,
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
  useIntegrationCatalog,
  type IntegrationCatalogEntry,
  type IntegrationCatalogData,
  type IntegrationCategory,
  type IntegrationStatus,
} from "@/hooks/integrations/use-integration-catalog"

interface IntegrationCatalogManagerProps {
  isAdmin: boolean
  currentUserId: string | null
}

interface FormState {
  provider: string
  label: string
  category: IntegrationCategory
  description: string
  status: IntegrationStatus
  logo_url: string
  full_description: string
}

const EMPTY_FORM: FormState = {
  provider: "",
  label: "",
  category: "ai_models",
  description: "",
  status: "production",
  logo_url: "",
  full_description: "",
}

const CATEGORIES: { value: IntegrationCategory; label: string; icon: string }[] = [
  { value: "ai_models", label: "AI Models", icon: "🤖" },
  { value: "ats", label: "ATS (Recrutamento)", icon: "👥" },
  { value: "calendar", label: "Calendário", icon: "📅" },
  { value: "communication", label: "Comunicação", icon: "💬" },
  { value: "crm_hris", label: "CRM / HRIS", icon: "🏢" },
  { value: "mcps_apis", label: "MCPs / APIs", icon: "🔌" },
]

const STATUSES: { value: IntegrationStatus; label: string; color: string }[] = [
  { value: "production", label: "Produção", color: "bg-status-success/15 text-status-success" },
  { value: "coming_soon", label: "Em breve", color: "bg-wedo-cyan/15 text-wedo-cyan-dark" },
  { value: "deprecated", label: "Descontinuada", color: "bg-status-error/10 text-status-error" },
]

export function IntegrationCatalogManager({
  isAdmin,
  currentUserId,
}: IntegrationCatalogManagerProps) {
  const t = useTranslations("settings.catalogs.integration")
  const tc = useTranslations("settings.catalogs.common")
  const {
    entries,
    masterCount,
    customCount,
    total,
    isLoading,
    error,
    refetch,
    createCustom,
    updateEntry,
    deleteEntry,
    customizeMaster,
  } = useIntegrationCatalog({ includeMaster: true })

  const [filter, setFilter] = useState<"all" | "master" | "custom">("all")
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [isSaving, setIsSaving] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const filteredEntries = useMemo(() => {
    if (filter === "master") return entries.filter((e) => e.is_master_template)
    if (filter === "custom") return entries.filter((e) => !e.is_master_template)
    return entries
  }, [entries, filter])

  function flashSuccess(msg: string) {
    setSuccessMsg(msg)
    setTimeout(() => setSuccessMsg(null), 2500)
  }

  function startCreate() {
    setEditingId("__new__")
    setForm(EMPTY_FORM)
    setFormError(null)
  }

  function startEdit(entry: IntegrationCatalogEntry) {
    const d = entry.data
    setEditingId(entry.id)
    setForm({
      provider: d.provider || "",
      label: d.label || "",
      category: d.category,
      description: d.description || "",
      status: d.status,
      logo_url: d.logo_url || "",
      full_description: d.full_description || "",
    })
    setFormError(null)
  }

  function cancelEdit() {
    setEditingId(null)
    setForm(EMPTY_FORM)
    setFormError(null)
  }

  function buildData(): IntegrationCatalogData {
    return {
      provider: form.provider.trim(),
      label: form.label.trim(),
      category: form.category,
      description: form.description.trim(),
      status: form.status,
      logo_url: form.logo_url.trim() || null,
      full_description: form.full_description.trim() || null,
    }
  }

  async function handleSave() {
    if (!form.label.trim() || form.label.trim().length < 2) {
      setFormError(t("validationLabel"))
      return
    }
    if (!form.provider.trim() || !/^[a-z0-9_]+$/.test(form.provider.trim())) {
      setFormError(t("validationProvider"))
      return
    }
    if (!form.description.trim()) {
      setFormError(t("validationDescription"))
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
        const updated = await updateEntry(editingId, buildData())
        if (updated) {
          flashSuccess(t("successUpdate"))
          cancelEdit()
        } else setFormError(error || t("failUpdate"))
      }
    } finally {
      setIsSaving(false)
    }
  }

  async function handleCustomize(entry: IntegrationCatalogEntry) {
    const ok = await customizeMaster(entry.id)
    if (ok) flashSuccess(tc("customizedMasterFlash", { label: entry.data.label }))
  }

  async function handleDelete(entry: IntegrationCatalogEntry) {
    if (!confirm(t("confirmDelete", { label: entry.data.label }))) return
    const ok = await deleteEntry(entry.id)
    if (ok) flashSuccess(t("successDelete"))
  }

  function canEdit(entry: IntegrationCatalogEntry): boolean {
    if (entry.is_master_template) return false
    if (isAdmin) return true
    return entry.created_by === currentUserId
  }

  function canDelete(entry: IntegrationCatalogEntry): boolean {
    if (entry.is_master_template) return false
    return isAdmin
  }

  if (isLoading) {
    return <HubLoadingState />
  }

  return (
    <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-lia-bg-primary/80 dark:bg-lia-bg-secondary/80 rounded-xl" data-testid="integration-catalog-manager">
      <CardHeader className="pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
            <Plug className="w-4 h-4 text-wedo-cyan" />
            {t("title")}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Chip variant="neutral" className="text-micro">
              {tc("countSummary", { master: masterCount, custom: customCount, total })}
            </Chip>
            <Button size="sm" onClick={startCreate} disabled={!!editingId} data-testid="integration-catalog-new-button">
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
              {f === "all" ? tc("filterAllFeminine") : f === "master" ? tc("filterMaster") : tc("filterCustom")}
            </button>
          ))}
        </div>

        {editingId && (
          <Card className="border border-wedo-cyan/30 bg-wedo-cyan/5 rounded-xl" data-testid="integration-catalog-form">
            <CardContent className="p-3 space-y-3">
              <div className="flex items-center justify-between">
                <h5 className={textStyles.h4}>
                  {editingId === "__new__" ? t("formTitleCreate") : t("formTitleEdit")}
                </h5>
                <Button variant="ghost" size="sm" onClick={cancelEdit} data-testid="integration-catalog-form-close">
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
                placeholder={t("placeholderProvider")}
                value={form.provider}
                onChange={(e) => setForm({ ...form, provider: e.target.value })}
                data-field="provider"
              />
              <Input
                placeholder={t("placeholderDescription")}
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                data-field="description"
              />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <Select
                  value={form.category}
                  onValueChange={(v) => setForm({ ...form, category: v as IntegrationCategory })}
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
                <Select
                  value={form.status}
                  onValueChange={(v) => setForm({ ...form, status: v as IntegrationStatus })}
                >
                  <SelectTrigger data-field="status"><SelectValue placeholder={t("placeholderStatus")} /></SelectTrigger>
                  <SelectContent>
                    {STATUSES.map((s) => (
                      <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Input
                placeholder={t("placeholderLogoUrl")}
                value={form.logo_url}
                onChange={(e) => setForm({ ...form, logo_url: e.target.value })}
                data-field="logo_url"
              />
              <textarea
                placeholder={t("placeholderFullDescription")}
                value={form.full_description}
                onChange={(e) => setForm({ ...form, full_description: e.target.value })}
                rows={3}
                className="w-full px-3 py-1.5 text-sm rounded-md border border-lia-border-subtle bg-lia-bg-primary"
                data-field="full_description"
              />
              {formError && (
                <div className="text-xs text-status-error flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> {formError}
                </div>
              )}
              <div className="flex justify-end gap-2">
                <Button variant="outline" size="sm" onClick={cancelEdit} data-testid="integration-catalog-form-cancel">{tc("cancel")}</Button>
                <Button size="sm" onClick={handleSave} disabled={isSaving} data-testid="integration-catalog-form-save">
                  {isSaving ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : null}
                  {tc("save")}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="space-y-2 max-h-content-lg overflow-y-auto" data-testid="integration-catalog-list">
          {filteredEntries.length === 0 && (
            <p className="text-xs text-lia-text-secondary text-center py-4">
              {t("emptyList")}
            </p>
          )}
          {filteredEntries.map((entry) => {
            const d = entry.data
            const catInfo = CATEGORIES.find((c) => c.value === d.category)
            const statusInfo = STATUSES.find((s) => s.value === d.status)
            return (
              <div
                key={entry.id}
                className="flex items-start justify-between gap-2 p-3 bg-lia-bg-secondary/50 rounded-xl border border-lia-border-subtle"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className="text-sm text-lia-text-primary font-medium">{d.label}</span>
                    <Chip variant="neutral" className="text-micro font-mono">{d.provider}</Chip>
                    {catInfo && (
                      <Chip variant="neutral" className="text-micro">
                        {catInfo.icon} {catInfo.label}
                      </Chip>
                    )}
                    {statusInfo && (
                      <Chip variant="neutral" className={`text-micro ${statusInfo.color}`}>
                        {statusInfo.label}
                      </Chip>
                    )}
                    {entry.is_master_template && (
                      <Chip variant="neutral" className="text-micro bg-wedo-purple/15 text-wedo-purple">
                        {tc("masterChip")}
                      </Chip>
                    )}
                  </div>
                  <p className="text-xs text-lia-text-secondary">{d.description}</p>
                </div>
                <div className="flex items-center gap-1">
                  {entry.is_master_template && (
                    <Button variant="ghost" size="sm" onClick={() => handleCustomize(entry)} title={tc("customize")}>
                      <Copy className="w-3 h-3" />
                    </Button>
                  )}
                  {canEdit(entry) && (
                    <Button variant="ghost" size="sm" onClick={() => startEdit(entry)} title={tc("edit")}>
                      <Pencil className="w-3 h-3" />
                    </Button>
                  )}
                  {canDelete(entry) && (
                    <Button variant="ghost" size="sm" onClick={() => handleDelete(entry)} title={tc("delete")}>
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
