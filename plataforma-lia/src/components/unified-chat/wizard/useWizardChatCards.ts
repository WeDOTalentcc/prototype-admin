/**
 * useWizardChatCards — owns the two non-persisted assistant cards the wizard
 * injects into the chat feed:
 *
 *   1. **Plano de trabalho** card — appears the first time the wizard
 *      reports a stage and stays in sync with `flowSteps`/title until the
 *      wizard resets. At terminal stages (`done`/`handoff`) it stays
 *      visible with all 6 steps marked completed and the title flipped to
 *      "Plano de trabalho — Concluído" (Task #830).
 *
 *   2. **Vaga publicada** closing card — injected once the wizard reaches
 *      a closing stage (`done`/`handoff`), carrying the actionable summary
 *      (job link, share link). Re-emissions of the same payload are
 *      deduped to avoid React churn.
 *
 * Extracted from `UnifiedChat.tsx` (Task A2) so the chat-feed behaviour is
 * testable in isolation and stays portable across surfaces. The hook is
 * parameterized on the caller's chat-state setter so it remains agnostic
 * to whether the messages live in `LiaFloatContext` or anywhere else that
 * exposes the same `LiaChatMessage[]` shape. (Originally also fed the
 * deprecated `expanded-chat-modal` surface — removed in Task #860.)
 *
 * Dedupe latches are kept in `useRef` so back-to-back wizard runs on the
 * same surface still re-emit their cards (the latch is reset whenever the
 * wizard leaves the relevant stage range).
 */

import { useEffect, useRef } from "react"
import type { Dispatch, SetStateAction } from "react"

import {
  WIZARD_PLAN_MESSAGE_ID,
  WIZARD_PUBLISHED_MESSAGE_ID,
  WIZARD_PUBLISHED_TITLE,
  buildPlanFlowSteps,
  buildPublishedJobCard,
  isWizardClosingStage,
  planCardTitleForStage,
  planStepsEqual,
  publishedJobCardsEqual,
  type WizardPublishedJobCardData,
} from "./wizard-plan-card"
import type { WizardStage } from "./wizard-types"
import type { FlowStep } from "@/components/workflow-rail/FlowStepMessage"
import type { LiaChatMessage } from "@/hooks/chat/lia-chat-connection-types"

export interface UseWizardChatCardsOptions {
  /** Current wizard stage (null when no wizard run is active). */
  wizardStage: WizardStage | null
  /** Latest stage payload merged by the wizard reducer. */
  wizardStageData: Record<string, unknown> | null
  /** Setter for the chat feed messages (`LiaChatMessage[]`). */
  setChatMessages: Dispatch<SetStateAction<LiaChatMessage[]>>
}

export function useWizardChatCards(options: UseWizardChatCardsOptions): void {
  const { wizardStage, wizardStageData, setChatMessages } = options

  const planCardInsertedRef = useRef(false)
  const publishedCardInsertedRef = useRef(false)

  // --- Plan card sync ---
  useEffect(() => {
    if (!wizardStage) {
      planCardInsertedRef.current = false
      setChatMessages((prev) => {
        const exists = prev.some((m) => m.id === WIZARD_PLAN_MESSAGE_ID)
        if (!exists) return prev
        return prev.filter((m) => m.id !== WIZARD_PLAN_MESSAGE_ID)
      })
      return
    }
    const flowSteps = buildPlanFlowSteps(wizardStage)
    const planTitle = planCardTitleForStage(wizardStage)
    const completed = isWizardClosingStage(wizardStage)
    setChatMessages((prev) => {
      const exists = prev.some((m) => m.id === WIZARD_PLAN_MESSAGE_ID)
      if (!exists) {
        if (planCardInsertedRef.current) return prev
        planCardInsertedRef.current = true
        const planMsg: LiaChatMessage = {
          id: WIZARD_PLAN_MESSAGE_ID,
          sender: "lia",
          content: planTitle,
          timestamp: new Date().toISOString(),
          metadata: { type: "wizard_plan", flowSteps, completed },
        }
        return [...prev, planMsg]
      }
      // Update existing card without forcing a new array if nothing changed.
      let changed = false
      const next = prev.map((m) => {
        if (m.id !== WIZARD_PLAN_MESSAGE_ID) return m
        const prevSteps = (m.metadata?.flowSteps as FlowStep[] | undefined) ?? []
        const prevCompleted = m.metadata?.completed === true
        if (
          m.content === planTitle &&
          prevCompleted === completed &&
          planStepsEqual(prevSteps, flowSteps)
        ) {
          return m
        }
        changed = true
        return {
          ...m,
          content: planTitle,
          metadata: {
            ...(m.metadata ?? {}),
            type: "wizard_plan",
            flowSteps,
            completed,
          },
        }
      })
      return changed ? next : prev
    })
  }, [wizardStage, setChatMessages])

  // --- Published card injection ---
  useEffect(() => {
    // Reset the dedupe latch on any non-closing stage (including null and a
    // brand-new `intake` after a previous run reached `handoff`). This way a
    // back-to-back wizard run still re-emits its closing card.
    if (!wizardStage || !isWizardClosingStage(wizardStage)) {
      publishedCardInsertedRef.current = false
      return
    }
    const cardData = buildPublishedJobCard(wizardStage, wizardStageData)
    if (!cardData) return
    setChatMessages((prev) => {
      const idx = prev.findIndex((m) => m.id === WIZARD_PUBLISHED_MESSAGE_ID)
      if (idx === -1) {
        if (publishedCardInsertedRef.current) return prev
        publishedCardInsertedRef.current = true
        const publishedMsg: LiaChatMessage = {
          id: WIZARD_PUBLISHED_MESSAGE_ID,
          sender: "lia",
          content: WIZARD_PUBLISHED_TITLE,
          timestamp: new Date().toISOString(),
          metadata: { type: "wizard_published_job", publishedJob: cardData },
        }
        return [...prev, publishedMsg]
      }
      // Same payload re-emitted — keep the existing card to avoid churn.
      const existing = prev[idx]
      const prevData =
        (existing.metadata?.publishedJob as WizardPublishedJobCardData | undefined) ?? null
      if (publishedJobCardsEqual(prevData, cardData)) return prev
      const next = prev.slice()
      next[idx] = {
        ...existing,
        metadata: {
          ...(existing.metadata ?? {}),
          type: "wizard_published_job",
          publishedJob: cardData,
        },
      }
      return next
    })
  }, [wizardStage, wizardStageData, setChatMessages])
}
