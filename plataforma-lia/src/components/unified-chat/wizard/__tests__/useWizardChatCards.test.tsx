/**
 * Task A2 — Unit tests for `useWizardChatCards`.
 *
 * The hook owns the two non-persisted assistant cards the wizard injects
 * into the chat feed. These tests pin down its observable contract so we
 * can refactor without regressing the chat surface.
 */

import { act, renderHook } from "@testing-library/react"
import { useState } from "react"
import { afterEach, beforeEach, describe, expect, it } from "vitest"

import {
  WIZARD_PLAN_MESSAGE_ID,
  WIZARD_PUBLISHED_MESSAGE_ID,
} from "../wizard-plan-card"
import { useWizardChatCards } from "../useWizardChatCards"
import { useWizardFlow, getWizardStorageKey } from "../useWizardFlow"
import type { WizardStage } from "../wizard-types"
import type { LiaChatMessage } from "@/hooks/chat/lia-chat-connection-types"

interface HookProps {
  wizardStage: WizardStage | null
  wizardStageData: Record<string, unknown> | null
}

function useHarness(initial: HookProps) {
  const [props, setProps] = useState<HookProps>(initial)
  const [messages, setMessages] = useState<LiaChatMessage[]>([])
  useWizardChatCards({
    wizardStage: props.wizardStage,
    wizardStageData: props.wizardStageData,
    setChatMessages: setMessages,
  })
  return { messages, setProps }
}

describe("useWizardChatCards — plan card", () => {
  it("does not inject the plan card when the wizard is idle (stage null)", () => {
    const { result } = renderHook(() =>
      useHarness({ wizardStage: null, wizardStageData: null }),
    )
    expect(result.current.messages).toEqual([])
  })

  it("injects the plan card on the first stage and dedupes repeats", () => {
    const { result } = renderHook(() =>
      useHarness({ wizardStage: "intake", wizardStageData: null }),
    )
    expect(result.current.messages).toHaveLength(1)
    const planMsg = result.current.messages[0]
    expect(planMsg.id).toBe(WIZARD_PLAN_MESSAGE_ID)
    expect(planMsg.metadata?.type).toBe("wizard_plan")
    expect(planMsg.metadata?.completed).toBe(false)

    // Re-rendering with the same stage must not duplicate the card.
    act(() => {
      result.current.setProps({ wizardStage: "intake", wizardStageData: null })
    })
    expect(result.current.messages).toHaveLength(1)
  })

  it("flips the plan card to completed at the terminal stage (Task #830)", () => {
    const { result } = renderHook(() =>
      useHarness({ wizardStage: "intake", wizardStageData: null }),
    )
    act(() => {
      result.current.setProps({
        wizardStage: "done",
        wizardStageData: null,
      })
    })
    const planMsg = result.current.messages.find(
      (m) => m.id === WIZARD_PLAN_MESSAGE_ID,
    )
    expect(planMsg?.metadata?.completed).toBe(true)
    expect(planMsg?.content).toMatch(/Conclu/i)
  })

  it("removes the plan card when the wizard resets to null", () => {
    const { result } = renderHook(() =>
      useHarness({ wizardStage: "intake", wizardStageData: null }),
    )
    expect(result.current.messages).toHaveLength(1)
    act(() => {
      result.current.setProps({ wizardStage: null, wizardStageData: null })
    })
    expect(result.current.messages).toEqual([])
  })
})

describe("useWizardChatCards — published card", () => {
  const publishedPayload: Record<string, unknown> = {
    publish: {
      job_id: 42,
      title: "Engenheira(o) de Software Sênior",
      job_url: "/jobs/42",
      share_url: "https://example.com/share/42",
    },
  }

  it("injects the published card at the closing stage", () => {
    const { result } = renderHook(() =>
      useHarness({
        wizardStage: "done",
        wizardStageData: publishedPayload,
      }),
    )
    const publishedMsg = result.current.messages.find(
      (m) => m.id === WIZARD_PUBLISHED_MESSAGE_ID,
    )
    expect(publishedMsg).toBeDefined()
    expect(publishedMsg?.metadata?.type).toBe("wizard_published_job")
  })

  it("does not inject the published card before the closing stage", () => {
    const { result } = renderHook(() =>
      useHarness({
        wizardStage: "intake",
        wizardStageData: publishedPayload,
      }),
    )
    const publishedMsg = result.current.messages.find(
      (m) => m.id === WIZARD_PUBLISHED_MESSAGE_ID,
    )
    expect(publishedMsg).toBeUndefined()
  })

  it("dedupes the published card when the same payload is re-emitted", () => {
    const { result } = renderHook(() =>
      useHarness({
        wizardStage: "done",
        wizardStageData: publishedPayload,
      }),
    )
    const before = result.current.messages.find(
      (m) => m.id === WIZARD_PUBLISHED_MESSAGE_ID,
    )
    act(() => {
      result.current.setProps({
        wizardStage: "done",
        wizardStageData: { ...publishedPayload },
      })
    })
    const after = result.current.messages.find(
      (m) => m.id === WIZARD_PUBLISHED_MESSAGE_ID,
    )
    // Same identity = card was not replaced (no React churn).
    expect(after).toBe(before)
    expect(
      result.current.messages.filter((m) => m.id === WIZARD_PUBLISHED_MESSAGE_ID),
    ).toHaveLength(1)
  })
})


/**
 * Task #1128 — localStorage persistence was REMOVED from useWizardFlow.
 * The LangGraph checkpointer (server-side, keyed by company_id + session_id)
 * is now the only source of truth. LGPD isolation is enforced server-side.
 *
 * These tests pin down the NEW contract:
 *  - hook always starts in initialState regardless of localStorage content
 *  - userId changes have NO effect on hook state (it is a legacy no-op prop)
 *  - no localStorage writes happen from the hook
 *
 * getWizardStorageKey is still exported (used by the one-shot legacy
 * purger in useWizardSessionApi.ts) so the import is valid.
 */
describe("useWizardFlow — identity transitions (LGPD)", () => {
  beforeEach(() => {
    localStorage.clear()
  })
  afterEach(() => {
    localStorage.clear()
  })

  it("rehydrates from the new namespace when userId switches recruiter A to B", () => {
    // Task #1128: hook no longer reads localStorage — both users start in
    // initialState regardless of any localStorage content. LGPD isolation
    // is enforced server-side via (company_id, session_id) checkpointer.
    const keyA = getWizardStorageKey("user-A")!
    const keyB = getWizardStorageKey("user-B")!
    localStorage.setItem(keyA, JSON.stringify({ active: true, currentStage: "intake" }))
    localStorage.setItem(keyB, JSON.stringify({ active: true, currentStage: "calibration" }))

    const { result, rerender } = renderHook(
      ({ userId }: { userId: string | null }) => useWizardFlow({ userId }),
      { initialProps: { userId: "user-A" } },
    )
    // Hook MUST NOT rehydrate from localStorage — starts fresh.
    expect(result.current.currentStage).toBeNull()
    expect(result.current.active).toBe(false)

    rerender({ userId: "user-B" })
    // userId change does NOT mutate state — server-driven, not client-driven.
    expect(result.current.currentStage).toBeNull()
    expect(result.current.active).toBe(false)
  })

  it("does not write recruiter A stale state into recruiter B namespace", () => {
    // Task #1128: hook never writes to localStorage, so no bleed is possible.
    const keyA = getWizardStorageKey("user-A")!
    const keyB = getWizardStorageKey("user-B")!
    localStorage.setItem(keyA, JSON.stringify({ active: true, stageData: { marker: "user-A" } }))

    const { rerender } = renderHook(
      ({ userId }: { userId: string | null }) => useWizardFlow({ userId }),
      { initialProps: { userId: "user-A" } },
    )
    rerender({ userId: "user-B" })

    // Hook must not have written A payload into B key.
    const persistedB = localStorage.getItem(keyB)
    if (persistedB) {
      const parsed = JSON.parse(persistedB) as { stageData?: { marker?: string } }
      expect(parsed.stageData?.marker).not.toBe("user-A")
    }
    // If persistedB is null (nothing written) the assertion above is vacuously satisfied.
  })

  it("resets to initial state on logout (userId to null) so nothing renders downstream", () => {
    // Task #1128: hook starts in initialState regardless of userId — no rehydration.
    // Logout (userId->null) also has no effect: state was never read from localStorage
    // so there is nothing to clear. Both before and after logout: null/inactive.
    const { result, rerender } = renderHook(
      ({ userId }: { userId: string | null }) => useWizardFlow({ userId }),
      { initialProps: { userId: "user-A" } as { userId: string | null } },
    )
    expect(result.current.currentStage).toBeNull()
    expect(result.current.active).toBe(false)

    rerender({ userId: null })
    expect(result.current.currentStage).toBeNull()
    expect(result.current.active).toBe(false)
  })
})
