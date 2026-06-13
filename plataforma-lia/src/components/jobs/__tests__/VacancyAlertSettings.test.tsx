import { describe, expect, it, vi } from "vitest"
import { render, screen } from "@testing-library/react"

// Mock the hook BEFORE importing the component
vi.mock("@/hooks/alerts/useVacancyAlertPreferences", () => ({
  useVacancyAlertPreferences: vi.fn(),
}))

import { VacancyAlertSettings } from "../VacancyAlertSettings"
import { useVacancyAlertPreferences } from "@/hooks/alerts/useVacancyAlertPreferences"

const mockHook = useVacancyAlertPreferences as ReturnType<typeof vi.fn>

describe("VacancyAlertSettings", () => {
  it("shows loading state", () => {
    mockHook.mockReturnValue({
      data: undefined,
      isLoading: true,
      savePreferences: vi.fn(),
      isSaving: false,
    })
    render(<VacancyAlertSettings vacancyId="v1" userId="u1" />)
    expect(screen.getByText(/carregando alertas/i)).toBeDefined()
  })

  it("renders 3 alert types when loaded", () => {
    mockHook.mockReturnValue({
      data: { preferences: [] },
      isLoading: false,
      savePreferences: vi.fn(),
      isSaving: false,
    })
    render(<VacancyAlertSettings vacancyId="v1" userId="u1" />)
    expect(screen.getByText("Novo candidato")).toBeDefined()
    expect(screen.getByText("Triagem concluída")).toBeDefined()
    expect(screen.getByText("Mudança de etapa")).toBeDefined()
  })

  it("renders frequency selects with correct default", () => {
    mockHook.mockReturnValue({
      data: {
        preferences: [
          { alert_type: "new_candidate", frequency: "weekly" },
        ],
      },
      isLoading: false,
      savePreferences: vi.fn(),
      isSaving: false,
    })
    render(<VacancyAlertSettings vacancyId="v1" userId="u1" />)
    const selects = screen.getAllByRole("combobox")
    expect(selects.length).toBe(3)
    // The one with server data should show "weekly"
    const newCandidateSelect = selects[0] as HTMLSelectElement
    expect(newCandidateSelect.value).toBe("weekly")
  })

  it("does not render when vacancyId is empty", () => {
    mockHook.mockReturnValue({
      data: undefined,
      isLoading: false,
      savePreferences: vi.fn(),
      isSaving: false,
    })
    const { container } = render(<VacancyAlertSettings vacancyId="" userId="u1" />)
    expect(container.textContent).toBe("")
  })
})
