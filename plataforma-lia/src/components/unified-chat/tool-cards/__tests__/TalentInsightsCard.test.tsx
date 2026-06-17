/**
 * TalentInsightsCard — unit tests
 *
 * Validates:
 * 1. Renders card with job title and metrics summary
 * 2. CTA button dispatches lia:open_modal with correct detail
 * 3. Handles missing optional metrics gracefully
 *
 * Created 2026-06-17.
 */

import React from "react"
import { render, screen, fireEvent } from "@testing-library/react"
import { TalentInsightsCard, type TalentInsightsCardData } from "../TalentInsightsCard"

const FULL_DATA: TalentInsightsCardData = {
  job_id: "job-123",
  job_title: "Engenheiro de Software Sr.",
  total_candidates: 42,
  conversion_rate: 15.7,
  hiring_probability: 78.3,
}

const MINIMAL_DATA: TalentInsightsCardData = {
  job_id: "job-456",
  job_title: "Analista Financeiro",
}

describe("TalentInsightsCard", () => {
  it("renders job title and metrics when all data provided", () => {
    render(<TalentInsightsCard data={FULL_DATA} />)
    expect(screen.getByText("Talent Pool Insights")).toBeInTheDocument()
    // Check that the subtitle contains the job title and candidate count
    const subtitle = screen.getByText(/Engenheiro de Software Sr\./)
    expect(subtitle).toBeInTheDocument()
    expect(subtitle.textContent).toContain("42 candidatos")
    expect(subtitle.textContent).toContain("16% conversao")
    expect(subtitle.textContent).toContain("78% prob. contratacao")
  })

  it("renders fallback text when no metrics provided", () => {
    render(<TalentInsightsCard data={MINIMAL_DATA} />)
    expect(screen.getByText("Talent Pool Insights")).toBeInTheDocument()
    const subtitle = screen.getByText(/Analista Financeiro/)
    expect(subtitle.textContent).toContain("Dados disponiveis para analise")
  })

  it("dispatches lia:open_modal on CTA click", () => {
    const events: CustomEvent[] = []
    const handler = (e: Event) => events.push(e as CustomEvent)
    window.addEventListener("lia:open_modal", handler)

    render(<TalentInsightsCard data={FULL_DATA} />)
    const button = screen.getByRole("button", { name: /Ver Insights/i })
    fireEvent.click(button)

    expect(events).toHaveLength(1)
    expect(events[0].detail).toEqual({
      modal_id: "talent_pool_insights",
      data: { job_id: "job-123", job_title: "Engenheiro de Software Sr." },
    })

    window.removeEventListener("lia:open_modal", handler)
  })

  it("CTA button is accessible with correct text", () => {
    render(<TalentInsightsCard data={FULL_DATA} />)
    const button = screen.getByRole("button", { name: /Ver Insights/i })
    expect(button).toBeInTheDocument()
    expect(button.getAttribute("type")).toBe("button")
  })
})
