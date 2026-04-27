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

export interface OfferReviewTrigger {
  candidateId: string
  jobId: string
  draftId?: string  // if draft already exists (from tool response)
}

export function useOfferReviewFlow() {
  const { startDraft, loadDraft, clearDraft } = useOfferDraftStore()

  /**
   * Open the offer review modal for a candidate+job pair.
   * If draftId is provided (from create_offer_draft tool), loads existing draft.
   * Otherwise creates new (or retrieves idempotent draft).
   */
  const openOfferReview = useCallback(async (trigger: OfferReviewTrigger) => {
    if (trigger.draftId) {
      await loadDraft(trigger.draftId)
    } else {
      await startDraft(trigger.candidateId, trigger.jobId)
    }
    // Modal is controlled by useOfferDraftStore.draft !== null
    // Components watching the store will open the modal
  }, [loadDraft, startDraft])

  const closeOfferReview = useCallback(() => {
    clearDraft()
  }, [clearDraft])

  return { openOfferReview, closeOfferReview }
}
