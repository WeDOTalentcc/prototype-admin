"use client"

import React, { useCallback, useEffect, useRef, useState } from "react"
import { useTranslations } from "next-intl"
import {
  Upload, Loader2, CheckCircle, AlertTriangle, X, FileText,
} from "lucide-react"
import { useLiaFloat } from "@/contexts/lia-float-context"
import { textStyles } from "@/lib/design-tokens"
import { apiFetch } from "@/lib/api/api-fetch"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"

type UploadState = "idle" | "uploading" | "extracting" | "sending" | "done" | "error"

const STATE_PROGRESS: Record<UploadState, number> = {
  idle: 0,
  uploading: 20,
  extracting: 50,
  sending: 80,
  done: 100,
  error: 0,
}

import { MAX_FILE_SIZE } from '@/constants/upload'
const VALID_EXTS = [".pdf", ".docx", ".txt"]

export type TargetSection =
  | "culture"
  | "tech_stack"
  | "benefits"
  | "workforce"
  | "compensation"
  | "policy"

interface SectionUploadDropZoneProps {
  /**
   * The card / section that originated the upload. Sent to the backend so
   * `process_uploaded_document` narrows the suggested fields to that area
   * and to the chat tool-call so the LIA confirmation step focuses there.
   */
  targetSection: TargetSection
  /** Document type sent to the backend extractor. */
  documentType: "handbook" | "tech_doc" | "org_chart" | "compensation"
  /** Human label used in the chat hand-off message. */
  sectionLabel: string
  /** Short helper text rendered inside the drop-zone. */
  hint?: string
}

export function SectionUploadDropZone({
  targetSection,
  documentType,
  sectionLabel,
  hint,
}: SectionUploadDropZoneProps) {
  const t = useTranslations("settings.sectionUpload")
  const [uploadState, setUploadState] = useState<UploadState>("idle")
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [warnings, setWarnings] = useState<string[]>([])
  const [progressPercent, setProgressPercent] = useState(0)
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const dropZoneRef = useRef<HTMLDivElement>(null)
  const progressTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
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
      setProgressPercent((prev) => {
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
    setErrorMessage(null)
    setWarnings([])
    setProgressPercent(0)
    setIsDragOver(false)
    if (progressTimerRef.current) clearInterval(progressTimerRef.current)
    if (fileInputRef.current) fileInputRef.current.value = ""
  }, [])

  const processFile = useCallback(async (file: File) => {
    const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase()
    if (!VALID_EXTS.includes(ext)) {
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

    setUploadState("uploading")
    setProgressPercent(0)
    animateProgress(STATE_PROGRESS.uploading)
    setErrorMessage(null)
    setWarnings([])

    try {
      const formData = new FormData()
      formData.append("file", file)
      formData.append("document_type", documentType)
      formData.append("target_section", targetSection)

      setUploadState("extracting")
      animateProgress(STATE_PROGRESS.extracting)

      const response = await apiFetch("/api/backend-proxy/documents/upload", {
        method: "POST",
        body: formData,
      })

      notifyChatOfSettingsUpdate({ actionId: "upload_section_doc", section: "documents" })
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        throw new Error(errData.error || t("errors.processFailed"))
      }

      const result = await response.json()
      const extractedText = result.extracted_text || ""
      const fairnessWarnings: string[] = result.fairness_warnings || []

      if (!extractedText || extractedText.trim().length < 10) {
        throw new Error(t("errors.insufficientText"))
      }

      setWarnings(fairnessWarnings)
      setUploadState("sending")
      animateProgress(STATE_PROGRESS.sending)

      const chatMessage = [
        t("chatToolHeader"),
        `[document_type:${documentType}]`,
        `[target_section:${targetSection}]`,
        `[file_name:${file.name}]`,
        `[text_length:${extractedText.length}]`,
        ``,
        t("chatReceivedSection", { fileName: file.name, sectionLabel }),
        t("chatUseTool", { docType: documentType, targetSection, sectionLabel }),
        t("chatAskConfirm"),
        ``,
        t("chatDocStart"),
        extractedText.substring(0, 8000),
        t("chatDocEnd"),
      ].join("\n")

      await sendChatMessage(chatMessage, "company_settings")

      animateProgress(100)
      setUploadState("done")
      setProgressPercent(100)
      setTimeout(resetState, 5000)
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : t("errors.processError"))
      setUploadState("error")
      setProgressPercent(0)
      setTimeout(resetState, 5000)
    }
  }, [animateProgress, documentType, resetState, sectionLabel, sendChatMessage, t, targetSection])

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    await processFile(file)
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
    if (file) await processFile(file)
  }

  const isProcessing =
    uploadState !== "idle" && uploadState !== "done" && uploadState !== "error"

  return (
    <div className="space-y-2" data-testid={`section-upload-${targetSection}`}>
      <div
        ref={dropZoneRef}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-lg p-3 text-center transition-colors motion-reduce:transition-none ${
          isDragOver
            ? "border-lia-btn-primary-bg bg-lia-btn-primary-bg/5"
            : "border-lia-border-subtle hover:border-lia-border-medium"
        } ${isProcessing ? "pointer-events-none opacity-60" : "cursor-pointer"}`}
        onClick={() => {
          if (!isProcessing) fileInputRef.current?.click()
        }}
      >
        {isProcessing ? (
          <Loader2 className="w-5 h-5 mx-auto mb-1 animate-spin motion-reduce:animate-none text-lia-btn-primary-bg" />
        ) : (
          <Upload
            className={`w-5 h-5 mx-auto mb-1 ${
              isDragOver ? "text-lia-btn-primary-bg" : "text-lia-text-tertiary"
            }`}
          />
        )}
        <p
          className={`${textStyles.labelSmall} ${
            isDragOver ? "text-lia-btn-primary-bg" : "text-lia-text-secondary"
          }`}
        >
          {isProcessing
            ? stateLabel(uploadState)
            : isDragOver
              ? t("dropFileHere")
              : t("dragSection", { sectionLabel: sectionLabel.toLowerCase() })}
        </p>
        <p className="text-micro text-lia-text-tertiary mt-0.5">
          {hint || t("defaultHint")}
        </p>
      </div>

      {isProcessing && (
        <div className="w-full h-1 bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-full overflow-hidden">
          <div
            className="h-full bg-lia-btn-primary-bg rounded-full transition-[width] duration-300 ease-out"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      )}

      {uploadState === "done" && (
        <div className="flex items-center gap-2 px-2 py-1.5 rounded-md text-micro bg-status-success/10 text-status-success border border-status-success/30">
          <CheckCircle className="w-3.5 h-3.5 flex-shrink-0" />
          <span>{t("doneMessage")}</span>
        </div>
      )}

      {uploadState === "error" && errorMessage && (
        <div className="flex items-center gap-2 px-2 py-1.5 rounded-md text-micro bg-status-error/10 text-status-error border border-status-error/30">
          <X className="w-3.5 h-3.5 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {warnings.length > 0 && uploadState !== "idle" && (
        <div className="px-2 py-1.5 rounded-md text-micro bg-status-warning/10 border border-status-warning/30">
          <div className="flex items-center gap-1 mb-0.5">
            <AlertTriangle className="w-3 h-3 text-status-warning" />
            <span className="font-medium text-status-warning">{t("fairnessTitle")}</span>
          </div>
          <p className="text-lia-text-secondary">
            {t("sensitiveTermsDetected", {
              terms: warnings.slice(0, 3).join(", ") + (warnings.length > 3 ? "…" : ""),
            })}
          </p>
        </div>
      )}

      <p className="text-micro text-lia-text-tertiary flex items-center gap-1">
        <FileText className="w-2.5 h-2.5" />
        {t("contextualUpload", { sectionLabel })}
      </p>

      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept=".pdf,.docx,.txt"
        onChange={handleFileSelect}
      />
    </div>
  )
}

export default SectionUploadDropZone
