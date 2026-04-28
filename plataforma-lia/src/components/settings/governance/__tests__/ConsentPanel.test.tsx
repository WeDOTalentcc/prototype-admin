/**
 * ConsentPanel — smoke test (Task #904 — code review fix)
 *
 * Verifica:
 *  - GET /consent/granular/{candidate_id} ao buscar
 *  - POST /consent/granular/{candidate_id}/update ao revogar
 */
import React from "react"
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import "@testing-library/jest-dom/vitest"

vi.mock("next-intl", () => {
  const tFn = (k: string) => k
  return { useTranslations: () => tFn }
})
vi.mock("@/hooks/company/useCompanyId", () => ({
  useCompanyId: () => ({ companyId: "co-1" }),
}))

import { ConsentPanel } from "@/components/settings/governance/ConsentPanel"

const fetchMock = vi.fn()
const summary = {
  candidate_id: "cand-42",
  company_id: "co-1",
  all_blocking_given: true,
  consents: [
    {
      purpose: "ai_screening",
      consent_type: "blocking",
      given: true,
      revoked: false,
      consent_date: "2025-01-01T00:00:00Z",
      source: "wizard",
    },
  ],
}

beforeEach(() => {
  fetchMock.mockReset()
  fetchMock.mockImplementation((url: string, init?: RequestInit) => {
    if (url.includes("/consent/granular/cand-42/update") && init?.method === "POST") {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ ok: true }) })
    }
    if (url.includes("/consent/granular/cand-42")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(summary) })
    }
    return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) })
  })
  vi.stubGlobal("fetch", fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe("ConsentPanel", () => {
  it("loads granular consents per candidate and revokes one", async () => {
    render(<ConsentPanel />)
    await screen.findByTestId("consent-panel")

    const input = screen.getByTestId("consent-candidate-input") as HTMLInputElement
    fireEvent.change(input, { target: { value: "cand-42" } })
    fireEvent.click(screen.getByTestId("consent-load"))

    await waitFor(() => {
      expect(screen.getByText("ai_screening")).toBeInTheDocument()
    })

    const urls = fetchMock.mock.calls.map((c) => c[0] as string)
    expect(urls.some((u) => u.includes("/consent/granular/cand-42"))).toBe(true)

    fireEvent.click(screen.getByTestId("consent-revoke-ai_screening"))

    await waitFor(() => {
      const calls = fetchMock.mock.calls
      const updateCall = calls.find(
        (c) => (c[0] as string).includes("/consent/granular/cand-42/update"),
      )
      expect(updateCall).toBeTruthy()
      expect((updateCall?.[1] as RequestInit | undefined)?.method).toBe("POST")
    })
  })
})
