/**
 * Tests — CandidateScoreBadge canonical building block.
 * Covers: returns null on null score, formats (wsi/decimal/percent), color tiers.
 */
import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { CandidateScoreBadge, formatScore, getScoreColor } from "../CandidateScoreBadge"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

describe("CandidateScoreBadge", () => {
  it("returns null when score is null", () => {
    const { container } = render(<CandidateScoreBadge score={null} />)
    expect(container.firstChild).toBeNull()
  })

  it("returns null when score is undefined", () => {
    const { container } = render(<CandidateScoreBadge score={undefined} />)
    expect(container.firstChild).toBeNull()
  })

  it("renders WSI format as X.X/10 (canonical Task #512)", () => {
    render(<CandidateScoreBadge score={8.234} format="wsi" />)
    expect(screen.getByText("8.2/10")).toBeInTheDocument()
  })

  it("renders decimal format as X.X/10", () => {
    render(<CandidateScoreBadge score={7.5} format="decimal" />)
    expect(screen.getByText("7.5/10")).toBeInTheDocument()
  })

  it("renders percent format as X% (legacy)", () => {
    render(<CandidateScoreBadge score={92} format="percent" />)
    expect(screen.getByText("92%")).toBeInTheDocument()
  })

  it("renders label when provided", () => {
    render(<CandidateScoreBadge score={8.2} format="wsi" label="WSI:" />)
    expect(screen.getByText("WSI:")).toBeInTheDocument()
  })
})

describe("getScoreColor (WSI tiers — Task #512)", () => {
  it("WSI score >=7.5 returns success color class", () => {
    const cls = getScoreColor(8.0, "wsi")
    expect(cls).toMatch(/success|green/i)
  })
  it("WSI score 6.0-7.4 returns warning color class", () => {
    const cls = getScoreColor(6.5, "wsi")
    expect(cls).toMatch(/warning|orange|yellow/i)
  })
  it("WSI score <6 returns error color class", () => {
    const cls = getScoreColor(5.0, "wsi")
    expect(cls).toMatch(/error|red/i)
  })
})

describe("formatScore helper", () => {
  it("wsi format always 1 decimal", () => {
    expect(formatScore(8.234, "wsi")).toBe("8.2/10")
    expect(formatScore(10, "wsi")).toBe("10.0/10")
  })
  it("percent format rounds to integer", () => {
    expect(formatScore(92.7, "percent")).toBe("93%")
  })
})
