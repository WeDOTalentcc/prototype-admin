/**
 * AITransparencyPanel — Wave 1 Agent #2 smoke tests (T-18 EU AI Act Annex III)
 *
 * Cobre:
 *  - render 4 tabs canonical (Art. 13 + decisions + Art. 14 + Annex III)
 *  - fetch GET /api/backend-proxy/ai-transparency/explainability-statement on mount
 *  - empty state quando lista de decisions vem vazia
 *  - POST override endpoint quando user clica em "Override"
 *  - render Model Card + fairness results em technical tab
 */
import React from "react"
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import "@testing-library/jest-dom/vitest"

vi.mock("next-intl", () => {
  const tFn = ((k: string) => k) as unknown as ReturnType<typeof Object>
  return { useTranslations: () => tFn }
})
vi.mock("@/hooks/company/useCompanyId", () => ({
  useCompanyId: () => ({ companyId: "co-1" }),
}))

import { AITransparencyPanel } from "@/components/_wedo_internal/governanca/AITransparencyPanel"

const STATEMENT_FIXTURE = {
  version: "1.0.0",
  updated_at: "2026-05-20T00:00:00Z",
  sections: [
    { id: "where", title: "Where AI operates", content: "Section content where." },
    { id: "why", title: "Why AI is used", content: "Section content why." },
  ],
}

const TECH_FIXTURE = {
  model_card: {
    model_name: "wsi-classifier",
    model_version: "v3.2",
    intended_use: "Triage candidatos",
    training_data_summary: "Anonymized aggregates",
    limitations: ["Não usa demographic data"],
    fairness_results: [
      { dimension: "gender", ratio: 0.92, passes_four_fifths: true },
      { dimension: "age", ratio: 0.71, passes_four_fifths: false },
    ],
    last_evaluation_at: "2026-05-15T00:00:00Z",
  },
  annex_iii_compliance: {
    art9_risk_management: true,
    art10_data_governance: true,
    art11_technical_docs: true,
    art12_record_keeping: true,
    art13_transparency: true,
    art14_human_oversight: true,
    art15_accuracy: false,
  },
}

const DECISIONS_FIXTURE = {
  total: 1,
  items: [
    {
      id: "dec-1",
      candidate_id_masked: "cand-***-42",
      decision_type: "auto_advance",
      criteria_used: ["wsi_score", "experience_match"],
      score: 0.87,
      human_reviewed: false,
      overridden: false,
      created_at: "2026-05-20T00:00:00Z",
    },
  ],
}

const fetchMock = vi.fn()

beforeEach(() => {
  fetchMock.mockReset()
  fetchMock.mockImplementation((url: string, init?: RequestInit) => {
    if (url.includes("/ai-transparency/explainability-statement")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(STATEMENT_FIXTURE),
      })
    }
    if (url.includes("/ai-transparency/automated-decisions")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(DECISIONS_FIXTURE),
      })
    }
    if (url.includes("/ai-transparency/human-oversight/") && init?.method === "POST") {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ overridden: true }),
      })
    }
    if (url.includes("/ai-transparency/technical-documentation")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(TECH_FIXTURE),
      })
    }
    return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) })
  })
  vi.stubGlobal("fetch", fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe("AITransparencyPanel", () => {
  it("renders 4 tabs canonical (explainability + decisions + oversight + technical)", async () => {
    render(<AITransparencyPanel />)
    await screen.findByTestId("ai-transparency-panel")
    expect(screen.getByTestId("ai-transparency-tab-explainability")).toBeInTheDocument()
    expect(screen.getByTestId("ai-transparency-tab-decisions")).toBeInTheDocument()
    expect(screen.getByTestId("ai-transparency-tab-oversight")).toBeInTheDocument()
    expect(screen.getByTestId("ai-transparency-tab-technical")).toBeInTheDocument()
  })

  it("fetches explainability statement on mount and renders sections", async () => {
    render(<AITransparencyPanel />)
    await waitFor(() => {
      const urls = fetchMock.mock.calls.map((c) => c[0] as string)
      expect(
        urls.some((u) => u.includes("/api/backend-proxy/ai-transparency/explainability-statement")),
      ).toBe(true)
    })
    await screen.findByText("Where AI operates")
    expect(screen.getByText("Why AI is used")).toBeInTheDocument()
  })

  it("renders empty state when no decisions are returned", async () => {
    fetchMock.mockImplementationOnce(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve(STATEMENT_FIXTURE) }),
    )
    fetchMock.mockImplementationOnce(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve({ items: [], total: 0 }) }),
    )

    render(<AITransparencyPanel />)
    await screen.findByTestId("ai-transparency-panel")
    fireEvent.click(screen.getByTestId("ai-transparency-tab-decisions"))
    await waitFor(() => {
      expect(screen.getByText("decisions.empty")).toBeInTheDocument()
    })
  })

  it("calls override endpoint with reason on submit", async () => {
    render(<AITransparencyPanel />)
    await screen.findByTestId("ai-transparency-panel")
    fireEvent.click(screen.getByTestId("ai-transparency-tab-oversight"))

    await screen.findByTestId("ai-transparency-override-dec-1")
    fireEvent.click(screen.getByTestId("ai-transparency-override-dec-1"))

    const reasonInput = await screen.findByTestId("ai-transparency-override-reason")
    fireEvent.change(reasonInput, { target: { value: "Falso positivo confirmado por recrutador" } })
    fireEvent.click(screen.getByTestId("ai-transparency-override-submit"))

    await waitFor(() => {
      const overrideCall = fetchMock.mock.calls.find(
        (c) =>
          (c[0] as string).includes("/ai-transparency/human-oversight/dec-1/override") &&
          (c[1] as RequestInit | undefined)?.method === "POST",
      )
      expect(overrideCall).toBeDefined()
      const body = JSON.parse((overrideCall![1] as RequestInit).body as string)
      expect(body.reason).toBe("Falso positivo confirmado por recrutador")
    })
  })

  it("renders Model Card structured data + fairness results in technical tab", async () => {
    render(<AITransparencyPanel />)
    await screen.findByTestId("ai-transparency-panel")
    fireEvent.click(screen.getByTestId("ai-transparency-tab-technical"))

    await screen.findByTestId("ai-transparency-technical")
    expect(screen.getByText("wsi-classifier")).toBeInTheDocument()
    expect(screen.getByText("v3.2")).toBeInTheDocument()
    expect(screen.getByText("Não usa demographic data")).toBeInTheDocument()
    // Fairness table renders dimensions
    expect(screen.getByText("gender")).toBeInTheDocument()
    expect(screen.getByText("0.920")).toBeInTheDocument()
    expect(screen.getByText("age")).toBeInTheDocument()
    expect(screen.getByText("0.710")).toBeInTheDocument()
    // Export PDF button present
    expect(screen.getByTestId("ai-transparency-export-pdf")).toBeInTheDocument()
  })
})
