/**
 * Tests — CandidatesTableArea component (Apify enrichment banner)
 *
 * Task #401: cover the banner added by Task #399 that surfaces how many
 * candidates were enriched via Apify in the current search. The banner must:
 * - render with `data-testid="enrichment-attempted-banner"` only when
 *   `enrichmentAttempted` is provided and greater than zero
 * - stay hidden when `enrichmentAttempted` is undefined or zero
 * - stay hidden while `isEnrichingContacts` is true (the enriching banner wins)
 */
/** @vitest-environment jsdom */
import React from "react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string, params?: Record<string, unknown>) =>
    params ? `${key}:${JSON.stringify(params)}` : key,
}))

vi.mock("@/components/ui/button", () => ({
  Button: ({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) => (
    <button onClick={onClick}>{children}</button>
  ),
}))
vi.mock("@/components/ui/chip", () => ({
  Chip: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
}))
vi.mock("@/components/tables", () => ({
  UnifiedCandidateTable: () => <div data-testid="unified-table" />,
}))
vi.mock("../CandidatesLoadMoreFooter", () => ({
  CandidatesLoadMoreFooter: () => <div data-testid="load-more-footer" />,
}))

import { CandidatesTableArea, type CandidatesTableAreaProps } from "../CandidatesTableArea"
import type { Candidate } from "../types"

const makeCandidate = (id: string): Candidate => ({
  id,
  candidateId: id,
  name: `Candidate ${id}`,
})

const makeProps = (
  overrides: Partial<CandidatesTableAreaProps> = {}
): CandidatesTableAreaProps => {
  const candidates = [makeCandidate("c1"), makeCandidate("c2")]
  return {
    sortedCandidates: candidates,
    selectedCandidatesForBatch: new Set<string>(),
    isLoading: false,
    error: null,
    onRetry: vi.fn(),
    visibleCandidates: candidates,
    visibleTableColumns: [],
    columnWidths: {},
    setColumnWidths: vi.fn(),
    setTableColumns: vi.fn(),
    pinnedCandidates: new Set<string>(),
    favorites: new Set<string>(),
    sortBy: "name",
    sortOrder: "asc",
    setSortBy: vi.fn(),
    setSortOrder: vi.fn(),
    setSelectedCandidatesForBatch: vi.fn(),
    onCandidateClick: vi.fn(),
    onTogglePin: vi.fn(),
    onToggleFavorite: vi.fn(),
    renderCellValue: () => null,
    tableContainerRef: { current: null } as React.RefObject<HTMLDivElement>,
    showSearchResults: false,
    currentPage: 1,
    setCurrentPage: vi.fn(),
    itemsPerPage: 20,
    getPaginatedCandidates: () => ({ total: candidates.length, totalPages: 1 }),
    clearAllFilters: vi.fn(),
    displayedResultsCount: candidates.length,
    isLoadingMore: false,
    onLoadMore: vi.fn(),
    ...overrides,
  }
}

describe("CandidatesTableArea — enrichment banner (Task #401)", () => {
  beforeEach(() => vi.clearAllMocks())

  it("renders the enrichment banner when enrichmentAttempted > 0", () => {
    render(<CandidatesTableArea {...makeProps({ enrichmentAttempted: 3 })} />)
    expect(screen.getByTestId("enrichment-attempted-banner")).toBeTruthy()
  })

  it("does not render the banner when enrichmentAttempted is undefined", () => {
    render(<CandidatesTableArea {...makeProps()} />)
    expect(screen.queryByTestId("enrichment-attempted-banner")).toBeNull()
  })

  it("does not render the banner when enrichmentAttempted is 0", () => {
    render(<CandidatesTableArea {...makeProps({ enrichmentAttempted: 0 })} />)
    expect(screen.queryByTestId("enrichment-attempted-banner")).toBeNull()
  })

  it("suppresses the banner while contacts are being enriched", () => {
    render(
      <CandidatesTableArea
        {...makeProps({ enrichmentAttempted: 5, isEnrichingContacts: true })}
      />
    )
    expect(screen.queryByTestId("enrichment-attempted-banner")).toBeNull()
  })

  it("includes the count and total in the banner translation params", () => {
    render(<CandidatesTableArea {...makeProps({ enrichmentAttempted: 4 })} />)
    const banner = screen.getByTestId("enrichment-attempted-banner")
    expect(banner.textContent).toContain('"count":4')
    expect(banner.textContent).toContain('"total":2')
  })
})
