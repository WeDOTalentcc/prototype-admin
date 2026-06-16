/**
 * Task #839 — component coverage for the Done stage card "Vaga publicada".
 *
 * The Scheduling-stage audit (`audit-criacao-vaga-2026-04-26.md`,
 * finding L-04) flagged that the `Done` stage only has integration + e2e
 * coverage — no component test that pins the visible contract of the
 * closing card injected into the chat feed. This file complements the
 * existing `WizardPlanFeedCard` test (Task #835) by covering the second
 * half of the Done state: the "Vaga publicada" card itself.
 *
 * The pure data builder (`buildPublishedJobCard`) is already covered by
 * `wizard-plan-card.test.ts`, so here we focus on rendering: the success
 * banner, the headline fallback, the optional handoff link button, and
 * the optional share link.
 */
import React from "react"
import { describe, it, expect, afterEach } from "vitest"
import { render, screen, cleanup, within } from "@testing-library/react"

import { WizardPublishedJobCard } from "../WizardPublishedJobCard"
import type { WizardPublishedJobCardData } from "../wizard-plan-card"

afterEach(() => {
  cleanup()
})

const baseData: WizardPublishedJobCardData = {
  jobId: 123,
  title: "Engenheira de Software Sênior",
  url: "/jobs/123",
  shareLink: null,
}

describe("WizardPublishedJobCard — Done-stage closing card (Task #839)", () => {
  it("renders the success banner, the recruiter-facing job title and the ID", () => {
    // The card uses an `<a>` LinkComponent so the test doesn't need a
    // Next router context — same escape hatch the storybook setup uses.
    render(<WizardPublishedJobCard data={baseData} LinkComponent="a" />)

    const card = screen.getByTestId("wizard-published-card")
    expect(card).toBeInTheDocument()
    expect(card).toHaveAttribute("role", "status")
    expect(card).toHaveAttribute("aria-live", "polite")

    expect(within(card).getByText("Vaga publicada")).toBeInTheDocument()
    expect(within(card).getByText("Engenheira de Software Sênior")).toBeInTheDocument()
    expect(within(card).getByText(/ID 123/)).toBeInTheDocument()
  })

  it("renders the internal job-page link when `url` is provided", () => {
    render(<WizardPublishedJobCard data={baseData} LinkComponent="a" />)

    const link = screen.getByTestId("wizard-published-job-link")
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute("href", "/jobs/123")
    expect(link).toHaveTextContent(/Abrir página da vaga/i)
  })

  it("hides both the internal link and the share link when neither URL is present", () => {
    render(
      <WizardPublishedJobCard
        data={{ ...baseData, url: null }}
        LinkComponent="a"
      />,
    )

    expect(screen.queryByTestId("wizard-published-job-link")).toBeNull()
    expect(screen.queryByText(/Link de compartilhamento/i)).toBeNull()
  })

  it("renders the share link when provided and opens it in a new tab", () => {
    render(
      <WizardPublishedJobCard
        data={{ ...baseData, shareLink: "https://share.example/abc" }}
        LinkComponent="a"
      />,
    )

    const shareLink = screen.getByRole("link", { name: /Link de compartilhamento/i })
    expect(shareLink).toHaveAttribute("href", "https://share.example/abc")
    expect(shareLink).toHaveAttribute("target", "_blank")
    expect(shareLink).toHaveAttribute("rel", expect.stringContaining("noopener"))
  })

  it("falls back to the headline 'Vaga publicada' when the title is null and omits the ID line when jobId is null", () => {
    render(
      <WizardPublishedJobCard
        data={{ jobId: null, title: null, url: null, shareLink: null }}
        LinkComponent="a"
      />,
    )

    const card = screen.getByTestId("wizard-published-card")
    // Both the badge AND the headline should read "Vaga publicada" — the
    // card stays informative even when the backend couldn't fetch any
    // detail beyond the closing-stage signal.
    expect(within(card).getAllByText("Vaga publicada").length).toBeGreaterThanOrEqual(2)
    expect(within(card).queryByText(/^ID /)).toBeNull()
  })
})
