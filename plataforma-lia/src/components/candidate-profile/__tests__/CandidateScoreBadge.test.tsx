/**
 * Tests -- CandidateScoreBadge canonical building block.
 * F1 mandatory: 3-tier colors, null renders dash, score=10 safe, NEVER /100.
 */
import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { CandidateScoreBadge, formatScore, getScoreColor } from "../CandidateScoreBadge"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

describe("CandidateScoreBadge -- F1 mandatory (WSI 0-10 canonical)", () => {
  it("score=8.5 wsi renders green tier", () => {
    const { container } = render(<CandidateScoreBadge score={8.5} format="wsi" />)
    expect(screen.getByText("8.5/10")).toBeInTheDocument()
    const el = container.firstChild as HTMLElement
    expect(el.className).toMatch(/success|green/i)
  })

  it("score=6.5 wsi renders warning tier", () => {
    const { container } = render(<CandidateScoreBadge score={6.5} format="wsi" />)
    expect(screen.getByText("6.5/10")).toBeInTheDocument()
    const el = container.firstChild as HTMLElement
    expect(el.className).toMatch(/warning|yellow|orange/i)
  })

  it("score=5.0 wsi renders error tier", () => {
    const { container } = render(<CandidateScoreBadge score={5.0} format="wsi" />)
    expect(screen.getByText("5.0/10")).toBeInTheDocument()
    const el = container.firstChild as HTMLElement
    expect(el.className).toMatch(/error|red/i)
  })

  it("score=null renders dash em with gray class", () => {
    const { container } = render(<CandidateScoreBadge score={null} format="wsi" />)
    expect(screen.getByText("—")).toBeInTheDocument()
    const el = container.firstChild as HTMLElement
    expect(el.className).toMatch(/gray|secondary|muted/i)
  })

  it("score=undefined renders dash em with gray class", () => {
    const { container } = render(<CandidateScoreBadge score={undefined} format="wsi" />)
    expect(screen.getByText("—")).toBeInTheDocument()
    const el = container.firstChild as HTMLElement
    expect(el.className).toMatch(/gray|secondary|muted/i)
  })

  it("score=10 renders without crash", () => {
    render(<CandidateScoreBadge score={10} format="wsi" />)
    expect(screen.getByText("10.0/10")).toBeInTheDocument()
  })

  it("NEVER renders /100 in any format", () => {
    const { container: c1 } = render(<CandidateScoreBadge score={8.5} format="wsi" />)
    expect(c1.textContent).not.toContain("/100")
    const { container: c2 } = render(<CandidateScoreBadge score={75} format="percent" />)
    expect(c2.textContent).not.toContain("/100")
  })
})

describe("CandidateScoreBadge -- original format/render", () => {
  it("WSI format renders X.X/10 (Task #512)", () => {
    render(<CandidateScoreBadge score={8.234} format="wsi" />)
    expect(screen.getByText("8.2/10")).toBeInTheDocument()
  })

  it("decimal format renders X.X/10", () => {
    render(<CandidateScoreBadge score={7.5} format="decimal" />)
    expect(screen.getByText("7.5/10")).toBeInTheDocument()
  })

  it("percent format renders X% (legacy)", () => {
    render(<CandidateScoreBadge score={92} format="percent" />)
    expect(screen.getByText("92%")).toBeInTheDocument()
  })

  it("renders label when provided", () => {
    render(<CandidateScoreBadge score={8.2} format="wsi" label="WSI:" />)
    expect(screen.getByText("WSI:")).toBeInTheDocument()
  })
})

describe("getScoreColor WSI tiers", () => {
  it("score >=7.5 returns success class", () => {
    expect(getScoreColor(8.0, "wsi")).toMatch(/success|green/i)
  })
  it("score 6.0-7.4 returns warning class", () => {
    expect(getScoreColor(6.5, "wsi")).toMatch(/warning|orange|yellow/i)
  })
  it("score <6 returns error class", () => {
    expect(getScoreColor(5.0, "wsi")).toMatch(/error|red/i)
  })
})

describe("formatScore helper", () => {
  it("wsi format 1 decimal", () => {
    expect(formatScore(8.234, "wsi")).toBe("8.2/10")
    expect(formatScore(10, "wsi")).toBe("10.0/10")
  })
  it("percent format rounds", () => {
    expect(formatScore(92.7, "percent")).toBe("93%")
  })
})
