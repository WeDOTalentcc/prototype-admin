"use client"

import { useState, useRef } from "react"
import { useSearchParams } from "next/navigation"
import { toast } from "sonner"
import { getCompanyPipelineStages, LIA_ASSISTED_STAGES, LIA_ASSISTED_STAGE_NAMES } from "@/lib/recruitment-stages"
import { usePipelineTemplates } from "@/hooks/pipeline/use-pipeline-templates"
import { useCompanyPipeline } from "@/hooks/company/use-company-pipeline"
import { useScreeningConfig } from "@/hooks/recruitment/useScreeningConfig"
import { SECTIONS, SWITCH_FIELDS, countFilledFields } from "./job-edit-tab.constants"
import type { JobEditTabProps, StageItem, StatusChangeConfirm } from "./job-edit-tab.types"

export function useJobEditTab({
  jobEditForm,
  setJobEditForm,
  onSaveSection,
  job,
  onJobUpdate,
  isCreationMode,
}: Pick<
  JobEditTabProps,
  | "jobEditForm"
  | "setJobEditForm"
  | "onSaveSection"
  | "job"
  | "onJobUpdate"
  | "isCreationMode"
>) {
  // Phase A.4 — deep-link support: ?section=<id> from URL hydrates the
  // initial activeSection on mount. See .planning/vacancy-pipeline-plan.md.
  const _searchParams = useSearchParams()
  const _ALLOWED_SECTIONS = new Set([
    "info-geral", "pessoas", "processo", "remuneracao",
    "configuracoes", "descricao", "perguntas",
  ])
  const _initialSection = (() => {
    const requested = _searchParams?.get("section")
    return requested && _ALLOWED_SECTIONS.has(requested) ? requested : "info-geral"
  })()
  const [activeSection, setActiveSection] = useState(_initialSection)
  const [editingSection, setEditingSection] = useState<string | null>(
    isCreationMode ? "info-geral" : null
  )
  const formBackupRef = useRef<Record<string, unknown> | null>(null)

  const { pipeline: companyPipelineFallback, loading: loadingCompanyPipeline } =
    useCompanyPipeline()

  // Fase 5 Unify: template selector na seção Processo
  const vacancyId = String(job?.backendId || (job as any)?.jobId || job?.id || "")
  const { templates, isLoading: isLoadingTemplates } = usePipelineTemplates()
  const [isApplyingTemplate, setIsApplyingTemplate] = useState(false)

  const { config: screeningConfig } = useScreeningConfig(
    (job?.backendId || job?.jobId || null) as string | number | null
  )

  const [statusChangeConfirm, setStatusChangeConfirm] =
    useState<StatusChangeConfirm | null>(null)

  // ── derived ────────────────────────────────────────────────────────────────
  const currentSection = SECTIONS.find((s) => s.id === activeSection) || SECTIONS[0]
  const isEditing = isCreationMode || editingSection === activeSection
  const filled = countFilledFields(jobEditForm, currentSection.fields)
  const total = currentSection.fields.length

  const screeningCompletion: Record<string, boolean> = {
    configuracoes:
      !!(
        screeningConfig &&
        ((screeningConfig as any).channels ||
          (screeningConfig as any).settings ||
          (screeningConfig as any).scheduling)
      ) ||
      !!(
        job?.screeningConfig &&
        ((job.screeningConfig as any)?.channels ||
          (job.screeningConfig as any)?.settings ||
          (job.screeningConfig as any)?.scheduling)
      ),
    descricao: !!(job?.description && (job.description as string).trim().length > 0),
    perguntas: !!(
      job?.screeningQuestions &&
      (job.screeningQuestions as unknown[]).length > 0
    ),
  }

  const localFallback = getCompanyPipelineStages()
    .filter((s) => s.isActive)
    .map((s, i) => ({
      stageName: s.displayName,
      order: i + 1,
      type: "interview" as const,
      name: s.name,
      stageCategory: s.stageCategory,
      isEditable: s.isEditable,
      isRemovable: s.isRemovable,
      isReorderable: s.isReorderable,
      slaDays: s.defaultSlaDays,
      defaultSlaDays: s.defaultSlaDays,
      liaAssisted: s.liaAssisted,
    }))

  const rawStages = (jobEditForm.interviewStages || []) as StageItem[]
  const stages: StageItem[] =
    rawStages.length > 0
      ? rawStages
      : (companyPipelineFallback as StageItem[] | null) ?? localFallback

  // ── helpers ────────────────────────────────────────────────────────────────
  const updateField = (field: string, value: unknown) => {
    setJobEditForm((prev) => ({ ...prev, [field]: value }))
  }

  const jobSectionCompletion = (sectionFields: string[]): boolean => {
    const f = countFilledFields(jobEditForm, sectionFields)
    return f >= Math.ceil(sectionFields.length * 0.3)
  }

  // ── status helpers ─────────────────────────────────────────────────────────
  const getScreeningImpact = (
    newStatus: string
  ): "pause" | "complete" | "ask_reactivate" | "none" => {
    const currentScreening =
      job?.screeningStatus || jobEditForm.screeningStatus || "not_configured"
    if (newStatus === "Paralisada" && currentScreening === "active") return "pause"
    if (newStatus === "Concluída" || newStatus === "Cancelada") {
      if (
        currentScreening === "active" ||
        currentScreening === "paused" ||
        currentScreening === "not_started"
      )
        return "complete"
    }
    if (
      newStatus === "Ativa" &&
      jobEditForm.status === "Paralisada" &&
      currentScreening === "paused"
    )
      return "ask_reactivate"
    return "none"
  }

  const handleStatusChangeWithScreening = (
    newStatus: string,
    reactivateScreening?: boolean
  ) => {
    const impact =
      statusChangeConfirm?.screeningImpact || getScreeningImpact(newStatus)
    updateField("status", newStatus)

    if (impact === "pause") {
      onJobUpdate?.({ ...job, status: newStatus, screeningStatus: "paused" })
      toast.success("Status alterado. Triagem pausada automaticamente.")
    } else if (impact === "complete") {
      onJobUpdate?.({ ...job, status: newStatus, screeningStatus: "completed" })
      toast.success("Status alterado. Triagem finalizada automaticamente.")
    } else if (impact === "ask_reactivate" && reactivateScreening) {
      onJobUpdate?.({ ...job, status: newStatus, screeningStatus: "active" })
      toast.success("Vaga reativada. Triagem reativada automaticamente.")
    } else {
      onJobUpdate?.({ ...job, status: newStatus })
      toast.success("Status da vaga alterado.")
    }
    setStatusChangeConfirm(null)
  }

  // ── section edit handlers ──────────────────────────────────────────────────
  const handleStartEditing = () => {
    formBackupRef.current = { ...jobEditForm }
    setEditingSection(activeSection)
  }

  const handleCancel = () => {
    if (formBackupRef.current) {
      setJobEditForm(formBackupRef.current)
    }
    setEditingSection(null)
    formBackupRef.current = null
  }

  const handleSave = async () => {
    await onSaveSection(currentSection.id, currentSection.fields)
    setEditingSection(null)
    formBackupRef.current = null
  }

  // ── stage handlers ─────────────────────────────────────────────────────────
  const addStage = () => {
    const newOrder =
      stages.length > 0 ? Math.max(...stages.map((s) => s.order)) + 1 : 1
    const offerIndex = stages.findIndex(
      (s) => s.name === "offer" || s.stageName === "Proposta"
    )
    const newStage: StageItem = {
      stageName: "",
      order: newOrder,
      type: "interview",
      stageCategory: "custom",
      name: `custom_${Date.now()}`,
      isEditable: true,
      isRemovable: true,
      isReorderable: true,
    }
    if (offerIndex !== -1) {
      const updated = [...stages]
      updated.splice(offerIndex, 0, newStage)
      updateField(
        "interviewStages",
        updated.map((s, i) => ({ ...s, order: i + 1 }))
      )
    } else {
      updateField("interviewStages", [...stages, newStage])
    }
  }

  const removeStage = (index: number) => {
    const stage = stages[index]
    if (stage.stageCategory === "system" || stage.isRemovable === false) return
    const updated = stages
      .filter((_, i) => i !== index)
      .map((s, i) => ({ ...s, order: i + 1 }))
    updateField("interviewStages", updated)
  }

  const updateStage = (index: number, field: string, value: unknown) => {
    const stage = stages[index]
    if (stage.stageCategory === "system" && field === "stageName") return
    const updated = stages.map((s, i) =>
      i === index ? { ...s, [field]: value } : s
    )
    updateField("interviewStages", updated)
  }

  const moveStage = (index: number, direction: "up" | "down") => {
    if (direction === "up" && index === 0) return
    if (direction === "down" && index === stages.length - 1) return
    const stage = stages[index]
    if (stage.stageCategory === "system" || stage.isReorderable === false) return
    const newIndex = direction === "up" ? index - 1 : index + 1
    const targetStage = stages[newIndex]
    if (
      targetStage.stageCategory === "system" ||
      targetStage.isReorderable === false
    )
      return
    const updated = [...stages]
    const temp = updated[index]
    updated[index] = updated[newIndex]
    updated[newIndex] = temp
    updateField(
      "interviewStages",
      updated.map((s, i) => ({ ...s, order: i + 1 }))
    )
  }

  const toggleStageActive = (index: number) => {
    const stage = stages[index]
    if (stage.stageCategory === "system") return
    const updated = stages.map((s, i) =>
      i === index ? { ...s, isActive: !s.isActive } : s
    )
    updateField("interviewStages", updated)
  }

  // ── language helpers (inline in JSX, but expose updateField) ───────────────
  // (addLanguage / removeLanguage / updateLanguage remain inline in the JSX
  //  because they depend on the local `langs` derived from jobEditForm)

  const applyTemplate = async (templateId: string) => {
    if (!vacancyId) return
    setIsApplyingTemplate(true)
    try {
      await fetch(`/api/backend-proxy/job-vacancies/${vacancyId}/apply-pipeline-template`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ template_id: templateId, source: "manual_modal" }),
      })
      toast.success("Template de pipeline aplicado com sucesso!")
      onJobUpdate?.({ is_pipeline_customized: false })
    } catch {
      toast.error("Erro ao aplicar template. Tente novamente.")
    } finally {
      setIsApplyingTemplate(false)
    }
  }

  return {
    // state
    activeSection,
    setActiveSection,
    editingSection,
    statusChangeConfirm,
    setStatusChangeConfirm,
    // derived
    currentSection,
    isEditing,
    filled,
    total,
    stages,
    rawStages,
    loadingCompanyPipeline,
    screeningCompletion,
    // helpers
    updateField,
    jobSectionCompletion,
    getScreeningImpact,
    handleStatusChangeWithScreening,
    handleStartEditing,
    handleCancel,
    handleSave,
    addStage,
    removeStage,
    updateStage,
    moveStage,
    toggleStageActive,
    LIA_ASSISTED_STAGES,
    LIA_ASSISTED_STAGE_NAMES,
    // Fase 5: template selector
    vacancyId,
    templates,
    isLoadingTemplates,
    isApplyingTemplate,
    applyTemplate,
  }
}
