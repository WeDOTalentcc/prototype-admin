/**
 * schedule-message-store — GAP-07-007
 *
 * Global Zustand store for ScheduleMessageModal.
 * Allows any surface (kanban card, candidate table, LIA action) to open the modal
 * without prop drilling through intermediate components.
 */
import { create } from "zustand"

interface ScheduleMessageState {
  open: boolean
  candidateId: string | null
  candidateName: string | null
  vacancyId: string | null
  // Actions
  openScheduleModal: (
    candidateId: string,
    candidateName: string,
    vacancyId?: string,
  ) => void
  closeScheduleModal: () => void
}

export const useScheduleMessageStore = create<ScheduleMessageState>((set) => ({
  open: false,
  candidateId: null,
  candidateName: null,
  vacancyId: null,

  openScheduleModal: (candidateId, candidateName, vacancyId) =>
    set({ open: true, candidateId, candidateName, vacancyId: vacancyId ?? null }),

  closeScheduleModal: () =>
    set({ open: false, candidateId: null, candidateName: null, vacancyId: null }),
}))
