"use client"

/**
 * EligibilityTemplatesManager — UI Settings dedicada para CRUD de templates
 * de elegibilidade per-tenant.
 *
 * Audit 2026-05-20 Sprint 1 F4 estendido:
 * - Lista master canonical + customs da company
 * - Admin: full CRUD (create/edit/delete) — decisao Paulo C
 * - Recrutador: create-novos OK; NAO pode delete; NAO pode editar de outros
 * - Customize master (cópia canonical A1 + snapshot B1)
 */

import React, { useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import {
  Library,
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { textStyles } from "@/lib/design-tokens"
import {
  useEligibilityTemplates,
  QUESTION_CATEGORIES,
  flattenTemplate,
  type EligibilityQuestionData,
  type QuestionCategory,
  type QuestionType,
  type EligibilityQuestionTemplate,
} from "@/hooks/screening/use-eligibility-templates"

interface EligibilityTemplatesManagerProps {
  /** Whether the current user is admin (decisão Paulo C: admin full CRUD, recruiter limitado) */
  isAdmin: boolean
  /** Current user id — para owner check (recrutador edita só os seus) */
  currentUserId: string | null
}

interface FormState {
  question: string
  type: QuestionType
  category: QuestionCategory
  contextHint: string
  options: string  // CSV
  eliminatory: boolean
  eliminatoryAnswer: string
}

const EMPTY_FORM: FormState = {
  question: "",
  type: "yes_no",
  category: "general",
  contextHint: "",
  options: "",
  eliminatory: false,
  eliminatoryAnswer: "",
}

export function EligibilityTemplatesManager({
  isAdmin,
  currentUserId,
}: EligibilityTemplatesManagerProps) {
  const t = useTranslations("settings.recruitment.screening")
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
  } = useEligibilityTemplates({ includeMaster: true })

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

  function startEdit(template: EligibilityQuestionTemplate) {
    const flat = flattenTemplate(template)
    setEditingId(template.id)
    setForm({
      question: flat.question || "",
      type: flat.type || "yes_no",
      category: flat.category || "general",
      contextHint: flat.contextHint || "",
      options: (flat.options || []).join(", "),
      eliminatory: flat.eliminatory ?? false,
      eliminatoryAnswer: flat.eliminatoryAnswer != null ? String(flat.eliminatoryAnswer) : "",
    })
    setFormError(null)
  }

  function cancelEdit() {
    setEditingId(null)
    setForm(EMPTY_FORM)
    setFormError(null)
  }

  function buildData(): EligibilityQuestionData {
    return {
      question: form.question.trim(),
      type: form.type,
      category: form.category,
      contextHint: form.contextHint.trim() || undefined,
      options: form.options.trim()
        ? form.options.split(",").map((s) => s.trim()).filter(Boolean)
        : undefined,
      eliminatory: form.eliminatory || undefined,
      eliminatoryAnswer: form.eliminatoryAnswer.trim() || undefined,
    }
  }

  async function handleSave() {
    if (!form.question.trim() || form.question.trim().length < 3) {
      setFormError("Pergunta deve ter pelo menos 3 caracteres")
      return
    }
    setIsSaving(true)
    setFormError(null)
    try {
      if (editingId === "__new__") {
        const created = await createCustom(buildData())
        if (created) {
          flashSuccess("Template criado com sucesso")
          cancelEdit()
        } else {
          setFormError(error || "Falha ao criar template")
        }
      } else if (editingId) {
        const updated = await updateTemplate(editingId, buildData())
        if (updated) {
          flashSuccess("Template atualizado")
          cancelEdit()
        } else {
          setFormError(error || "Falha ao atualizar template")
        }
      }
    } finally {
      setIsSaving(false)
    }
  }

  async function handleCustomize(template: EligibilityQuestionTemplate) {
    const ok = await customizeMaster(template.id)
    if (ok) {
      flashSuccess(`Master "${template.data.question.slice(0, 30)}..." customizado`)
    }
  }

  async function handleDelete(template: EligibilityQuestionTemplate) {
    if (!confirm(`Excluir template "${template.data.question.slice(0, 60)}..."?`)) return
    const ok = await deleteTemplate(template.id)
    if (ok) {
      flashSuccess("Template excluído")
    }
  }

  function canEdit(template: EligibilityQuestionTemplate): boolean {
    if (template.is_master_template) return false  // master immutable; deve customizar
    if (isAdmin) return true
    return template.created_by === currentUserId  // recrutador só os próprios
  }

  function canDelete(template: EligibilityQuestionTemplate): boolean {
    if (template.is_master_template) return false
    return isAdmin  // decisão C: apenas admin deleta
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
    <Card className="border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl">
      <CardHeader className="pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
            <Library className="w-4 h-4 text-wedo-cyan" />
            Gerenciador de Templates de Triagem
          </CardTitle>
          <div className="flex items-center gap-2">
            <Chip variant="neutral" className="text-micro">
              {masterCount} master · {customCount} custom · {total} total
            </Chip>
            <Button size="sm" onClick={startCreate} disabled={!!editingId}>
              <Plus className="w-3 h-3 mr-1" /> Novo template
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

        {/* Filter chips */}
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

        {/* Form (edit/create) */}
        {editingId && (
          <Card className="border border-wedo-cyan/30 bg-wedo-cyan/5 rounded-xl">
            <CardContent className="p-3 space-y-3">
              <div className="flex items-center justify-between">
                <h5 className={textStyles.h4}>
                  {editingId === "__new__" ? "Criar template novo" : "Editar template"}
                </h5>
                <Button variant="ghost" size="sm" onClick={cancelEdit}>
                  <X className="w-3 h-3" />
                </Button>
              </div>
              <Input
                placeholder="Pergunta (obrigatório, mín. 3 chars)"
                value={form.question}
                onChange={(e) => setForm({ ...form, question: e.target.value })}
              />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <Select value={form.type} onValueChange={(v) => setForm({ ...form, type: v as QuestionType })}>
                  <SelectTrigger><SelectValue placeholder="Tipo" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="yes_no">Sim/Não</SelectItem>
                    <SelectItem value="text">Texto livre</SelectItem>
                    <SelectItem value="scale">Escala</SelectItem>
                    <SelectItem value="multiple">Múltipla escolha</SelectItem>
                  </SelectContent>
                </Select>
                <Select
                  value={form.category}
                  onValueChange={(v) => setForm({ ...form, category: v as QuestionCategory })}
                >
                  <SelectTrigger><SelectValue placeholder="Categoria" /></SelectTrigger>
                  <SelectContent>
                    {(Object.keys(QUESTION_CATEGORIES) as QuestionCategory[]).map((cat) => (
                      <SelectItem key={cat} value={cat}>
                        {QUESTION_CATEGORIES[cat].icon} {QUESTION_CATEGORIES[cat].label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Input
                placeholder="Dica de contexto (opcional)"
                value={form.contextHint}
                onChange={(e) => setForm({ ...form, contextHint: e.target.value })}
              />
              {form.type === "multiple" && (
                <Input
                  placeholder="Opções separadas por vírgula"
                  value={form.options}
                  onChange={(e) => setForm({ ...form, options: e.target.value })}
                />
              )}
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-1 text-xs">
                  <input
                    type="checkbox"
                    checked={form.eliminatory}
                    onChange={(e) => setForm({ ...form, eliminatory: e.target.checked })}
                  />
                  Eliminatória
                </label>
                {form.eliminatory && (
                  <Input
                    className="w-40"
                    placeholder="Resposta esperada"
                    value={form.eliminatoryAnswer}
                    onChange={(e) => setForm({ ...form, eliminatoryAnswer: e.target.value })}
                  />
                )}
              </div>
              {formError && (
                <div className="text-xs text-status-error flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> {formError}
                </div>
              )}
              <div className="flex justify-end gap-2">
                <Button variant="outline" size="sm" onClick={cancelEdit}>
                  Cancelar
                </Button>
                <Button size="sm" onClick={handleSave} disabled={isSaving}>
                  {isSaving ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : null}
                  Salvar
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Templates list */}
        <div className="space-y-2 max-h-content-lg overflow-y-auto">
          {filteredTemplates.length === 0 && (
            <p className="text-xs text-lia-text-secondary text-center py-4">
              Nenhum template nessa categoria.
            </p>
          )}
          {filteredTemplates.map((template) => {
            const flat = flattenTemplate(template)
            const catInfo = QUESTION_CATEGORIES[flat.category]
            return (
              <div
                key={template.id}
                className="flex items-start justify-between gap-2 p-3 bg-lia-bg-secondary/50 rounded-xl border border-lia-border-subtle"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <Chip variant="neutral" className={`text-micro ${catInfo?.color || ""}`}>
                      {catInfo?.icon} {catInfo?.label || flat.category}
                    </Chip>
                    {template.is_master_template && (
                      <Chip variant="neutral" className="text-micro bg-wedo-purple/15 text-wedo-purple">
                        Master canonical
                      </Chip>
                    )}
                    {flat.eliminatory && (
                      <Chip variant="neutral" className="text-micro bg-status-error/10 text-status-error">
                        Eliminatória
                      </Chip>
                    )}
                  </div>
                  <p className="text-sm text-lia-text-primary">{flat.question}</p>
                  {flat.contextHint && (
                    <p className="text-xs text-lia-text-secondary mt-1">{flat.contextHint}</p>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  {template.is_master_template && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCustomize(template)}
                      title="Customizar (cria cópia para a empresa)"
                    >
                      <Copy className="w-3 h-3" />
                    </Button>
                  )}
                  {canEdit(template) && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => startEdit(template)}
                      title="Editar"
                    >
                      <Pencil className="w-3 h-3" />
                    </Button>
                  )}
                  {canDelete(template) && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(template)}
                      title="Excluir (admin only)"
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
