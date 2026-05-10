"use client"

/**
 * useOfferDraftStore — shared Zustand store for OfferReviewModal.
 *
 * Single source of truth for the draft being edited across three surfaces:
 * OfferReviewModal, UnifiedChat (lateral), and TransitionChatPanel.
 * PR-B.
 */
import { create } from "zustand"
import { devtools } from "zustand/middleware"
import type { OfferDraft, OfferDraftUpdate, SalaryWarning } from "@/types/offer"
import { offersApi } from "@/services/lia-api/offers-api"

interface OfferDraftState {
  draft: OfferDraft | null
  isOpen: boolean
  isLoading: boolean
  isSaving: boolean
  error: string | null
  salaryWarnings: SalaryWarning[]

  // Actions
  startDraft: (candidateId: string, jobId: string) => Promise<void>
  loadDraft: (offerId: string) => Promise<void>
  updateField: (updates: OfferDraftUpdate) => Promise<void>
  sendAuto: () => Promise<{ success: boolean; message: string }>
  prepareManual: () => Promise<{ subject: string; body: string; templateId?: string } | null>
  cancel: (reason?: string) => Promise<void>
  setDraft: (draft: OfferDraft) => void
  setOpen: (open: boolean) => void
  clearDraft: () => void
  reset: () => void
  setSalaryWarnings: (warnings: SalaryWarning[]) => void
}

function computeSalaryWarnings(draft: OfferDraft): SalaryWarning[] {
  const warnings: SalaryWarning[] = []
  const salary = draft.offered_salary
  if (!salary) return warnings
  const range = draft.job_data_snapshot?.salary_range
  if (!range) return warnings
  const { min, max } = range
  if (max && salary > max * 1.1) {
    warnings.push({ level: "warning", message: `Salário acima de 110% do máximo da faixa (R$ ${max.toLocaleString("pt-BR")})` })
  }
  if (min && salary < min) {
    warnings.push({ level: "info", message: `Salário abaixo do mínimo da faixa (R$ ${min.toLocaleString("pt-BR")})` })
  }
  return warnings
}

const initialState = {
  draft: null as OfferDraft | null,
  isOpen: false,
  isLoading: false,
  isSaving: false,
  error: null as string | null,
  salaryWarnings: [] as SalaryWarning[],
}

export const useOfferDraftStore = create<OfferDraftState>()(devtools((set, get) => ({
  ...initialState,

  startDraft: async (candidateId: string, jobId: string) => {
    set({ isLoading: true, error: null })
    try {
      const draft = await offersApi.createDraft({ candidate_id: candidateId, job_id: jobId })
      set({ draft, isLoading: false, salaryWarnings: computeSalaryWarnings(draft) })
    } catch (err) {
      set({ error: String(err), isLoading: false })
    }
  },

  loadDraft: async (offerId: string) => {
    set({ isLoading: true, error: null })
    try {
      const draft = await offersApi.getDraft(offerId)
      set({ draft, isLoading: false, salaryWarnings: computeSalaryWarnings(draft) })
    } catch (err) {
      set({ error: String(err), isLoading: false })
    }
  },

  updateField: async (updates: OfferDraftUpdate) => {
    const { draft } = get()
    if (!draft) return
    // Optimistic update
    const optimistic = { ...draft, ...updates }
    set({ draft: optimistic, isSaving: true, salaryWarnings: computeSalaryWarnings(optimistic) })
    try {
      const updated = await offersApi.updateDraft(draft.id, updates)
      set({ draft: updated, isSaving: false, salaryWarnings: computeSalaryWarnings(updated) })
    } catch (err) {
      // Rollback on error
      set({ draft, isSaving: false, error: String(err) })
    }
  },

  sendAuto: async () => {
    const { draft } = get()
    if (!draft) return { success: false, message: "Sem rascunho ativo" }
    set({ isSaving: true })
    try {
      const result = await offersApi.sendAuto(draft.id)
      set({ draft: { ...draft, status: "sent" }, isSaving: false })
      return { success: true, message: result.message }
    } catch (err) {
      set({ isSaving: false, error: String(err) })
      return { success: false, message: String(err) }
    }
  },

  prepareManual: async () => {
    const { draft } = get()
    if (!draft) return null
    try {
      const result = await offersApi.prepareManual(draft.id)
      return {
        subject: result.subject_pre_filled,
        body: result.body_pre_filled,
        templateId: result.template_id,
      }
    } catch (err) {
      set({ error: String(err) })
      return null
    }
  },

  cancel: async (reason?: string) => {
    const { draft } = get()
    if (!draft) return
    try {
      await offersApi.cancel(draft.id, reason)
      set({ draft: null })
    } catch (err) {
      set({ error: String(err) })
    }
  },

  setDraft: (draft: OfferDraft) => set({ draft, salaryWarnings: computeSalaryWarnings(draft) }),

  setOpen: (open: boolean) => set({ isOpen: open }),

  clearDraft: () => set({ draft: null, error: null, salaryWarnings: [] }),

  reset: () => set(initialState),

  setSalaryWarnings: (warnings) => set({ salaryWarnings: warnings }),
}), { name: "OfferDraftStore" })
)
