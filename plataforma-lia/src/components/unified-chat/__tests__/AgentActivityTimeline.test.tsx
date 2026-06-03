import React from "react"
import { describe, it, expect, vi } from "vitest"
import { render, screen, act } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"
import ptBR from "../../../../messages/pt-BR.json"
import { AgentActivityTimeline } from "../AgentActivityTimeline"

// Isolate the unit — stub the fallback sibling.
vi.mock("../ThinkingStepsCard", () => ({
  ThinkingStepsCard: ({ steps }: { steps: string[] }) => (
    <div data-testid="fallback">{steps.length}</div>
  ),
}))

function renderWithIntl(ui: React.ReactNode, onError?: (e: unknown) => void) {
  return render(
    <NextIntlClientProvider
      locale="pt"
      messages={ptBR as Record<string, unknown>}
      onError={onError as never}
    >
      {ui}
    </NextIntlClientProvider>,
  )
}

function emit(detail: Record<string, unknown>) {
  act(() => {
    window.dispatchEvent(new CustomEvent("lia:agent-activity", { detail }))
  })
}

describe("AgentActivityTimeline", () => {
  it("renders fallback ThinkingStepsCard when there is no structured activity", () => {
    renderWithIntl(<AgentActivityTimeline fallbackSteps={["a", "b"]} />)
    expect(screen.getByTestId("fallback")).toHaveTextContent("2")
  })

  it("shows a tool running then completed with duration", () => {
    renderWithIntl(<AgentActivityTimeline fallbackSteps={[]} />)
    emit({ type: "tool_started", name: "search_candidates", tool_id: "r1" })
    expect(screen.getByText(/search candidates/i)).toBeInTheDocument()
    emit({
      type: "tool_finished",
      name: "search_candidates",
      tool_id: "r1",
      status: "ok",
      duration_ms: 1234,
    })
    expect(screen.getByText("1.2s")).toBeInTheDocument()
  })

  it("renders a reasoning step label", () => {
    renderWithIntl(<AgentActivityTimeline fallbackSteps={[]} />)
    emit({ type: "reasoning_step", label: "Analisando a vaga" })
    expect(screen.getByText("Analisando a vaga")).toBeInTheDocument()
  })

  // HITL-critical surface discipline: mount/unmount across turns must not throw
  // or leak the window listener (Rules-of-Hooks + cleanup).
  it("survives unmount + remount without throwing", () => {
    const first = renderWithIntl(<AgentActivityTimeline fallbackSteps={[]} />)
    emit({ type: "tool_started", name: "x", tool_id: "r2" })
    first.unmount()
    // event after unmount must be a no-op (listener cleaned up)
    emit({ type: "tool_started", name: "y", tool_id: "r3" })
    expect(() =>
      renderWithIntl(<AgentActivityTimeline fallbackSteps={[]} />),
    ).not.toThrow()
  })

  describe("i18n canonical contract", () => {
    it("renders chat.agentActivity keys without MISSING_MESSAGE", () => {
      const errors: unknown[] = []
      renderWithIntl(
        <AgentActivityTimeline fallbackSteps={[]} />,
        (e) => errors.push(e),
      )
      emit({ type: "tool_started", name: "x", tool_id: "r4" })
      const missing = errors.filter((e) =>
        String((e as { message?: string })?.message ?? e).includes(
          "MISSING_MESSAGE",
        ),
      )
      expect(missing).toEqual([])
    })
  })
})
