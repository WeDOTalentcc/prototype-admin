import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

export interface FailedDelivery {
  candidateId: string
  reason: string
  channel: 'email' | 'whatsapp' | 'both'
  at: number
}

interface FailedDeliveryState {
  failures: Record<string, FailedDelivery>
  addFailure: (d: FailedDelivery) => void
  clearFailure: (candidateId: string) => void
  clearAll: () => void
  hasFailure: (candidateId: string) => boolean
  getFailure: (candidateId: string) => FailedDelivery | undefined
}

export const useFailedDeliveryStore = create<FailedDeliveryState>()(
  devtools(
    (set, get) => ({
      failures: {},
      addFailure: (d) =>
        set(
          (s) => ({ failures: { ...s.failures, [d.candidateId]: d } }),
          false,
          'bulk/addFailure'
        ),
      clearFailure: (candidateId) =>
        set(
          (s) => {
            const { [candidateId]: _removed, ...rest } = s.failures
            return { failures: rest }
          },
          false,
          'bulk/clearFailure'
        ),
      clearAll: () => set({ failures: {} }, false, 'bulk/clearAll'),
      hasFailure: (candidateId) => candidateId in get().failures,
      getFailure: (candidateId) => get().failures[candidateId],
    }),
    { name: 'failed-delivery-store' }
  )
)
