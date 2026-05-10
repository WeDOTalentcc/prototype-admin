"use client"

/**
 * OfferReviewModal — 2-column modal for reviewing and sending offer letters.
 *
 * Left column: job data snapshot (read-only)
 * Right column: offer fields (editable, debounced auto-save)
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
import { offersApi } from "@/services/lia-api/offers-api"
import { JobDataPanel } from "./JobDataPanel"
import { OfferDataForm } from "./OfferDataForm"
import type { OfferDraftUpdate } from "@/types/offer"

const DEBOUNCE_MS = 600

export function OfferReviewModal() {
  const { draft, isSaving, salaryWarnings, updateField, sendAuto, prepareManual, cancel, clearDraft } =
    useOfferDraftStore()

  const [sendMode, setSendMode] = useState<"auto" | "manual" | null>(null)
  const [isSending, setIsSending] = useState(false)
  // HITL two-step confirm guard: idle → confirming → send
  const [confirmState, setConfirmState] = useState<"idle" | "confirming">("idle")
  const [sendResult, setSendResult] = useState<{ success: boolean; message: string } | null>(null)

  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pendingUpdates = useRef<OfferDraftUpdate>({})

  const isOpen = draft !== null && draft.status === "draft"

  // Debounced save: accumulate updates, flush after DEBOUNCE_MS of inactivity
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

  const handleSendAuto = useCallback(async () => {
    // HITL two-step: require explicit confirmation before sending
    if (confirmState !== "confirming") {
      setConfirmState("confirming")
      return
    }
    if (debounceTimer.current) clearTimeout(debounceTimer.current)
    if (Object.keys(pendingUpdates.current).length > 0) {
      await updateField({ ...pendingUpdates.current })
      pendingUpdates.current = {}
    }
    setIsSending(true)
    setConfirmState("idle")
    // Send with explicit user confirmation flag (HITL audit requirement)
    try {
      const draft = useOfferDraftStore.getState().draft
      if (draft) {
        const result = await offersApi.sendDraft(draft.id, { user_confirmation: true })
        setSendResult({ success: result.success ?? true, message: result.message ?? "Proposta enviada!" })
      }
    } catch (err) {
      setSendResult({ success: false, message: String(err) })
    }
    setIsSending(false)
  }, [confirmState, updateField])

  const handlePrepareManual = useCallback(async () => {
    if (debounceTimer.current) clearTimeout(debounceTimer.current)
    if (Object.keys(pendingUpdates.current).length > 0) {
      await updateField({ ...pendingUpdates.current })
      pendingUpdates.current = {}
    }
    const prepared = await prepareManual()
    if (prepared) {
      // Emit event for SendEmailModal to pick up (existing flow, untouched)
      window.dispatchEvent(new CustomEvent("lia:open_send_email_modal", { detail: prepared }))
      clearDraft()
    }
  }, [updateField, prepareManual, clearDraft])

  const handleCancel = useCallback(() => {
    if (debounceTimer.current) clearTimeout(debounceTimer.current)
    cancel()
  }, [cancel])

  // Auto-close after successful send (2s delay to show result)
  useEffect(() => {
    if (sendResult?.success) {
      const t = setTimeout(clearDraft, 2000)
      return () => clearTimeout(t)
    }
  }, [sendResult, clearDraft])

  if (!draft) return null

  const candidateName = draft.candidate_data_snapshot?.name ?? "Candidato"
  const jobTitle = draft.job_data_snapshot?.title ?? "Vaga"

  return (
    <Dialog open={isOpen} onOpenChange={(open) => { if (!open) handleCancel() }}>
      <DialogContent
        className="max-w-3xl w-full max-h-[90vh] flex flex-col p-0"
        aria-label={`Carta-oferta para ${candidateName}`}
      >
        <DialogHeader className="px-6 pt-5 pb-3 border-b border-border">
          <DialogTitle className="text-base font-semibold">
            Carta-Oferta — {candidateName}
          </DialogTitle>
          <p className="text-xs text-muted-foreground">{jobTitle}</p>
        </DialogHeader>

        {/* 2-column body */}
        <div className="flex flex-1 overflow-hidden">
          {/* Left: job data (read-only) */}
          <div className="w-[44%] overflow-y-auto border-r border-border">
            <JobDataPanel job={draft.job_data_snapshot} />
          </div>
          {/* Right: offer form (editable) */}
          <div className="flex-1 overflow-y-auto">
            <OfferDataForm
              draft={draft}
              isSaving={isSaving}
              salaryWarnings={salaryWarnings}
              onChange={handleChange}
            />
          </div>
        </div>

        {/* Send result toast */}
        {sendResult && (
          <div className={`mx-6 mb-2 text-xs px-3 py-2 rounded-md ${sendResult.success ? "bg-green-50 text-green-800 border border-green-200" : "bg-red-50 text-red-800 border border-red-200"}`}>
            {sendResult.message}
          </div>
        )}

        <DialogFooter className="px-6 pb-5 pt-3 border-t border-border flex gap-2 justify-between">
          <Button variant="ghost" size="sm" onClick={handleCancel} disabled={isSending}>
            Cancelar rascunho
          </Button>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePrepareManual}
              disabled={isSaving || isSending || !draft.offered_salary}
            >
              Envio Manual
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={handleSendAuto}
              disabled={isSaving || isSending || !draft.offered_salary}
              className="bg-gray-900 text-white hover:bg-gray-800"
            >
              {isSending ? "Enviando..." : confirmState === "confirming" ? "Confirmar Envio" : "Enviar Proposta"}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
