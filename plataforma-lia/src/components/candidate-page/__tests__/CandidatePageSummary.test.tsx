/**
 * Tests — CandidatePageSummary (F9 Item 3, 2-col polish for mode="page").
 *
 * Sticky right-rail summary panel used in <CandidatePage mode="page">. Pure
 * display component — renders identity, canonical WSI badge, optional pipeline
 * stage chip, and contact / link affordances when the underlying candidate
 * object carries them.
 */
import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { CandidatePageSummary } from "../CandidatePageSummary"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string, vars?: Record<string, unknown>) =>
    vars && vars.name ? key + " " + String(vars.name) : key,
}))

const baseCandidate = {
  id: "cand_123",
  candidateId: "cand_123",
  name: "Felipe Ribeiro",
  position: "Senior Engineer",
  location: "São Paulo, BR",
  email: "felipe@example.com",
  phone: "+55 11 99999-0000",
  linkedin_url: "https://linkedin.com/in/felipe",
  github_url: "https://github.com/felipe",
  portfolio_url: "https://felipe.dev",
  liaAnalysis: { score: 82 },
}

describe("CandidatePageSummary", () => {
  it("renders candidate identity (name + ID + position)", () => {
    render(<CandidatePageSummary candidate={baseCandidate} liaScore={82} />)
    expect(screen.getByText("Felipe Ribeiro")).toBeInTheDocument()
    expect(screen.getByText(/ID cand_123/)).toBeInTheDocument()
    expect(screen.getByText("Senior Engineer")).toBeInTheDocument()
  })

  it("renders contact links (mailto + tel) when email + phone present", () => {
    render(<CandidatePageSummary candidate={baseCandidate} liaScore={82} />)
    const email = screen.getByTestId("summary-email-link")
    const phone = screen.getByTestId("summary-phone-link")
    expect(email).toHaveAttribute("href", "mailto:felipe@example.com")
    expect(phone).toHaveAttribute("href", "tel:+55 11 99999-0000")
  })

  it("renders external link buttons (LinkedIn, GitHub, Portfolio) with target=_blank", () => {
    render(<CandidatePageSummary candidate={baseCandidate} liaScore={82} />)
    const linkedin = screen.getByTestId("summary-linkedin-link")
    const github = screen.getByTestId("summary-github-link")
    const portfolio = screen.getByTestId("summary-portfolio-link")
    expect(linkedin).toHaveAttribute("target", "_blank")
    expect(linkedin).toHaveAttribute("rel", "noopener noreferrer")
    expect(github).toHaveAttribute("href", "https://github.com/felipe")
    expect(portfolio).toHaveAttribute("href", "https://felipe.dev")
  })

  it("omits stage chip when candidate has no pipeline stage", () => {
    render(<CandidatePageSummary candidate={baseCandidate} liaScore={82} />)
    expect(screen.queryByText(/Triagem|Entrevista/)).not.toBeInTheDocument()
  })

  it("renders stage chip when candidate.pipeline_stage is set", () => {
    render(
      <CandidatePageSummary
        candidate={{ ...baseCandidate, pipeline_stage: "Triagem" }}
        liaScore={82}
      />,
    )
    expect(screen.getByText("Triagem")).toBeInTheDocument()
  })

  it("hides contact block entirely when no email, phone, location", () => {
    const lean = {
      id: "x",
      candidateId: "x",
      name: "Lean Candidate",
    }
    render(<CandidatePageSummary candidate={lean} liaScore={0} />)
    expect(screen.queryByTestId("summary-email-link")).not.toBeInTheDocument()
    expect(screen.queryByTestId("summary-phone-link")).not.toBeInTheDocument()
  })

  it("hides links block when no external URLs", () => {
    const noLinks = {
      id: "y",
      name: "No Links",
      email: "x@y.com",
    }
    render(<CandidatePageSummary candidate={noLinks} liaScore={50} />)
    expect(screen.queryByTestId("summary-linkedin-link")).not.toBeInTheDocument()
    expect(screen.queryByTestId("summary-github-link")).not.toBeInTheDocument()
    expect(screen.queryByTestId("summary-portfolio-link")).not.toBeInTheDocument()
  })

  it("falls back to current_title/headline when position absent", () => {
    const c = {
      id: "z",
      name: "Headline Only",
      headline: "Building things",
    }
    render(<CandidatePageSummary candidate={c} liaScore={70} />)
    expect(screen.getByText("Building things")).toBeInTheDocument()
  })

  it("displays — when name is empty (LGPD-safe fallback)", () => {
    const c = { id: "anon" }
    render(<CandidatePageSummary candidate={c} liaScore={0} />)
    expect(screen.getByText("—")).toBeInTheDocument()
  })

  it("renders 'Contratado' global-state chip when is_hired=true and no kanban stage", () => {
    const hired = {
      id: "h1",
      name: "Hired Candidate",
      is_hired: true,
      hired_job_title: "Senior Backend",
    }
    render(<CandidatePageSummary candidate={hired} liaScore={70} />)
    const chip = screen.getByTestId("summary-global-state-chip")
    expect(chip).toHaveTextContent("Contratado · Senior Backend")
  })

  it("renders 'Bloqueado' global-state chip when is_blacklisted=true (precedence over hired)", () => {
    const blocked = {
      id: "b1",
      name: "Blocked Candidate",
      is_hired: true,
      is_blacklisted: true,
    }
    render(<CandidatePageSummary candidate={blocked} liaScore={50} />)
    expect(screen.getByText("Bloqueado")).toBeInTheDocument()
    expect(screen.queryByText(/Contratado/)).not.toBeInTheDocument()
  })

  it("does NOT render global-state chip when kanban stage is present (drawer wins)", () => {
    const drawerCtx = {
      id: "d1",
      name: "Drawer Candidate",
      pipeline_stage: "Triagem",
      is_hired: true,
    }
    render(<CandidatePageSummary candidate={drawerCtx} liaScore={70} />)
    expect(screen.getByTestId("summary-stage-chip")).toHaveTextContent("Triagem")
    expect(screen.queryByTestId("summary-global-state-chip")).not.toBeInTheDocument()
  })

  it("renders no chip for active candidates (raw 'active' status is noise)", () => {
    const active = {
      id: "a1",
      name: "Active Candidate",
    }
    render(<CandidatePageSummary candidate={active} liaScore={70} />)
    expect(screen.queryByTestId("summary-stage-chip")).not.toBeInTheDocument()
    expect(screen.queryByTestId("summary-global-state-chip")).not.toBeInTheDocument()
  })
})
