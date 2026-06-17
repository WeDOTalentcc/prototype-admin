/**
 * ConsentPanel — extended tests (T-21c Wave 2 Agent C)
 *
 * Cobre:
 *  - 3 tabs canonical (candidate-granular / training-data / metrics)
 *  - backward compat: candidate-granular tab funcional (preserva 273 LOC)
 *  - GET company training consent on mount (training-data tab)
 *  - POST grant on Grant button click
 *  - POST revoke flow with reason
 */
import React from "react"
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import "@testing-library/jest-dom/vitest"

vi.mock("next-intl", () => {
  // Return last key segment so test assertions can match canonical UI strings
  const tFn = (k: string) => k
  return { useTranslations: () => tFn }
})
vi.mock("@/hooks/company/useCompanyId", () => ({
  useCompanyId: () => ({ companyId: "co-1" }),
}))

import { ConsentPanel } from "@/components/settings/governance/ConsentPanel"

const fetchMock = vi.fn()

const candidateSummary = {
  candidate_id: "cand-42",
  company_id: "co-1",
  all_blocking_given: true,
  consents: [
    {
      purpose: "ai_screening",
      consent_type: "blocking",
      given: true,
      revoked: false,
      consent_date: "2026-05-01T00:00:00Z",
      source: "wizard",
    },
  ],
}

const trainingConsentInactive = {
  consent_given: false,
  is_active: false,
  granted_at: null,
  revoked_at: null,
  version: "1.0",
  legal_basis: "LGPD_ART_7_I",
}

const trainingConsentActive = {
  consent_given: true,
  is_active: true,
  granted_at: "2026-05-20T14:00:00Z",
  revoked_at: null,
  version: "1.0",
  legal_basis: "LGPD_ART_7_I",
}

function defaultFetchImpl(url: string, init?: RequestInit) {
  // Candidate granular
  if (url.includes("/consent/granular/cand-42/update") && init?.method === "POST") {
    return Promise.resolve({ ok: true, json: () => Promise.resolve({ ok: true }) })
  }
  if (url.includes("/consent/granular/cand-42")) {
    return Promise.resolve({ ok: true, json: () => Promise.resolve(candidateSummary) })
  }
  // Training data status (T-21c)
  if (
    url.includes("/admin/consent/company-training-consent/grant") &&
    init?.method === "POST"
  ) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ success: true, consent_given: true }),
    })
  }
  if (
    url.includes("/admin/consent/company-training-consent/revoke") &&
    init?.method === "POST"
  ) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ success: true }),
    })
  }
  if (url.includes("/admin/consent/company-training-consent")) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve(trainingConsentInactive),
    })
  }
  // Metrics
  if (url.includes("/consent/stats")) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ stats: [] }),
    })
  }
  return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) })
}

beforeEach(() => {
  fetchMock.mockReset()
  fetchMock.mockImplementation(defaultFetchImpl)
  vi.stubGlobal("fetch", fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe("ConsentPanel (T-21c extended)", () => {
  it("renders 3 canonical tabs", async () => {
    render(<ConsentPanel />)
    expect(screen.getByTestId("consent-tab-candidate")).toBeInTheDocument()
    expect(screen.getByTestId("consent-tab-training-data")).toBeInTheDocument()
    expect(screen.getByTestId("consent-tab-metrics")).toBeInTheDocument()
  })

  it("backward compat: candidate-granular tab continues to load and revoke", async () => {
    render(<ConsentPanel />)
    await screen.findByTestId("consent-panel-candidate")

    const input = screen.getByTestId("consent-candidate-input") as HTMLInputElement
    fireEvent.change(input, { target: { value: "cand-42" } })
    fireEvent.click(screen.getByTestId("consent-load"))

    await waitFor(() => {
      expect(screen.getByText("ai_screening")).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId("consent-revoke-ai_screening"))

    await waitFor(() => {
      const updateCall = fetchMock.mock.calls.find(
        (c) => (c[0] as string).includes("/consent/granular/cand-42/update"),
      )
      expect(updateCall).toBeTruthy()
      expect((updateCall?.[1] as RequestInit | undefined)?.method).toBe("POST")
    })
  })

  it("fetches company training consent on tab activation", async () => {
    const user = userEvent.setup()
    render(<ConsentPanel />)
    await user.click(screen.getByTestId("consent-tab-training-data"))
    await screen.findByTestId("consent-panel-training-data")

    await waitFor(() => {
      const call = fetchMock.mock.calls.find((c) =>
        (c[0] as string).includes("/admin/consent/company-training-consent"),
      )
      expect(call).toBeTruthy()
    })
  })

  it("POSTs grant when admin clicks Grant button", async () => {
    const user = userEvent.setup()
    render(<ConsentPanel />)
    await user.click(screen.getByTestId("consent-tab-training-data"))
    await screen.findByTestId("consent-panel-training-data")

    // Aguarda load completar — grant button aparece quando inactive
    const grantBtn = await screen.findByTestId("training-consent-grant")
    await user.click(grantBtn)

    await waitFor(() => {
      const grantCall = fetchMock.mock.calls.find(
        (c) =>
          (c[0] as string).includes("/admin/consent/company-training-consent/grant") &&
          (c[1] as RequestInit | undefined)?.method === "POST",
      )
      expect(grantCall).toBeTruthy()
      const body = JSON.parse((grantCall?.[1] as RequestInit).body as string)
      expect(body.consent_text).toBeTruthy()
      expect(body.consent_text.length).toBeGreaterThan(10)
      // REGRA 2: company_id NUNCA no payload (vem do JWT/header)
      expect(body.company_id).toBeUndefined()
    })
  })

  it("POSTs revoke with reason when admin confirms", async () => {
    // Simula consent ativo no GET
    fetchMock.mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes("/admin/consent/company-training-consent/revoke")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true, revoked_at: "2026-05-20T16:00:00Z" }),
        })
      }
      if (url.includes("/admin/consent/company-training-consent")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(trainingConsentActive) })
      }
      return defaultFetchImpl(url, init)
    })

    const user = userEvent.setup()
    render(<ConsentPanel />)
    await user.click(screen.getByTestId("consent-tab-training-data"))
    await screen.findByTestId("consent-panel-training-data")

    const openRevoke = await screen.findByTestId("training-consent-revoke-open")
    await user.click(openRevoke)

    const reasonInput = await screen.findByTestId("training-consent-revoke-reason")
    fireEvent.change(reasonInput, { target: { value: "Política interna mudou" } })

    await user.click(screen.getByTestId("training-consent-revoke-confirm"))

    await waitFor(() => {
      const revokeCall = fetchMock.mock.calls.find(
        (c) =>
          (c[0] as string).includes("/admin/consent/company-training-consent/revoke") &&
          (c[1] as RequestInit | undefined)?.method === "POST",
      )
      expect(revokeCall).toBeTruthy()
      const body = JSON.parse((revokeCall?.[1] as RequestInit).body as string)
      expect(body.reason).toBe("Política interna mudou")
    })
  })
})
