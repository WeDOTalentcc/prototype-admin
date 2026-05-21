"use client"

/**
 * AlertRuleTemplatesManager — P0.G #2 (audit 2026-05-21).
 *
 * UI Settings dedicada para CRUD de templates de alert rules per-tenant.
 * Pareado com Sprint 3 (catalogo dinamico ``alert_rule_templates`` + hook
 * canonical ``useAlertRuleTemplates``).
 *
 * Pattern canonical: monolithic Manager mesma estrutura de
 * ``EligibilityTemplatesManager.tsx``. Adaptado para AlertRuleData shape
 * (event_type, label, audience, channels[], delay_minutes,
 * schedule_lgpd_compliant).
 *
 * Decisoes Paulo (canonical 2026-05-20): A1 + B1 + C.
 */

import React, { useMemo, useState } from "react"
import {
  Bell,
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
import {
  useAlertRuleTemplates,
  type AlertRuleTemplate,
  type AlertRuleData,
  type AlertAudience,
  type AlertChannel,
} from "@/hooks/communication/use-alert-rule-templates"

interface AlertRuleTemplatesManagerProps {
  isAdmin: boolean
  currentUserId: string | null
}

interface FormState {
  event_type: string
  label: string
  audience: AlertAudience
  channels: AlertChannel[]
  delay_minutes: string
  schedule_lgpd_compliant: boolean
}

const EMPTY_FORM: FormState = {
  event_type: "",
  label: "",
  audience: "recruiter",
  channels: ["email"],
  delay_minutes: "0",
  schedule_lgpd_compliant: true,
}

const AUDIENCES: { value: AlertAudience; label: string }[] = [
  { value: "recruiter", label: "Recrutador" },
  { value: "admin", label: "Admin" },
  { value: "candidate", label: "Candidato" },
]

const CHANNELS: { value: AlertChannel; label: string }[] = [
  { value: "email", label: "Email" },
  { value: "in_app", label: "In-app" },
  { value: "teams", label: "Teams" },
  { value: "whatsapp", label: "WhatsApp" },
]

export function AlertRuleTemplatesManager({
  isAdmin,
  currentUserId,
}: AlertRuleTemplatesManagerProps) {
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
  } = useAlertRuleTemplates({ includeMaster: true })

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

  function startEdit(template: AlertRuleTemplate) {
    const d = template.data
    setEditingId(template.id)
    setForm({
      event_type: d.event_type || "",
      label: d.label || "",
      audience: (d.audience as AlertAudience) || "recruiter",
      channels: Array.isArray(d.channels) ? d.channels : ["email"],
      delay_minutes: d.delay_minutes != null ? String(d.delay_minutes) : "0",
      schedule_lgpd_compliant: d.schedule_lgpd_compliant ?? true,
    })
    setFormError(null)
  }

  function cancelEdit() {
    setEditingId(null)
    setForm(EMPTY_FORM)
    setFormError(null)
  }

  function buildData(): AlertRuleData {
    return {
      event_type: form.event_type.trim(),
      label: form.label.trim(),
      audience: form.audience,
      channels: form.channels.length > 0 ? form.channels : ["email"],
      delay_minutes: form.delay_minutes.trim() ? Number(form.delay_minutes) : 0,
      schedule_lgpd_compliant: form.schedule_lgpd_compliant,
    }
  }

  function toggleChannel(ch: AlertChannel) {
    setForm((prev) => {
      const has = prev.channels.includes(ch)
      return {
        ...prev,
        channels: has ? prev.channels.filter((c) => c !== ch) : [...prev.channels, ch],
      }
    })
  }

  async function handleSave() {
    if (!form.label.trim() || form.label.trim().length < 3) {
      setFormError("Label deve ter pelo menos 3 caracteres")
      return
    }
    if (!form.event_type.trim() || !/^[a-z0-9_.]+$/.test(form.event_type.trim())) {
      setFormError("Event type deve ser slug (a-z, 0-9, _, ., ex: candidate.applied)")
      return
    }
    if (form.channels.length === 0) {
      setFormError("Selecione ao menos 1 canal")
      return
    }
    setIsSaving(true)
    setFormError(null)
    try {
      if (editingId === "__new__") {
        const created = await createCustom(buildData())
        if (created) {
          flashSuccess("Alert rule criada")
          cancelEdit()
        } else setFormError(error || "Falha ao criar")
      } else if (editingId) {
        const updated = await updateTemplate(editingId, buildData())
        if (updated) {
          flashSuccess("Alert rule atualizada")
          cancelEdit()
        } else setFormError(error || "Falha ao atualizar")
      }
    } finally {
      setIsSaving(false)
    }
  }

  async function handleCustomize(template: AlertRuleTemplate) {
    const ok = await customizeMaster(template.id)
    if (ok) flashSuccess(`Master "${template.data.label}" customizado`)
  }

  async function handleDelete(template: AlertRuleTemplate) {
    if (!confirm(`Excluir alert "${template.data.label}"?`)) return
    const ok = await deleteTemplate(template.id)
    if (ok) flashSuccess("Alert rule excluída")
  }

  function canEdit(template: AlertRuleTemplate): boolean {
    if (template.is_master_template) return false
    if (isAdmin) return true
    return template.created_by === currentUserId
  }

  function canDelete(template: AlertRuleTemplate): boolean {
    if (template.is_master_template) return false
    return isAdmin
  }

  if (isLoading) {
    return (
      <Card className="border border-lia-border-subtle/50 rounded-xl">
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="w-5 h-5 animate-spin text-lia-text-secondary" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-lia-bg-primary/80 dark:bg-lia-bg-secondary/80 rounded-xl">
      <CardHeader className="pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
            <Bell className="w-4 h-4 text-wedo-cyan" />
            Gerenciador de Alertas (Notificações)
          </CardTitle>
          <div className="flex items-center gap-2">
            <Chip variant="neutral" className="text-micro">
              {masterCount} master · {customCount} custom · {total} total
            </Chip>
            <Button size="sm" onClick={startCreate} disabled={!!editingId}>
              <Plus className="w-3 h-3 mr-1" /> Nova regra
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <div className="flex items-center gap-2 p-2 bg-status-error/10 rounded-md text-xs text-status-error">
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
            <Button variant="ghost" size="sm" onClick={refetch}>Tentar novamente</Button>
          </div>
        )}
        {successMsg && (
          <div className="flex items-center gap-2 p-2 bg-status-success/10 rounded-md text-xs text-status-success">
            <CheckCircle className="w-4 h-4" />
            {successMsg}
          </div>
        )}

        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-lia-text-secondary">Filtrar:</span>
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
              {f === "all" ? "Todos" : f === "master" ? "Master canonical" : "Customs da empresa"}
            </button>
          ))}
        </div>

        {editingId && (
          <Card className="border border-wedo-cyan/30 bg-wedo-cyan/5 rounded-xl">
            <CardContent className="p-3 space-y-3">
              <div className="flex items-center justify-between">
                <h5 className={textStyles.h4}>
                  {editingId === "__new__" ? "Criar alert rule" : "Editar alert rule"}
                </h5>
                <Button variant="ghost" size="sm" onClick={cancelEdit}>
                  <X className="w-3 h-3" />
                </Button>
              </div>
              <Input
                placeholder="Label (ex: Candidato aplicou em vaga)"
                value={form.label}
                onChange={(e) => setForm({ ...form, label: e.target.value })}
              />
              <Input
                placeholder="Event type (slug: candidate.applied, interview.cancelled)"
                value={form.event_type}
                onChange={(e) => setForm({ ...form, event_type: e.target.value })}
              />
              <Select
                value={form.audience}
                onValueChange={(v) => setForm({ ...form, audience: v as AlertAudience })}
              >
                <SelectTrigger><SelectValue placeholder="Audience" /></SelectTrigger>
                <SelectContent>
                  {AUDIENCES.map((a) => (
                    <SelectItem key={a.value} value={a.value}>{a.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div>
                <p className="text-xs text-lia-text-secondary mb-1">Canais (multi-seleção):</p>
                <div className="flex flex-wrap gap-2">
                  {CHANNELS.map((c) => (
                    <label key={c.value} className="flex items-center gap-1 text-xs cursor-pointer">
                      <input
                        type="checkbox"
                        checked={form.channels.includes(c.value)}
                        onChange={() => toggleChannel(c.value)}
                      />
                      {c.label}
                    </label>
                  ))}
                </div>
              </div>
              <Input
                type="number"
                placeholder="Delay em minutos (0 = imediato)"
                value={form.delay_minutes}
                onChange={(e) => setForm({ ...form, delay_minutes: e.target.value })}
              />
              <label className="flex items-center gap-1 text-xs">
                <input
                  type="checkbox"
                  checked={form.schedule_lgpd_compliant}
                  onChange={(e) => setForm({ ...form, schedule_lgpd_compliant: e.target.checked })}
                />
                Respeita janela LGPD (horario comercial Brasilia)
              </label>
              {formError && (
                <div className="text-xs text-status-error flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> {formError}
                </div>
              )}
              <div className="flex justify-end gap-2">
                <Button variant="outline" size="sm" onClick={cancelEdit}>Cancelar</Button>
                <Button size="sm" onClick={handleSave} disabled={isSaving}>
                  {isSaving ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : null}
                  Salvar
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="space-y-2 max-h-content-lg overflow-y-auto">
          {filteredTemplates.length === 0 && (
            <p className="text-xs text-lia-text-secondary text-center py-4">
              Nenhuma alert rule nessa categoria.
            </p>
          )}
          {filteredTemplates.map((template) => {
            const d = template.data
            return (
              <div
                key={template.id}
                className="flex items-start justify-between gap-2 p-3 bg-lia-bg-secondary/50 rounded-xl border border-lia-border-subtle"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className="text-sm text-lia-text-primary font-medium">{d.label}</span>
                    <Chip variant="neutral" className="text-micro font-mono">{d.event_type}</Chip>
                    <Chip variant="neutral" className="text-micro">
                      {AUDIENCES.find((a) => a.value === d.audience)?.label || d.audience}
                    </Chip>
                    {template.is_master_template && (
                      <Chip variant="neutral" className="text-micro bg-wedo-purple/15 text-wedo-purple">
                        Master canonical
                      </Chip>
                    )}
                  </div>
                  <p className="text-xs text-lia-text-secondary">
                    Canais: {d.channels.join(", ")} · Delay: {d.delay_minutes}min
                    {d.schedule_lgpd_compliant && " · LGPD janela ✓"}
                  </p>
                </div>
                <div className="flex items-center gap-1">
                  {template.is_master_template && (
                    <Button variant="ghost" size="sm" onClick={() => handleCustomize(template)} title="Customizar">
                      <Copy className="w-3 h-3" />
                    </Button>
                  )}
                  {canEdit(template) && (
                    <Button variant="ghost" size="sm" onClick={() => startEdit(template)} title="Editar">
                      <Pencil className="w-3 h-3" />
                    </Button>
                  )}
                  {canDelete(template) && (
                    <Button variant="ghost" size="sm" onClick={() => handleDelete(template)} title="Excluir">
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
