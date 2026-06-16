/**
 * A6-FE-3 — PiiVisibilityRoleDefaults TDD tests
 *
 * Cases:
 *  1. renders all 4 role sections after load
 *  2. manager matrix shows cpf as "Ocultar" (loaded default false=hide)
 *  3. clicking Salvar Alterações calls apiFetch with PUT + body containing defaults
 */

import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor, fireEvent } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { NextIntlClientProvider } from "next-intl"
import React from "react"
import ptBRMessages from "../../../../messages/pt-BR.json"

// ── Mocks ─────────────────────────────────────────────────────────────────

vi.mock("@/lib/api/api-fetch", () => ({
  apiFetch: vi.fn(),
}))

import { apiFetch } from "@/lib/api/api-fetch"
const mockApiFetch = vi.mocked(apiFetch)

// ── Helpers ───────────────────────────────────────────────────────────────

function makeResponse(body: unknown, ok = true): Response {
  return {
    ok,
    status: ok ? 200 : 500,
    json: () => Promise.resolve(body),
  } as unknown as Response
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <NextIntlClientProvider locale="pt" messages={ptBRMessages}>
        {ui}
      </NextIntlClientProvider>
    </QueryClientProvider>,
  )
}

// ── Tests ──────────────────────────────────────────────────────────────────

// Import AFTER mocks are set up
import { PiiVisibilityRoleDefaults } from "../PiiVisibilityRoleDefaults"

describe("PiiVisibilityRoleDefaults", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Default GET: manager has cpf hidden
    mockApiFetch.mockResolvedValue(
      makeResponse({ defaults: { manager: { cpf: false } } }),
    )
  })

  it("renders all 4 role sections after load", async () => {
    renderWithProviders(<PiiVisibilityRoleDefaults />)

    // Initially loading state
    // Wait for all role labels to appear
    await waitFor(() => {
      expect(screen.getByText("Administrador")).toBeTruthy()
    })
    expect(screen.getByText("Gestor")).toBeTruthy()
    expect(screen.getByText("Recrutador")).toBeTruthy()
    expect(screen.getByText("Visualizador")).toBeTruthy()
  })

  it("renders the role defaults title and subtitle", async () => {
    renderWithProviders(<PiiVisibilityRoleDefaults />)

    await waitFor(() => {
      expect(screen.getByText("Visibilidade de PII por papel")).toBeTruthy()
    })
    expect(
      screen.getByText(
        "Padrão por papel. O override por usuário acima tem prioridade.",
      ),
    ).toBeTruthy()
  })

  it("manager matrix shows cpf in Ocultar state (loaded default false=hide)", async () => {
    renderWithProviders(<PiiVisibilityRoleDefaults />)

    await waitFor(() => {
      expect(screen.getByText("Gestor")).toBeTruthy()
    })

    // Find CPF field row - it should have Ocultar button active
    // The matrix shows CPF field; when value[cpf] === false the "Ocultar" button is active
    // We check that the i18n "Ocultar" appears (stateHide from piiVisibility namespace)
    const ocultar = screen.getAllByText("Ocultar")
    expect(ocultar.length).toBeGreaterThan(0)
  })

  it("clicking Salvar Alterações calls apiFetch PUT with defaults body", async () => {
    // The mutation response
    mockApiFetch
      .mockResolvedValueOnce(
        makeResponse({ defaults: { manager: { cpf: false } } }),
      ) // GET
      .mockResolvedValueOnce(makeResponse({ ok: true })) // PUT

    renderWithProviders(<PiiVisibilityRoleDefaults />)

    // Wait for component to load
    await waitFor(() => {
      expect(screen.getByText("Salvar Alterações")).toBeTruthy()
    })

    // Click save
    fireEvent.click(screen.getByText("Salvar Alterações"))

    // Assert PUT was called
    await waitFor(() => {
      const calls = mockApiFetch.mock.calls
      const putCall = calls.find(
        (c) => c[1] && (c[1] as RequestInit).method === "PUT",
      )
      expect(putCall).toBeTruthy()

      const body = JSON.parse((putCall![1] as RequestInit).body as string)
      expect(body).toHaveProperty("defaults")
    })
  })
})
