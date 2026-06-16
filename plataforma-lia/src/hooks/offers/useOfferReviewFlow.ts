"use client"

/**
 * useOfferReviewFlow — orchestrates the 3 entry triggers for OfferReviewModal.
 *
 * Entry triggers:
 *   A) Rail A Card 5.1 — ui_action="open_offer_review"
 *   B) Kanban drag to "Oferta" column (called by useKanbanTransitions)
 *   C) Unified Chat command "preparar proposta para X" (via create_offer_draft tool)
 *
 * PR-B.
 */
import { useCallback } from "react"
import { useOfferDraftStore } from "@/stores/offer-draft-store"
import { offersApi } from "@/services/lia-api/offers-api"
import { toast } from "@/lib/toast"

export interface OfferReviewTrigger {
  candidateId: string
  jobId: string
  draftId?: string  // if draft already exists (from tool response)
}

export function useOfferReviewFlow() {
  const { startDraft, loadDraft, clearDraft, setDraft, setOpen } = useOfferDraftStore()

  /**
   * Open the offer review modal for a candidate+job pair.
   * If draftId is provided (from create_offer_draft tool), loads existing draft.
   * Otherwise creates new (or retrieves idempotent draft).
   */
  const openOfferReview = useCallback(async (trigger: OfferReviewTrigger) => {
    try {
      if (trigger.draftId) {
        await loadDraft(trigger.draftId)
      } else {
        // Explicitly call offersApi.createDraft so callers can verify draft creation path
        const newDraft = await offersApi.createDraft({
          candidate_id: trigger.candidateId,
          job_id: trigger.jobId,
        })
        setDraft(newDraft)  // populate store directly — avoids round-trip GET
        setOpen(true)
      }
      // Modal is controlled by useOfferDraftStore.draft !== null
      // Components watching the store will open the modal
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro ao abrir proposta"
      toast.error("Não foi possível abrir a proposta", { description: message })
      console.error("[useOfferReviewFlow] openOfferReview error:", err)
    }
  }, [loadDraft, setDraft, setOpen])

  const closeOfferReview = useCallback(() => {
    clearDraft()
  }, [clearDraft])

  return { openOfferReview, closeOfferReview }
}
