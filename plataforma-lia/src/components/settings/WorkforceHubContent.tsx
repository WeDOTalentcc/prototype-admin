"use client"

import React, { useRef, useState } from "react"
import { useTranslations } from "next-intl"
import { Paperclip, MessageSquare, ClipboardPaste, Loader2, X } from "lucide-react"
import { WorkforceSection } from "./WorkforceSection"
import { useGoalsPlanningHub } from "./useGoalsPlanningHub"
import { useSettingsConversational } from "@/hooks/settings/use-settings-conversational"
import { textStyles, cardStyles } from "@/lib/design-tokens"
import { apiFetch } from "@/lib/api/api-fetch"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"

/**
 * Rich content for the Workforce card inside the "Minha Empresa" hub.
 *
 * Replaces the old summary-only field list with the canonical
 * `WorkforceSection` table (department × month, totals, inline editing)
 * and exposes three concrete HITL-gated capture paths, all converging on
 * the `import_workforce_plan` tool (input_mode spreadsheet | text | paste).
 * Every path returns to the recruiter via LIA chat for explicit approval
 * before any data is persisted — see Task #768 backend changes.
 */
export function WorkforceHubContent() {
  const t = useTranslations("settings.workforce")
  const hub = useGoalsPlanningHub({ activeSubsection: "workforce" })
  const { triggerAction, sendChatPrompt } = useSettingsConversational()
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [pasteOpen, setPasteOpen] = useState(false)
  const [pasteText, setPasteText] = useState("")

  // 1) Attach spreadsheet — real file upload to the existing import
  //    endpoint, then hand off to LIA for HITL approval preview.
  const handleAttachClick = () => {
    setUploadError(null)
    fileInputRef.current?.click()
  }

  const handleFileChosen = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    setUploading(true)
    setUploadError(null)
    try {
      const formData = new FormData()
      formData.append("file", file)
      const res = await apiFetch("/api/backend-proxy/workforce/entries/import", {
        method: "POST",
        body: formData,
      })
      notifyChatOfSettingsUpdate({ actionId: "upload_workforce_doc", section: "workforce" })
      if (!res.ok) {
        const msg = await res.text().catch(() => "")
        throw new Error(msg || t("uploadFailed"))
      }
      triggerAction("configure_workforce", {
        section: "minha-empresa",
        prompt: t("spreadsheetPrompt", { fileName: file.name }),
        payload: { input_mode: "spreadsheet", source_filename: file.name },
        source: "ui",
      })
      hub.fetchWorkforceData?.()
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : t("uploadFailed"))
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ""
    }
  }

  // 2) Describe in free text — open chat with an explicit instruction to
  //    use input_mode=text (LLM extraction path).
  const handleDescribe = () => {
    triggerAction("configure_workforce", {
      section: "minha-empresa",
      prompt: t("describePrompt"),
      payload: { input_mode: "text" },
      source: "ui",
    })
  }

  // 3) Paste structured data — modal capture that ships raw_text
  //    verbatim via the chat prefill so the LIA action receives it with
  //    input_mode=paste and runs the deterministic parser.
  const handlePasteSubmit = () => {
    const trimmed = pasteText.trim()
    if (!trimmed) return
    triggerAction("configure_workforce", {
      section: "minha-empresa",
      payload: { input_mode: "paste", raw_text: trimmed },
      source: "ui",
    })
    sendChatPrompt(`${t("pastePromptPrefix")}\n\n${trimmed}`)
    setPasteOpen(false)
    setPasteText("")
  }

  const btnClass =
    "flex items-center justify-center gap-2 px-3 py-2 rounded-md border border-lia-border-default bg-lia-bg-primary dark:bg-lia-bg-secondary hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse text-xs font-medium text-lia-text-primary disabled:opacity-60"

  return (
    <div className="space-y-3">
      <div
        className={`${cardStyles.flat} rounded-md border border-lia-border-subtle dark:border-lia-border-default p-3`}
      >
        <p className={`${textStyles.captionBold} mb-2 text-lia-text-primary`}>
          {t("howToSend")}
        </p>
        <p className={`${textStyles.caption} mb-3 text-lia-text-secondary`}>
          {t("pathsExplanation")}
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          <button
            type="button"
            onClick={handleAttachClick}
            disabled={uploading}
            className={btnClass}
          >
            {uploading ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
            ) : (
              <Paperclip className="w-3.5 h-3.5" />
            )}
            {t("attachSpreadsheet")}
          </button>
          <button type="button" onClick={handleDescribe} className={btnClass}>
            <MessageSquare className="w-3.5 h-3.5" />
            {t("describeInChat")}
          </button>
          <button
            type="button"
            onClick={() => setPasteOpen(true)}
            className={btnClass}
          >
            <ClipboardPaste className="w-3.5 h-3.5" />
            {t("pasteData")}
          </button>
        </div>
        {uploadError && (
          <p className="mt-2 text-micro text-status-error">{uploadError}</p>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xls,.xlsx,text/csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          className="hidden"
          onChange={handleFileChosen}
        />
      </div>

      {pasteOpen && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          onClick={(e) => {
            if (e.target === e.currentTarget) setPasteOpen(false)
          }}
        >
          <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-md border border-lia-border-default w-full max-w-lg mx-4 p-4 shadow-xl">
            <div className="flex items-center justify-between mb-2">
              <p className={`${textStyles.h3} text-lia-text-primary`}>
                {t("pasteDialogTitle")}
              </p>
              <button
                type="button"
                onClick={() => setPasteOpen(false)}
                aria-label={t("closeDialog")}
                className="p-1 rounded-md hover:bg-lia-bg-tertiary"
              >
                <X className="w-4 h-4 text-lia-text-tertiary" />
              </button>
            </div>
            <p className={`${textStyles.caption} mb-2 text-lia-text-secondary`}>
              {t("pasteDialogDesc")}
            </p>
            <textarea
              value={pasteText}
              onChange={(e) => setPasteText(e.target.value)}
              rows={8}
              placeholder={t("pastePlaceholder")}
              className="w-full font-mono text-xs border border-lia-border-default rounded-md px-2 py-1.5 bg-lia-bg-primary dark:bg-lia-bg-elevated text-lia-text-primary"
            />
            <div className="flex justify-end gap-2 mt-3">
              <button
                type="button"
                onClick={() => setPasteOpen(false)}
                className="px-3 py-1.5 text-xs rounded-md border border-lia-border-default text-lia-text-secondary hover:bg-lia-bg-secondary"
              >
                {t("cancel")}
              </button>
              <button
                type="button"
                onClick={handlePasteSubmit}
                disabled={!pasteText.trim()}
                className="px-3 py-1.5 text-xs rounded-md bg-lia-btn-primary-bg text-white hover:bg-lia-btn-primary-hover disabled:opacity-60"
              >
                {t("sendToLia")}
              </button>
            </div>
          </div>
        </div>
      )}

      <WorkforceSection hub={hub} />
    </div>
  )
}
