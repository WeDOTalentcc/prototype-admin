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
 * Hotfix tests for the LGPD cross-tenant bleed regression flagged in the
 * post-merge architect review of Task A4. The contract is: when `userId`
 * changes mid-session (logout → login, identity hydration finally
 * resolves, recruiter swap on a shared browser, etc.), the previous
 * user's wizard state must NOT be observable through the new identity
 * AND must NOT leak into the new identity's localStorage namespace.
 */
describe("useWizardFlow — identity transitions (LGPD)", () => {
  beforeEach(() => {
    localStorage.clear()
  })
  afterEach(() => {
    localStorage.clear()
  })

  function seedPersistedStage(userId: string, stage: WizardStage) {
    const key = getWizardStorageKey(userId)
    if (!key) throw new Error("test setup: invalid userId")
    localStorage.setItem(
      key,
      JSON.stringify({
        active: true,
        currentStage: stage,
        stageData: { marker: userId },
        completeness: 1,
        requiresApproval: false,
        stageHistory: [stage],
        threadId: null,
        error: null,
      }),
    )
  }

  it("rehydrates from the new namespace when userId switches recruiter A → B", () => {
    seedPersistedStage("user-A", "intake")
    seedPersistedStage("user-B", "calibration")

    const { result, rerender } = renderHook(
      ({ userId }: { userId: string | null }) => useWizardFlow({ userId }),
      { initialProps: { userId: "user-A" } },
    )
    expect(result.current.currentStage).toBe("intake")
    expect(result.current.stageData?.marker).toBe("user-A")

    rerender({ userId: "user-B" })
    expect(result.current.currentStage).toBe("calibration")
    expect(result.current.stageData?.marker).toBe("user-B")
  })

  it("does not write recruiter A's stale state into recruiter B's namespace", () => {
    seedPersistedStage("user-A", "intake")
    // user-B has nothing persisted — must stay empty after the swap.
    const keyB = getWizardStorageKey("user-B")!

    const { rerender } = renderHook(
      ({ userId }: { userId: string | null }) => useWizardFlow({ userId }),
      { initialProps: { userId: "user-A" } },
    )
    rerender({ userId: "user-B" })

    const persistedB = localStorage.getItem(keyB)
    if (persistedB) {
      const parsed = JSON.parse(persistedB) as { stageData?: { marker?: string } }
      expect(parsed.stageData?.marker).not.toBe("user-A")
    }
    // The dispatched REHYDRATE on key-change must have wiped in-memory
    // state down to `initialState` for B (no persisted snapshot exists).
    // i.e. the persist effect either writes nothing (state.active=false →
    // removeItem) or writes B's own state — never A's payload.
  })

  it("resets to initial state on logout (userId → null) so nothing renders downstream", () => {
    seedPersistedStage("user-A", "intake")

    const { result, rerender } = renderHook(
      ({ userId }: { userId: string | null }) => useWizardFlow({ userId }),
      { initialProps: { userId: "user-A" } as { userId: string | null } },
    )
    expect(result.current.currentStage).toBe("intake")

    rerender({ userId: null })
    expect(result.current.currentStage).toBeNull()
    expect(result.current.active).toBe(false)
  })
})
