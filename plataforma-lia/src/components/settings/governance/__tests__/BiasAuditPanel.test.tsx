/**
 * BiasAuditPanel — smoke test (Task #904 — code review fix)
 *
 * Verifica:
 *  - chamada inicial para /fairness-audit/logs
 *  - drill-down: chamada para /bias-audit/job/{id} ao submeter o form
 *  - render da Four-Fifths table com dimensões/grupos/ratio/alert
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

import { BiasAuditPanel } from "@/components/settings/governance/BiasAuditPanel"

const fetchMock = vi.fn()

beforeEach(() => {
  fetchMock.mockReset()
  fetchMock.mockImplementation((url: string) => {
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
                created_at: "2025-01-01T00:00:00Z",
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
            evaluated_at: "2025-01-02T00:00:00Z",
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
    return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) })
  })
  vi.stubGlobal("fetch", fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe("BiasAuditPanel", () => {
  it("loads logs and runs Four-Fifths drill-down", async () => {
    render(<BiasAuditPanel />)
    await screen.findByTestId("bias-audit-panel")

    await waitFor(() => {
      const urls = fetchMock.mock.calls.map((c) => c[0] as string)
      expect(urls.some((u) => u.includes("/api/backend-proxy/fairness-audit/logs"))).toBe(true)
    })
    expect(screen.getByText("j1")).toBeInTheDocument()

    const input = screen.getByTestId("bias-audit-job-input") as HTMLInputElement
    fireEvent.change(input, { target: { value: "j-42" } })
    fireEvent.click(screen.getByTestId("bias-audit-drill-submit"))

    const table = await screen.findByTestId("bias-audit-fourfifths")
    expect(table.textContent).toContain("gender")
    expect(table.textContent).toContain("0.600")
    const urls = fetchMock.mock.calls.map((c) => c[0] as string)
    expect(urls.some((u) => u.includes("/api/backend-proxy/bias-audit/job/j-42"))).toBe(true)
  })
})
