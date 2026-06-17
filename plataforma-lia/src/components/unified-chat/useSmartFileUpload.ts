"use client"

import { useCallback, useEffect, useRef, useState } from "react"

/**
 * Smart File Upload — C.1 Phase C.
 *
 * Routes uploaded files to the correct pipeline:
 * - CV → screening pipeline (with LGPD consent check)
 * - JD → wizard intake (auto-starts job creation, requires LGPD consent
 *   once per session — Task #838 / M-01)
 * - Generic → file analysis
 *
 * Reuses existing file input from UnifiedChatInput.tsx.
 */

type FileType = "cv" | "jd" | "generic"

interface FileRouting {
  type: FileType
  action: string
  description: string
  requiresConsent: boolean
}

// Session-scoped flag (Task #838): once a recruiter explicitly accepts the
// granular JD-upload consent, subsequent JD uploads in the same browser tab
// skip the dialog. Server-side, repeat consents are also bypassed for any
// company that has already granted it (recorded in audit_logs).
const JD_CONSENT_SESSION_KEY = "lia-jd-upload-consent"

function hasSessionJdConsent(): boolean {
  if (typeof window === "undefined") return false
  try {
    return window.sessionStorage.getItem(JD_CONSENT_SESSION_KEY) === "1"
  } catch {
    return false
  }
}

function rememberSessionJdConsent(): void {
  if (typeof window === "undefined") return
  try {
    window.sessionStorage.setItem(JD_CONSENT_SESSION_KEY, "1")
  } catch {
    /* ignore quota / privacy mode */
  }
}

// Preflight contra `/api/backend-proxy/jd-import/consent-status`. Fail-open
// conservador: qualquer erro/rede → assume "sem consent" e o diálogo será
// mostrado. NUNCA assumir consent em caso de falha.
async function fetchBackendJdConsent(signal: AbortSignal): Promise<boolean> {
  try {
    const res = await fetch("/api/backend-proxy/jd-import/consent-status", {
      method: "GET",
      credentials: "include",
      signal,
    })
    if (!res.ok) return false
    const data = await res.json()
    return data && typeof data.has_consent === "boolean" ? data.has_consent : false
  } catch {
    return false
  }
}

// Filename heuristics (mirrors backend file_router.py)
const CV_PATTERN = /\b(?:curricul|cv|resume|curr[íi]culo|perfil|candidat)/i
const JD_PATTERN = /\b(?:job.?desc|vaga|descri[cç][aã]o.?(?:da|de).?vaga|jd|requisitos|cargo|posi[cç][aã]o)/i

import { MAX_FILE_SIZE } from '@/constants/upload'
const ALLOWED_EXTENSIONS = new Set([
  "pdf", "docx", "doc", "txt", "csv", "xlsx", "json", "png", "jpg", "jpeg", "pptx",
])

function classifyFile(filename: string): FileType {
  const lower = filename.toLowerCase()
  if (CV_PATTERN.test(lower)) return "cv"
  if (JD_PATTERN.test(lower)) return "jd"
  return "generic"
}

function getRouting(type: FileType): FileRouting {
  switch (type) {
    case "cv":
      return {
        type: "cv",
        action: "cv_screening",
        description: "CV detectado. Iniciando triagem...",
        requiresConsent: true, // LGPD
      }
    case "jd":
      return {
        type: "jd",
        action: "wizard_intake",
        description: "JD detectado. Iniciando criacao de vaga...",
        // LGPD Art. 7º — consentimento granular pedido uma vez por sessão
        // (bypass via sessionStorage; back-end também libera empresas que já
        // têm registro de consentimento em audit_logs).
        requiresConsent: !hasSessionJdConsent(),
      }
    default:
      return {
        type: "generic",
        action: "file_analysis",
        description: "Analisando arquivo...",
        requiresConsent: false,
      }
  }
}

export function useSmartFileUpload() {
  const [routing, setRouting] = useState<FileRouting | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showConsentDialog, setShowConsentDialog] = useState(false)
  const [pendingFile, setPendingFile] = useState<File | null>(null)
  const [pendingType, setPendingType] = useState<FileType | null>(null)

  // Task #838 / M-01 — preflight de bypass: consulta o backend (audit_logs)
  // uma única vez por mount. Se a empresa do usuário já consentiu, espelha
  // o flag em sessionStorage para que `getRouting('jd')` (síncrono) também
  // pule o diálogo. Não invalida o sessionStorage existente.
  const preflightDoneRef = useRef(false)
  useEffect(() => {
    if (preflightDoneRef.current) return
    if (typeof window === "undefined") return
    if (hasSessionJdConsent()) {
      preflightDoneRef.current = true
      return
    }
    const ctrl = new AbortController()
    fetchBackendJdConsent(ctrl.signal).then((granted) => {
      if (granted) rememberSessionJdConsent()
      preflightDoneRef.current = true
    })
    return () => ctrl.abort()
  }, [])

  function dispatchJdPrefill(file: File) {
    window.dispatchEvent(new CustomEvent("lia:prefill-message", {
      detail: { message: `Criar vaga a partir do arquivo: ${file.name}` },
    }))
    window.dispatchEvent(new CustomEvent("lia:file-upload-confirmed", {
      detail: { file, type: "jd", consentAcknowledged: true },
    }))
  }

  const processFile = useCallback((file: File) => {
    setError(null)
    setRouting(null)

    // Validate
    if (file.size > MAX_FILE_SIZE) {
      setError(`Arquivo muito grande (${Math.round(file.size / (1024 * 1024))}MB). Maximo: 10MB.`)
      return null
    }
    if (file.size === 0) {
      setError("Arquivo vazio.")
      return null
    }

    const ext = file.name.split(".").pop()?.toLowerCase() || ""
    if (!ALLOWED_EXTENSIONS.has(ext)) {
      setError(`Tipo .${ext} nao suportado.`)
      return null
    }

    // Classify
    const type = classifyFile(file.name)
    const route = getRouting(type)
    setRouting(route)

    // LGPD consent check
    if (route.requiresConsent) {
      setPendingFile(file)
      setPendingType(type)
      setShowConsentDialog(true)
      return route
    }

    // Auto-start wizard for JD files (consent already granted in this session)
    if (type === "jd") {
      dispatchJdPrefill(file)
    }

    return route
  }, [])

  const confirmConsent = useCallback(() => {
    setShowConsentDialog(false)
    if (pendingFile) {
      if (pendingType === "jd") {
        rememberSessionJdConsent()
        dispatchJdPrefill(pendingFile)
      } else {
        // Proceed with CV screening after consent
        window.dispatchEvent(new CustomEvent("lia:file-upload-confirmed", {
          detail: { file: pendingFile, type: "cv", consentAcknowledged: true },
        }))
      }
      setPendingFile(null)
      setPendingType(null)
    }
  }, [pendingFile, pendingType])

  const cancelConsent = useCallback(() => {
    setShowConsentDialog(false)
    setPendingFile(null)
    setPendingType(null)
    setRouting(null)
  }, [])

  return {
    processFile,
    routing,
    error,
    showConsentDialog,
    pendingType,
    confirmConsent,
    cancelConsent,
  }
}
