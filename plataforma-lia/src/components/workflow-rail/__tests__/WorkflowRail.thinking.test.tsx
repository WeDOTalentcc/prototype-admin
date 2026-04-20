/**
 * Tests — WorkflowRail "thinking" pulse (Task #655)
 *
 * Regression coverage for the workflow:thinking → WorkflowRail pulse wiring.
 * The live-thinking feedback has silently regressed twice; this test pins
 * down the contract so the next regression fails loudly.
 *
 * Flow exercised:
 *   1. Render WorkflowRail (collapsed ball view) with a seeded campaign entry.
 *   2. Dispatch window CustomEvent('workflow:thinking', { detail: { id, isThinking: true } }).
 *      → useWorkflowRail flips entry.isThinking, WorkflowRail renders the
 *        Loader2 spinner + animate-ping pulse ring on the floating ball.
 *   3. Dispatch the same event with isThinking: false.
 *      → Spinner + pulse ring disappear; the Compass icon returns.
 */
import React from "react"
import { act, render } from "@testing-library/react"
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest"

// ── Mocks ────────────────────────────────────────────────────────────────────

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

// Force the rail into the collapsed "ball" view so the test exercises the
// most distinctive thinking indicator (the animate-ping pulse ring), and
// avoids unrelated layout effects from the expanded chip strip.
vi.mock("@/stores/workflow-rail-store", () => {
  const state = {
    enabled: true,
    expanded: false,
    position: null as { x: number; y: number } | null,
    setExpanded: vi.fn(),
    setPosition: vi.fn(),
  }
  return {
    useWorkflowRailStore: <T,>(selector: (s: typeof state) => T) => selector(state),
  }
})

vi.mock("@/hooks/useActiveChatPresence", () => ({
  useActiveChatPresence: () => ({
    mode: "sidebar" as const,
    isShowingReels: false,
    isChatVisible: false,
    focusChat: vi.fn(),
  }),
}))

// ── Imports after mocks ──────────────────────────────────────────────────────

import WorkflowRail from "../WorkflowRail"

// ── Test ─────────────────────────────────────────────────────────────────────

describe("WorkflowRail — workflow:thinking pulse", () => {
  beforeEach(() => {
    // useWorkflowRail loads initial entries from the API on mount; return an
    // empty payload so the test starts from a clean slate.
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ data: [] }), { status: 200 })
      ),
    )
    // No NEXT_PUBLIC_RAILS_WS_URL → useWorkflowRail falls back to polling
    // and never opens a real socket during the test.
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  it("renders the spinner and pulse ring while LIA is thinking, and removes them when done", async () => {
    const { container } = render(
      <WorkflowRail userId="user-1" onNavigate={vi.fn()} onCreateJob={vi.fn()} />
    )

    const ENTRY_ID = "entry-thinking-1"

    // Wait for the initial loadEntries() fetch to resolve and flush its
    // setEntries() before seeding — otherwise the empty API response would
    // overwrite our seeded campaign entry (loadEntries keeps only `search`
    // entries from the previous state).
    await act(async () => {
      await Promise.resolve()
      await Promise.resolve()
    })

    // Seed an entry through the same window event the chat uses, so the test
    // covers the real listener wiring (not just an internal state setter).
    await act(async () => {
      window.dispatchEvent(
        new CustomEvent("workflow:started", {
          detail: { id: ENTRY_ID, type: "campaign", label: "Vaga teste", stage: "sourcing" },
        }),
      )
    })

    // Sanity: the rail is now mounted (entries.length > 0 means the
    // hasEntries early-return doesn't fire and the ball is rendered).
    expect(container.querySelector('button[aria-label^="Abrir trilho"]')).not.toBeNull()

    // Initial state: no thinking → no animate-ping pulse ring on the ball.
    expect(container.querySelector(".animate-ping")).toBeNull()
    expect(container.querySelector(".animate-spin")).toBeNull()

    // 1. Flip on: dispatch workflow:thinking with isThinking=true.
    await act(async () => {
      window.dispatchEvent(
        new CustomEvent("workflow:thinking", {
          detail: { id: ENTRY_ID, isThinking: true },
        }),
      )
    })

    // The ball now shows the Loader2 (animate-spin) + the animate-ping ring.
    expect(container.querySelector(".animate-spin")).not.toBeNull()
    expect(container.querySelector(".animate-ping")).not.toBeNull()

    // 2. Flip off: dispatch workflow:thinking with isThinking=false.
    await act(async () => {
      window.dispatchEvent(
        new CustomEvent("workflow:thinking", {
          detail: { id: ENTRY_ID, isThinking: false },
        }),
      )
    })

    // Spinner + pulse ring are gone.
    expect(container.querySelector(".animate-spin")).toBeNull()
    expect(container.querySelector(".animate-ping")).toBeNull()
  })
})
