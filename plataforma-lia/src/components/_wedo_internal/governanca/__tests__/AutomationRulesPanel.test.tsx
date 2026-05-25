/**
 * AutomationRulesPanel — smoke test (Task #904 — code review fix)
 *
 * Verifica:
 *  - chamada para /automation-rules/company/{companyId}
 *  - render das colunas extras: Executions, Last run
 *  - toggle dispara POST /automation-rules/{ruleId}/toggle
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

import { AutomationRulesPanel } from "@/components/_wedo_internal/governanca/AutomationRulesPanel"

const fetchMock = vi.fn()

beforeEach(() => {
  fetchMock.mockReset()
  fetchMock.mockImplementation((url: string, init?: RequestInit) => {
    if (url.includes("/automation-rules/company/co-1") && (!init || init.method !== "POST")) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve([
            {
              id: "r1",
              name: "Auto-screen",
              trigger_type: "candidate.applied",
              priority: 1,
              enabled: true,
              execution_count: 99,
              last_executed_at: "2025-01-01T00:00:00Z",
              last_execution_status: "success",
            },
          ]),
      })
    }
    if (url.includes("/automation-rules/r1/toggle")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ ok: true }) })
    }
    return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) })
  })
  vi.stubGlobal("fetch", fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe("AutomationRulesPanel", () => {
  it("lists rules with executions/last-run and toggles", async () => {
    render(<AutomationRulesPanel />)
    await screen.findByTestId("automation-rules-panel")

    await waitFor(() => {
      expect(screen.getByText("Auto-screen")).toBeInTheDocument()
    })
    expect(screen.getAllByText("99").length).toBeGreaterThan(0)
    expect(screen.getByText("success")).toBeInTheDocument()

    fireEvent.click(screen.getByTestId("automation-rule-toggle-r1"))
    await waitFor(() => {
      const urls = fetchMock.mock.calls.map((c) => c[0] as string)
      expect(urls.some((u) => u.includes("/automation-rules/r1/toggle"))).toBe(true)
    })
  })
})
