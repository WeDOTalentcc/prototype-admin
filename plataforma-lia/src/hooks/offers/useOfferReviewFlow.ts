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

export interface OfferReviewTrigger {
  candidateId: string
  jobId: string
  draftId?: string  // if draft already exists (from tool response)
}

export function useOfferReviewFlow() {
  const { setDraft, setOpen, loadDraft, clearDraft } = useOfferDraftStore()

  /**
   * Open the offer review modal for a candidate+job pair.
   * Calls offersApi.createDraft when no draftId is provided.
   * Calls setDraft and setOpen(true) to surface the modal.
   */
  const start = useCallback(async (trigger: OfferReviewTrigger) => {
    if (trigger.draftId) {
      await loadDraft(trigger.draftId)
      setOpen(true)
    } else {
      const draft = await offersApi.createDraft({
        candidate_id: trigger.candidateId,
        job_id: trigger.jobId,
      })
      setDraft(draft)
      setOpen(true)
    }
  }, [loadDraft, setDraft, setOpen])

  // Alias for backward compat
  const openOfferReview = start

  const closeOfferReview = useCallback(() => {
    setOpen(false)
    clearDraft()
  }, [setOpen, clearDraft])

  return { start, openOfferReview, closeOfferReview }
}
