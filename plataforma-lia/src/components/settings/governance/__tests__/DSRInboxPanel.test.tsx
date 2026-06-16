/**
 * DSRInboxPanel — smoke test (Task #904 — code review fix)
 *
 * Verifica:
 *  - chamadas para /data-subject-requests e /data-subject-requests/stats
 *  - render de uma DSR row + botão Export CSV (habilita com items)
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

import { DSRInboxPanel } from "@/components/settings/governance/DSRInboxPanel"

const fetchMock = vi.fn()

beforeEach(() => {
  fetchMock.mockReset()
  fetchMock.mockImplementation((url: string) => {
    if (url.includes("/data-subject-requests/stats")) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            total_requests: 1,
            pending_requests: 1,
            processing_requests: 0,
            overdue_requests: 0,
            sla_compliance_rate: 1,
          }),
      })
    }
    if (url.includes("/data-subject-requests")) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            items: [
              {
                id: "dsr-aaaaaaaa-bbbb",
                request_type: "access",
                status: "pending",
                subject_email: "x@y.co",
                created_at: "2025-01-01T00:00:00Z",
                sla_deadline: "2025-01-30T00:00:00Z",
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

describe("DSRInboxPanel", () => {
  it("calls list+stats endpoints and shows export button", async () => {
    render(<DSRInboxPanel />)
    await screen.findByTestId("dsr-inbox-panel")

    await waitFor(() => {
      const urls = fetchMock.mock.calls.map((c) => c[0] as string)
      expect(urls.some((u) => u.startsWith("/api/backend-proxy/data-subject-requests"))).toBe(true)
      expect(urls.some((u) => u.includes("/data-subject-requests/stats"))).toBe(true)
    })
    expect(screen.getByText("x@y.co")).toBeInTheDocument()
    const exportBtn = screen.getByTestId("dsr-export-csv") as HTMLButtonElement
    expect(exportBtn).toBeEnabled()
  })
})
