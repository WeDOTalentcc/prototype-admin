import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

interface WizardDraftData {
  jobDraftId?: string
  basicInfoFields?: Record<string, unknown>
  salaryInfo?: Record<string, unknown>
  technicalSkills?: unknown[]
  behavioralCompetencies?: unknown[]
  jobDescription?: string
  wsiCandidates?: unknown[]
  currentStage?: string
  lastSavedAt?: string
}

interface WizardState {
  draft: WizardDraftData | null
  draftId: string | null
}

interface WizardActions {
  setDraft: (draft: WizardDraftData | null) => void
  setDraftId: (id: string | null) => void
  clearDraft: () => void
}

export type WizardStore = WizardState & WizardActions

export const useWizardStore = create<WizardStore>()(
  devtools(
    persist(
      (set) => ({
        draft: null,
        draftId: null,

        setDraft: (draft) =>
          set({ draft }, false, 'wizard/setDraft'),

        setDraftId: (id) =>
          set({ draftId: id }, false, 'wizard/setDraftId'),

        clearDraft: () =>
          set({ draft: null, draftId: null }, false, 'wizard/clearDraft'),
      }),
      {
        name: 'lia-wizard-store',
        partialize: (state) => ({
          draft: state.draft,
          draftId: state.draftId,
        }),
      }
    ),
    { name: 'WizardStore' }
  )
)
