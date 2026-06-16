/**
 * Sensor: JobInfoGeralSection visibility canonical contract.
 *
 * Plan canonical: ~/.claude/plans/jolly-roaming-moler.md (Sprint 1 RBAC)
 * Skill: harness-engineering (sensor computacional)
 *
 * Verifica:
 * - Options do <select> usam valores CANONICAL lowercase (public/internal/confidential)
 * - NÃO usa valores PT capitalizado (Pública/Interna/Confidencial) que quebravam backend
 * - access_list UI aparece SÓ quando visibility === "confidential"
 *
 * Sprint 1 RBAC bug histórico: <option value="Pública"> ≠ backend canonical "public"
 * → silent save failure → 0 vagas confidenciais persistidas (audit DB 2026-05-25).
 */

import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import "@testing-library/jest-dom/vitest"
import { JobInfoGeralSection } from "../JobInfoGeralSection"

vi.mock("@/hooks/jobs/use-job-metadata", () => ({
  useJobStatuses: () => ({ options: [], isLoading: false }),
  useJobPriorities: () => ({ options: [], isLoading: false }),
  useJobUrgencyLevels: () => ({ options: [], isLoading: false }),
  useJobWorkplaceTypes: () => ({ options: [], isLoading: false }),
  useJobEmploymentTypes: () => ({ options: [], isLoading: false }),
  useJobSeniorities: () => ({ options: [], isLoading: false }),
  useDepartmentsSearch: () => ({ options: [], isLoading: false }),
  useCitiesSearch: () => ({ options: [], isLoading: false }),
}))

vi.mock("@/components/ui/lia-editor", () => ({
  LiaEditor: () => <div data-testid="lia-editor-mock" />,
}))

const baseProps = {
  jobEditForm: { visibility: "public" },
  job: null,
  companyDefaults: {},
  isEditing: true,
  updateField: vi.fn(),
  setActiveSection: vi.fn(),
  setStatusChangeConfirm: vi.fn(),
  getScreeningImpact: () => "",
}

describe("JobInfoGeralSection — visibility canonical contract (Sprint 1 RBAC)", () => {
  it("options do select usam valores CANONICAL lowercase", () => {
    render(<JobInfoGeralSection {...baseProps} />)
    const select = screen.getByTestId("job-visibility-select") as HTMLSelectElement
    const values = Array.from(select.options).map((o) => o.value)
    expect(values).toEqual(["public", "internal", "confidential"])
  })

  it("NÃO usa valores PT capitalizado (bug histórico)", () => {
    render(<JobInfoGeralSection {...baseProps} />)
    const select = screen.getByTestId("job-visibility-select") as HTMLSelectElement
    const values = Array.from(select.options).map((o) => o.value)
    expect(values).not.toContain("Pública")
    expect(values).not.toContain("Confidencial")
  })

  it("access_list UI NÃO aparece quando visibility !== 'confidential'", () => {
    render(<JobInfoGeralSection {...baseProps} jobEditForm={{ visibility: "public" }} />)
    expect(screen.queryByTestId("job-access-list-section")).not.toBeInTheDocument()
  })

  it("access_list UI aparece quando visibility === 'confidential'", () => {
    render(<JobInfoGeralSection {...baseProps} jobEditForm={{ visibility: "confidential" }} />)
    expect(screen.getByTestId("job-access-list-section")).toBeInTheDocument()
    expect(screen.getByTestId("access-list-editor")).toBeInTheDocument()
  })
})
