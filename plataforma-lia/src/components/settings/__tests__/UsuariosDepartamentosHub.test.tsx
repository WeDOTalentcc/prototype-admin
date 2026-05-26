/**
 * Smoke tests — UsuariosDepartamentosHub
 *
 * Verifica que o hub monta e não lança. Também cobre a troca de tab via
 * evento `settings-open-subtab` (regressão de rules-of-hooks).
 */
import React from "react"
import { render, act } from "@testing-library/react"
import { describe, it, vi, beforeAll } from "vitest"

beforeAll(() => {
  if (typeof window !== "undefined" && !window.matchMedia) {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: (query: string) => ({
        matches: false, media: query, onchange: null,
        addEventListener: () => {}, removeEventListener: () => {},
        addListener: () => {}, removeListener: () => {},
        dispatchEvent: () => false,
      }),
    })
  }
})

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

vi.mock("@/hooks/company/useCompanyId", () => ({
  useCompanyId: () => ({ companyId: "test-co", isLoading: false, error: null }),
}))

vi.mock("@/hooks/settings/useCompanyData", () => ({
  useCompanyData: () => ({
    state: { company: null, culture: null, hiringPolicy: null, loading: false, error: null },
    actions: { saveBasicInfo: vi.fn(), saveCulture: vi.fn(), saveHiringPolicy: vi.fn() },
    initialDepartments: [],
    initialApprovers: [],
  }),
}))

vi.mock("@/hooks/settings/useDepartmentManagement", () => ({
  useDepartmentManagement: () => ({
    state: { departments: [], loading: false, error: null, editingDepartment: null, newDepartment: null },
    actions: {
      createDepartment: vi.fn(),
      updateDepartment: vi.fn(),
      deleteDepartment: vi.fn(),
      setEditingDepartment: vi.fn(),
      setNewDepartment: vi.fn(),
    },
  }),
}))

vi.mock("@/components/settings/use-user-management", () => ({
  useUserManagement: () => ({ users: [], isLoading: false, error: null }),
}))

vi.mock("@/components/settings/user-management", () => ({
  UserManagement: () => <div data-testid="user-management-stub" />,
}))
vi.mock("@/components/settings/DepartmentsTab", () => ({
  DepartmentsTab: () => <div data-testid="departments-tab-stub" />,
}))
vi.mock("@/components/settings/DepartmentScopeBanner", () => ({
  DepartmentScopeBanner: () => null,
}))

import { UsuariosDepartamentosHub } from "@/components/settings/UsuariosDepartamentosHub"

describe("UsuariosDepartamentosHub — smoke rerender (rules-of-hooks + mount)", () => {
  it("monta sem props sem lançar (tab padrão: users)", () => {
    const { unmount } = render(<UsuariosDepartamentosHub />)
    unmount()
  })

  it("troca para tab departments via evento settings-open-subtab sem lançar", async () => {
    const { unmount } = render(<UsuariosDepartamentosHub />)
    await act(async () => {
      window.dispatchEvent(
        new CustomEvent("settings-open-subtab", {
          detail: { section: "usuarios-departamentos", tab: "departments" },
        })
      )
    })
    unmount()
  })

  it("rerenderiza (event users→departments→users) sem lançar (detecta rules-of-hooks regression)", async () => {
    const { unmount } = render(<UsuariosDepartamentosHub />)
    await act(async () => {
      window.dispatchEvent(
        new CustomEvent("settings-open-subtab", {
          detail: { section: "usuarios-departamentos", tab: "departments" },
        })
      )
    })
    await act(async () => {
      window.dispatchEvent(
        new CustomEvent("settings-open-subtab", {
          detail: { section: "usuarios-departamentos", tab: "users" },
        })
      )
    })
    unmount()
  })
})
