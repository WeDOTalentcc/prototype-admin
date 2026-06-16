"use client"

import React, { useState, useRef, useCallback, useEffect } from "react"
import { useTranslations, useLocale } from "next-intl"
import { Card, CardContent } from "@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import {
  Upload, FileText, CheckCircle, AlertTriangle, Loader2, X, Clock,
  BookOpen, Network, DollarSign, Code,
} from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import { useLiaFloat } from "@/contexts/lia-float-context"
import { useAuth } from "@/contexts/auth-context"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import type { LucideIcon } from "lucide-react"
import { apiFetch } from "@/lib/api/api-fetch"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"

type UploadState = "idle" | "uploading" | "extracting" | "sending" | "done" | "error"

interface DocumentTypeInfo {
  id: string
  labelKey: string
  descriptionKey: string
  icon: LucideIcon
}

const DOCUMENT_TYPES: DocumentTypeInfo[] = [
  { id: "handbook", labelKey: "handbookLabel", descriptionKey: "handbookDescription", icon: BookOpen },
  { id: "org_chart", labelKey: "orgChartLabel", descriptionKey: "orgChartDescription", icon: Network },
  { id: "compensation", labelKey: "compensationLabel", descriptionKey: "compensationDescription", icon: DollarSign },
  { id: "tech_doc", labelKey: "techDocLabel", descriptionKey: "techDocDescription", icon: Code },
]

const STATE_PROGRESS: Record<UploadState, number> = {
  idle: 0,
  uploading: 20,
  extracting: 50,
  sending: 80,
  done: 100,
  error: 0,
}

interface UploadedDoc {
  documentType: string
  fileName: string
  uploadedAt: string
  textLength: number
  warnings: string[]
}

const STORAGE_KEY_PREFIX = "lia_uploaded_documents"

// P2-W2-09: chave inclui companyId para isolar dados por tenant.
// Sem companyId, dois users de empresas diferentes com mesmo email
// compartilhariam o mesmo slot de localStorage — data leak cross-tenant.
function getStorageKey(companyId: string | null | undefined, userEmail: string | undefined): string {
  const tenantScope = companyId || "no-company"
  const userScope = userEmail || "anonymous"
  return `${STORAGE_KEY_PREFIX}_${tenantScope}_${userScope}`
}

function loadUploadedDocs(storageKey: string): UploadedDoc[] {
  if (typeof window === "undefined") return []
  try {
    const raw = localStorage.getItem(storageKey)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveUploadedDoc(storageKey: string, doc: UploadedDoc) {
  const docs = loadUploadedDocs(storageKey)
  const filtered = docs.filter(d => d.documentType !== doc.documentType)
  filtered.push(doc)
  localStorage.setItem(storageKey, JSON.stringify(filtered))
}

import { MAX_FILE_SIZE } from '@/constants/upload'

export function DocumentUploadCard() {
  const t = useTranslations("settings.documentUpload")
  const locale = useLocale()
  const { user } = useAuth()
  const { companyId } = useCompanyId()
  const storageKey = getStorageKey(companyId, user?.email ?? undefined)
  const [uploadState, setUploadState] = useState<UploadState>("idle")
  const [activeDocType, setActiveDocType] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [fairnessWarnings, setFairnessWarnings] = useState<string[]>([])
  const [uploadedDocs, setUploadedDocs] = useState<UploadedDoc[]>(() => loadUploadedDocs(storageKey))
  const [progressPercent, setProgressPercent] = useState(0)
  const [isDragOver, setIsDragOver] = useState(false)
  const [pendingDocType, setPendingDocType] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const progressTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const dropZoneRef = useRef<HTMLDivElement>(null)
  const { sendChatMessage } = useLiaFloat()

  const stateLabel = (state: UploadState): string => {
    if (state === "idle" || state === "error") return ""
    return t(`states.${state}` as never)
  }

  useEffect(() => {
    return () => {
      if (progressTimerRef.current) clearInterval(progressTimerRef.current)
    }
  }, [])

  const animateProgress = useCallback((target: number) => {
    if (progressTimerRef.current) clearInterval(progressTimerRef.current)
    progressTimerRef.current = setInterval(() => {
      setProgressPercent(prev => {
        if (prev >= target) {
          if (progressTimerRef.current) clearInterval(progressTimerRef.current)
          return target
        }
        return prev + 2
      })
    }, 50)
  }, [])

  const resetState = useCallback(() => {
    setUploadState("idle")
    setActiveDocType(null)
    setPendingDocType(null)
    setErrorMessage(null)
    setFairnessWarnings([])
    setProgressPercent(0)
    setIsDragOver(false)
    if (progressTimerRef.current) clearInterval(progressTimerRef.current)
    if (fileInputRef.current) fileInputRef.current.value = ""
  }, [])

  const processFile = useCallback(async (file: File, docType: string) => {
    const validExts = [".pdf", ".docx", ".txt"]
    const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase()

    if (!validExts.includes(ext)) {
      setErrorMessage(t("errors.unsupportedFormat"))
      setUploadState("error")
      setTimeout(resetState, 4000)
      return
    }

    if (file.size > MAX_FILE_SIZE) {
      setErrorMessage(t("errors.fileTooLarge"))
      setUploadState("error")
      setTimeout(resetState, 4000)
      return
    }

    setActiveDocType(docType)
    setUploadState("uploading")
    setProgressPercent(0)
    animateProgress(STATE_PROGRESS.uploading)
    setErrorMessage(null)
    setFairnessWarnings([])

    try {
      const formData = new FormData()
      formData.append("file", file)
      formData.append("document_type", docType)

      setUploadState("extracting")
      animateProgress(STATE_PROGRESS.extracting)

      const response = await apiFetch("/api/backend-proxy/documents/upload", {
        method: "POST",
        body: formData,
      })

      notifyChatOfSettingsUpdate({ actionId: "upload_document", section: "documents" })
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        throw new Error(errData.error || t("errors.processFailed"))
      }

      const result = await response.json()
      const extractedText = result.extracted_text || ""
      const warnings: string[] = result.fairness_warnings || []

      if (!extractedText || extractedText.trim().length < 10) {
        throw new Error(t("errors.insufficientText"))
      }

      setFairnessWarnings(warnings)
      setUploadState("sending")
      animateProgress(STATE_PROGRESS.sending)

      const docTypeInfo = DOCUMENT_TYPES.find(d => d.id === docType)
      const docTypeLabel = docTypeInfo ? t(`types.${docTypeInfo.labelKey}` as never) : docType

      const chatMessage = [
        t("chatToolHeader"),
        `[document_type:${docType}]`,
        `[file_name:${file.name}]`,
        `[text_length:${extractedText.length}]`,
        ``,
        t("chatReceivedDoc", { fileName: file.name, docTypeLabel }),
        t("chatUseTool", { docType }),
        t("chatAskConfirm"),
        t("chatExample"),
        ``,
        t("chatDocStart"),
        extractedText.substring(0, 8000),
        t("chatDocEnd"),
      ].join("\n")

      await sendChatMessage(chatMessage, "company_settings")

      animateProgress(100)

      const newDoc: UploadedDoc = {
        documentType: docType,
        fileName: file.name,
        uploadedAt: new Date().toISOString(),
        textLength: extractedText.length,
        warnings,
      }
      saveUploadedDoc(storageKey, newDoc)
      setUploadedDocs(loadUploadedDocs(storageKey))

      setUploadState("done")
      setProgressPercent(100)
      setTimeout(resetState, 6000)
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : t("errors.processError"))
      setUploadState("error")
      setProgressPercent(0)
      setTimeout(resetState, 5000)
    }
  }, [animateProgress, resetState, sendChatMessage, storageKey, t])

  const handleSelectDocType = (docTypeId: string) => {
    setPendingDocType(docTypeId)
    setActiveDocType(docTypeId)
    fileInputRef.current?.click()
  }

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    const docType = pendingDocType || activeDocType
    if (!file || !docType) return
    await processFile(file, docType)
  }

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    if (dropZoneRef.current && !dropZoneRef.current.contains(e.relatedTarget as Node)) {
      setIsDragOver(false)
    }
  }

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)

    const file = e.dataTransfer?.files?.[0]
    if (!file) return

    const docType = pendingDocType || "handbook"
    await processFile(file, docType)
  }

  const getDocUploadInfo = (docTypeId: string): UploadedDoc | undefined => {
    return uploadedDocs.find(d => d.documentType === docTypeId)
  }

  const isProcessing = uploadState !== "idle" && uploadState !== "done" && uploadState !== "error"

  return (
    <div className="space-y-3">
      <div
        ref={dropZoneRef}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-lg p-4 text-center transition-colors motion-reduce:transition-none ${
          isDragOver
            ? "border-lia-btn-primary-bg bg-lia-btn-primary-bg/5"
            : "border-lia-border-subtle hover:border-lia-border-medium"
        } ${isProcessing ? "pointer-events-none opacity-60" : "cursor-pointer"}`}
        onClick={() => {
          if (!isProcessing) {
            setPendingDocType("handbook")
            fileInputRef.current?.click()
          }
        }}
      >
        <Upload className={`w-6 h-6 mx-auto mb-1.5 ${isDragOver ? "text-lia-btn-primary-bg" : "text-lia-text-tertiary"}`} />
        <p className={`${textStyles.labelSmall} ${isDragOver ? "text-lia-btn-primary-bg" : "text-lia-text-secondary"}`}>
          {isDragOver ? t("dropFileHere") : t("dragOrClick")}
        </p>
        <p className="text-micro text-lia-text-tertiary mt-0.5">{t("fileSizeHint")}</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {DOCUMENT_TYPES.map((docType) => {
          const uploaded = getDocUploadInfo(docType.id)
          const isActive = activeDocType === docType.id && isProcessing
          const IconComp = docType.icon
          const docLabel = t(`types.${docType.labelKey}` as never)
          const docDesc = t(`types.${docType.descriptionKey}` as never)

          return (
            <Card
              key={docType.id}
              className={`border rounded-lg transition-colors motion-reduce:transition-none cursor-pointer ${
                isActive
                  ? "border-lia-btn-primary-bg bg-lia-btn-primary-bg/5"
                  : uploaded
                  ? "border-status-success/30 bg-status-success/5 hover:border-status-success/50"
                  : "border-lia-border-subtle hover:border-lia-border-medium"
              } ${isProcessing && !isActive ? "opacity-50 pointer-events-none" : ""}`}
              onClick={() => !isProcessing && handleSelectDocType(docType.id)}
            >
              <CardContent className="p-3">
                <div className="flex items-start gap-2.5">
                  <div className={`w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0 ${
                    uploaded ? "bg-status-success/10" : "bg-lia-bg-tertiary dark:bg-lia-bg-elevated"
                  }`}>
                    {isActive ? (
                      <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none text-lia-btn-primary-bg" />
                    ) : uploaded ? (
                      <CheckCircle className="w-4 h-4 text-status-success" />
                    ) : (
                      <IconComp className="w-4 h-4 text-lia-text-secondary" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`${textStyles.labelSmall} truncate`}>{docLabel}</p>
                    {isActive ? (
                      <p className="text-micro text-lia-btn-primary-bg font-medium mt-0.5">
                        {stateLabel(uploadState)}
                      </p>
                    ) : uploaded ? (
                      <div className="mt-0.5">
                        <p className="text-micro text-status-success truncate">{uploaded.fileName}</p>
                        <p className="text-micro text-lia-text-tertiary flex items-center gap-1 mt-0.5">
                          <Clock className="w-2.5 h-2.5" />
                          {new Date(uploaded.uploadedAt).toLocaleDateString(locale)}
                        </p>
                      </div>
                    ) : (
                      <p className="text-micro text-lia-text-tertiary mt-0.5">{docDesc}</p>
                    )}

                    {uploaded && uploaded.warnings.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {uploaded.warnings.slice(0, 2).map((w, i) => (
                          <Chip
                            key={i}
                            variant="warning"
                            className="text-micro bg-status-warning/10 rounded-full px-1.5 py-0"
                          >
                            <AlertTriangle className="w-2.5 h-2.5 mr-0.5" />
                            {w.length > 50 ? w.substring(0, 50) + "…" : w}
                          </Chip>
                        ))}
                        {uploaded.warnings.length > 2 && (
                          <Chip variant="warning" className="text-micro rounded-full px-1.5 py-0">
                            +{uploaded.warnings.length - 2}
                          </Chip>
                        )}
                      </div>
                    )}
                  </div>
                  {!isActive && !uploaded && (
                    <Upload className="w-3.5 h-3.5 text-lia-text-tertiary flex-shrink-0 mt-0.5" />
                  )}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {isProcessing && (
        <div className="px-3 py-2.5 rounded-lg border border-lia-border-subtle bg-lia-bg-secondary">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs text-lia-text-secondary font-medium">
              {stateLabel(uploadState)}
            </span>
            <span className="text-micro text-lia-text-tertiary">{progressPercent}%</span>
          </div>
          <div className="w-full h-1.5 bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-full overflow-hidden">
            <div
              className="h-full bg-lia-btn-primary-bg rounded-full transition-[width] duration-300 ease-out"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      )}

      {uploadState === "done" && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs bg-status-success/10 text-status-success border border-status-success/30">
          <CheckCircle className="w-3.5 h-3.5 flex-shrink-0" />
          <span>{t("doneMessage")}</span>
        </div>
      )}

      {uploadState === "error" && errorMessage && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs bg-status-error/10 text-status-error border border-status-error/30">
          <X className="w-3.5 h-3.5 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {fairnessWarnings.length > 0 && uploadState !== "idle" && (
        <div className="px-3 py-2 rounded-lg text-xs bg-status-warning/10 border border-status-warning/30">
          <div className="flex items-center gap-1.5 mb-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-status-warning" />
            <span className="font-medium text-status-warning">{t("fairnessTitle")}</span>
          </div>
          <p className="text-micro text-lia-text-secondary mb-1.5">
            {t("fairnessSubtitle")}
          </p>
          <div className="flex flex-wrap gap-1">
            {fairnessWarnings.map((warning, i) => (
              <Chip
                key={i}
                variant="warning"
                className="text-micro bg-status-warning/10 rounded-full"
              >
                {warning}
              </Chip>
            ))}
          </div>
        </div>
      )}

      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept=".pdf,.docx,.txt"
        onChange={handleFileSelect}
      />

      <p className={`${textStyles.caption} text-center`}>
        <FileText className="w-3 h-3 inline mr-1" />
        {t("footer")}
      </p>
    </div>
  )
}

export default DocumentUploadCard
