/**
 * PolicyEnginePanel — smoke test (Task #904 — code review fix)
 *
 * Verifica:
 *  - chamada para /policy-engine/policies
 *  - render de uma policy
 */
import React from "react"
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import "@testing-library/jest-dom/vitest"

vi.mock("next-intl", () => {
  const tFn = (k: string) => k
  return { useTranslations: () => tFn }
})
vi.mock("@/hooks/company/useCompanyId", () => ({
  useCompanyId: () => ({ companyId: "co-1" }),
}))

import { PolicyEnginePanel } from "@/components/_wedo_internal/governanca/PolicyEnginePanel"

const fetchMock = vi.fn()

beforeEach(() => {
  fetchMock.mockReset()
  fetchMock.mockImplementation((url: string) => {
    if (
      url.endsWith("/api/backend-proxy/policy-engine") ||
      url.includes("/api/backend-proxy/policy-engine?")
    ) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            business_rules: [
              { id: "p1", name: "PCD priority", rule_type: "scoring_boost", is_active: true },
            ],
            rate_limit_rules: [],
            escalation_rules: [
              { id: "e1", name: "Escalate to HR", trigger_type: "fairness_alert", is_active: true },
            ],
            total_business_rules: 1,
            total_rate_limit_rules: 0,
            total_escalation_rules: 1,
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

describe("PolicyEnginePanel", () => {
  it("calls policies endpoint and renders rows", async () => {
    render(<PolicyEnginePanel />)
    await screen.findByTestId("policy-engine-panel")

    await waitFor(() => {
      const urls = fetchMock.mock.calls.map((c) => c[0] as string)
      expect(
        urls.some(
          (u) =>
            u.endsWith("/api/backend-proxy/policy-engine") ||
            u.includes("/api/backend-proxy/policy-engine?"),
        ),
      ).toBe(true)
    })
    expect(screen.getByText("PCD priority")).toBeInTheDocument()
    expect(screen.getByText("Escalate to HR")).toBeInTheDocument()
  })
})
