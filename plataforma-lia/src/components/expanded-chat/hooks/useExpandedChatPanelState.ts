import { useState, useRef, useEffect } from "react"
import type { WizardMode } from '../types'

interface UseExpandedChatPanelStateParams {
  isJobCreationMode: boolean
  wizardMode: WizardMode
}

export function useExpandedChatPanelState({
  isJobCreationMode,
  wizardMode,
}: UseExpandedChatPanelStateParams) {
  // Panel resize state
  const [panelWidth, setPanelWidth] = useState(42) // percentage
  const [isResizing, setIsResizing] = useState(false)
  const resizeRef = useRef<HTMLDivElement>(null)
  const [isPanelOpen, setIsPanelOpen] = useState(true) // Controls right panel visibility
  const [stageTransition, setStageTransition] = useState<'idle' | 'loading' | 'waiting-response'>('idle') // Controls panel loading state during stage transitions
  const [isFullscreen, setIsFullscreen] = useState(false)

  // Control panel visibility based on wizard mode
  useEffect(() => {
    if (isJobCreationMode) {
      // Hide panel for pre_wizard, fast_track, and general modes
      // Show panel only for create_from_scratch mode
      if (wizardMode === 'pre_wizard' || wizardMode === 'fast_track' || wizardMode === 'general') {
        setIsPanelOpen(false)
      } else if (wizardMode === 'create_from_scratch') {
        setIsPanelOpen(true)
      }
    }
  }, [isJobCreationMode, wizardMode])

  return {
    panelWidth,
    setPanelWidth,
    isResizing,
    setIsResizing,
    resizeRef,
    isPanelOpen,
    setIsPanelOpen,
    stageTransition,
    setStageTransition,
    isFullscreen,
    setIsFullscreen,
  }
}
