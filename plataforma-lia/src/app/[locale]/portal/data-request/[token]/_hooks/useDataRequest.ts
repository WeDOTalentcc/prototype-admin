"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { useParams } from "next/navigation"

// Phase 3a: LGPD Art. 11 — campos sensiveis que requerem consentimento explicito
export const SENSITIVE_DATA_REQUEST_FIELDS = new Set([
  "disability_info",
  "pcd_type",
  "pcd_document",
  "gender",
  "race_ethnicity",
  "racial_autodeclaration",
])

export function hasSensitiveDataRequestFields(fields: FieldConfig[]): boolean {
  return fields.some((f) => SENSITIVE_DATA_REQUEST_FIELDS.has(f.name) || SENSITIVE_DATA_REQUEST_FIELDS.has(f.field_type))
}


export interface PortalData {
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

export interface FieldConfig {
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

export interface FieldCompleted {
  name: string
  value?: string
  file_url?: string
  file_name?: string
  submitted_at: string
}

export interface FieldError {
  name: string
  error: string
}

export type PortalStep = "loading" | "error" | "expired" | "otp" | "form" | "completed"

export function formatCPF(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 11)
  if (digits.length <= 3) return digits
  if (digits.length <= 6) return `${digits.slice(0, 3)}.${digits.slice(3)}`
  if (digits.length <= 9) return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6)}`
  return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9)}`
}

export function formatCNPJ(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 14)
  if (digits.length <= 2) return digits
  if (digits.length <= 5) return `${digits.slice(0, 2)}.${digits.slice(2)}`
  if (digits.length <= 8) return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5)}`
  if (digits.length <= 12) return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8)}`
  return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8, 12)}-${digits.slice(12)}`
}

export function formatPhone(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 11)
  if (digits.length <= 2) return digits.length > 0 ? `(${digits}` : ""
  if (digits.length <= 6) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`
  if (digits.length <= 10) return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`
  return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`
}

export function formatCurrency(value: string): string {
  const digits = value.replace(/\D/g, "")
  if (!digits) return ""
  const numValue = parseInt(digits, 10) / 100
  return numValue.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

export function useDataRequest() {
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
  // Phase 3a: LGPD Art. 11 sensitive-field consent
  const [consentChecked, setConsentChecked] = useState(false)
  const [consentId, setConsentId] = useState<string | null>(null)

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
      if (response.ok) {
        if (portalData) {
          setPortalData({ ...portalData, completion_percentage: data.completion_percentage })
        }
      }
    } catch (error) {
    } finally {
      setSaving(false)
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

    // Phase 3a: if sensitive fields present and not yet consented, record consent first
    const _hasSensitive = portalData ? hasSensitiveDataRequestFields(portalData.fields) : false
    if (_hasSensitive && !consentId) {
      if (!consentChecked) {
        // UI should disable submit button until consentChecked — this is belt-and-suspenders
        return
      }
      // Record consent before submitting
      try {
        const consentResp = await fetch(`/api/portal/data-request/${token}/consent`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ canal: "web", versao_disclaimer: "1.0" }),
        })
        const consentData = await consentResp.json()
        if (!consentResp.ok || !consentData.consent_id) {
          setErrorMessage(consentData.detail || "Erro ao registrar consentimento LGPD.")
          return
        }
        setConsentId(consentData.consent_id)
        // Continue with submit using the fresh consent_id
        await _doSubmit(consentData.consent_id)
        return
      } catch {
        setErrorMessage("Erro de conexão ao registrar consentimento.")
        return
      }
    }

    await _doSubmit(consentId)
  }

  const _doSubmit = async (_consentId: string | null) => {
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
        body: JSON.stringify({ fields, is_final: true, consent_id: _consentId }),
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

  const primaryColor = portalData?.branding.primary_color || "var(--lia-btn-primary-bg)"
  const primaryBgColor = primaryColor.startsWith('#') ? `${primaryColor}20` : 'var(--lia-bg-secondary)'

  return {
    token,
    step,
    portalData,
    errorMessage,
    otpCode,
    otpLoading,
    otpError,
    otpChannel,
    setOtpChannel,
    otpSent,
    otpResendTimer,
    otpInputRefs,
    formValues,
    formErrors,
    fileUploads,
    uploadProgress,
    submitting,
    saving,
    primaryColor,
    primaryBgColor,
    requestOTP,
    verifyOTP,
    handleOtpChange,
    handleOtpKeyDown,
    handleOtpPaste,
    handleFieldChange,
    handleFileChange,
    saveProgress,
    submitForm,
    // Phase 3a: LGPD sensitive-field consent state
    consentChecked,
    setConsentChecked,
    consentId,
    hasSensitiveFields: portalData ? hasSensitiveDataRequestFields(portalData.fields) : false,
  }
}
