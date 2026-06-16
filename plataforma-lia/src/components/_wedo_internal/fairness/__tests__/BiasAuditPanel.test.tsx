/**
 * BiasAuditPanel — smoke test + T-17 NYC LL144 extension (Wave 1 Agent #3)
 *
 * Verifica:
 *  - chamada inicial para /fairness-audit/logs (backward compat real-time)
 *  - drill-down: chamada para /bias-audit/job/{id} (backward compat)
 *  - render da Four-Fifths table com dimensoes/grupos/ratio/alert (backward compat)
 *  - Tabs canonical: real-time + annual-report + trust-portal
 *  - Annual: load + generate (POST .../annual/generate)
 *  - Trust Portal: toggle Switch (PATCH .../{id}/publish)
 *  - Backward compat: real-time tab continua funcional
 */
import React from "react"
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import "@testing-library/jest-dom/vitest"

vi.mock("next-intl", () => {
  const tFn = (k: string) => k
  return { useTranslations: () => tFn }
})
vi.mock("@/hooks/company/useCompanyId", () => ({
  useCompanyId: () => ({ companyId: "co-1" }),
}))

import { BiasAuditPanel } from "@/components/_wedo_internal/fairness/BiasAuditPanel"

const fetchMock = vi.fn()

function buildAnnualReport(overrides: Record<string, unknown> = {}) {
  return {
    report_id: "rep-2026",
    year: 2026,
    status: "generated",
    dimensions_count: 4,
    four_fifths_pass: true,
    generated_at: "2026-01-15T00:00:00Z",
    is_public: false,
    public_slug: null,
    chi2_p_value: 0.12,
    eeoc_compliant: true,
    ...overrides,
  }
}

beforeEach(() => {
  fetchMock.mockReset()
  fetchMock.mockImplementation((url: string, init?: RequestInit) => {
    const method = init?.method ?? "GET"

    if (url.includes("/fairness-audit/logs")) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            items: [
              {
                id: "f1",
                job_id: "j1",
                category: "gender",
                is_blocked: true,
                blocked_terms: ["x"],
                created_at: "2026-01-01T00:00:00Z",
              },
            ],
          }),
      })
    }
    if (url.includes("/bias-audit/job/")) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            job_id: "j-42",
            evaluated_at: "2026-01-02T00:00:00Z",
            total_candidates: 100,
            has_alerts: true,
            dimensions: [
              {
                dimension: "gender",
                groups: { f: { ratio: 0.6 }, m: { ratio: 1.0 } },
                adverse_impact_ratio: 0.6,
                below_threshold: true,
                alert_level: "warning",
                eeoc_compliant: false,
              },
            ],
          }),
      })
    }
    if (url.includes("/bias-audit/annual/generate") && method === "POST") {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ report_id: "rep-2026", status: "generated" }),
      })
    }
    if (url.match(/\/bias-audit\/annual\/[^/]+\/publish/) && method === "PATCH") {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ report_id: "rep-2026", is_public: true }),
      })
    }
    if (url.includes("/bias-audit/annual")) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            reports: [buildAnnualReport()],
          }),
      })
    }
    return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) })
  })
  vi.stubGlobal("fetch", fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe("BiasAuditPanel — T-17 NYC LL144 extension", () => {
  it("renders 3 tabs (real-time + annual-report + trust-portal)", async () => {
    render(<BiasAuditPanel />)
    await screen.findByTestId("bias-audit-panel")

    expect(screen.getByTestId("bias-audit-tab-realtime")).toBeInTheDocument()
    expect(screen.getByTestId("bias-audit-tab-annual")).toBeInTheDocument()
    expect(screen.getByTestId("bias-audit-tab-trust")).toBeInTheDocument()
  })

  it("preserves real-time tab functionality canonical (backward compat)", async () => {
    render(<BiasAuditPanel />)
    await screen.findByTestId("bias-audit-panel")

    // initial logs fetch happened
    await waitFor(() => {
      const urls = fetchMock.mock.calls.map((c) => c[0] as string)
      expect(urls.some((u) => u.includes("/api/backend-proxy/fairness-audit/logs"))).toBe(true)
    })
    expect(screen.getByText("j1")).toBeInTheDocument()

    // drill-down still works
    const input = screen.getByTestId("bias-audit-job-input") as HTMLInputElement
    fireEvent.change(input, { target: { value: "j-42" } })
    fireEvent.click(screen.getByTestId("bias-audit-drill-submit"))

    const table = await screen.findByTestId("bias-audit-fourfifths")
    expect(table.textContent).toContain("gender")
    expect(table.textContent).toContain("0.600")
    const urls = fetchMock.mock.calls.map((c) => c[0] as string)
    expect(urls.some((u) => u.includes("/api/backend-proxy/bias-audit/job/j-42"))).toBe(true)
  })

  it("fetches existing annual reports on mount (eager load canonical)", async () => {
    render(<BiasAuditPanel />)
    await screen.findByTestId("bias-audit-panel")

    await waitFor(() => {
      const urls = fetchMock.mock.calls.map((c) => c[0] as string)
      expect(
        urls.some(
          (u) =>
            u.includes("/api/backend-proxy/bias-audit/annual") &&
            !u.includes("generate") &&
            !u.includes("publish"),
        ),
      ).toBe(true)
    })
  })

  it("calls generate endpoint on 'Generate Annual Report' click", async () => {
    const user = userEvent.setup()
    render(<BiasAuditPanel />)
    await screen.findByTestId("bias-audit-panel")

    // wait for eager load to finish so reports are in state
    await waitFor(() => {
      const urls = fetchMock.mock.calls.map((c) => c[0] as string)
      expect(urls.some((u) => u.includes("/bias-audit/annual") && !u.includes("generate"))).toBe(true)
    })

    // switch to annual-report tab so generate button is visible
    await user.click(screen.getByTestId("bias-audit-tab-annual"))
    await screen.findByTestId("bias-audit-annual-row-2026")

    await user.click(screen.getByTestId("bias-audit-annual-generate"))

    await waitFor(() => {
      const generateCall = fetchMock.mock.calls.find(
        (c) =>
          typeof c[0] === "string" &&
          (c[0] as string).includes("/bias-audit/annual/generate") &&
          (c[1] as RequestInit | undefined)?.method === "POST",
      )
      expect(generateCall).toBeTruthy()
    })
  })

  it("toggles public status via PATCH .../publish on Trust Portal tab", async () => {
    const user = userEvent.setup()
    render(<BiasAuditPanel />)
    await screen.findByTestId("bias-audit-panel")

    // wait for eager load to populate latestReport
    await waitFor(() => {
      const urls = fetchMock.mock.calls.map((c) => c[0] as string)
      expect(urls.some((u) => u.includes("/bias-audit/annual") && !u.includes("generate"))).toBe(true)
    })

    await user.click(screen.getByTestId("bias-audit-tab-trust"))

    const toggle = await screen.findByTestId("bias-audit-trust-toggle")
    await user.click(toggle)

    await waitFor(() => {
      const publishCall = fetchMock.mock.calls.find(
        (c) =>
          typeof c[0] === "string" &&
          /\/bias-audit\/annual\/[^/]+\/publish/.test(c[0] as string) &&
          (c[1] as RequestInit | undefined)?.method === "PATCH",
      )
      expect(publishCall).toBeTruthy()
    })
  })
})
