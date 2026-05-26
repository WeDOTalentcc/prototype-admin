"use client"

import { useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import {
  Plus,
  Edit,
  Copy,
  Archive,
  Trash2,
  Save,
  X,
  GripVertical,
  Layers,
  Sparkles,
} from "lucide-react"
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core"
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { Chip } from "@/components/ui/chip"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

import { usePipelineTemplates, type PipelineTemplateFull, type PipelineStage } from "@/hooks/pipeline/use-pipeline-templates"

type StageType = "automatic" | "manual" | "hybrid"

interface EditorDraft {
  id: string | null
  name: string
  description: string
  is_default: boolean
  is_active: boolean
  is_archived: boolean
  department_hint: string[]
  seniority_hint: string[]
  job_family_hint: string[]
  stages: PipelineStage[]
}

const EMPTY_DRAFT: EditorDraft = {
  id: null,
  name: "",
  description: "",
  is_default: false,
  is_active: true,
  is_archived: false,
  department_hint: [],
  seniority_hint: [],
  job_family_hint: [],
  stages: [],
}

function parseCsv(input: string): string[] {
  return input
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)
}

function toCsv(arr: string[] | undefined | null): string {
  return (arr ?? []).join(", ")
}

function templateToDraft(tpl: PipelineTemplateFull): EditorDraft {
  return {
    id: tpl.id,
    name: tpl.name,
    description: tpl.description ?? "",
    is_default: tpl.is_default,
    is_active: tpl.is_active,
    is_archived: tpl.is_archived ?? false,
    department_hint: tpl.department_hint ?? [],
    seniority_hint: tpl.seniority_hint ?? [],
    job_family_hint: tpl.job_family_hint ?? [],
    stages: (tpl.stages ?? []).map((s, i) => ({
      name: s.name,
      order: s.order ?? i + 1,
      type: (s.type as StageType) ?? "manual",
      sla_days: s.sla_days ?? 0,
      instructions: s.instructions ?? "",
    })),
  }
}

interface SortableStageProps {
  stage: PipelineStage
  index: number
  onUpdate: (idx: number, patch: Partial<PipelineStage>) => void
  onRemove: (idx: number) => void
  tFields: (k: string) => string
  tStageType: (k: string) => string
  tActions: (k: string) => string
}

function SortableStage({ stage, index, onUpdate, onRemove, tFields, tStageType, tActions }: SortableStageProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: String(index),
  })
  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }
  return (
    <div
      ref={setNodeRef}
      style={style}
      className="flex items-start gap-3 p-3 border border-lia-border-subtle rounded-md bg-lia-bg-primary"
    >
      <button
        type="button"
        className="mt-2 cursor-grab text-lia-text-tertiary hover:text-lia-text-secondary"
        {...attributes}
        {...listeners}
        aria-label="Drag handle"
      >
        <GripVertical className="w-4 h-4" />
      </button>
      <div className="flex-1 grid grid-cols-1 md:grid-cols-12 gap-3">
        <div className="md:col-span-5">
          <Label className="text-xs">{tFields("stageName")}</Label>
          <Input
            value={stage.name}
            onChange={(e) => onUpdate(index, { name: e.target.value })}
            placeholder={tFields("stageNamePlaceholder")}
          />
        </div>
        <div className="md:col-span-3">
          <Label className="text-xs">{tFields("stageType")}</Label>
          <Select
            value={stage.type}
            onValueChange={(v) => onUpdate(index, { type: v as StageType })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="automatic">{tStageType("automatic")}</SelectItem>
              <SelectItem value="manual">{tStageType("manual")}</SelectItem>
              <SelectItem value="hybrid">{tStageType("hybrid")}</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="md:col-span-2">
          <Label className="text-xs">{tFields("slaDays")}</Label>
          <Input
            type="number"
            min={0}
            value={stage.sla_days}
            onChange={(e) => onUpdate(index, { sla_days: Number(e.target.value) || 0 })}
          />
        </div>
        <div className="md:col-span-2 flex items-end justify-end">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => onRemove(index)}
            className="text-status-error hover:bg-status-error/10"
            aria-label={tActions("removeStage")}
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
        <div className="md:col-span-12">
          <Label className="text-xs">{tFields("stageInstructions")}</Label>
          <Textarea
            value={stage.instructions ?? ""}
            onChange={(e) => onUpdate(index, { instructions: e.target.value })}
            rows={2}
            placeholder={tFields("stageInstructionsPlaceholder")}
          />
        </div>
      </div>
    </div>
  )
}

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

function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel,
  cancelLabel,
  destructive,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onCancel() }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>
            {cancelLabel}
          </Button>
          <Button
            variant={destructive ? "destructive" : "primary"}
            onClick={onConfirm}
          >
            {confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function PipelineTemplatesTab({ onSettingsChange }: { onSettingsChange?: (changed: boolean) => void }) {
  const t = useTranslations("settings.recruitment.pipelineTemplates")
  const tActions = useTranslations("settings.recruitment.pipelineTemplates.actions")
  const tFields = useTranslations("settings.recruitment.pipelineTemplates.fields")
  const tStates = useTranslations("settings.recruitment.pipelineTemplates.states")
  const tEmpty = useTranslations("settings.recruitment.pipelineTemplates.empty")
  const tStageType = useTranslations("settings.recruitment.pipelineTemplates.stageType")
  const tHints = useTranslations("settings.recruitment.pipelineTemplates.hints")

  const {
    templates,
    isLoading,
    error,
    createTemplate,
    updateTemplate,
    cloneTemplate,
    archiveTemplate,
    deleteTemplate,
    seedDefaults,
  } = usePipelineTemplates()

  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [draft, setDraft] = useState<EditorDraft>(EMPTY_DRAFT)
  const [isDirty, setIsDirty] = useState(false)
  const [confirmArchive, setConfirmArchive] = useState<string | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  )

  const selectedTemplate = useMemo(
    () => templates.find((t) => t.id === selectedId) ?? null,
    [templates, selectedId]
  )

  function markDirty() {
    setIsDirty(true)
    onSettingsChange?.(true)
  }

  function loadTemplateIntoEditor(tpl: PipelineTemplateFull | null) {
    if (!tpl) {
      setDraft(EMPTY_DRAFT)
    } else {
      setDraft(templateToDraft(tpl))
    }
    setIsDirty(false)
  }

  function handleSelect(id: string) {
    if (isDirty && !window.confirm(t("unsavedConfirm"))) return
    setSelectedId(id)
    const tpl = templates.find((x) => x.id === id) ?? null
    loadTemplateIntoEditor(tpl)
  }

  function handleNew() {
    if (isDirty && !window.confirm(t("unsavedConfirm"))) return
    setSelectedId(null)
    setDraft({ ...EMPTY_DRAFT, name: t("newTemplateDefaultName") })
    setIsDirty(true)
  }

  async function handleSeedDefaults() {
    try {
      setBusy(true)
      await seedDefaults()
    } finally {
      setBusy(false)
    }
  }

  async function handleSave() {
    if (!draft.name.trim() || draft.stages.length === 0) return
    try {
      setBusy(true)
      const payload = {
        name: draft.name.trim(),
        description: draft.description.trim() || null,
        is_default: draft.is_default,
        is_active: draft.is_active,
        department_hint: draft.department_hint,
        seniority_hint: draft.seniority_hint,
        job_family_hint: draft.job_family_hint,
        stages: draft.stages.map((s, i) => ({ ...s, order: i + 1 })),
      }
      if (draft.id) {
        const updated = await updateTemplate(draft.id, payload)
        if (updated) loadTemplateIntoEditor(updated)
      } else {
        const created = await createTemplate(payload)
        if (created) {
          setSelectedId(created.id)
          loadTemplateIntoEditor(created)
        }
      }
      setIsDirty(false)
      onSettingsChange?.(false)
    } finally {
      setBusy(false)
    }
  }

  async function handleClone(id: string) {
    try {
      setBusy(true)
      const cloned = await cloneTemplate(id)
      if (cloned) {
        setSelectedId(cloned.id)
        loadTemplateIntoEditor(cloned)
      }
    } finally {
      setBusy(false)
    }
  }

  async function handleArchive(id: string) {
    try {
      setBusy(true)
      await archiveTemplate(id)
      if (selectedId === id) {
        setSelectedId(null)
        loadTemplateIntoEditor(null)
      }
    } finally {
      setConfirmArchive(null)
      setBusy(false)
    }
  }

  async function handleDelete(id: string) {
    try {
      setBusy(true)
      await deleteTemplate(id)
      if (selectedId === id) {
        setSelectedId(null)
        loadTemplateIntoEditor(null)
      }
    } finally {
      setConfirmDelete(null)
      setBusy(false)
    }
  }

  function updateStage(idx: number, patch: Partial<PipelineStage>) {
    setDraft((d) => ({
      ...d,
      stages: d.stages.map((s, i) => (i === idx ? { ...s, ...patch } : s)),
    }))
    markDirty()
  }

  function addStage() {
    setDraft((d) => ({
      ...d,
      stages: [
        ...d.stages,
        {
          name: t("newStageDefaultName"),
          order: d.stages.length + 1,
          type: "manual",
          sla_days: 0,
          instructions: "",
        },
      ],
    }))
    markDirty()
  }

  function removeStage(idx: number) {
    setDraft((d) => ({
      ...d,
      stages: d.stages.filter((_, i) => i !== idx),
    }))
    markDirty()
  }

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event
    if (!over || active.id === over.id) return
    const from = Number(active.id)
    const to = Number(over.id)
    setDraft((d) => ({
      ...d,
      stages: arrayMove(d.stages, from, to).map((s, i) => ({ ...s, order: i + 1 })),
    }))
    markDirty()
  }

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-base font-semibold text-lia-text-primary">{t("title")}</h2>
          <p className="text-sm text-lia-text-secondary mt-1 max-w-2xl">{t("subtitle")}</p>
        </div>
        <Button onClick={handleNew} className="gap-2">
          <Plus className="w-4 h-4" />
          {t("newTemplate")}
        </Button>
      </div>

      {error && (
        <Card className="border-status-error/30 bg-status-error/5">
          <CardContent className="p-4 text-sm text-status-error">
            {t("loadError")}
          </CardContent>
        </Card>
      )}

      {!isLoading && templates.length === 0 && !error ? (
        <Card>
          <CardContent className="p-10 text-center space-y-4">
            <Layers className="w-12 h-12 mx-auto opacity-30" />
            <div>
              <h3 className="text-lg font-medium">{tEmpty("title")}</h3>
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
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* List */}
          <div className="lg:col-span-5 space-y-3">
            {isLoading && (
              <Card><CardContent className="p-4 text-sm text-lia-text-secondary">{t("loading")}</CardContent></Card>
            )}
            {templates.map((tpl) => {
              const isSelected = tpl.id === selectedId
              const hintBadges = [
                ...(tpl.department_hint ?? []),
                ...(tpl.seniority_hint ?? []),
                ...(tpl.job_family_hint ?? []),
              ].slice(0, 3)
              const stageCount = (tpl.stages ?? []).length
              const usage = tpl.usage_count ?? 0
              return (
                <Card
                  key={tpl.id}
                  className={cn(
                    "cursor-pointer transition-colors",
                    isSelected ? "border-lia-btn-primary-bg ring-1 ring-lia-btn-primary-bg" : "hover:border-lia-border-strong"
                  )}
                  onClick={() => handleSelect(tpl.id)}
                >
                  <CardContent className="p-4 space-y-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-lia-text-primary truncate">{tpl.name}</h3>
                        {tpl.description && (
                          <p className="text-sm text-lia-text-secondary line-clamp-2 mt-0.5">{tpl.description}</p>
                        )}
                      </div>
                      <Chip variant={tpl.is_archived ? "neutral" : "success"}>
                        {tpl.is_archived ? tStates("archived") : tStates("active")}
                      </Chip>
                    </div>

                    {hintBadges.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {hintBadges.map((h, i) => (
                          <Chip key={`${h}-${i}`} variant="neutral" className="text-xs">{h}</Chip>
                        ))}
                      </div>
                    )}

                    <div className="flex items-center justify-between text-xs text-lia-text-secondary">
                      <span>
                        {stageCount === 1 ? tHints("stagesCount_one", { count: stageCount }) : tHints("stagesCount_other", { count: stageCount })}
                        {" · "}
                        {usage === 1 ? tHints("usageCount_one", { count: usage }) : tHints("usageCount_other", { count: usage })}
                      </span>
                      <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleSelect(tpl.id)}
                          aria-label={tActions("edit")}
                          className="h-7 w-7 p-0"
                        >
                          <Edit className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={busy}
                          onClick={() => handleClone(tpl.id)}
                          aria-label={tActions("clone")}
                          className="h-7 w-7 p-0"
                        >
                          <Copy className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={busy || tpl.is_archived}
                          onClick={() => setConfirmArchive(tpl.id)}
                          aria-label={tActions("archive")}
                          className="h-7 w-7 p-0"
                        >
                          <Archive className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>

          {/* Editor */}
          <div className="lg:col-span-7">
            <Card>
              <CardContent className="p-5 space-y-5">
                {!draft.id && !isDirty ? (
                  <div className="text-center py-10 text-sm text-lia-text-secondary">
                    {t("selectOrCreate")}
                  </div>
                ) : (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="md:col-span-2">
                        <Label>{tFields("name")}</Label>
                        <Input
                          value={draft.name}
                          onChange={(e) => { setDraft((d) => ({ ...d, name: e.target.value })); markDirty() }}
                          placeholder={tFields("namePlaceholder")}
                        />
                      </div>
                      <div className="md:col-span-2">
                        <Label>{tFields("description")}</Label>
                        <Textarea
                          value={draft.description}
                          onChange={(e) => { setDraft((d) => ({ ...d, description: e.target.value })); markDirty() }}
                          rows={2}
                        />
                      </div>
                      <div className="flex items-center gap-3">
                        <Switch
                          checked={draft.is_default}
                          onCheckedChange={(v) => { setDraft((d) => ({ ...d, is_default: v })); markDirty() }}
                        />
                        <Label className="cursor-pointer">{tFields("isDefault")}</Label>
                      </div>
                      <div className="flex items-center gap-3">
                        <Switch
                          checked={draft.is_active}
                          onCheckedChange={(v) => { setDraft((d) => ({ ...d, is_active: v })); markDirty() }}
                        />
                        <Label className="cursor-pointer">{tFields("isActive")}</Label>
                      </div>

                      <div className="md:col-span-2">
                        <Label>{tFields("departmentHint")}</Label>
                        <Input
                          value={toCsv(draft.department_hint)}
                          onChange={(e) => { setDraft((d) => ({ ...d, department_hint: parseCsv(e.target.value) })); markDirty() }}
                          placeholder={tFields("departmentHintPlaceholder")}
                        />
                        <p className="text-xs text-lia-text-tertiary mt-1">{tFields("csvHelp")}</p>
                      </div>
                      <div>
                        <Label>{tFields("seniorityHint")}</Label>
                        <Input
                          value={toCsv(draft.seniority_hint)}
                          onChange={(e) => { setDraft((d) => ({ ...d, seniority_hint: parseCsv(e.target.value) })); markDirty() }}
                          placeholder={tFields("seniorityHintPlaceholder")}
                        />
                      </div>
                      <div>
                        <Label>{tFields("jobFamilyHint")}</Label>
                        <Input
                          value={toCsv(draft.job_family_hint)}
                          onChange={(e) => { setDraft((d) => ({ ...d, job_family_hint: parseCsv(e.target.value) })); markDirty() }}
                          placeholder={tFields("jobFamilyHintPlaceholder")}
                        />
                      </div>
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-sm font-semibold">{t("stagesHeading")}</h3>
                        <Button type="button" variant="outline" size="sm" onClick={addStage} className="gap-1.5">
                          <Plus className="w-3.5 h-3.5" />
                          {tActions("addStage")}
                        </Button>
                      </div>
                      {draft.stages.length === 0 ? (
                        <p className="text-sm text-lia-text-secondary py-6 text-center border border-dashed rounded-md">
                          {t("noStages")}
                        </p>
                      ) : (
                        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
                          <SortableContext
                            items={draft.stages.map((_, i) => String(i))}
                            strategy={verticalListSortingStrategy}
                          >
                            <div className="space-y-2">
                              {draft.stages.map((stage, idx) => (
                                <SortableStage
                                  key={`${idx}-${stage.name}`}
                                  stage={stage}
                                  index={idx}
                                  onUpdate={updateStage}
                                  onRemove={removeStage}
                                  tFields={tFields}
                                  tStageType={tStageType}
                                  tActions={tActions}
                                />
                              ))}
                            </div>
                          </SortableContext>
                        </DndContext>
                      )}
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-lia-border-subtle">
                      <div>
                        {selectedTemplate && !selectedTemplate.is_default && (
                          <Button
                            variant="ghost"
                            size="sm"
                            disabled={busy}
                            onClick={() => setConfirmDelete(selectedTemplate.id)}
                            className="text-status-error hover:bg-status-error/10 gap-1.5"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                            {tActions("delete")}
                          </Button>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          onClick={() => {
                            loadTemplateIntoEditor(selectedTemplate)
                            onSettingsChange?.(false)
                          }}
                          disabled={busy || !isDirty}
                          className="gap-1.5"
                        >
                          <X className="w-3.5 h-3.5" />
                          {tActions("cancel")}
                        </Button>
                        <Button
                          onClick={handleSave}
                          disabled={busy || !isDirty || !draft.name.trim() || draft.stages.length === 0}
                          className="gap-1.5"
                        >
                          <Save className="w-3.5 h-3.5" />
                          {tActions("save")}
                        </Button>
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

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
    </div>
  )
}
