/**
 * useWizardChatCards — owns the non-persisted assistant cards the wizard
 * injects into the chat feed:
 *
 *   1. **Plano de trabalho** card — appears the first time the wizard
 *      reports a stage and stays in sync with `flowSteps`/title until the
 *      wizard resets. At terminal stages (`done`/`handoff`) it stays
 *      visible with all 6 steps marked completed and the title flipped to
 *      "Plano de trabalho — Concluído" (Task #830).
 *
 *   2. **Pipeline template** selection card (Onda 28 — E.8) — injected
 *      whenever the backend surfaces `data.suggestions_data.pipeline_template`
 *      in the wizard payload. The recruiter sees the 5 preset pipelines
 *      with the backend's recommendation highlighted, picks one, and the
 *      hook forwards the choice as a free-text chat reply via
 *      `onSelectTemplate` so LIA's stage_basic_info handler resolves it
 *      with the same NLU path used by the typed answer.
 *
 *   3. **Vaga publicada** closing card — injected once the wizard reaches
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
  WIZARD_TEMPLATE_MESSAGE_ID,
  WIZARD_TEMPLATE_TITLE,
  buildPipelineTemplateCard,
  buildPlanFlowSteps,
  buildPublishedJobCard,
  isWizardClosingStage,
  pipelineTemplateCardsEqual,
  planCardTitleForStage,
  planStepsEqual,
  publishedJobCardsEqual,
  type PipelineTemplateCardData,
  type PipelineTemplateOption,
  type WizardPublishedJobCardData,
} from "./wizard-plan-card"
import type { WizardStage } from "./wizard-types"
import type { FlowStep } from "@/components/unified-chat/FlowStepMessage"
import type { LiaChatMessage } from "@/hooks/chat/lia-chat-connection-types"


export const WIZARD_STAGE_CARD_MESSAGE_ID = "lia-wizard-stage-card"

const STAGE_CARD_STAGES = new Set([
  "intake",
  "jd_enrichment",
  "competency",
  "wsi_questions",
  "calibration",
])

function stageCardDataEqual(
  a: Record<string, unknown> | null,
  b: Record<string, unknown> | null,
): boolean {
  if (a === b) return true
  if (!a || !b) return false
  return JSON.stringify(a) === JSON.stringify(b)
}
export interface UseWizardChatCardsOptions {
  /** Current wizard stage (null when no wizard run is active). */
  wizardStage: WizardStage | null
  /** Latest stage payload merged by the wizard reducer. */
  wizardStageData: Record<string, unknown> | null
  /** Setter for the chat feed messages (`LiaChatMessage[]`). */
  setChatMessages: Dispatch<SetStateAction<LiaChatMessage[]>>
  /**
   * Optional callback fired when the recruiter picks a pipeline template
   * tile from the in-feed selection card. The chat surface should forward
   * the selection as a regular chat message so LIA's NLU resolves it the
   * same way as a typed answer (e.g. "Vou usar o template Técnico").
   * When omitted, the card still renders but tile clicks are no-ops.
   */
  onSelectTemplate?: (option: PipelineTemplateOption) => void
}

export function useWizardChatCards(options: UseWizardChatCardsOptions): void {
  const { wizardStage, wizardStageData, setChatMessages, onSelectTemplate } =
    options

  const planCardInsertedRef = useRef(false)
  const publishedCardInsertedRef = useRef(false)
  const templateCardInsertedRef = useRef(false)

  // Keep the latest `onSelectTemplate` in a ref so the metadata payload
  // stays stable across re-renders (we don't want a parent prop change to
  // cascade into a chat-feed message diff and re-mount the card).
  const onSelectTemplateRef = useRef<typeof onSelectTemplate>(onSelectTemplate)
  useEffect(() => {
    onSelectTemplateRef.current = onSelectTemplate
  }, [onSelectTemplate])

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

  // --- Pipeline template selection card (Onda 28 — E.8) ---
  // Injects the 5-option preset picker as soon as the backend surfaces a
  // `suggestions_data.pipeline_template` block. The card is non-persisted
  // (assistant id `lia-wizard-template-card`) and re-emissions of the
  // same suggestion update in place via `pipelineTemplateCardsEqual` so
  // the card never duplicates. Once the wizard moves past the basic-info
  // stage we drop the card to keep the feed tidy — the recruiter has
  // already picked at that point.
  useEffect(() => {
    const cardData = buildPipelineTemplateCard(wizardStageData)
    if (!cardData) {
      // Reset the latch whenever the suggestion goes away (e.g. wizard
      // moves on, or the recruiter resets) so a fresh suggestion later
      // in the run still injects a brand-new card.
      templateCardInsertedRef.current = false
      setChatMessages((prev) => {
        const exists = prev.some((m) => m.id === WIZARD_TEMPLATE_MESSAGE_ID)
        if (!exists) return prev
        return prev.filter((m) => m.id !== WIZARD_TEMPLATE_MESSAGE_ID)
      })
      return
    }
    setChatMessages((prev) => {
      const idx = prev.findIndex((m) => m.id === WIZARD_TEMPLATE_MESSAGE_ID)
      if (idx === -1) {
        if (templateCardInsertedRef.current) return prev
        templateCardInsertedRef.current = true
        const templateMsg: LiaChatMessage = {
          id: WIZARD_TEMPLATE_MESSAGE_ID,
          sender: "lia",
          content: WIZARD_TEMPLATE_TITLE,
          timestamp: new Date().toISOString(),
          metadata: {
            type: "wizard_template_select",
            templateCard: cardData,
            // Stable thunk via ref — caller swap doesn't churn the message.
            onSelectTemplate: (option: PipelineTemplateOption) => {
              onSelectTemplateRef.current?.(option)
            },
          },
        }
        return [...prev, templateMsg]
      }
      // Same payload re-emitted — keep the existing card to avoid churn.
      const existing = prev[idx]
      const prevData =
        (existing.metadata?.templateCard as
          | PipelineTemplateCardData
          | undefined) ?? null
      if (pipelineTemplateCardsEqual(prevData, cardData)) return prev
      const next = prev.slice()
      next[idx] = {
        ...existing,
        metadata: {
          ...(existing.metadata ?? {}),
          type: "wizard_template_select",
          templateCard: cardData,
        },
      }
      return next
    })
  }, [wizardStageData, setChatMessages])

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


  // --- Stage card injection (inline enriched cards in chat feed) ---
  // When the wizard emits stage data for a card-eligible stage, inject
  // (or update) a single stage card message. The message carries the
  // stage name and full payload so UnifiedMessageList can dispatch to
  // the right card component (WizardIntakeCard, WizardJdCard, etc.).
  const stageCardInsertedRef = useRef(false)
  const prevStageForCardRef = useRef<WizardStage | null>(null)

  useEffect(() => {
    const isCardStage =
      wizardStage != null && STAGE_CARD_STAGES.has(wizardStage)

    // Reset latch on stage transition so the new stage can inject
    if (wizardStage !== prevStageForCardRef.current) {
      stageCardInsertedRef.current = false
      prevStageForCardRef.current = wizardStage
    }

    if (!isCardStage || !wizardStageData) {
      // Reset latch when leaving a card-eligible stage so the next
      // entry re-injects. Keep existing card visible (don't remove —
      // it serves as history of what LIA produced).
      stageCardInsertedRef.current = false
      return
    }

    setChatMessages((prev) => {
      // Find any existing stage card for the CURRENT stage
      const idx = prev.findIndex(
        (m) =>
          m.id === WIZARD_STAGE_CARD_MESSAGE_ID &&
          m.metadata?.wizardStage === wizardStage,
      )

      // Also check if there's a stale card from a DIFFERENT stage
      const staleIdx = prev.findIndex(
        (m) =>
          m.id === WIZARD_STAGE_CARD_MESSAGE_ID &&
          m.metadata?.wizardStage !== wizardStage,
      )

      let base = prev
      // Promote stale card to a permanent ID so it stays as history
      if (staleIdx !== -1) {
        const staleMsg = prev[staleIdx]
        const permanentId = `lia-wizard-stage-${staleMsg.metadata?.wizardStage ?? "unknown"}`
        base = prev.map((m, i) =>
          i === staleIdx ? { ...m, id: permanentId } : m,
        )
      }

      if (idx === -1) {
        // No card for this stage in messages — inject (or re-inject after
        // messages reset on reconnect; functional updater prevents duplicates
        // since the second call's `prev` will already have the card).
        stageCardInsertedRef.current = true
        const msg: LiaChatMessage = {
          id: WIZARD_STAGE_CARD_MESSAGE_ID,
          sender: "lia",
          content: "",
          timestamp: new Date().toISOString(),
          metadata: {
            type: "wizard_stage_card",
            wizardStage,
            wizardStageData,
          },
        }
        return [...base, msg]
      }

      // Update existing card if data changed
      const existing = base[idx]
      const prevData =
        (existing.metadata?.wizardStageData as Record<string, unknown>) ?? null
      if (
        existing.metadata?.wizardStage === wizardStage &&
        stageCardDataEqual(prevData, wizardStageData)
      ) {
        return base
      }

      const next = base.slice()
      next[idx] = {
        ...existing,
        metadata: {
          ...(existing.metadata ?? {}),
          type: "wizard_stage_card",
          wizardStage,
          wizardStageData,
        },
      }
      return next
    })
  }, [wizardStage, wizardStageData, setChatMessages])}
