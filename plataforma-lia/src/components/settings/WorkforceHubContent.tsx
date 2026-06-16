"use client"

import { useTranslations } from "next-intl"
import { MessageSquare } from "lucide-react"
import { WorkforceSection } from "./WorkforceSection"
import { useGoalsPlanningHub } from "./useGoalsPlanningHub"
import { useSettingsConversational } from "@/hooks/settings/use-settings-conversational"
import { textStyles } from "@/lib/design-tokens"

/**
 * Rich content for the Workforce card inside the "Minha Empresa" hub.
 *
 * Single canonical import surface: the `SmartImportZone` rendered by
 * `WorkforceSection` (drag/drop · select file · download template) is the
 * only upload path. Recruiters who prefer natural language get one discreet
 * conversational affordance that opens the LIA chat with input_mode=text,
 * converging on the same `import_workforce_plan` tool for HITL approval.
 */
export function WorkforceHubContent() {
  const t = useTranslations("settings.workforce")
  const hub = useGoalsPlanningHub({ activeSubsection: "workforce" })
  const { triggerAction } = useSettingsConversational()

  // Conversational path — opens chat with an explicit instruction to use
  // input_mode=text (LLM extraction). The file-upload path lives in the
  // canonical SmartImportZone above; no bespoke upload UI here.
  const handleDescribe = () => {
    triggerAction("configure_workforce", {
      section: "minha-empresa",
      prompt: t("describePrompt"),
      payload: { input_mode: "text" },
      source: "ui",
    })
  }

  const chatAffordance = (
    <button
      type="button"
      onClick={handleDescribe}
      className={`${textStyles.caption} inline-flex items-center gap-1.5 text-lia-text-secondary hover:text-lia-text-primary`}
    >
      <MessageSquare className="w-3.5 h-3.5" />
      {t("preferChat")}
    </button>
  )

  return <WorkforceSection hub={hub} chatAffordance={chatAffordance} />
}
