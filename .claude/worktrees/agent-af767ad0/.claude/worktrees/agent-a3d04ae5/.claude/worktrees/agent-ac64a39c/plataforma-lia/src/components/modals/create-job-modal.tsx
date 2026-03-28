"use client"

import React, { useState } from "react"
import { Brain, ClipboardList, X, Loader2, AlertCircle } from "lucide-react"
import { liaApi } from "@/services/lia-api"
import { toast } from "sonner"

interface CreateJobModalProps {
  isOpen: boolean
  onClose: () => void
  onCreateWithWizard: () => void
  onJobCreated?: (jobId: string, jobTitle: string) => void
}

type ModalStep = "choose" | "manual-form"

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

      toast.success("Vaga criada com sucesso!")

      const jobId = response.id
      const jobTitle = formData.title.trim()
      handleClose()
      onJobCreated?.(jobId, jobTitle)
    } catch (error: any) {
      console.error("[CreateJobModal] Failed to create job:", error)
      const detail = error?.message || "Erro desconhecido"
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

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 bg-gray-900/50 dark:bg-gray-950/70 z-50 flex items-center justify-center"
      onClick={handleClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-job-modal-title"
    >
      <div
        className="bg-white dark:bg-gray-800 rounded-md shadow-xl w-full max-w-md mx-4 animate-in fade-in zoom-in-95 duration-200"
        onClick={e => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2
            id="create-job-modal-title"
            className="text-base font-semibold text-gray-900 dark:text-gray-100 font-['Open_Sans',sans-serif]"
          >
            {step === "choose" ? "Nova Vaga" : "Criar Vaga Manualmente"}
          </h2>
          <button
            onClick={handleClose}
            className="p-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:text-gray-300 dark:hover:bg-gray-700 transition-colors"
            aria-label="Fechar"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="px-6 py-4">
          {step === "choose" && (
            <div className="space-y-3">
              <p className="text-xs text-gray-600 dark:text-gray-400 font-['Open_Sans',sans-serif] mb-4">
                Como você deseja criar a vaga?
              </p>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={handleChooseWizard}
                  className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md p-4 text-left transition-all duration-150 hover:shadow-md hover:-translate-y-0.5 cursor-pointer group"
                >
                  <div className="w-10 h-10 rounded-md bg-[#60BED1]/10 flex items-center justify-center mb-3">
                    <Brain className="w-5 h-5 text-[#60BED1]" />
                  </div>
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 font-['Open_Sans',sans-serif] mb-1">
                    Criar com a LIA
                  </h3>
                  <p className="text-xs text-gray-600 dark:text-gray-400 font-['Open_Sans',sans-serif]">
                    A LIA guia você no processo
                  </p>
                </button>

                <button
                  onClick={handleChooseManual}
                  className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md p-4 text-left transition-all duration-150 hover:shadow-md hover:-translate-y-0.5 cursor-pointer group"
                >
                  <div className="w-10 h-10 rounded-md bg-gray-100 dark:bg-gray-700 flex items-center justify-center mb-3">
                    <ClipboardList className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  </div>
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 font-['Open_Sans',sans-serif] mb-1">
                    Criar manualmente
                  </h3>
                  <p className="text-xs text-gray-600 dark:text-gray-400 font-['Open_Sans',sans-serif]">
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
                  className="text-[11px] font-semibold text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block"
                >
                  Título da Vaga <span className="text-red-500">*</span>
                </label>
                <input
                  id="job-title"
                  type="text"
                  value={formData.title}
                  onChange={e => updateField("title", e.target.value)}
                  placeholder="Ex: Engenheiro de Software Senior"
                  className={`w-full px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder:text-gray-400 bg-white dark:bg-gray-800 border rounded-md transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 font-['Open_Sans',sans-serif] ${
                    errors.title
                      ? "border-red-500 focus:ring-red-500/20 bg-red-50 dark:bg-red-900/10"
                      : "border-gray-300 dark:border-gray-600 hover:border-gray-400 focus:border-gray-900 dark:focus:border-gray-50"
                  }`}
                  aria-required="true"
                />
                {errors.title && (
                  <p className="text-xs text-red-600 dark:text-red-400 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    {errors.title}
                  </p>
                )}
              </div>

              <div className="space-y-1.5">
                <label
                  htmlFor="job-department"
                  className="text-[11px] font-semibold text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block"
                >
                  Departamento
                </label>
                <select
                  id="job-department"
                  value={formData.department}
                  onChange={e => updateField("department", e.target.value)}
                  className="w-full px-3 py-2 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md transition-all duration-150 hover:border-gray-400 focus:border-gray-900 dark:focus:border-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 cursor-pointer font-['Open_Sans',sans-serif]"
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
                    className="text-[11px] font-semibold text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block"
                  >
                    Modelo de Trabalho
                  </label>
                  <select
                    id="job-work-model"
                    value={formData.workModel}
                    onChange={e => updateField("workModel", e.target.value)}
                    className="w-full px-3 py-2 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md transition-all duration-150 hover:border-gray-400 focus:border-gray-900 dark:focus:border-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 cursor-pointer font-['Open_Sans',sans-serif]"
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
                    className="text-[11px] font-semibold text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block"
                  >
                    Forma de Contratação
                  </label>
                  <select
                    id="job-employment-type"
                    value={formData.employmentType}
                    onChange={e => updateField("employmentType", e.target.value)}
                    className="w-full px-3 py-2 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md transition-all duration-150 hover:border-gray-400 focus:border-gray-900 dark:focus:border-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 cursor-pointer font-['Open_Sans',sans-serif]"
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
                  className="text-[11px] font-semibold text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block"
                >
                  Gestor Responsável <span className="text-red-500">*</span>
                </label>
                <input
                  id="job-manager"
                  type="text"
                  value={formData.manager}
                  onChange={e => updateField("manager", e.target.value)}
                  placeholder="Nome do gestor"
                  className={`w-full px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder:text-gray-400 bg-white dark:bg-gray-800 border rounded-md transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 font-['Open_Sans',sans-serif] ${
                    errors.manager
                      ? "border-red-500 focus:ring-red-500/20 bg-red-50 dark:bg-red-900/10"
                      : "border-gray-300 dark:border-gray-600 hover:border-gray-400 focus:border-gray-900 dark:focus:border-gray-50"
                  }`}
                  aria-required="true"
                />
                {errors.manager && (
                  <p className="text-xs text-red-600 dark:text-red-400 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    {errors.manager}
                  </p>
                )}
              </div>

              <div className="space-y-1.5">
                <label
                  htmlFor="job-manager-email"
                  className="text-[11px] font-semibold text-gray-800 dark:text-gray-200 font-['Open_Sans',sans-serif] block"
                >
                  Email do Gestor <span className="text-red-500">*</span>
                </label>
                <input
                  id="job-manager-email"
                  type="email"
                  value={formData.managerEmail}
                  onChange={e => updateField("managerEmail", e.target.value)}
                  placeholder="gestor@empresa.com"
                  className={`w-full px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder:text-gray-400 bg-white dark:bg-gray-800 border rounded-md transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 font-['Open_Sans',sans-serif] ${
                    errors.managerEmail
                      ? "border-red-500 focus:ring-red-500/20 bg-red-50 dark:bg-red-900/10"
                      : "border-gray-300 dark:border-gray-600 hover:border-gray-400 focus:border-gray-900 dark:focus:border-gray-50"
                  }`}
                  aria-required="true"
                />
                {errors.managerEmail && (
                  <p className="text-xs text-red-600 dark:text-red-400 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    {errors.managerEmail}
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {step === "manual-form" && (
          <div className="px-6 py-4 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <button
              onClick={() => {
                setStep("choose")
                setErrors({})
              }}
              className="text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 font-medium font-['Open_Sans',sans-serif] transition-colors"
            >
              Voltar
            </button>
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium rounded-md bg-gray-900 text-white hover:bg-gray-800 active:bg-gray-700 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-gray-900/20 disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed font-['Open_Sans',sans-serif] flex items-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Criando...
                </>
              ) : (
                "Criar e Configurar"
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
