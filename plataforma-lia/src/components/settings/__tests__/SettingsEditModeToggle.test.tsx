import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { SettingsEditModeToggle } from "@/components/settings/SettingsEditModeToggle"

vi.mock("@/contexts/auth-context", () => ({
  useAuth: vi.fn(),
}))

import { useAuth } from "@/contexts/auth-context"
const mockUseAuth = vi.mocked(useAuth)

describe("SettingsEditModeToggle — P2-2 B.4", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    if (typeof window !== "undefined") {
      window.localStorage.clear()
    }
  })

  it("renderiza pra admin", () => {
    mockUseAuth.mockReturnValue({ user: { role: "admin" } } as any)
    render(<SettingsEditModeToggle hubId="minha-empresa" />)
    expect(screen.getByTestId("settings-edit-mode-toggle")).toBeInTheDocument()
  })

  it("não renderiza pra viewer (canToggle=false)", () => {
    mockUseAuth.mockReturnValue({ user: { role: "viewer" } } as any)
    const { container } = render(<SettingsEditModeToggle hubId="minha-empresa" />)
    expect(container.firstChild).toBeNull()
  })

  it("não renderiza pra recruiter em integrations", () => {
    mockUseAuth.mockReturnValue({ user: { role: "recruiter" } } as any)
    const { container } = render(<SettingsEditModeToggle hubId="integrations" />)
    expect(container.firstChild).toBeNull()
  })

  it("mostra Edit3 + 'Modo edição' quando isEditing=true (default)", () => {
    mockUseAuth.mockReturnValue({ user: { role: "admin" } } as any)
    render(<SettingsEditModeToggle hubId="minha-empresa" />)
    expect(screen.getByText("Modo edição")).toBeInTheDocument()
  })

  it("click alterna pra read-only", () => {
    mockUseAuth.mockReturnValue({ user: { role: "admin" } } as any)
    render(<SettingsEditModeToggle hubId="minha-empresa" />)
    fireEvent.click(screen.getByTestId("settings-edit-mode-toggle"))
    expect(screen.getByText("Modo visualização")).toBeInTheDocument()
  })

  it("aria-pressed reflete estado", () => {
    mockUseAuth.mockReturnValue({ user: { role: "admin" } } as any)
    render(<SettingsEditModeToggle hubId="minha-empresa" />)
    const btn = screen.getByTestId("settings-edit-mode-toggle")
    expect(btn).toHaveAttribute("aria-pressed", "true")
    fireEvent.click(btn)
    expect(btn).toHaveAttribute("aria-pressed", "false")
  })
})
