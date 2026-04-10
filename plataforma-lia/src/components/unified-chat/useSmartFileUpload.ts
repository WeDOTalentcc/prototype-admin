"use client"

import { useCallback, useState } from "react"

/**
 * Smart File Upload — C.1 Phase C.
 *
 * Routes uploaded files to the correct pipeline:
 * - CV → screening pipeline (with LGPD consent check)
 * - JD → wizard intake (auto-starts job creation)
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

// Filename heuristics (mirrors backend file_router.py)
const CV_PATTERN = /\b(?:curricul|cv|resume|curr[íi]culo|perfil|candidat)/i
const JD_PATTERN = /\b(?:job.?desc|vaga|descri[cç][aã]o.?(?:da|de).?vaga|jd|requisitos|cargo|posi[cç][aã]o)/i

const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10MB
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
        requiresConsent: false,
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

    // LGPD consent check for CVs
    if (route.requiresConsent) {
      setPendingFile(file)
      setShowConsentDialog(true)
      return route
    }

    // Auto-start wizard for JD files
    if (type === "jd") {
      window.dispatchEvent(new CustomEvent("lia:prefill-message", {
        detail: { message: `Criar vaga a partir do arquivo: ${file.name}` },
      }))
    }

    return route
  }, [])

  const confirmConsent = useCallback(() => {
    setShowConsentDialog(false)
    if (pendingFile) {
      // Proceed with CV screening after consent
      window.dispatchEvent(new CustomEvent("lia:file-upload-confirmed", {
        detail: { file: pendingFile, type: "cv" },
      }))
      setPendingFile(null)
    }
  }, [pendingFile])

  const cancelConsent = useCallback(() => {
    setShowConsentDialog(false)
    setPendingFile(null)
    setRouting(null)
  }, [])

  return {
    processFile,
    routing,
    error,
    showConsentDialog,
    confirmConsent,
    cancelConsent,
  }
}
