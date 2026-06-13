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
 * P1-2 fix: OfferHITLBanner wired (was ghost component).
 * P1-9 fix: offer_link copiável após envio bem-sucedido.
 */
import { useCallback, useEffect, useRef, useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { useOfferDraftStore } from "@/stores/offer-draft-store"
import { offersApi } from "@/services/lia-api/offers-api"
import { JobDataPanel } from "./JobDataPanel"
import { OfferDataForm } from "./OfferDataForm"
import { OfferHITLBanner, type ConfirmState } from "./OfferHITLBanner"
import type { OfferDraftUpdate } from "@/types/offer"

const DEBOUNCE_MS = 600

export function OfferReviewModal() {
  const { draft, isSaving, salaryWarnings, updateField, prepareManual, cancel, clearDraft } =
    useOfferDraftStore()

  const [confirmState, setConfirmState] = useState<ConfirmState>("idle")
  const [isSending, setIsSending] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")
  const [offerLink, setOfferLink] = useState<string | null>(null)

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

  // Flush pending debounced updates before any network action
  const flushPendingUpdates = useCallback(async () => {
    if (debounceTimer.current) clearTimeout(debounceTimer.current)
    if (Object.keys(pendingUpdates.current).length > 0) {
      const toSave = { ...pendingUpdates.current }
      pendingUpdates.current = {}
      await updateField(toSave)
    }
  }, [updateField])

  // Step 1: user clicks "Enviar Proposta" → banner shows confirmation
  const handleRequestConfirm = useCallback(() => {
    setConfirmState("confirming")
  }, [])

  // Step 2: user clicks "Cancelar" in banner → back to idle
  const handleCancelConfirm = useCallback(() => {
    setConfirmState("idle")
  }, [])

  // Step 3: user clicks "Confirmar envio" in banner → fire send
  const handleConfirmSend = useCallback(async () => {
    await flushPendingUpdates()
    setIsSending(true)
    try {
      const currentDraft = useOfferDraftStore.getState().draft
      if (currentDraft) {
        const result = await offersApi.sendAuto(currentDraft.id)
        setOfferLink(result.offer_link ?? null)
        setConfirmState("success")
      }
    } catch (err) {
      setConfirmState("error")
      setErrorMessage(err instanceof Error ? err.message : "Erro ao enviar proposta.")
    }
    setIsSending(false)
  }, [flushPendingUpdates])

  // Clear error → back to idle
  const handleClearError = useCallback(() => {
    setConfirmState("idle")
    setErrorMessage("")
  }, [])

  const handlePrepareManual = useCallback(async () => {
    await flushPendingUpdates()
    const prepared = await prepareManual()
    if (prepared) {
      window.dispatchEvent(new CustomEvent("lia:open_send_email_modal", { detail: prepared }))
      clearDraft()
    }
  }, [flushPendingUpdates, prepareManual, clearDraft])

  const handleCancel = useCallback(() => {
    if (debounceTimer.current) clearTimeout(debounceTimer.current)
    cancel()
  }, [cancel])

  // Auto-close 4s after successful send (extra time allows copying the link)
  useEffect(() => {
    if (confirmState === "success") {
      const t = setTimeout(clearDraft, 4000)
      return () => clearTimeout(t)
    }
  }, [confirmState, clearDraft])

  if (!draft) return null

  const candidateName = draft.candidate_data_snapshot?.name ?? "Candidato"
  const jobTitle = draft.job_data_snapshot?.title ?? "Vaga"
  const canSend = !isSaving && !isSending && !!draft.offered_salary

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

        {/* HITL confirmation / success / error banner (P1-2 fix — was ghost) */}
        <div className="px-6">
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

        {/* Copy-link field shown after successful send (P1-9 fix) */}
        {confirmState === "success" && offerLink && (
          <div className="mx-6 mb-1 flex items-center gap-2 text-xs bg-green-50 border border-green-200 rounded-lg px-3 py-2">
            <span className="flex-1 truncate font-mono text-green-800">{offerLink}</span>
            <button
              type="button"
              onClick={() => navigator.clipboard.writeText(offerLink).catch(() => {})}
              className="shrink-0 px-2 py-1 rounded bg-green-100 hover:bg-green-200 text-green-700 font-medium transition-colors"
            >
              Copiar link
            </button>
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
              disabled={!canSend || confirmState !== "idle"}
            >
              Envio Manual
            </Button>
            {/* "Enviar Proposta" only visible in idle state; confirmation moves into banner */}
            {confirmState === "idle" && (
              <Button
                variant="secondary"
                size="sm"
                onClick={handleRequestConfirm}
                disabled={!canSend}
                className="bg-gray-900 text-white hover:bg-gray-800"
              >
                Enviar Proposta
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
