import { describe, expect, it, vi } from "vitest"
import { render, screen } from "@testing-library/react"

// Mock the hook BEFORE importing the component
vi.mock("@/hooks/alerts/useVacancyAlertPreferences", () => ({
  useVacancyAlertPreferences: vi.fn(),
  useAlertPreview: vi.fn(),
}))

import { VacancyAlertSettings } from "../VacancyAlertSettings"
import {
  useVacancyAlertPreferences,
  useAlertPreview,
} from "@/hooks/alerts/useVacancyAlertPreferences"

const mockHook = useVacancyAlertPreferences as ReturnType<typeof vi.fn>
const mockPreview = useAlertPreview as ReturnType<typeof vi.fn>

describe("VacancyAlertSettings", () => {
  beforeEach(() => {
    mockPreview.mockReturnValue({ data: null, isLoading: false })
  })

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
    expect(screen.getByText(/Triagem conclu/i)).toBeDefined()
    expect(screen.getByText(/Mudan/i)).toBeDefined()
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

describe("VacancyAlertSettings — badge", () => {
  it("mostra badge com contagem quando preview_count > 0", () => {
    mockHook.mockReturnValue({
      data: { preferences: [] },
      isLoading: false,
      savePreferences: vi.fn(),
      isSaving: false,
    })
    mockPreview.mockImplementation((_vid: string, alertType: string) => ({
      data: {
        alert_type: alertType,
        preview_count: alertType === "new_candidate" ? 5 : 0,
        description: "5 novos",
      },
      isLoading: false,
    }))
    render(<VacancyAlertSettings vacancyId="vac-123" userId="u1" />)
    expect(screen.getByText("5")).toBeTruthy()
  })

  it("nao mostra badge quando preview_count = 0", () => {
    mockHook.mockReturnValue({
      data: { preferences: [] },
      isLoading: false,
      savePreferences: vi.fn(),
      isSaving: false,
    })
    mockPreview.mockReturnValue({
      data: { alert_type: "new_candidate", preview_count: 0, description: "" },
      isLoading: false,
    })
    render(<VacancyAlertSettings vacancyId="vac-123" userId="u1" />)
    const badges = document.querySelectorAll(".rounded-full")
    expect(badges.length).toBe(0)
  })
})
