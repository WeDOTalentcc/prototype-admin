/**
 * Sensor: StaffLayoutClient gate por role.
 *
 * Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
 * Skill: harness-engineering (sensor computacional)
 *
 * Verifica:
 * - Recruiter logado → redirect para /acesso-negado
 * - Wedotalent_admin logado → renderiza children
 * - Não autenticado → redirect para /login
 * - Loading state → mostra placeholder
 */

import { render, screen, waitFor } from "@testing-library/react"
import { describe, expect, it, vi, beforeEach } from "vitest"
import StaffLayoutClient from "../StaffLayoutClient"

const mockReplace = vi.fn()

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockReplace, push: vi.fn() }),
  usePathname: () => "/wedo-admin",
}))

vi.mock("@/components/dashboard-app", () => ({
  DashboardApp: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="dashboard-app">{children}</div>
  ),
}))

const mockStoreState = {
  user: null as { id: string; role: string } | null,
  isLoading: false,
  isAuthenticated: false,
}

vi.mock("@/stores/auth-store", () => ({
  useAuthStore: (selector: (state: typeof mockStoreState) => unknown) =>
    selector(mockStoreState),
}))

describe("StaffLayoutClient — role gate", () => {
  beforeEach(() => {
    mockReplace.mockClear()
    mockStoreState.user = null
    mockStoreState.isLoading = false
    mockStoreState.isAuthenticated = false
  })

  it("renders loading placeholder while auth is loading", () => {
    mockStoreState.isLoading = true
    render(
      <StaffLayoutClient>
        <div data-testid="child">child</div>
      </StaffLayoutClient>,
    )
    expect(screen.getByText(/verificando acesso/i)).toBeInTheDocument()
    expect(screen.queryByTestId("child")).not.toBeInTheDocument()
    expect(mockReplace).not.toHaveBeenCalled()
  })

  it("redirects unauthenticated users to /login", async () => {
    mockStoreState.isLoading = false
    mockStoreState.isAuthenticated = false
    mockStoreState.user = null
    render(
      <StaffLayoutClient>
        <div data-testid="child">child</div>
      </StaffLayoutClient>,
    )
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/login")
    })
    expect(screen.queryByTestId("child")).not.toBeInTheDocument()
  })

  it("redirects recruiter to /acesso-negado", async () => {
    mockStoreState.isAuthenticated = true
    mockStoreState.user = { id: "u1", role: "recruiter" }
    render(
      <StaffLayoutClient>
        <div data-testid="child">child</div>
      </StaffLayoutClient>,
    )
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/acesso-negado")
    })
    expect(screen.queryByTestId("child")).not.toBeInTheDocument()
  })

  it("redirects admin (tenant_admin) to /acesso-negado (only wedotalent_admin allowed)", async () => {
    mockStoreState.isAuthenticated = true
    mockStoreState.user = { id: "u2", role: "admin" }
    render(
      <StaffLayoutClient>
        <div data-testid="child">child</div>
      </StaffLayoutClient>,
    )
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/acesso-negado")
    })
    expect(screen.queryByTestId("child")).not.toBeInTheDocument()
  })

  it("renders children when role is wedotalent_admin", () => {
    mockStoreState.isAuthenticated = true
    mockStoreState.user = { id: "u3", role: "wedotalent_admin" }
    render(
      <StaffLayoutClient>
        <div data-testid="child">child</div>
      </StaffLayoutClient>,
    )
    expect(screen.getByTestId("dashboard-app")).toBeInTheDocument()
    expect(screen.getByTestId("child")).toBeInTheDocument()
    expect(mockReplace).not.toHaveBeenCalled()
  })
})
