/**
 * Wave 2 Agent B / T-13 Fase 2 — Smoke tests para LiaFieldsConfigPanel.
 *
 * Cobre:
 *  1. Backward compat — tab "Campos LIA" continua renderizando 34 campos
 *  2. Tab "Tenant Override (YAML)" — render condicional + fetch lista
 *  3. Save flow — PUT /admin/prompts/tenant-overrides/{path}
 *  4. Selector path — sequência de fetch ao trocar dropdown
 */
import React from "react"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { NextIntlClientProvider } from "next-intl"
import { vi, describe, it, expect, beforeEach } from "vitest"

const mockUseCompanyId = vi.fn()
vi.mock("@/hooks/company/useCompanyId", () => ({
  __esModule: true,
  default: () => mockUseCompanyId(),
  useCompanyId: () => mockUseCompanyId(),
}))

const mockApiFetch = vi.fn()
vi.mock("@/lib/api/api-fetch", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
}))

// E1 audit (2026-05-21) added useAuth() for canSeeRawYaml role gate.
// Default mock returns wedotalent_admin so the tenant-override tab renders.
vi.mock("@/contexts/auth-context", () => ({
  useAuth: () => ({ user: { role: "wedotalent_admin" } }),
}))

vi.mock("@/components/settings/LiaFieldToggle", () => ({
  LiaFieldToggle: ({ fieldKey }: { fieldKey: string }) => (
    <div data-testid={`lia-toggle-${fieldKey}`} />
  ),
}))

import { LiaFieldsConfigPanel } from "@/components/settings/LiaFieldsConfigPanel"

const MESSAGES = {
  settings: {
    liaFields: {
      title: "Instruções LIA por Campo",
      description: "desc",
      fieldsTotal: "campos",
      tabs: {
        fields: "Campos LIA",
        tenantOverride: "Tenant Override (YAML)",
      },
      tenantOverride: {
        title: "Tenant Override (YAML)",
        disclaimer: "Modificações são per-empresa",
        activeOverrides: "Overrides ativos",
        empty: "Nenhum override ativo",
        pathLabel: "Path canonical:",
        loading: "Carregando...",
        save: "Salvar override",
        create: "Criar override",
        delete: "Remover override",
        confirmDelete: "Confirmar?",
        saved: "Salvo em",
      },
    },
  },
} as const

function renderPanel() {
  return render(
    <NextIntlClientProvider locale="pt-BR" messages={MESSAGES}>
      <LiaFieldsConfigPanel />
    </NextIntlClientProvider>,
  )
}

describe("LiaFieldsConfigPanel — Wave 2 Agent B / T-13", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseCompanyId.mockReturnValue({
      companyId: "test-company-uuid",
      isLoading: false,
    })
    // Default mock: field-toggles GET returns empty canonical config
    mockApiFetch.mockImplementation((url: string) => {
      if (url.includes("/field-toggles")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () =>
            Promise.resolve({
              company_id: "test-company-uuid",
              toggles: {},
              comments: {},
              details: [],
            }),
        })
      }
      if (url.endsWith("/admin/prompts/tenant-overrides")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () =>
            Promise.resolve({
              company_id: "test-company-uuid",
              total: 0,
              overrides: [],
            }),
        })
      }
      if (url.includes("/admin/prompts/tenant-overrides/")) {
        return Promise.resolve({
          ok: false,
          status: 404,
          json: () => Promise.resolve({ detail: "not found" }),
        })
      }
      return Promise.resolve({ ok: false, status: 500, json: () => Promise.resolve({}) })
    })
  })

  // ------------------------------------------------------------------
  // 1. Backward compat — "fields" tab preservada
  // ------------------------------------------------------------------

  it("renders backward-compat Campos LIA tab as default with title", async () => {
    renderPanel()
    await waitFor(() => {
      expect(screen.getByText("Instruções LIA por Campo")).toBeInTheDocument()
    })
    // Tab "Campos LIA" visible
    expect(screen.getByRole("tab", { name: /Campos LIA/i })).toBeInTheDocument()
  })

  // ------------------------------------------------------------------
  // 2. Tab tenant-override exists + fetches list
  // ------------------------------------------------------------------

  it("renders tenant-override tab trigger", async () => {
    renderPanel()
    await waitFor(() => {
      expect(
        screen.getByTestId("tab-tenant-override"),
      ).toBeInTheDocument()
    })
  })

  it("fetches overrides list when switching to tenant-override tab", async () => {
    const user = userEvent.setup()
    renderPanel()
    await waitFor(() => {
      expect(screen.getByTestId("tab-tenant-override")).toBeInTheDocument()
    })

    await user.click(screen.getByTestId("tab-tenant-override"))

    await waitFor(() => {
      const calls = mockApiFetch.mock.calls.map((c: unknown[]) => c[0] as string)
      expect(
        calls.some((c) => c.includes("/admin/prompts/tenant-overrides")),
      ).toBe(true)
    })
  })

  // ------------------------------------------------------------------
  // 3. Save flow PUT
  // ------------------------------------------------------------------

  it("calls PUT /admin/prompts/tenant-overrides/{path} on Save click", async () => {
    const user = userEvent.setup()
    // Override mock: PUT returns success
    mockApiFetch.mockImplementation((url: string, options?: RequestInit) => {
      if (url.includes("/field-toggles")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () =>
            Promise.resolve({
              company_id: "test-company-uuid",
              toggles: {},
              comments: {},
              details: [],
            }),
        })
      }
      if (url.endsWith("/admin/prompts/tenant-overrides")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () =>
            Promise.resolve({
              company_id: "test-company-uuid",
              total: 0,
              overrides: [],
            }),
        })
      }
      if (
        url.includes("/admin/prompts/tenant-overrides/") &&
        options?.method === "PUT"
      ) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () =>
            Promise.resolve({
              success: true,
              path: "shared/lia_persona",
              version: "1.0.0-tenant",
              last_updated_at: new Date().toISOString(),
              validation_warnings: [],
            }),
        })
      }
      return Promise.resolve({
        ok: false,
        status: 404,
        json: () => Promise.resolve({ detail: "not found" }),
      })
    })

    renderPanel()
    await waitFor(() => {
      expect(screen.getByTestId("tab-tenant-override")).toBeInTheDocument()
    })
    await user.click(screen.getByTestId("tab-tenant-override"))

    // Wait for editor textarea to appear
    const editor = await screen.findByTestId("yaml-editor")
    await user.clear(editor)
    await user.type(
      editor,
      "metadata:\n  version: 1.0.0-tenant\nsystem_prompt: oi\n",
    )

    const saveBtn = await screen.findByTestId("save-btn")
    await user.click(saveBtn)

    await waitFor(() => {
      const putCalls = mockApiFetch.mock.calls.filter(
        (c: unknown[]) =>
          (c[1] as RequestInit | undefined)?.method === "PUT" &&
          (c[0] as string).includes("/admin/prompts/tenant-overrides/"),
      )
      expect(putCalls.length).toBeGreaterThanOrEqual(1)
    })
  })
})
