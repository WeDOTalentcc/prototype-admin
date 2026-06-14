"use client"

import React, { useState } from "react"
import { Brain, ClipboardList, X, Loader2, AlertCircle } from "lucide-react"
import { liaApi } from "@/services/lia-api"
import { usePipelineTemplates } from "@/hooks/pipeline/use-pipeline-templates"
import { toast } from "sonner"

interface CreateJobModalProps {
  isOpen: boolean
  onClose: () => void
  onCreateWithWizard: () => void
  onJobCreated?: (jobId: string, jobTitle: string) => void
}

type ModalStep = "choose" | "manual-form" | "choose-pipeline"

interface ManualFormData {
  title: string
  department: string
  workModel: string
  employmentType: string
  manager: string
  managerEmail: string
}

interface FormErrors {
  title?: string
  manager?: string
  managerEmail?: string
}

const WORK_MODEL_OPTIONS = [
  { value: "remoto", label: "Remoto" },
  { value: "hibrido", label: "Híbrido" },
  { value: "presencial", label: "Presencial" },
]

const EMPLOYMENT_TYPE_OPTIONS = [
  "CLT",
  "PJ",
  "Estágio",
  "Temporário",
  "Freelancer",
]

const DEPARTMENT_OPTIONS = [
  "Tecnologia",
  "Produto",
  "Design",
  "Marketing",
  "Vendas",
  "Financeiro",
  "RH",
  "Operações",
  "Jurídico",
  "Administrativo",
  "Engenharia",
  "Dados",
  "Suporte",
  "Outro",
]

function validateEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

export function CreateJobModal({ isOpen, onClose, onCreateWithWizard, onJobCreated }: CreateJobModalProps) {
  const [step, setStep] = useState<ModalStep>("choose")
  const [formData, setFormData] = useState<ManualFormData>({
    title: "",
    department: "",
    workModel: "",
    employmentType: "",
    manager: "",
    managerEmail: "",
  })
  const [errors, setErrors] = useState<FormErrors>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [createdJobId, setCreatedJobId] = useState<string | null>(null)
  const [isApplyingTemplate, setIsApplyingTemplate] = useState(false)

  const { templates, isLoading: isLoadingTemplates } = usePipelineTemplates()

  const resetModal = () => {
    setStep("choose")
    setFormData({ title: "", department: "", workModel: "", employmentType: "", manager: "", managerEmail: "" })
    setErrors({})
    setIsSubmitting(false)
  }

  const handleClose = () => {
    resetModal()
    onClose()
  }

  const handleChooseWizard = () => {
    handleClose()
    onCreateWithWizard()
  }

  const handleChooseManual = () => {
    setStep("manual-form")
  }

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}
    if (!formData.title.trim()) {
      newErrors.title = "Título é obrigatório"
    }
    if (!formData.manager.trim()) {
      newErrors.manager = "Nome do gestor é obrigatório"
    }
    if (!formData.managerEmail.trim()) {
      newErrors.managerEmail = "Email do gestor é obrigatório"
    } else if (!validateEmail(formData.managerEmail)) {
      newErrors.managerEmail = "Email inválido"
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async () => {
    if (!validateForm()) return

    setIsSubmitting(true)
    try {
      const response = await liaApi.createJobVacancy({
        title: formData.title.trim(),
        department: formData.department || undefined,
        work_model: formData.workModel || undefined,
        employment_type: formData.employmentType || undefined,
        manager: formData.manager.trim(),
        manager_email: formData.managerEmail.trim(),
        status: "Rascunho",
      })

      const jobId = response.id
      setCreatedJobId(jobId)
      setStep("choose-pipeline")
      toast.success("Vaga criada! Escolha o pipeline de seleção.")
    } catch (error: unknown) {
      const detail = error instanceof Error ? error.message : "Erro desconhecido"
      toast.error(`Erro ao criar vaga: ${detail}`)
    } finally {
      setIsSubmitting(false)
    }
  }

  const updateField = (field: keyof ManualFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    if (errors[field as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [field]: undefined }))
    }
  }

  const handleApplyTemplate = async (templateId: string) => {
    if (!createdJobId) return
    setIsApplyingTemplate(true)
    try {
      await fetch(`/api/backend-proxy/job-vacancies/${createdJobId}/apply-pipeline-template`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ template_id: templateId, source: "manual_modal" }),
      })
      toast.success("Pipeline aplicado com sucesso!")
    } catch {
      toast.error("Não foi possível aplicar o template. Configure o pipeline depois nas Configurações da vaga.")
    } finally {
      setIsApplyingTemplate(false)
      const jobTitle = formData.title.trim()
      handleClose()
      onJobCreated?.(createdJobId, jobTitle)
    }
  }

  const handleSkipPipeline = () => {
    if (!createdJobId) return
    const jobTitle = formData.title.trim()
    handleClose()
    onJobCreated?.(createdJobId, jobTitle)
  }

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 bg-lia-btn-primary-bg/50/70 z-50 flex items-center justify-center"
      onClick={handleClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-job-modal-title"
    >
      <div
        className="bg-lia-bg-primary rounded-xl shadow-lia-lg w-full max-w-md mx-4 animate-in fade-in zoom-in-95 duration-200"
        onClick={e => e.stopPropagation()}
      >
        <div className="px-6 pt-5 pb-3 flex items-center justify-between">
          <h2
            id="create-job-modal-title"
            className="text-base font-semibold text-lia-text-primary"
          >
            {step === "choose" ? "Nova Vaga" : step === "manual-form" ? "Criar Vaga Manualmente" : "Pipeline de Seleção"}
          </h2>
          <button
            onClick={handleClose}
            className="p-1 rounded-md text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-bg transition-colors motion-reduce:transition-none"
            aria-label="Fechar"
            data-dismiss="true"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="px-6 py-4">
          {step === "choose" && (
            <div className="space-y-3">
              <p className="text-xs text-lia-text-secondary mb-4" aria-live="polite" aria-atomic="true">
                Como você deseja criar a vaga?
              </p>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={handleChooseWizard}
                  className="bg-lia-bg-primary border border-lia-border-subtle rounded-xl p-4 text-left transition-[border-color,box-shadow,transform] motion-reduce:transition-none duration-150 hover:shadow-lia-default hover:-translate-y-0.5 hover:border-lia-border-medium cursor-pointer group"
                >
                  <div className="w-10 h-10 rounded-lg bg-wedo-cyan/10 flex items-center justify-center mb-3">
                    <Brain className="w-5 h-5 text-wedo-cyan" />
                  </div>
                  <h3 className="text-sm font-semibold text-lia-text-primary mb-1">
                    Criar em conversa
                  </h3>
                  <p className="text-xs text-lia-text-secondary">
                    Crie a vaga conversando, passo a passo
                  </p>
                </button>

                <button
                  onClick={handleChooseManual}
                  className="bg-lia-bg-primary border border-lia-border-subtle rounded-xl p-4 text-left transition-[border-color,box-shadow,transform] motion-reduce:transition-none duration-150 hover:shadow-lia-default hover:-translate-y-0.5 hover:border-lia-border-medium cursor-pointer group"
                >
                  <div className="w-10 h-10 rounded-lg bg-lia-bg-tertiary flex items-center justify-center mb-3">
                    <ClipboardList className="w-5 h-5 text-lia-text-secondary" />
                  </div>
                  <h3 className="text-sm font-semibold text-lia-text-primary mb-1">
                    Criar manualmente
                  </h3>
                  <p className="text-xs text-lia-text-secondary">
                    Preencha os dados diretamente
                  </p>
                </button>
              </div>
            </div>
          )}

          {step === "manual-form" && (
            <div className="space-y-4">
              <div className="space-y-1.5">
                <label
                  htmlFor="job-title"
                  className="text-xs font-semibold text-lia-text-primary block"
                >
                  Título da Vaga <span className="text-status-error">*</span>
                </label>
                <input
                  id="job-title"
                  type="text"
                  value={formData.title}
                  onChange={e => updateField("title", e.target.value)}
                  placeholder="Ex: Engenheiro de Software Senior"
                  className={`w-full px-3 py-2 text-sm text-lia-text-primary placeholder:text-lia-text-disabled bg-lia-bg-primary border rounded-md transition-colors motion-reduce:transition-none duration-150 focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 ${
                    errors.title
                      ? "border-status-error/30 focus:ring-red-500/20 bg-status-error/10 dark:bg-status-error/10"
                      : "border-lia-border-default hover:border-lia-border-medium focus:border-lia-btn-primary-bg"
                  }`}
                  aria-required="true"
                />
                {errors.title && (
                  <p className="text-xs text-status-error dark:text-status-error flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    {errors.title}
                  </p>
                )}
              </div>

              <div className="space-y-1.5">
                <label
                  htmlFor="job-department"
                  className="text-xs font-semibold text-lia-text-primary block"
                >
                  Departamento
                </label>
                <select
                  id="job-department"
                  value={formData.department}
                  onChange={e => updateField("department", e.target.value)}
                  className="w-full px-3 py-2 text-sm text-lia-text-primary bg-lia-bg-primary border border-lia-border-default rounded-xl transition-colors motion-reduce:transition-none duration-150 hover:border-lia-border-medium focus:border-lia-btn-primary-bg focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 cursor-pointer"
                >
                  <option value="">Selecione...</option>
                  {DEPARTMENT_OPTIONS.map(dept => (
                    <option key={dept} value={dept}>{dept}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label
                    htmlFor="job-work-model"
                    className="text-xs font-semibold text-lia-text-primary block"
                  >
                    Modelo de Trabalho
                  </label>
                  <select
                    id="job-work-model"
                    value={formData.workModel}
                    onChange={e => updateField("workModel", e.target.value)}
                    className="w-full px-3 py-2 text-sm text-lia-text-primary bg-lia-bg-primary border border-lia-border-default rounded-xl transition-colors motion-reduce:transition-none duration-150 hover:border-lia-border-medium focus:border-lia-btn-primary-bg focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 cursor-pointer"
                  >
                    <option value="">Selecione...</option>
                    {WORK_MODEL_OPTIONS.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label
                    htmlFor="job-employment-type"
                    className="text-xs font-semibold text-lia-text-primary block"
                  >
                    Forma de Contratação
                  </label>
                  <select
                    id="job-employment-type"
                    value={formData.employmentType}
                    onChange={e => updateField("employmentType", e.target.value)}
                    className="w-full px-3 py-2 text-sm text-lia-text-primary bg-lia-bg-primary border border-lia-border-default rounded-xl transition-colors motion-reduce:transition-none duration-150 hover:border-lia-border-medium focus:border-lia-btn-primary-bg focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 cursor-pointer"
                  >
                    <option value="">Selecione...</option>
                    {EMPLOYMENT_TYPE_OPTIONS.map(opt => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <label
                  htmlFor="job-manager"
                  className="text-xs font-semibold text-lia-text-primary block"
                >
                  Gestor Responsável <span className="text-status-error">*</span>
                </label>
                <input
                  id="job-manager"
                  type="text"
                  value={formData.manager}
                  onChange={e => updateField("manager", e.target.value)}
                  placeholder="Nome do gestor"
                  className={`w-full px-3 py-2 text-sm text-lia-text-primary placeholder:text-lia-text-disabled bg-lia-bg-primary border rounded-md transition-colors motion-reduce:transition-none duration-150 focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 ${
                    errors.manager
                      ? "border-status-error/30 focus:ring-red-500/20 bg-status-error/10 dark:bg-status-error/10"
                      : "border-lia-border-default hover:border-lia-border-medium focus:border-lia-btn-primary-bg"
                  }`}
                  aria-required="true"
                />
                {errors.manager && (
                  <p className="text-xs text-status-error dark:text-status-error flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    {errors.manager}
                  </p>
                )}
              </div>

              <div className="space-y-1.5">
                <label
                  htmlFor="job-manager-email"
                  className="text-xs font-semibold text-lia-text-primary block"
                >
                  Email do Gestor <span className="text-status-error">*</span>
                </label>
                <input
                  id="job-manager-email"
                  type="email"
                  value={formData.managerEmail}
                  onChange={e => updateField("managerEmail", e.target.value)}
                  placeholder="gestor@empresa.com"
                  className={`w-full px-3 py-2 text-sm text-lia-text-primary placeholder:text-lia-text-disabled bg-lia-bg-primary border rounded-md transition-colors motion-reduce:transition-none duration-150 focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 ${
                    errors.managerEmail
                      ? "border-status-error/30 focus:ring-red-500/20 bg-status-error/10 dark:bg-status-error/10"
                      : "border-lia-border-default hover:border-lia-border-medium focus:border-lia-btn-primary-bg"
                  }`}
                  aria-required="true"
                />
                {errors.managerEmail && (
                  <p className="text-xs text-status-error dark:text-status-error flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    {errors.managerEmail}
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {step === "choose-pipeline" && (
          <div className="space-y-3" role="region" aria-label="Seleção de pipeline">
            <p className="text-xs text-lia-text-secondary">
              Escolha um template de pipeline para esta vaga ou use o pipeline padrão da empresa.
            </p>
            {isLoadingTemplates ? (
              <div className="flex justify-center py-8">
                <Loader2 className="w-4 h-4 animate-spin text-lia-text-tertiary" aria-label="Carregando templates" />
              </div>
            ) : templates.length === 0 ? (
              <p className="text-xs text-lia-text-tertiary text-center py-6">
                Nenhum template disponível. Você pode criar templates em Configurações → Pipeline.
              </p>
            ) : (
              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {templates.map(template => (
                  <button
                    key={template.id}
                    onClick={() => handleApplyTemplate(template.id)}
                    disabled={isApplyingTemplate}
                    className="w-full text-left p-3 rounded-lg border border-lia-border-subtle hover:border-lia-btn-primary-bg hover:bg-lia-btn-primary-bg/5 transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20"
                    aria-label={`Aplicar template ${template.name}`}
                  >
                    <div className="text-sm font-medium text-lia-text-primary">{template.name}</div>
                    {template.description && (
                      <div className="text-xs text-lia-text-secondary mt-0.5 line-clamp-1">{template.description}</div>
                    )}
                    <div className="text-xs text-lia-text-tertiary mt-1">
                      {template.stages.length} etapa{template.stages.length !== 1 ? "s" : ""}
                      {template.department_hint && template.department_hint.length > 0 && (
                        <span className="ml-2 text-wedo-cyan-text">· {template.department_hint[0]}</span>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {step === "manual-form" && (
          <div className="px-6 py-4 bg-lia-bg-secondary/50 rounded-b-xl flex items-center justify-between">
            <button
              onClick={() => {
                setStep("choose")
                setErrors({})
              }}
              className="text-xs text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse font-medium transition-colors motion-reduce:transition-none"
            >
              Voltar
            </button>
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium rounded-xl bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover active:bg-lia-btn-primary-bg dark:hover:bg-lia-interactive-active transition-colors motion-reduce:transition-none duration-150 focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 disabled:bg-lia-border-default disabled:text-lia-text-tertiary disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                  Criando...
                </>
              ) : (
                "Criar e Configurar"
              )}
            </button>
          </div>
        )}
      </div>

        {step === "choose-pipeline" && (
          <div className="px-6 py-4 bg-lia-bg-secondary/50 rounded-b-xl flex items-center justify-between gap-3">
            <button
              onClick={handleSkipPipeline}
              disabled={isApplyingTemplate}
              className="text-xs text-lia-text-secondary hover:text-lia-text-primary font-medium transition-colors disabled:opacity-50"
            >
              Usar pipeline padrão
            </button>
            {isApplyingTemplate && (
              <div className="flex items-center gap-1.5 text-xs text-lia-text-secondary">
                <Loader2 className="w-3 h-3 animate-spin" />
                Aplicando...
              </div>
            )}
          </div>
        )}
    </div>
  )
}
