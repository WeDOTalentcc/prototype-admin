import React from "react"
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
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

function wrap(ui: React.ReactNode, onError?: (e: unknown) => void) {
  return (
    <NextIntlClientProvider
      locale="pt"
      messages={ptBR as Record<string, unknown>}
      onError={onError as never}
    >
      {ui}
    </NextIntlClientProvider>
  )
}

function emit(detail: Record<string, unknown>) {
  act(() => {
    window.dispatchEvent(new CustomEvent("lia:agent-activity", { detail }))
  })
}

// The timeline reveals queued steps on an adaptive cadence (≤420ms). Advancing
// well past one beat flushes the next reveal deterministically.
function tick(ms = 600) {
  act(() => {
    vi.advanceTimersByTime(ms)
  })
}

describe("AgentActivityTimeline", () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })
  afterEach(() => {
    vi.clearAllTimers()
    vi.useRealTimers()
  })

  it("renders fallback ThinkingStepsCard when there is no structured activity", () => {
    renderWithIntl(<AgentActivityTimeline fallbackSteps={["a", "b"]} />)
    expect(screen.getByTestId("fallback")).toHaveTextContent("2")
  })

  it("renders nothing when empty and showFallback is false (answer streaming)", () => {
    const { container } = renderWithIntl(
      <AgentActivityTimeline fallbackSteps={["a"]} showFallback={false} />,
    )
    expect(container).toBeEmptyDOMElement()
  })

  it("reveals a queued reasoning step after the cadence beat (not synchronously)", () => {
    renderWithIntl(<AgentActivityTimeline fallbackSteps={[]} />)
    emit({ type: "reasoning_step", label: "Analisando a vaga" })
    // queued — not visible immediately (paced reveal, no flash)
    expect(screen.queryByText("Analisando a vaga")).not.toBeInTheDocument()
    tick()
    expect(screen.getByText("Analisando a vaga")).toBeInTheDocument()
  })

  it("shows a tool running then patches it to completed with duration", () => {
    renderWithIntl(<AgentActivityTimeline fallbackSteps={[]} />)
    emit({ type: "tool_started", name: "search_candidates", tool_id: "r1" })
    tick()
    // tool name is localized via activity-labels (pt → "Buscando candidatos")
    expect(screen.getByText("Buscando candidatos")).toBeInTheDocument()
    emit({
      type: "tool_finished",
      name: "search_candidates",
      tool_id: "r1",
      status: "ok",
      duration_ms: 1234,
    })
    expect(screen.getByText("1.2s")).toBeInTheDocument()
  })

  it("dedupes a repeated tool_started for the same tool_id", () => {
    renderWithIntl(<AgentActivityTimeline fallbackSteps={[]} />)
    emit({ type: "tool_started", name: "rank_cvs", tool_id: "dup" })
    emit({ type: "tool_started", name: "rank_cvs", tool_id: "dup" })
    tick()
    expect(screen.getAllByText(/rank cvs/i)).toHaveLength(1)
  })

  it("does not flicker a sub-second tool: settled-in-queue reveals already done", () => {
    renderWithIntl(<AgentActivityTimeline fallbackSteps={[]} />)
    // finish lands before the queued start is ever revealed
    emit({ type: "tool_started", name: "fast_tool", tool_id: "f1" })
    emit({
      type: "tool_finished",
      name: "fast_tool",
      tool_id: "f1",
      status: "ok",
      duration_ms: 90,
    })
    tick()
    expect(screen.getByText(/fast tool/i)).toBeInTheDocument()
    expect(screen.getByText("90ms")).toBeInTheDocument()
  })

  describe("graceful conclusion (completed → onFinished)", () => {
    it("paces still-queued steps out one-by-one after completion (no dump), then calls onFinished after they drain + grace", () => {
      const onFinished = vi.fn()
      const view = renderWithIntl(
        <AgentActivityTimeline
          fallbackSteps={[]}
          completed={false}
          onFinished={onFinished}
        />,
      )
      emit({ type: "reasoning_step", label: "Passo um" })
      emit({ type: "reasoning_step", label: "Passo dois" })
      emit({ type: "reasoning_step", label: "Passo três" })
      // turn ends before the queue has drained
      view.rerender(
        wrap(
          <AgentActivityTimeline
            fallbackSteps={[]}
            completed={true}
            onFinished={onFinished}
          />,
        ),
      )
      // NOT dumped synchronously — the held answer gives the timeline room to
      // play the remaining steps out one at a time (the "written-out" feel).
      expect(screen.queryByText("Passo um")).not.toBeInTheDocument()
      // first step appears on its cadence beat, the rest still pending
      tick(500)
      expect(screen.getByText("Passo um")).toBeInTheDocument()
      expect(screen.queryByText("Passo três")).not.toBeInTheDocument()
      // hand-off only after every step has been revealed + the grace window
      expect(onFinished).not.toHaveBeenCalled()
      tick(2000)
      expect(screen.getByText("Passo dois")).toBeInTheDocument()
      expect(screen.getByText("Passo três")).toBeInTheDocument()
      expect(onFinished).toHaveBeenCalledTimes(1)
    })

    it("back-to-back turn within the grace window does not mix old steps in", () => {
      const onFinished = vi.fn()
      const view = renderWithIntl(
        <AgentActivityTimeline
          fallbackSteps={[]}
          completed={false}
          onFinished={onFinished}
        />,
      )
      // turn 1
      emit({ type: "reasoning_step", label: "Turno um passo" })
      tick()
      expect(screen.getByText("Turno um passo")).toBeInTheDocument()
      // turn 1 concludes
      view.rerender(
        wrap(
          <AgentActivityTimeline
            fallbackSteps={[]}
            completed={true}
            onFinished={onFinished}
          />,
        ),
      )
      // a new turn starts BEFORE the 750ms grace elapses → completed flips back
      view.rerender(
        wrap(
          <AgentActivityTimeline
            fallbackSteps={[]}
            completed={false}
            onFinished={onFinished}
          />,
        ),
      )
      // full reset: turn 1's step is gone, only turn 2's step shows
      emit({ type: "reasoning_step", label: "Turno dois passo" })
      tick()
      expect(screen.queryByText("Turno um passo")).not.toBeInTheDocument()
      expect(screen.getByText("Turno dois passo")).toBeInTheDocument()
      // the stale onFinished from turn 1 was cancelled (no premature hand-off)
      tick(800)
      expect(onFinished).not.toHaveBeenCalled()
    })

    it("new turn that starts while the previous turn is still draining does not mix old steps in", () => {
      const onFinished = vi.fn()
      const view = renderWithIntl(
        <AgentActivityTimeline
          fallbackSteps={[]}
          completed={false}
          onFinished={onFinished}
        />,
      )
      // turn 1 queues several steps but they have NOT all been revealed yet
      emit({ type: "reasoning_step", label: "Velho passo um" })
      emit({ type: "reasoning_step", label: "Velho passo dois" })
      emit({ type: "reasoning_step", label: "Velho passo três" })
      // turn 1 concludes — pacing begins (queue still draining, phase NOT yet done)
      view.rerender(
        wrap(
          <AgentActivityTimeline
            fallbackSteps={[]}
            completed={true}
            onFinished={onFinished}
          />,
        ),
      )
      // a brand-new turn starts mid-drain (before the queue empties / grace fires)
      view.rerender(
        wrap(
          <AgentActivityTimeline
            fallbackSteps={[]}
            completed={false}
            onFinished={onFinished}
          />,
        ),
      )
      // full reset: none of turn 1's queued steps survive into turn 2
      emit({ type: "reasoning_step", label: "Novo passo" })
      tick(2000)
      expect(screen.queryByText("Velho passo um")).not.toBeInTheDocument()
      expect(screen.queryByText("Velho passo dois")).not.toBeInTheDocument()
      expect(screen.queryByText("Velho passo três")).not.toBeInTheDocument()
      expect(screen.getByText("Novo passo")).toBeInTheDocument()
      // the stale onFinished from turn 1 was cancelled (no premature hand-off)
      expect(onFinished).not.toHaveBeenCalled()
    })

    it("a late event after completion is dropped and never blocks onFinished", () => {
      const onFinished = vi.fn()
      const view = renderWithIntl(
        <AgentActivityTimeline
          fallbackSteps={[]}
          completed={false}
          onFinished={onFinished}
        />,
      )
      emit({ type: "tool_started", name: "trail_tool", tool_id: "t1" })
      tick()
      view.rerender(
        wrap(
          <AgentActivityTimeline
            fallbackSteps={[]}
            completed={true}
            onFinished={onFinished}
          />,
        ),
      )
      // trailing event of the concluded turn arrives during the grace window
      emit({ type: "reasoning_step", label: "Evento atrasado" })
      // dropped — terminal frame is untouched, hand-off still fires after grace
      expect(screen.queryByText("Evento atrasado")).not.toBeInTheDocument()
      tick(800)
      expect(onFinished).toHaveBeenCalledTimes(1)
    })

    it("settles a still-running tool spinner on completion", () => {
      const view = renderWithIntl(
        <AgentActivityTimeline fallbackSteps={[]} completed={false} />,
      )
      emit({ type: "tool_started", name: "slow_tool", tool_id: "s1" })
      tick()
      view.rerender(
        wrap(<AgentActivityTimeline fallbackSteps={[]} completed={true} />),
      )
      // terminal frame summarizes the single action (no stuck spinner / no throw)
      expect(screen.getByText(/slow tool/i)).toBeInTheDocument()
    })
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
      renderWithIntl(<AgentActivityTimeline fallbackSteps={[]} />, (e) =>
        errors.push(e),
      )
      emit({ type: "tool_started", name: "x", tool_id: "r4" })
      tick()
      const missing = errors.filter((e) =>
        String((e as { message?: string })?.message ?? e).includes(
          "MISSING_MESSAGE",
        ),
      )
      expect(missing).toEqual([])
    })
  })
})
