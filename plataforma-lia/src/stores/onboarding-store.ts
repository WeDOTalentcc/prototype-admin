import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

interface OnboardingState {
  userData: Record<string, unknown> | null
  firstAccess: boolean
  canReplayOnboarding: boolean
  onboardingDismissed: boolean
  welcomeDismissed: boolean
}

interface OnboardingActions {
  setUserData: (data: Record<string, unknown> | null) => void
  updateUserData: (newData: Record<string, unknown>) => void
  setFirstAccess: (value: boolean) => void
  setCanReplayOnboarding: (value: boolean) => void
  setOnboardingDismissed: (value: boolean) => void
  setWelcomeDismissed: (value: boolean) => void
  clearOnboarding: () => void
}

export type OnboardingStore = OnboardingState & OnboardingActions

export const useOnboardingStore = create<OnboardingStore>()(
  devtools(
    persist(
      (set, get) => ({
        userData: null,
        firstAccess: false,
        canReplayOnboarding: false,
        onboardingDismissed: false,
        welcomeDismissed: false,

        setUserData: (data) =>
          set({ userData: data }, false, 'onboarding/setUserData'),

        updateUserData: (newData) => {
          const current = get().userData
          if (current) {
            set({ userData: { ...current, ...newData } }, false, 'onboarding/updateUserData')
          }
        },

        setFirstAccess: (value) =>
          set({ firstAccess: value }, false, 'onboarding/setFirstAccess'),

        setCanReplayOnboarding: (value) =>
          set({ canReplayOnboarding: value }, false, 'onboarding/setCanReplayOnboarding'),

        setOnboardingDismissed: (value) =>
          set({ onboardingDismissed: value }, false, 'onboarding/setOnboardingDismissed'),

        setWelcomeDismissed: (value) =>
          set({ welcomeDismissed: value }, false, 'onboarding/setWelcomeDismissed'),

        clearOnboarding: () =>
          set({
            userData: null,
            firstAccess: false,
            canReplayOnboarding: false,
            onboardingDismissed: false,
            welcomeDismissed: false,
          }, false, 'onboarding/clearOnboarding'),
      }),
      {
        name: 'lia-onboarding-store',
      }
    ),
    { name: 'OnboardingStore' }
  )
)
