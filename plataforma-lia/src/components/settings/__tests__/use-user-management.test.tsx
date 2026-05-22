/**
 * Camada 3 backlog — Item 1
 *
 * Contract test for `useUserManagement`: fail-loud when company context is
 * missing (REGRA 4 — no silent demo_company sentinel in fetch URL).
 *
 * Cobre:
 *  1. test_throws_when_company_id_missing — error state set, no fetch
 *  2. test_uses_company_id_when_provided — fetch uses real effectiveCompanyId
 *  3. test_no_demo_company_sentinel_in_fetch — defensive substring check
 */
import React from "react"
import { renderHook, act, waitFor } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"
import { vi, describe, it, expect, beforeEach } from "vitest"

const mockUseCurrentCompany = vi.fn()
vi.mock("@/hooks/company/use-current-company", () => ({
  useCurrentCompany: () => mockUseCurrentCompany(),
}))

const mockUseSCIMConfig = vi.fn(() => ({ isSCIMEnabled: false, scimConfig: null }))
vi.mock("@/hooks/company/use-scim-config", () => ({
  useSCIMConfig: () => mockUseSCIMConfig(),
}))

const mockApiFetch = vi.fn()
vi.mock("@/lib/api/api-fetch", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
}))

import { useUserManagement } from "@/components/settings/use-user-management"

const MESSAGES = {
  settings: {
    users: {
      roleAdmin: "Admin",
      roleRecruiter: "Recruiter",
      roleManager: "Manager",
      roleViewer: "Viewer",
      errorLoadUsers: "Erro ao carregar usuários",
      errorSaveUser: "Erro ao salvar",
      errorResendInvite: "Erro ao reenviar",
      errorDeleteUser: "Erro ao deletar",
      userCreatedSuccess: "Usuário {email} criado",
      inviteResentSuccess: "Convite reenviado para {email}",
      confirmDeleteUser: "Confirmar?",
    },
  },
}

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <NextIntlClientProvider locale="pt" messages={MESSAGES}>
    {children}
  </NextIntlClientProvider>
)

describe("useUserManagement — fail-loud company context", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockApiFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ data: [] }),
    })
  })

  it("test_throws_when_company_id_missing — sets error state and skips fetch", async () => {
    mockUseCurrentCompany.mockReturnValue({ companyId: null, tenantId: null })

    const { result } = renderHook(() => useUserManagement(), { wrapper })

    await waitFor(() => {
      expect(result.current.error).toBe(
        "No company context available — please re-login",
      )
    })
    expect(mockApiFetch).not.toHaveBeenCalled()
    expect(result.current.users).toEqual([])
  })

  it("test_uses_company_id_when_provided — fetch uses real effectiveCompanyId", async () => {
    mockUseCurrentCompany.mockReturnValue({
      companyId: "real-uuid-1234",
      tenantId: null,
    })

    renderHook(() => useUserManagement(), { wrapper })

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith(
        expect.stringContaining("company_id=real-uuid-1234"),
      )
    })
  })

  it("test_no_demo_company_sentinel_in_fetch — defensive substring check", async () => {
    mockUseCurrentCompany.mockReturnValue({
      companyId: "real-uuid-5678",
      tenantId: "tenant-abc",
    })

    renderHook(() => useUserManagement(), { wrapper })

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalled()
    })
    const allCalls = mockApiFetch.mock.calls.flat()
    const fetchUrls = allCalls.filter((arg): arg is string => typeof arg === "string")
    for (const url of fetchUrls) {
      expect(url).not.toContain("demo_company")
    }
  })

  it("test_handleSaveUser_sets_error_when_no_company — does not POST", async () => {
    mockUseCurrentCompany.mockReturnValue({ companyId: null, tenantId: null })

    const { result } = renderHook(() => useUserManagement(), { wrapper })

    await waitFor(() => {
      expect(result.current.error).toBeTruthy()
    })

    mockApiFetch.mockClear()
    await act(async () => {
      await result.current.handleSaveUser()
    })

    // Save aborted — no POST fired
    expect(
      mockApiFetch.mock.calls.some(
        (call) =>
          typeof call[1] === "object" &&
          call[1] !== null &&
          (call[1] as { method?: string }).method === "POST",
      ),
    ).toBe(false)
  })
})
