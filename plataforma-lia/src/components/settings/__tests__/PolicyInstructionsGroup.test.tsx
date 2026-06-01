/**
 * PolicyInstructionsGroup tests (V2.2) — 7 instruções de processo na superfície
 * de LIA & Personalização, salvando em policy_instructions via /instructions.
 */
import React from "react"
import { describe, test, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

const mockFetch = vi.fn()
global.fetch = mockFetch as unknown as typeof fetch
vi.mock("@/hooks/settings/useSettingsBroadcast", () => ({
  SETTINGS_QUERY_KEYS: { hiringPolicy: () => ["hiring-policy"] },
  dispatchSettingsUpdate: vi.fn(),
}))

import { PolicyInstructionsGroup, PROCESS_INSTRUCTIONS } from "../PolicyInstructionsGroup"

function renderGroup(props = {}) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(<QueryClientProvider client={qc}><PolicyInstructionsGroup {...props} /></QueryClientProvider>)
}

describe("PolicyInstructionsGroup", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockResolvedValue({ ok: true, status: 200, json: async () => ({ policy_instructions: {} }) })
  })

  test("exposes exactly the 7 process concepts (no redundant ones)", () => {
    const keys = PROCESS_INSTRUCTIONS.map((p) => p.key)
    expect(keys).toHaveLength(7)
    for (const removed of ["diversity_inclusion_guidelines", "remote_work_policy", "salary_negotiation_policy", "communication_window"]) {
      expect(keys).not.toContain(removed)
    }
  })

  test("renders all 7 instruction cards", async () => {
    renderGroup()
    await waitFor(() => {
      for (const p of PROCESS_INSTRUCTIONS) {
        expect(screen.getByTestId(`instruction-block-${p.key}`), `missing ${p.key}`).toBeTruthy()
      }
    })
  })

  test("read-only disables textareas", async () => {
    renderGroup({ isReadOnly: true })
    await waitFor(() => {
      const ta = screen.getByTestId("instruction-block-no_show_policy").querySelector("textarea")
      expect(ta?.disabled).toBe(true)
    })
  })
})
