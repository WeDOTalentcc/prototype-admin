import { create } from "zustand"
import { persist } from "zustand/middleware"

interface RailPosition {
  x: number
  y: number
}

interface WorkflowRailState {
  enabled: boolean
  expanded: boolean
  position: RailPosition | null
  toggleEnabled: () => void
  setEnabled: (v: boolean) => void
  setExpanded: (v: boolean) => void
  toggleExpanded: () => void
  setPosition: (p: RailPosition | null) => void
}

export const useWorkflowRailStore = create<WorkflowRailState>()(
  persist(
    (set) => ({
      enabled: true,
      expanded: true,
      position: null,
      toggleEnabled: () => set((s) => ({ enabled: !s.enabled })),
      setEnabled: (enabled) => set({ enabled }),
      setExpanded: (expanded) => set({ expanded }),
      toggleExpanded: () => set((s) => ({ expanded: !s.expanded })),
      setPosition: (position) => set({ position }),
    }),
    { name: "wedo-workflow-rail-ui" }
  )
)
