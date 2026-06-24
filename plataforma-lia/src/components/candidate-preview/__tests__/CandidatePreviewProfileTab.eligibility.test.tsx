/**
 * Behavioral tests — CandidatePreviewProfileTab eligibility section
 *
 * Verifies that EligibilityResultsSection is rendered when the candidate has
 * `eligibility_results`, is absent when none exist, and appears before the
 * ProfileLiaOpinionCard (WSI scores/opinions) in the rendered output.
 */
import { describe, it, expect, vi } from "vitest"
import { render, screen, within } from "@testing-library/react"
import { CandidatePreviewProfileTab } from "../CandidatePreviewProfileTab"

// ── Mock heavy child components to keep the test focused on eligibility ──────

vi.mock("@/hooks/company/use-current-company", () => ({
  useCurrentCompany: () => ({ companyId: "test-company-id" }),
}))

vi.mock("@/components/experience-highlight-card", () => ({
  ExperienceHighlightCard: () => <div data-testid="experience-highlight-card" />,
}))

vi.mock("../QualificationMatrixCard", () => ({
  QualificationMatrixCard: () => <div data-testid="qualification-matrix-card" />,
}))

vi.mock("../ProfileLiaOpinionCard", () => ({
  ProfileLiaOpinionCard: () => <div data-testid="profile-lia-opinion-card" />,
}))

vi.mock("../ProfileSkillsMapCard", () => ({
  ProfileSkillsMapCard: () => <div data-testid="profile-skills-map-card" />,
}))

vi.mock("../ProfileExperienceCards", () => ({
  ProfileExperienceCards: () => <div data-testid="profile-experience-cards" />,
}))

vi.mock("../ProfileInfoCards", () => ({
  ProfileInfoCards: () => <div data-testid="profile-info-cards" />,
}))

// ── Shared props ─────────────────────────────────────────────────────────────

const baseProps = {
  jobId: "job-001",
  opinionsData: null,
  isLoadingOpinions: false,
  isAnalyzingWithLia: false,
  lastAnalysisDate: null,
  formatAnalysisDate: () => "",
  handleAnalyzeWithLia: vi.fn(),
  formatCurrency: (v: unknown) => String(v ?? ""),
  languagesData: [],
  hasSalaryData: () => false,
  hasAddressData: () => false,
  getAddressString: () => "",
}

const eligibilityResults = [
  {
    id: "q1",
    question: "Possui disponibilidade para viagens?",
    answer: "Sim",
    passed: true,
    is_eliminatory: true,
  },
  {
    id: "q2",
    question: "Você possui inglês fluente?",
    answer: "Não",
    passed: false,
    is_eliminatory: true,
  },
]

// ── Tests ────────────────────────────────────────────────────────────────────

describe("CandidatePreviewProfileTab — seção de elegibilidade", () => {
  it("exibe EligibilityResultsSection quando candidato tem eligibility_results", () => {
    const candidate = { id: "c1", eligibility_results: eligibilityResults }
    render(<CandidatePreviewProfileTab candidate={candidate} {...baseProps} />)

    expect(screen.getByText("Pré-triagem — Elegibilidade")).toBeInTheDocument()
  })

  it("não exibe EligibilityResultsSection quando candidato não tem eligibility_results", () => {
    const candidate = { id: "c1" }
    render(<CandidatePreviewProfileTab candidate={candidate} {...baseProps} />)

    expect(screen.queryByText("Pré-triagem — Elegibilidade")).not.toBeInTheDocument()
  })

  it("não exibe EligibilityResultsSection quando eligibility_results é array vazio", () => {
    const candidate = { id: "c1", eligibility_results: [] }
    render(<CandidatePreviewProfileTab candidate={candidate} {...baseProps} />)

    expect(screen.queryByText("Pré-triagem — Elegibilidade")).not.toBeInTheDocument()
  })

  it("EligibilityResultsSection aparece antes de ProfileLiaOpinionCard no DOM", () => {
    const candidate = { id: "c1", eligibility_results: eligibilityResults }
    const { container } = render(
      <CandidatePreviewProfileTab candidate={candidate} {...baseProps} />
    )

    const eligibilitySection = container.querySelector('[aria-expanded]')
    const opinionsCard = container.querySelector('[data-testid="profile-lia-opinion-card"]')

    expect(eligibilitySection).not.toBeNull()
    expect(opinionsCard).not.toBeNull()

    // compareDocumentPosition: 4 means eligibilitySection precedes opinionsCard
    const position = eligibilitySection!.compareDocumentPosition(opinionsCard!)
    expect(position & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  })

  it("exibe status correto: candidato eliminado quando alguma pergunta não foi atendida", () => {
    const candidate = { id: "c1", eligibility_results: eligibilityResults }
    render(<CandidatePreviewProfileTab candidate={candidate} {...baseProps} />)

    expect(screen.getByText(/Eliminado/i)).toBeInTheDocument()
  })

  it("exibe status aprovado quando todas as perguntas são atendidas", () => {
    const allPassed = eligibilityResults.map((r) => ({ ...r, passed: true }))
    const candidate = { id: "c1", eligibility_results: allPassed }
    render(<CandidatePreviewProfileTab candidate={candidate} {...baseProps} />)

    expect(screen.getByText(/Todas as 2 perguntas atendidas/)).toBeInTheDocument()
  })
})
