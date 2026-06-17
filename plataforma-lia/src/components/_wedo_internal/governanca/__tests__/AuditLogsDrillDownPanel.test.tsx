/**
 * AuditLogsDrillDownPanel — smoke test (Task #904 — code review fix)
 *
 * Verifica:
 *  - chamadas para os 3 endpoints (logs, stats, retention-policies)
 *  - render dos cards de stats e das linhas de log
 *  - existência dos controles de filtro (event_type, actor, days, severity),
 *    pagination (next/prev) e link de export CSV.
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

import { AuditLogsDrillDownPanel } from "@/components/_wedo_internal/governanca/AuditLogsDrillDownPanel"

const fetchMock = vi.fn()

beforeEach(() => {
  fetchMock.mockReset()
  fetchMock.mockImplementation((url: string) => {
    if (url.includes("/audit-logs/stats")) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({ total_logs: 42, recent_24h: 5, by_severity: { high: 2, critical: 1 } }),
      })
    }
    if (url.includes("/audit-logs/retention-policies")) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            policies: [{ id: "p1", category: "auth", retention_days: 365 }],
          }),
      })
    }
    if (url.includes("/audit-logs?")) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            total: 1,
            logs: [
              {
                id: "l1",
                event_type: "user.login",
                severity: "high",
                actor_email: "a@b.co",
                created_at: "2025-01-01T00:00:00Z",
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

describe("AuditLogsDrillDownPanel", () => {
  it("calls 3 endpoints, renders rows, filters and pagination", async () => {
    render(<AuditLogsDrillDownPanel />)
    await screen.findByTestId("audit-logs-panel")

    await waitFor(() => {
      const urls = fetchMock.mock.calls.map((c) => c[0] as string)
      const listUrl = urls.find((u) => u.startsWith("/api/backend-proxy/audit-logs?"))
      expect(listUrl).toBeDefined()
      expect(listUrl).toContain("date_from=")
      expect(listUrl).toContain("limit=")
      expect(listUrl).toContain("offset=")
      expect(urls.some((u) => u.includes("/audit-logs/stats"))).toBe(true)
      expect(urls.some((u) => u.includes("/audit-logs/retention-policies"))).toBe(true)
    })

    expect(screen.getByText("user.login")).toBeInTheDocument()
    expect(screen.getByTestId("audit-logs-event-type")).toBeInTheDocument()
    expect(screen.getByTestId("audit-logs-actor")).toBeInTheDocument()
    expect(screen.getByTestId("audit-logs-days")).toBeInTheDocument()
    expect(screen.getByTestId("audit-logs-severity-filter")).toBeInTheDocument()
    expect(screen.getByTestId("audit-logs-prev")).toBeDisabled()
    expect(screen.getByTestId("audit-logs-next")).toBeInTheDocument()
    const exportLink = screen.getByTestId("audit-logs-export") as HTMLAnchorElement
    expect(exportLink.getAttribute("href")).toContain("/api/backend-proxy/audit-logs/export")
    expect(screen.getByTestId("audit-logs-retention")).toBeInTheDocument()
  })
})
