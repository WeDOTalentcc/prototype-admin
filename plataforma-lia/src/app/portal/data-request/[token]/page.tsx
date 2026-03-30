"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { 
  Loader2, 
  CheckCircle2, 
  AlertCircle, 
  Upload, 
  X, 
  Eye,
  FileText,
  Image as ImageIcon,
  Phone,
  Mail,
  Calendar,
  CreditCard,
  Hash,
  Type,
  MapPin,
  Building,
  User
} from "lucide-react"

interface PortalData {
  id: string
  status: string
  expires_at: string
  is_expired: boolean
  otp_verified: boolean
  otp_required: boolean
  fields: FieldConfig[]
  fields_completed: FieldCompleted[]
  completion_percentage: number
  branding: {
    logo_url: string | null
    primary_color: string
    welcome_message: string | null
    thank_you_message: string | null
    privacy_policy_url: string | null
    terms_url: string | null
  }
  candidate_info: {
    name: string
    email: string | null
    email_masked: string | null
  }
  vacancy_info: {
    title: string
    department: string | null
  } | null
}

interface FieldConfig {
  name: string
  label: string
  field_type: string
  required: boolean
  placeholder?: string
  description?: string
  options?: string[]
  validation_rules?: {
    pattern?: string
    min_length?: number
    max_length?: number
    pattern_error?: string
  }
  max_file_size_mb?: number
  allowed_file_types?: string[]
}

interface FieldCompleted {
  name: string
  value?: string
  file_url?: string
  file_name?: string
  submitted_at: string
}

interface FieldError {
  name: string
  error: string
}

type PortalStep = "loading" | "error" | "expired" | "otp" | "form" | "completed"

const FIELD_TYPE_ICONS: Record<string, React.ReactNode> = {
  text: <Type className="w-4 h-4" />,
  cpf: <CreditCard className="w-4 h-4" />,
  cnpj: <Building className="w-4 h-4" />,
  email: <Mail className="w-4 h-4" />,
  phone: <Phone className="w-4 h-4" />,
  date: <Calendar className="w-4 h-4" />,
  number: <Hash className="w-4 h-4" />,
  currency: <CreditCard className="w-4 h-4" />,
  file: <FileText className="w-4 h-4" />,
  photo: <ImageIcon className="w-4 h-4" />,
  address: <MapPin className="w-4 h-4" />,
  select: <Type className="w-4 h-4" />,
  textarea: <Type className="w-4 h-4" />,
}

function formatCPF(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 11)
  if (digits.length <= 3) return digits
  if (digits.length <= 6) return `${digits.slice(0, 3)}.${digits.slice(3)}`
  if (digits.length <= 9) return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6)}`
  return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9)}`
}

function formatCNPJ(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 14)
  if (digits.length <= 2) return digits
  if (digits.length <= 5) return `${digits.slice(0, 2)}.${digits.slice(2)}`
  if (digits.length <= 8) return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5)}`
  if (digits.length <= 12) return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8)}`
  return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8, 12)}-${digits.slice(12)}`
}

function formatPhone(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 11)
  if (digits.length <= 2) return digits.length > 0 ? `(${digits}` : ""
  if (digits.length <= 6) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`
  if (digits.length <= 10) return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`
  return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`
}

function formatCurrency(value: string): string {
  const digits = value.replace(/\D/g, "")
  if (!digits) return ""
  const numValue = parseInt(digits, 10) / 100
  return numValue.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

export default function CandidatePortalPage() {
  const params = useParams()
  const token = params.token as string

  const [step, setStep] = useState<PortalStep>("loading")
  const [portalData, setPortalData] = useState<PortalData | null>(null)
  const [errorMessage, setErrorMessage] = useState("")
  
  const [otpCode, setOtpCode] = useState(["", "", "", "", "", ""])
  const [otpLoading, setOtpLoading] = useState(false)
  const [otpError, setOtpError] = useState("")
  const [otpChannel, setOtpChannel] = useState<"email" | "whatsapp">("email")
  const [otpSent, setOtpSent] = useState(false)
  const [otpResendTimer, setOtpResendTimer] = useState(0)
  const otpInputRefs = useRef<(HTMLInputElement | null)[]>([])

  const [formValues, setFormValues] = useState<Record<string, string>>({})
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [fileUploads, setFileUploads] = useState<Record<string, { file: File; preview?: string }>>({})
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({})
  const [submitting, setSubmitting] = useState(false)
  const [saving, setSaving] = useState(false)

  const fetchPortalData = useCallback(async () => {
    try {
      const response = await fetch(`/api/portal/data-request/${token}`)
      if (!response.ok) {
        const data = await response.json()
        if (response.status === 404) {
          setErrorMessage("Solicitação não encontrada. Verifique o link recebido.")
        } else if (response.status === 410) {
          setStep("expired")
          setErrorMessage(data.detail || "Esta solicitação expirou ou foi cancelada.")
          return
        } else {
          setErrorMessage(data.detail || "Erro ao carregar dados.")
        }
        setStep("error")
        return
      }

      const data: PortalData = await response.json()
      setPortalData(data)

      if (data.status === "completed") {
        setStep("completed")
      } else if (data.otp_required && !data.otp_verified) {
        setStep("otp")
      } else {
        setStep("form")
        initializeFormValues(data)
      }
    } catch (error) {
      setErrorMessage("Erro de conexão. Tente novamente.")
      setStep("error")
    }
  }, [token])

  const initializeFormValues = (data: PortalData) => {
    const values: Record<string, string> = {}
    for (const completed of data.fields_completed) {
      if (completed.value) {
        values[completed.name] = completed.value
      }
    }
    setFormValues(values)
  }

  useEffect(() => {
    if (token) {
      fetchPortalData()
    }
  }, [token, fetchPortalData])

  useEffect(() => {
    if (otpResendTimer > 0) {
      const timer = setTimeout(() => setOtpResendTimer(otpResendTimer - 1), 1000)
      return () => clearTimeout(timer)
    }
  }, [otpResendTimer])

  const requestOTP = async () => {
    setOtpLoading(true)
    setOtpError("")
    try {
      const response = await fetch(`/api/portal/data-request/${token}/request-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channel: otpChannel }),
      })
      const data = await response.json()
      if (!response.ok) {
        setOtpError(data.detail || "Erro ao enviar código.")
        return
      }
      setOtpSent(true)
      setOtpResendTimer(60)
    } catch (error) {
      setOtpError("Erro de conexão. Tente novamente.")
    } finally {
      setOtpLoading(false)
    }
  }

  const verifyOTP = async () => {
    const code = otpCode.join("")
    if (code.length !== 6) {
      setOtpError("Digite o código completo de 6 dígitos.")
      return
    }

    setOtpLoading(true)
    setOtpError("")
    try {
      const response = await fetch(`/api/portal/data-request/${token}/verify-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code }),
      })
      const data = await response.json()
      if (!response.ok) {
        setOtpError(data.detail || "Código incorreto. Tente novamente.")
        if (data.attempts_remaining !== undefined) {
          setOtpError(`Código incorreto. ${data.attempts_remaining} tentativa(s) restante(s).`)
        }
        return
      }
      if (data.verified) {
        await fetchPortalData()
      } else {
        setOtpError(data.message || "Código incorreto.")
      }
    } catch (error) {
      setOtpError("Erro de conexão. Tente novamente.")
    } finally {
      setOtpLoading(false)
    }
  }

  const handleOtpChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return

    const newOtp = [...otpCode]
    newOtp[index] = value.slice(-1)
    setOtpCode(newOtp)

    if (value && index < 5) {
      otpInputRefs.current[index + 1]?.focus()
    }
  }

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !otpCode[index] && index > 0) {
      otpInputRefs.current[index - 1]?.focus()
    }
  }

  const handleOtpPaste = (e: React.ClipboardEvent) => {
    e.preventDefault()
    const pastedData = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6)
    const newOtp = [...otpCode]
    for (let i = 0; i < pastedData.length; i++) {
      newOtp[i] = pastedData[i]
    }
    setOtpCode(newOtp)
    if (pastedData.length === 6) {
      otpInputRefs.current[5]?.focus()
    }
  }

  const handleFieldChange = (fieldName: string, value: string, fieldType: string) => {
    let formattedValue = value

    switch (fieldType) {
      case "cpf":
        formattedValue = formatCPF(value)
        break
      case "cnpj":
        formattedValue = formatCNPJ(value)
        break
      case "phone":
        formattedValue = formatPhone(value)
        break
      case "currency":
        formattedValue = formatCurrency(value)
        break
    }

    setFormValues((prev) => ({ ...prev, [fieldName]: formattedValue }))
    if (formErrors[fieldName]) {
      setFormErrors((prev) => {
        const next = { ...prev }
        delete next[fieldName]
        return next
      })
    }
  }

  const handleFileChange = async (fieldName: string, file: File | null) => {
    if (!file) {
      setFileUploads((prev) => {
        const next = { ...prev }
        delete next[fieldName]
        return next
      })
      return
    }

    const field = portalData?.fields.find((f) => f.name === fieldName)
    const maxSize = (field?.max_file_size_mb || 10) * 1024 * 1024

    if (file.size > maxSize) {
      setFormErrors((prev) => ({
        ...prev,
        [fieldName]: `Arquivo muito grande. Máximo: ${field?.max_file_size_mb || 10}MB`,
      }))
      return
    }

    const allowedTypes = field?.allowed_file_types || ["image/jpeg", "image/png", "application/pdf"]
    if (!allowedTypes.includes(file.type)) {
      setFormErrors((prev) => ({
        ...prev,
        [fieldName]: "Tipo de arquivo não permitido.",
      }))
      return
    }

    let preview: string | undefined
    if (file.type.startsWith("image/")) {
      preview = URL.createObjectURL(file)
    }

    setFileUploads((prev) => ({
      ...prev,
      [fieldName]: { file, preview },
    }))
    setFormErrors((prev) => {
      const next = { ...prev }
      delete next[fieldName]
      return next
    })
  }

  const uploadFile = async (fieldName: string, file: File): Promise<boolean> => {
    const formData = new FormData()
    formData.append("field_name", fieldName)
    formData.append("file", file)

    try {
      setUploadProgress((prev) => ({ ...prev, [fieldName]: 0 }))
      
      const response = await fetch(`/api/portal/data-request/${token}/upload`, {
        method: "POST",
        body: formData,
      })

      setUploadProgress((prev) => ({ ...prev, [fieldName]: 100 }))

      if (!response.ok) {
        const data = await response.json()
        setFormErrors((prev) => ({
          ...prev,
          [fieldName]: data.detail || "Erro no upload.",
        }))
        return false
      }
      return true
    } catch (error) {
      setFormErrors((prev) => ({
        ...prev,
        [fieldName]: "Erro no upload. Tente novamente.",
      }))
      return false
    }
  }

  const saveProgress = async () => {
    setSaving(true)
    try {
      const fields = Object.entries(formValues).map(([name, value]) => ({
        name,
        value: value.replace(/\D/g, "").length > 0 || value ? getRawValue(name, value) : null,
      }))

      const response = await fetch(`/api/portal/data-request/${token}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fields, is_final: false }),
      })

      const data = await response.json()
      if (!response.ok) {
      } else {
        if (portalData) {
          setPortalData({ ...portalData, completion_percentage: data.completion_percentage })
        }
      }
    } catch (error) {
    } finally {
      setSaving(false)
    }
  }

  const getRawValue = (fieldName: string, value: string): string => {
    const field = portalData?.fields.find((f) => f.name === fieldName)
    if (!field) return value

    switch (field.field_type) {
      case "cpf":
      case "cnpj":
      case "phone":
        return value.replace(/\D/g, "")
      case "currency":
        return value.replace(/[^\d,]/g, "").replace(",", ".")
      default:
        return value
    }
  }

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {}
    const requiredFields = portalData?.fields.filter((f) => f.required) || []

    for (const field of requiredFields) {
      const value = formValues[field.name]
      const hasFile = fileUploads[field.name]
      const completedFile = portalData?.fields_completed.find(
        (c) => c.name === field.name && c.file_url
      )

      if (field.field_type === "file" || field.field_type === "photo") {
        if (!hasFile && !completedFile) {
          errors[field.name] = "Este campo é obrigatório."
        }
      } else if (!value || !value.trim()) {
        errors[field.name] = "Este campo é obrigatório."
      }
    }

    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  const submitForm = async () => {
    if (!validateForm()) return

    setSubmitting(true)
    try {
      for (const [fieldName, upload] of Object.entries(fileUploads)) {
        const success = await uploadFile(fieldName, upload.file)
        if (!success) {
          setSubmitting(false)
          return
        }
      }

      const fields = Object.entries(formValues).map(([name, value]) => ({
        name,
        value: getRawValue(name, value),
      }))

      const response = await fetch(`/api/portal/data-request/${token}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fields, is_final: true }),
      })

      const data = await response.json()
      if (!response.ok) {
        if (data.fields_with_errors?.length > 0) {
          const errors: Record<string, string> = {}
          for (const err of data.fields_with_errors as FieldError[]) {
            errors[err.name] = err.error
          }
          setFormErrors(errors)
        } else {
          setErrorMessage(data.detail || "Erro ao enviar dados.")
        }
      } else {
        if (data.status === "completed") {
          setStep("completed")
          if (portalData) {
            setPortalData({ ...portalData, status: "completed", completion_percentage: 100 })
          }
        } else {
          if (portalData) {
            setPortalData({ ...portalData, completion_percentage: data.completion_percentage })
          }
        }
      }
    } catch (error) {
      setErrorMessage("Erro de conexão. Tente novamente.")
    } finally {
      setSubmitting(false)
    }
  }

  const primaryColor = portalData?.branding.primary_color || "var(--gray-950)"
  const primaryBgColor = primaryColor.startsWith('#') ? `${primaryColor}20` : 'var(--gray-bg-12)'

  const renderField = (field: FieldConfig) => {
    const value = formValues[field.name] || ""
    const error = formErrors[field.name]
    const upload = fileUploads[field.name]
    const completedFile = portalData?.fields_completed.find(
      (c) => c.name === field.name && c.file_url
    )

    const icon = FIELD_TYPE_ICONS[field.field_type] || <Type className="w-4 h-4" />

    if (field.field_type === "file" || field.field_type === "photo") {
      return (
        <div key={field.name} className="space-y-2">
          <Label className="flex items-center gap-2 text-sm font-medium lia-text-700 dark:lia-text-200">
            {icon}
            {field.label}
            {field.required && <span className="text-status-error">*</span>}
          </Label>
          {field.description && (
            <p className="text-xs lia-text-500 dark:lia-text-400">{field.description}</p>
          )}
          
          <div className="relative">
            {upload?.preview ? (
              <div className="relative rounded-md overflow-hidden border border-lia-border-subtle">
                <img
                  src={upload.preview}
                  alt="Preview"
                  className="w-full h-48 object-cover"
                />
                <button
                  type="button"
                  onClick={() => handleFileChange(field.name, null)}
                  className="absolute top-2 right-2 p-1 bg-status-error text-white rounded-full hover:bg-status-error"
                >
                  <X className="w-4 h-4" />
                </button>
                <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-xs p-2 truncate">
                  {upload.file.name}
                </div>
              </div>
            ) : upload?.file ? (
              <div className="flex items-center gap-3 p-4 border border-lia-border-subtle rounded-md">
                <FileText className="w-8 h-8 lia-text-400 dark:lia-text-500" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium lia-text-700 dark:lia-text-200 truncate">
                    {upload.file.name}
                  </p>
                  <p className="text-xs lia-text-500 dark:lia-text-400">
                    {(upload.file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => handleFileChange(field.name, null)}
                   className="p-1 lia-text-400 dark:lia-text-500 hover:text-status-error"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            ) : completedFile ? (
              <div className="flex items-center gap-3 p-4 border border-status-success/30 bg-status-success/10 rounded-md">
                <CheckCircle2 className="w-6 h-6 text-status-success" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium lia-text-700 dark:lia-text-200 truncate">
                    {completedFile.file_name || "Arquivo enviado"}
                  </p>
                  <p className="text-xs text-status-success">Arquivo já enviado</p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    const input = document.getElementById(`file-${field.name}`) as HTMLInputElement
                    input?.click()
                  }}
                   className="text-xs lia-text-500 dark:lia-text-400 hover:lia-text-700 dark:hover:lia-text-200 underline"
                >
                  Substituir
                </button>
              </div>
            ) : (
              <label
                htmlFor={`file-${field.name}`}
                className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-lia-border-default rounded-md cursor-pointer hover:border-gray-400 dark:hover:border-gray-500 hover:bg-gray-50 dark:hover:bg-gray-700 dark:lia-border-600 transition-colors"
              >
                <Upload className="w-8 h-8 lia-text-400 dark:lia-text-500 mb-2" />
                <span className="text-sm lia-text-500 dark:lia-text-400">
                  {field.field_type === "photo" ? "Toque para tirar foto ou selecionar" : "Toque para selecionar arquivo"}
                </span>
                <span className="text-xs lia-text-400 dark:lia-text-500 mt-1">
                  Máx: {field.max_file_size_mb || 10}MB
                </span>
              </label>
            )}
            
            <input
              id={`file-${field.name}`}
              type="file"
              accept={
                field.field_type === "photo"
                  ? "image/*"
                  : field.allowed_file_types?.join(",") || "image/*,application/pdf"
              }
              capture={field.field_type === "photo" ? "environment" : undefined}
              className="hidden"
              onChange={(e) => handleFileChange(field.name, e.target.files?.[0] || null)}
            />
          </div>

          {uploadProgress[field.name] !== undefined && uploadProgress[field.name] < 100 && (
            <div className="mt-2">
              <Progress value={uploadProgress[field.name]} className="h-1" />
              <p className="text-xs lia-text-500 dark:lia-text-400 mt-1">Enviando... {uploadProgress[field.name]}%</p>
            </div>
          )}

          {error && (
            <p className="text-xs text-status-error flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {error}
            </p>
          )}
        </div>
      )
    }

    if (field.field_type === "select" && field.options) {
      return (
        <div key={field.name} className="space-y-2">
           <Label className="flex items-center gap-2 text-sm font-medium lia-text-700 dark:lia-text-200">
            {icon}
            {field.label}
            {field.required && <span className="text-status-error">*</span>}
          </Label>
          {field.description && (
            <p className="text-xs lia-text-500 dark:lia-text-400">{field.description}</p>
          )}
          <select
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value, field.field_type)}
            className="flex h-10 w-full rounded-md border border-lia-border-default bg-white dark:lia-bg-800 dark:lia-text-100 dark:lia-border-600 px-3 py-2 text-sm focus:outline-none focus:border-gray-400 focus:ring-2 focus:ring-gray-200"
          >
            <option value="">Selecione...</option>
            {field.options.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
          {error && (
            <p className="text-xs text-status-error flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {error}
            </p>
          )}
        </div>
      )
    }

    if (field.field_type === "textarea") {
      return (
        <div key={field.name} className="space-y-2">
           <Label className="flex items-center gap-2 text-sm font-medium lia-text-700 dark:lia-text-200">
            {icon}
            {field.label}
            {field.required && <span className="text-status-error">*</span>}
          </Label>
          {field.description && (
             <p className="text-xs lia-text-500 dark:lia-text-400">{field.description}</p>
          )}
          <textarea
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value, field.field_type)}
            placeholder={field.placeholder}
            rows={4}
            className="flex w-full rounded-md border border-lia-border-default bg-white dark:lia-bg-800 dark:lia-text-100 dark:lia-border-600 px-3 py-2 text-sm focus:outline-none focus:border-gray-400 focus:ring-2 focus:ring-gray-200 resize-none"
          />
          {error && (
            <p className="text-xs text-status-error flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {error}
            </p>
          )}
        </div>
      )
    }

    return (
      <div key={field.name} className="space-y-2">
         <Label className="flex items-center gap-2 text-sm font-medium lia-text-700 dark:lia-text-200">
          {icon}
          {field.label}
          {field.required && <span className="text-status-error">*</span>}
        </Label>
        {field.description && (
           <p className="text-xs lia-text-500 dark:lia-text-400">{field.description}</p>
        )}
        <Input
          type={field.field_type === "date" ? "date" : "text"}
          value={value}
          onChange={(e) => handleFieldChange(field.name, e.target.value, field.field_type)}
          placeholder={field.placeholder}
          inputMode={
            ["cpf", "cnpj", "phone", "number", "currency"].includes(field.field_type)
              ? "numeric"
              : "text"
          }
          className={error ? "border-status-error/30 focus:border-status-error/30" : ""}
        />
        {error && (
          <p className="text-xs text-status-error flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            {error}
          </p>
        )}
      </div>
    )
  }

  if (step === "loading") {
    return (
      <div className="min-h-screen bg-gray-50 dark:lia-bg-900 flex items-center justify-center p-4">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin lia-text-400 dark:lia-text-500 mx-auto mb-4" />
          <p className="lia-text-500 dark:lia-text-400">Carregando...</p>
        </div>
      </div>
    )
  }

  if (step === "error") {
    return (
      <div className="min-h-screen bg-gray-50 dark:lia-bg-900 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 text-center">
            <AlertCircle className="w-16 h-16 text-status-error mx-auto mb-4" />
            <h1 className="text-xl font-semibold lia-text-900 dark:lia-text-100 mb-2">Ops!</h1>
            <p className="lia-text-600 dark:lia-text-300">{errorMessage}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (step === "expired") {
    return (
      <div className="min-h-screen bg-gray-50 dark:lia-bg-900 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 text-center">
            <AlertCircle className="w-16 h-16 text-status-warning mx-auto mb-4" />
            <h1 className="text-xl font-semibold lia-text-900 dark:lia-text-100 mb-2">Link Expirado</h1>
            <p className="lia-text-600 dark:lia-text-300">{errorMessage}</p>
            <p className="text-sm lia-text-500 dark:lia-text-400 mt-4">
              Entre em contato com o recrutador para solicitar um novo link.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (step === "otp") {
    return (
      <div className="min-h-screen bg-gray-50 dark:lia-bg-900 flex flex-col">
        {portalData?.branding.logo_url && (
          <div className="p-4 flex justify-center">
            <img
              src={portalData.branding.logo_url}
              alt="Logo"
              className="h-12 object-contain"
            />
          </div>
        )}

        <div className="flex-1 flex items-center justify-center p-4">
          <Card className="w-full max-w-md">
            <CardHeader className="text-center">
              <div
                className="w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center"
                style={{backgroundColor: primaryBgColor}}
              >
                <User className="w-8 h-8" style={{color: primaryColor}} />
              </div>
              <CardTitle className="text-xl">Olá, {portalData?.candidate_info.name}!</CardTitle>
              <CardDescription>
                Para sua segurança, precisamos verificar sua identidade.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {!otpSent ? (
                <>
                  <p className="text-sm lia-text-600 dark:lia-text-300 text-center">
                    Enviaremos um código de 6 dígitos para você.
                  </p>
                  
                  <div className="space-y-3">
                    <button
                      onClick={() => setOtpChannel("email")}
                      className={`w-full p-4 rounded-md border-2 flex items-center gap-3 transition-colors ${
                        otpChannel === "email"
                          ? "border-gray-900 dark:lia-border-500 bg-gray-50 dark:lia-bg-700"
                          : "border-lia-border-subtle hover:border-lia-border-default"
                      }`}
                    >
                      <Mail className="w-5 h-5 lia-text-600 dark:lia-text-300" />
                      <div className="text-left">
                        <p className="text-sm font-medium">E-mail</p>
                        <p className="text-xs lia-text-500 dark:lia-text-400">
                          {portalData?.candidate_info.email_masked}
                        </p>
                      </div>
                    </button>
                  </div>

                  <Button
                    onClick={requestOTP}
                    disabled={otpLoading}
                    className="w-full h-12"
                    style={{backgroundColor: primaryColor}}
                  >
                    {otpLoading ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      "Enviar Código"
                    )}
                  </Button>
                </>
              ) : (
                <>
                  <p className="text-sm lia-text-600 dark:lia-text-300 text-center">
                    Digite o código de 6 dígitos enviado para{" "}
                    <span className="font-medium">
                      {portalData?.candidate_info.email_masked}
                    </span>
                  </p>

                  <div className="flex justify-center gap-2">
                    {otpCode.map((digit, index) => (
                      <input
                        key={index}
                        ref={(el) => { otpInputRefs.current[index] = el }}
                        type="text"
                        inputMode="numeric"
                        maxLength={1}
                        value={digit}
                        onChange={(e) => handleOtpChange(index, e.target.value)}
                        onKeyDown={(e) => handleOtpKeyDown(index, e)}
                        onPaste={index === 0 ? handleOtpPaste : undefined}
                        className="w-12 h-14 text-center text-2xl font-semibold border-2 border-lia-border-default dark:lia-border-600 rounded-md focus:border-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-200 dark:lia-bg-800 dark:lia-text-100"
                      />
                    ))}
                  </div>

                  {otpError && (
                    <p className="text-sm text-status-error text-center flex items-center justify-center gap-1">
                      <AlertCircle className="w-4 h-4" />
                      {otpError}
                    </p>
                  )}

                  <Button
                    onClick={verifyOTP}
                    disabled={otpLoading || otpCode.join("").length !== 6}
                    className="w-full h-12"
                    style={{backgroundColor: primaryColor}}
                  >
                    {otpLoading ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      "Verificar"
                    )}
                  </Button>

                  <div className="text-center">
                    {otpResendTimer > 0 ? (
                      <p className="text-sm lia-text-500 dark:lia-text-400">
                        Reenviar código em {otpResendTimer}s
                      </p>
                    ) : (
                      <button
                        onClick={requestOTP}
                        disabled={otpLoading}
                        className="text-sm hover:underline"
                        style={{color: primaryColor}}
                      >
                        Reenviar código
                      </button>
                    )}
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  if (step === "completed") {
    return (
      <div className="min-h-screen bg-gray-50 dark:lia-bg-900 flex flex-col">
        {portalData?.branding.logo_url && (
          <div className="p-4 flex justify-center">
            <img
              src={portalData.branding.logo_url}
              alt="Logo"
              className="h-12 object-contain"
            />
          </div>
        )}

        <div className="flex-1 flex items-center justify-center p-4">
          <Card className="w-full max-w-md">
            <CardContent className="pt-8 pb-8 text-center">
              <div
                className="w-20 h-20 rounded-full mx-auto mb-6 flex items-center justify-center"
                style={{backgroundColor: primaryBgColor}}
              >
                <CheckCircle2 className="w-10 h-10" style={{color: primaryColor}} />
              </div>
              <h1 className="text-2xl font-semibold lia-text-900 dark:lia-text-100 mb-3">
                Obrigado!
              </h1>
              <p className="lia-text-600 dark:lia-text-300 mb-6">
                {portalData?.branding.thank_you_message ||
                  "Seus dados foram enviados com sucesso. Entraremos em contato em breve."}
              </p>
              {portalData?.vacancy_info && (
                <div className="bg-gray-50 dark:lia-bg-800 rounded-md p-4 text-left">
                  <p className="text-xs lia-text-500 dark:lia-text-400 uppercase tracking-wider mb-1">
                    Vaga
                  </p>
                  <p className="text-sm font-medium lia-text-900 dark:lia-text-100">
                    {portalData.vacancy_info.title}
                  </p>
                  {portalData.vacancy_info.department && (
                    <p className="text-xs lia-text-500 dark:lia-text-400">
                      {portalData.vacancy_info.department}
                    </p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:lia-bg-900 flex flex-col">
      {portalData?.branding.logo_url && (
        <div className="p-4 flex justify-center bg-white dark:lia-bg-800 border-b dark:lia-border-700">
          <img
            src={portalData.branding.logo_url}
            alt="Logo"
            className="h-10 object-contain"
          />
        </div>
      )}

      <div className="sticky top-0 z-10 bg-white dark:lia-bg-800 border-b dark:lia-border-700 px-4 py-3">
        <div className="max-w-lg mx-auto">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium lia-text-500 dark:lia-text-400">Progresso</span>
            <span className="text-xs font-semibold" style={{color: primaryColor}}>
              {Math.round(portalData?.completion_percentage || 0)}%
            </span>
          </div>
          <div className="relative h-2 bg-gray-200 dark:lia-bg-700 rounded-full overflow-hidden">
            <div
              className="absolute left-0 top-0 h-full transition-[width,height] duration-500 rounded-full"
              style={{width: `${portalData?.completion_percentage || 0}%`,
                backgroundColor: primaryColor}}
            />
          </div>
        </div>
      </div>

      <div className="flex-1 p-4">
        <div className="max-w-lg mx-auto">
          {portalData?.branding.welcome_message && (
            <div className="mb-6 p-4 bg-white dark:lia-bg-800 rounded-md border dark:lia-border-700">
              <p className="text-sm lia-text-600 dark:lia-text-300">{portalData.branding.welcome_message}</p>
            </div>
          )}

          {portalData?.vacancy_info && (
            <div className="mb-6 p-4 bg-white dark:lia-bg-800 rounded-md border dark:lia-border-700">
              <p className="text-xs lia-text-500 dark:lia-text-400 uppercase tracking-wider mb-1">
                Preenchendo dados para
              </p>
              <p className="text-base font-medium lia-text-900 dark:lia-text-100">
                {portalData.vacancy_info.title}
              </p>
              {portalData.vacancy_info.department && (
                <p className="text-sm lia-text-500 dark:lia-text-400">{portalData.vacancy_info.department}</p>
              )}
            </div>
          )}

          <Card className="mb-6">
            <CardContent className="pt-6 space-y-6">
              {portalData?.fields.map((field) => renderField(field))}
            </CardContent>
          </Card>

          <div className="space-y-3 pb-8">
            <Button
              onClick={submitForm}
              disabled={submitting || saving}
              className="w-full h-12 text-base font-medium"
              style={{backgroundColor: primaryColor}}
            >
              {submitting ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin mr-2" />
                  Enviando...
                </>
              ) : (
                "Enviar Dados"
              )}
            </Button>

            <Button
              onClick={saveProgress}
              disabled={submitting || saving}
              variant="outline"
              className="w-full h-10"
            >
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  Salvando...
                </>
              ) : (
                "Salvar e Continuar Depois"
              )}
            </Button>

            {portalData?.branding.privacy_policy_url && (
              <p className="text-xs text-center lia-text-500 dark:lia-text-400">
                Ao enviar, você concorda com nossa{" "}
                <a
                  href={portalData.branding.privacy_policy_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline hover:lia-text-700 dark:hover:lia-text-200"
                >
                  Política de Privacidade
                </a>
                {portalData.branding.terms_url && (
                  <>
                    {" "}e{" "}
                    <a
                      href={portalData.branding.terms_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline hover:lia-text-700 dark:hover:lia-text-200"
                    >
                      Termos de Uso
                    </a>
                  </>
                )}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
