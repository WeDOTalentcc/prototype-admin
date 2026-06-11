import { SPLIT_STAGES } from "./DynamicContextPanel"
import type { WizardStage } from "./wizard-types"

export type WizardPanelMode = "docked" | "expanded"

export function wizardPanelVisibility(args: {
  stage: string | null | undefined
  mode: WizardPanelMode
}): { showPanel: boolean; showDock: boolean } {
  const isSplit = !!args.stage && SPLIT_STAGES.includes(args.stage as WizardStage)
  return {
    showPanel: isSplit && args.mode === "expanded",
    showDock: isSplit && args.mode === "docked",
  }
}
