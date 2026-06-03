import React from "react"
import { describe, it, expect } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"
import ptBR from "../../../../messages/pt-BR.json"
import { AgentActivitySummary } from "../AgentActivitySummary"

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

const ITEMS = [
  { kind: "tool", name: "search_candidates", status: "ok", durationMs: 1200 },
  { kind: "tool", name: "rank_cvs", status: "ok", durationMs: 800 },
]

describe("AgentActivitySummary", () => {
  it("renders nothing when there is no activity", () => {
    const { container } = renderWithIntl(<AgentActivitySummary items={[]} />)
    expect(container).toBeEmptyDOMElement()
  })

  it("shows a collapsed count and expands the tool list on click", () => {
    renderWithIntl(<AgentActivitySummary items={ITEMS} />)
    // collapsed: shows count, total duration (1200+800=2000ms -> 2.0s)
    expect(screen.getByText(/2/)).toBeInTheDocument()
    // tool names hidden until expanded
    expect(screen.queryByText(/search candidates/i)).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole("button"))
    expect(screen.getByText(/search candidates/i)).toBeInTheDocument()
    expect(screen.getByText(/rank cvs/i)).toBeInTheDocument()
  })

  describe("i18n canonical contract", () => {
    it("renders chat.agentActivity keys without MISSING_MESSAGE", () => {
      const errors: unknown[] = []
      renderWithIntl(<AgentActivitySummary items={ITEMS} />, (e) => errors.push(e))
      const missing = errors.filter((e) =>
        String((e as { message?: string })?.message ?? e).includes(
          "MISSING_MESSAGE",
        ),
      )
      expect(missing).toEqual([])
    })
  })
})
