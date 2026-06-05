/**
 * TDD — CandidatePage dual-mode (F4)
 *
 * Validates that <CandidatePage> supports two render modes:
 *   - mode="modal"  — full-screen overlay, isOpen controls visibility, close button triggers onClose
 *   - mode="page"   — standalone layout (no fixed/overlay), fills content area
 *   - backward compat: mode not provided defaults to modal behaviour
 */
import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { CandidatePage } from "@/components/candidate-page"

vi.mock("next/navigation", () => ({
  useRouter: () => ({ back: vi.fn(), push: vi.fn() }),
  useParams: () => ({ id: "test-123" }),
}))

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

vi.mock("swr", () => ({
  default: () => ({
    data: undefined,
    error: null,
    isLoading: false,
    mutate: vi.fn(),
  }),
}))

vi.mock("@/components/candidate-preview/useCandidatePreviewCore", () => ({
  useCandidatePreviewCore: () => ({
    activeTab: "profile",
    setActiveTab: vi.fn(),
    showLiaModal: false,
    setShowLiaModal: vi.fn(),
    liaChatMessages: [],
    isLiaChatLoading: false,
    liaConversation: [],
    setLiaConversation: vi.fn(),
    sendLiaMessage: vi.fn(),
    opinionsSubTab: "history",
    setOpinionsSubTab: vi.fn(),
    opinionsHistory: [],
    isLoadingHistory: false,
    savedAnalyses: [],
    isLoadingAnalyses: false,
    expandedOpinionId: null,
    setExpandedOpinionId: vi.fn(),
    expandedAnalysisId: null,
    setExpandedAnalysisId: vi.fn(),
    analysisToDelete: null,
    setAnalysisToDelete: vi.fn(),
    copiedItemId: null,
    handleCopyOpinion: vi.fn(),
    handleCopyAnalysis: vi.fn(),
    cleanTextForCopy: vi.fn(),
    showUpdateOpinionAlert: false,
    setShowUpdateOpinionAlert: vi.fn(),
    lastOpinionDate: null,
    generateNewOpinion: vi.fn(),
    isDeletingAnalysis: false,
    handleDeleteAnalysis: vi.fn(),
    showInsufficientDataModal: false,
    setShowInsufficientDataModal: vi.fn(),
    dataRequirements: null,
    handleProceedWithLimitedData: vi.fn(),
    screeningModalOpen: false,
    setScreeningModalOpen: vi.fn(),
    screeningModalData: null,
    setScreeningModalData: vi.fn(),
    discModalOpen: false,
    setDiscModalOpen: vi.fn(),
    discModalData: null,
    setDiscModalData: vi.fn(),
    bigFiveModalOpen: false,
    setBigFiveModalOpen: vi.fn(),
    bigFiveModalCandidate: null,
    setBigFiveModalCandidate: vi.fn(),
    selectedFile: null,
    setSelectedFile: vi.fn(),
    previewType: null,
    setPreviewType: vi.fn(),
    showPreview: false,
    setShowPreview: vi.fn(),
    handleAnalyzeWithLia: vi.fn(),
    formatCurrency: vi.fn(() => "R$ 0"),
    getLanguagesData: vi.fn(() => []),
    hasSalaryData: vi.fn(() => false),
    hasAddressData: vi.fn(() => false),
  }),
}))

vi.mock("@/hooks/candidates/use-candidate-field-update", () => ({
  useCandidateFieldUpdate: () => ({
    updateField: vi.fn(),
    isSaving: vi.fn(() => false),
  }),
}))

vi.mock("@/lib/feature-flags", () => ({
  isFeatureEnabled: () => false,
  FF_CANDIDATE_EDIT: "ff_candidate_edit",
}))

vi.mock("@/components/candidate-page/CandidatePageHeader", () => ({
  CandidatePageHeader: ({ onClose }: { onClose: () => void }) => (
    <header data-testid="candidate-page-header">
      <button data-testid="close-button" onClick={onClose}>Fechar</button>
    </header>
  ),
}))

vi.mock("@/components/candidate-page/CandidatePageSummary", () => ({
  CandidatePageSummary: () => <div data-testid="candidate-page-summary">Summary</div>,
}))

vi.mock("@/components/candidate-preview/CandidatePreviewProfileTab", () => ({
  CandidatePreviewProfileTab: () => <div data-testid="profile-tab">Profile</div>,
}))

vi.mock("@/components/candidate-preview/CandidateActivitiesTab", () => ({
  CandidateActivitiesTab: () => <div data-testid="activities-tab">Activities</div>,
}))

vi.mock("@/components/candidate-preview/CandidateFilesTab", () => ({
  CandidateFilesTab: () => <div data-testid="files-tab">Files</div>,
}))

vi.mock("@/components/candidate-preview/CandidateOpinionsTab", () => ({
  CandidateOpinionsTab: () => <div data-testid="opinions-tab">Opinions</div>,
}))

vi.mock("@/components/candidate-preview/CandidatePreviewModals", () => ({
  CandidatePreviewModals: () => <div data-testid="candidate-modals">Modals</div>,
}))

vi.mock("@/components/candidate-profile/CandidateEditContext", () => ({
  CandidateEditProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useCandidateEdit: () => ({ editable: false, updateField: undefined, isSaving: undefined }),
}))

vi.mock("@/components/ui/tooltip", () => ({
  TooltipProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

const baseCandidate: Record<string, unknown> = {
  id: "cand_001",
  candidateId: "cand_001",
  name: "Maria Souza",
  position: "Product Manager",
  location: "Sao Paulo, SP",
  email: "maria@example.com",
  liaAnalysis: { score: 75 },
}

describe("CandidatePage — dual-mode (F4)", () => {

  it("Teste 1: mode=modal + isOpen=true — renders overlay container (fixed inset-0)", () => {
    const { container } = render(
      <CandidatePage candidate={baseCandidate} mode="modal" isOpen={true} onClose={vi.fn()} />
    )
    const root = container.firstElementChild as HTMLElement
    expect(root).not.toBeNull()
    expect(root.className).toContain("fixed")
    expect(root.className).toContain("inset-0")
  })

  it("Teste 2: mode=page — renders standalone container (no fixed/overlay)", () => {
    const { container } = render(
      <CandidatePage candidate={baseCandidate} mode="page" />
    )
    const root = container.firstElementChild as HTMLElement
    expect(root).not.toBeNull()
    expect(root.className).not.toContain("fixed")
    expect(root.className).not.toContain("inset-0")
    expect(root.className).toContain("min-h-screen")
  })

  it("Teste 3: backward compat — mode not provided defaults to modal (fixed positioning)", () => {
    const { container } = render(
      <CandidatePage candidate={baseCandidate} isOpen={true} onClose={vi.fn()} />
    )
    const root = container.firstElementChild as HTMLElement
    expect(root.className).toContain("fixed")
  })

  it("Teste 4: mode=modal + isOpen=false — renders nothing (null)", () => {
    const { container } = render(
      <CandidatePage candidate={baseCandidate} mode="modal" isOpen={false} />
    )
    expect(container.firstElementChild).toBeNull()
  })

  it("Teste 5: mode=modal — close button calls onClose prop", async () => {
    const onClose = vi.fn()
    render(
      <CandidatePage candidate={baseCandidate} mode="modal" isOpen={true} onClose={onClose} />
    )
    const closeBtn = screen.getByTestId("close-button")
    await userEvent.click(closeBtn)
    expect(onClose).toHaveBeenCalledOnce()
  })

  it("Teste 6: mode=page — onClose defaults to no-op and does not crash on close", async () => {
    render(<CandidatePage candidate={baseCandidate} mode="page" />)
    const closeBtn = screen.queryByTestId("close-button")
    if (closeBtn) {
      await userEvent.click(closeBtn)
    }
    expect(screen.getByTestId("candidate-page-header")).toBeInTheDocument()
  })
})
