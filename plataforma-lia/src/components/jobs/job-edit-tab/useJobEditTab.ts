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
  const { templates, isLoading: isLoadingTemplates, createTemplate } = usePipelineTemplates()
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

  // #5 Fase 1: herança de sub-status + campos de coleta da empresa, por NOME da etapa.
  // O editor da vaga exibe (read-only) o que cada etapa carrega da Jornada da empresa.
  // Etapa com override próprio (subStatuses/dataFields já no interviewStages) tem precedência.
  const inheritedByName = new Map<string, Pick<StageItem, "subStatuses" | "dataFields">>()
  const companyStagesForInherit = (((companyPipelineFallback as StageItem[] | null) ?? localFallback) as StageItem[])
  for (const cs of companyStagesForInherit) {
    const key = cs.name || cs.stageName
    if (key) inheritedByName.set(key, { subStatuses: cs.subStatuses, dataFields: cs.dataFields })
  }
  // override por vaga só conta quando vem do interviewStages persistido (rawStages),
  // não do fallback da empresa (que carrega subStatuses da própria empresa = herança).
  const hasRaw = rawStages.length > 0
  const enrichedStages: StageItem[] = stages.map((s) => {
    const inh = inheritedByName.get(s.name || s.stageName || "")
    const inheritedSub = inh?.subStatuses
    const inheritedData = inh?.dataFields
    const subOverridden = hasRaw && Array.isArray(s.subStatuses)
    return {
      ...s,
      // efetivo p/ display/consumo: override próprio senão herdado
      subStatuses: subOverridden ? s.subStatuses : inheritedSub,
      dataFields: (hasRaw && s.dataFields) ? s.dataFields : inheritedData,
      // transientes do editor (não persistem)
      _inheritedSubStatuses: inheritedSub,
      _subStatusesOverridden: subOverridden,
    }
  })

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
    if (newStatus === "Pausada" && currentScreening === "active") return "pause"
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
      (jobEditForm.status === "Pausada" || jobEditForm.status === "Paralisada") &&
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

  // Reordenação por arrastar (dnd-kit). Substitui moveStage(up/down).
  // Mantém os guards: não move etapa de sistema nem dropa numa posição de sistema.
  const reorderStages = (fromIndex: number, toIndex: number) => {
    if (fromIndex === toIndex) return
    const from = stages[fromIndex]
    const to = stages[toIndex]
    if (!from || !to) return
    if (from.stageCategory === "system" || from.isReorderable === false) return
    if (to.stageCategory === "system" || to.isReorderable === false) return
    const updated = [...stages]
    const [moved] = updated.splice(fromIndex, 1)
    updated.splice(toIndex, 0, moved)
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

  const [isSavingAsTemplate, setIsSavingAsTemplate] = useState(false)

  const saveStagesAsTemplate = async (templateName: string) => {
    const trimmed = templateName.trim()
    if (!trimmed || isSavingAsTemplate) return
    setIsSavingAsTemplate(true)
    try {
      const mappedStages = stages
        .filter(s => s.stageCategory !== "system")
        .map((s, idx) => ({
          name: (s as any).name || s.stageName,
          order: s.order || idx + 1,
          type: (["automatic", "manual", "hybrid"].includes(s.type)
            ? s.type
            : "manual") as "automatic" | "manual" | "hybrid",
          sla_days: s.slaDays ?? (s as any).sla_days ?? 3,
        }))
      await createTemplate({ name: trimmed, stages: mappedStages })
      toast.success("Template salvo com sucesso!")
    } catch {
      toast.error("Erro ao salvar template. Tente novamente.", { description: "Verifique sua conexão e tente novamente." })
    } finally {
      setIsSavingAsTemplate(false)
    }
  }

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
      toast.error("Erro ao aplicar template. Tente novamente.", { description: "Verifique sua conexão e tente novamente." })
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
    stages: enrichedStages,
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
    reorderStages,
    toggleStageActive,
    LIA_ASSISTED_STAGES,
    LIA_ASSISTED_STAGE_NAMES,
    // Fase 5: template selector
    vacancyId,
    saveStagesAsTemplate,
    isSavingAsTemplate,
    templates,
    isLoadingTemplates,
    isApplyingTemplate,
    applyTemplate,
  }
}
