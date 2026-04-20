"use client"

import { useCallback } from "react"

export type SettingsActionId =
  | "configure_profile"
  | "configure_culture"
  | "configure_tech_stack"
  | "configure_benefits"
  | "configure_workforce"
  | "analyze_website"
  | "process_document"

export interface SettingsActionEventDetail {
  actionId: SettingsActionId
  section: string
  field?: string
  prompt?: string
  payload?: Record<string, unknown>
  source?: "chat" | "ui" | "onboarding"
}

const ACTION_TO_TAB: Record<SettingsActionId, string> = {
  configure_profile: "minha-empresa",
  configure_culture: "minha-empresa",
  configure_tech_stack: "minha-empresa",
  configure_benefits: "minha-empresa",
  configure_workforce: "minha-empresa",
  analyze_website: "minha-empresa",
  process_document: "minha-empresa",
}

export const SETTINGS_ACTION_EVENT = "lia:settings-action"
export const SETTINGS_OPEN_TAB_EVENT = "settings-open-tab"

export function useSettingsConversational() {
  const dispatchAction = useCallback((detail: SettingsActionEventDetail) => {
    if (typeof window === "undefined") return
    const tab = detail.section || ACTION_TO_TAB[detail.actionId] || "minha-empresa"
    window.dispatchEvent(
      new CustomEvent(SETTINGS_ACTION_EVENT, {
        detail: { ...detail, section: tab },
      }),
    )
    window.dispatchEvent(
      new CustomEvent(SETTINGS_OPEN_TAB_EVENT, { detail: tab }),
    )
  }, [])

  const sendChatPrompt = useCallback((prompt: string) => {
    if (typeof window === "undefined") return
    window.dispatchEvent(
      new CustomEvent("lia:chat-prompt", { detail: { prompt, source: "settings" } }),
    )
  }, [])

  const triggerAction = useCallback(
    (actionId: SettingsActionId, opts?: Partial<SettingsActionEventDetail>) => {
      const detail: SettingsActionEventDetail = {
        actionId,
        section: opts?.section || ACTION_TO_TAB[actionId],
        field: opts?.field,
        prompt: opts?.prompt,
        payload: opts?.payload,
        source: opts?.source || "ui",
      }
      dispatchAction(detail)
      if (detail.prompt) {
        sendChatPrompt(detail.prompt)
      }
    },
    [dispatchAction, sendChatPrompt],
  )

  return { triggerAction, dispatchAction, sendChatPrompt, ACTION_TO_TAB }
}
