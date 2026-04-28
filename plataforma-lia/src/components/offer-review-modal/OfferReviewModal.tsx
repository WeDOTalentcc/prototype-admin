"use client"

/**
 * OfferReviewModal — 2-column modal for reviewing and sending offer letters.
 *
 * Left column: job data snapshot (read-only)
 * Right column: offer fields (editable, debounced auto-save)
 *
 * HITL two-step: idle → confirming → success/error.
 * Send requires user_confirmation: true (Guard 2 — never bypasses HITL).
 *
 * Opened when useOfferDraftStore.draft !== null.
 * Entry triggers (managed by useOfferReviewFlow):
 *   A) Rail A Card 5.1 ui_action="open_offer_review"
 *   B) Kanban drag to "Oferta" column
 *   C) Unified Chat "preparar proposta para X"
 *
 * PR-B.
 */
import { useCallback, useEffect, useRef, useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { useOfferDraftStore } from "@/stores/offer-draft-store"
import { JobDataPanel } from "./JobDataPanel"
import { OfferDataForm } from "./OfferDataForm"
import { OfferHITLBanner } from "./OfferHITLBanner"
import type { ConfirmState } from "./OfferHITLBanner"
import type { OfferDraftUpdate } from "@/types/offer"

const DEBOUNCE_MS = 600

export function OfferReviewModal() {
  const { draft, isSaving, salaryWarnings, updateField, sendAuto, prepareManual, cancel, clearDraft } =
    useOfferDraftStore()

  const [sendMode, setSendMode] = useState<"auto" | "manual" | null>(null)
  const [isSending, setIsSending] = useState(false)
  const [confirmState, setConfirmState] = useState<ConfirmState>("idle")
  const [errorMessage, setErrorMessage] = useState("")

  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pendingUpdates = useRef<OfferDraftUpdate>({})

  const isOpen = draft !== null && draft.status === "draft"

  const handleChange = useCallback(
    (updates: OfferDraftUpdate) => {
      Object.assign(pendingUpdates.current, updates)
      if (debounceTimer.current) clearTimeout(debounceTimer.current)
      debounceTimer.current = setTimeout(async () => {
        const toSave = { ...pendingUpdates.current }
        pendingUpdates.current = {}
        await updateField(toSave)
      }, DEBOUNCE_MS)
    },
    [updateField],
  )

  // Step 1: request confirmation (idle → confirming)
  const handleRequestConfirm = useCallback(() => {
    if (!draft?.offered_salary) return
    setConfirmState("confirming")
    setSendMode("auto")
  }, [draft])

  // Step 2: confirmed — send with user_confirmation: true
  const handleConfirmSend = useCallback(async () => {
    if (debounceTimer.current) clearTimeout(debounceTimer.current)
    if (Object.keys(pendingUpdates.current).length > 0) {
      await updateField({ ...pendingUpdates.current })
      pendingUpdates.current = {}
    }
    setIsSending(true)
    // HITL gate: user_confirmation: true — recrutador confirmou explicitamente
    const result = await sendAuto()
    setIsSending(false)
    if (result.success) {
      setConfirmState("success")
    } else {
      setErrorMessage(result.message)
      setConfirmState("error")
    }
  }, [updateField, sendAuto])

  const handleCancelConfirm = useCallback(() => {
    setConfirmState("idle")
    setSendMode(null)
  }, [])

  const handleClearError = useCallback(() => {
    setConfirmState("idle")
    setErrorMessage("")
    setSendMode(null)
  }, [])

  const handlePrepareManual = useCallback(async () => {
    if (debounceTimer.current) clearTimeout(debounceTimer.current)
    if (Object.keys(pendingUpdates.current).length > 0) {
      await updateField({ ...pendingUpdates.current })
      pendingUpdates.current = {}
    }
    const prepared = await prepareManual()
    if (prepared) {
      window.dispatchEvent(new CustomEvent("lia:open_send_email_modal", { detail: prepared }))
      clearDraft()
    }
  }, [updateField, prepareManual, clearDraft])

  const handleCancel = useCallback(() => {
    if (debounceTimer.current) clearTimeout(debounceTimer.current)
    cancel()
  }, [cancel])

  // Auto-close after successful send
  useEffect(() => {
    if (confirmState === "success") {
      const t = setTimeout(clearDraft, 2000)
      return () => clearTimeout(t)
    }
  }, [confirmState, clearDraft])

  if (!draft) return null

  const candidateName = draft.candidate_data_snapshot?.name ?? "Candidato"
  const jobTitle = draft.job_data_snapshot?.title ?? "Vaga"

  return (
    <Dialog open={isOpen} onOpenChange={(open) => { if (!open) handleCancel() }}>
      <DialogContent
        className="max-w-6xl w-full max-h-[90vh] flex flex-col p-0"
        aria-label={`Carta-oferta para ${candidateName}`}
      >
        <DialogHeader className="px-6 pt-5 pb-3 border-b border-border">
          <DialogTitle className="text-[14px] font-semibold">
            Carta-Oferta — {candidateName}
          </DialogTitle>
          <p className="text-[11px] text-muted-foreground">{jobTitle}</p>
        </DialogHeader>

        <div className="flex flex-1 overflow-hidden">
          <div className="w-[44%] overflow-y-auto border-r border-border">
            <JobDataPanel job={draft.job_data_snapshot} />
          </div>
          <div className="flex-1 overflow-y-auto">
            <OfferDataForm
              draft={draft}
              isSaving={isSaving}
              salaryWarnings={salaryWarnings}
              onChange={handleChange}
            />
          </div>
        </div>

        <div className="px-6 pb-2">
          <OfferHITLBanner
            confirmState={confirmState}
            errorMessage={errorMessage}
            isSending={isSending}
            candidateName={candidateName}
            onCancelConfirm={handleCancelConfirm}
            onConfirmSend={handleConfirmSend}
            onClearError={handleClearError}
          />
        </div>

        <DialogFooter className="px-6 pb-5 pt-3 border-t border-border flex gap-2 justify-between">
          <Button variant="ghost" size="sm" onClick={handleCancel} disabled={isSending}>
            Cancelar rascunho
          </Button>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePrepareManual}
              disabled={isSaving || isSending || !draft.offered_salary || confirmState !== "idle"}
            >
              Envio Manual
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={handleRequestConfirm}
              disabled={isSaving || isSending || !draft.offered_salary || confirmState !== "idle"}
              className="bg-gray-800 text-white hover:bg-gray-700"
            >
              Enviar Proposta
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
