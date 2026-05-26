/**
 * Sprint 7B-3b Part 2 v2 (2026-05-26) — AgentsTab swap canonical test.
 *
 * Garante que AgentsTab chama /custom-agents?category=sourcing (NUNCA mais
 * /sourcing-agents) e timeline via /custom-agents/{id}/timeline.
 */
import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import AgentsTab from "../AgentsTab"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

describe("AgentsTab — Sprint 7B-3b Part 2 v2 endpoint swap", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("chama /api/backend-proxy/custom-agents?category=sourcing com talent_pool_id + job_id", async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.startsWith("/api/backend-proxy/custom-agents?")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ agents: [], total: 0 }),
        })
      }
      return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) })
    })
    vi.stubGlobal("fetch", fetchMock)

    render(
      <AgentsTab
        jobId="job-xyz"
        talentPoolId="pool-abc"
        onStartCalibration={vi.fn()}
        onCreateAgent={vi.fn()}
      />,
    )

    await waitFor(() => expect(fetchMock).toHaveBeenCalled())

    const calledUrls = fetchMock.mock.calls.map((c) => c[0] as string)
    const listCall = calledUrls.find((u) => u.includes("/custom-agents?"))
    expect(listCall).toBeTruthy()
    expect(listCall).toContain("category=sourcing")
    expect(listCall).toContain("talent_pool_id=pool-abc")
    expect(listCall).toContain("job_id=job-xyz")
    // CRITICAL: nao chamou endpoint legacy
    expect(calledUrls.find((u) => u.includes("/sourcing-agents"))).toBeUndefined()
  })

  it("usa CustomAgent.name no render (nao agent_name) + endpoint timeline canonical", async () => {
    const fakeAgent = {
      id: "agent-1",
      company_id: "comp-1",
      name: "Captacao Eng",
      role: "sourcing_agent",
      description: null,
      system_prompt: "",
      allowed_tools: [],
      domain: "sourcing",
      icon: "Bot",
      status: "active",
      config: { calibration_v: 2 },
      max_steps: 10,
      temperature: 0.7,
      model_override: null,
      enable_memory: false,
      context_level: "standard",
      excluded_tools: [],
      category: "sourcing",
      runtime_metrics: { profiles_viewed: 1, profiles_approved: 1, profiles_rejected: 0 },
      search_strategy: { required_skills: ["Python"] },
      outreach_config: null,
      legacy_sourcing_agent_id: null,
      total_executions: 0,
      avg_confidence: 0,
      last_executed_at: null,
      created_at: "2026-05-25T00:00:00Z",
      updated_at: null,
    }

    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/custom-agents/agent-1/timeline")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ timeline: [] }),
        })
      }
      if (url.startsWith("/api/backend-proxy/custom-agents?")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ agents: [fakeAgent], total: 1 }),
        })
      }
      return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) })
    })
    vi.stubGlobal("fetch", fetchMock)

    render(
      <AgentsTab
        onStartCalibration={vi.fn()}
        onCreateAgent={vi.fn()}
      />,
    )

    await waitFor(() => expect(screen.getByText("Captacao Eng")).toBeTruthy())

    const calledUrls = fetchMock.mock.calls.map((c) => c[0] as string)
    const timelineCall = calledUrls.find((u) => u.includes("/timeline"))
    expect(timelineCall).toContain("/custom-agents/agent-1/timeline")
    expect(timelineCall).not.toContain("/sourcing-agents")
  })

  it("erro de backend nao expoe stack — exibe mensagem amigavel", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: "boom" }),
    })
    vi.stubGlobal("fetch", fetchMock)

    render(
      <AgentsTab
        onStartCalibration={vi.fn()}
        onCreateAgent={vi.fn()}
      />,
    )

    await waitFor(() =>
      expect(screen.getByText(/Nao foi possivel carregar/i)).toBeTruthy(),
    )
  })
})
