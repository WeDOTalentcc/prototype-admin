/**
 * Q4.2 Sandbox "Testar antes de ativar" — AgentSandboxPanel + AgentSandboxInline.
 *
 * Garante (AUDIT 7 gap C1 + Fase 3 Sprint 3 inline):
 *  - banner "MODO SIMULAÇÃO" renderiza (cor distinta, role=status)
 *  - chips de mensagens-exemplo de RH disparam o dry-run num clique (Sprint 3 T3)
 *  - simular chama POST /custom-agents/{id}/dry-run e exibe would_do_actions
 *  - "Enviaria…/Moveria…" aparecem a partir das ações interceptadas
 *  - CTA "Ativar agente" chama onActivate após o recrutador validar
 *  - reusa DecisionTreeBody (mockado) — sem viewer paralelo
 */
import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useTranslations: () => {
    const t = (key: string, vals?: Record<string, unknown>) =>
      vals ? `${key}:${JSON.stringify(vals)}` : key
    t.has = (key: string) => key.startsWith("wouldDoVerb.")
    return t
  },
}))

vi.mock("@/hooks/company/use-ai-persona", () => ({
  useAiPersona: () => ({ persona: { name: "Aria" } }),
}))

// Reuso canonical do DecisionTreeBody — mockado pra isolar o painel.
vi.mock("../../decision-tree/DecisionTreeDrawer", () => ({
  DecisionTreeBody: ({ agentDisplayName }: { agentDisplayName: string }) => (
    <div data-testid="mock-decision-tree-body">{agentDisplayName}</div>
  ),
}))

import { AgentSandboxPanel, AgentSandboxInline } from "../AgentSandboxPanel"
import type { CustomAgent } from "../types"

const AGENT = {
  id: "agent-1",
  name: "Triador",
  domain: "screening",
  category: "screening",
  description: "",
  context_level: "full",
  max_steps: 8,
  allowed_tools: ["send_email", "search_candidates"],
  total_executions: 0,
  avg_confidence: 0,
} as unknown as CustomAgent

const DRY_RUN_RESPONSE = {
  agent_id: "agent-1",
  agent_name: "Triador",
  response: "Avaliei o candidato e recomendo avançar.",
  confidence: 0.8,
  would_do_actions: [
    { tool: "send_email", args: { candidate_id: "cand-1", subject: "Convite" } },
    { tool: "move_candidate", args: { candidate_id: "cand-1", stage: "entrevista" } },
  ],
  reasoning_trace: [{ step_type: "thought", label: "Pensando", data_fields_accessed: [] }],
  tool_calls: ["send_email", "move_candidate"],
  execution_time_ms: 1200,
  tokens_input: 100,
  tokens_output: 50,
  model_used: "gpt-4o",
  dry_run: true,
}

beforeEach(() => {
  vi.restoreAllMocks()
  Object.defineProperty(window, "localStorage", {
    value: { getItem: () => "tok", setItem: () => {}, removeItem: () => {} },
    writable: true,
  })
})

describe("AgentSandboxPanel (Dialog wrapper)", () => {
  it("renders the SIMULATION banner with role=status", () => {
    render(<AgentSandboxPanel agent={AGENT} open onClose={() => {}} onActivate={() => {}} />)
    const banner = screen.getByTestId("sandbox-simulation-banner")
    expect(banner).toBeTruthy()
    expect(banner.getAttribute("role")).toBe("status")
    expect(banner.textContent).toContain("simulationBanner")
  })

  it("simulates and renders would-do actions from the dry-run response", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => DRY_RUN_RESPONSE,
    })
    vi.stubGlobal("fetch", fetchMock)

    render(<AgentSandboxPanel agent={AGENT} open onClose={() => {}} onActivate={() => {}} />)

    fireEvent.change(screen.getByTestId("sandbox-message-input"), {
      target: { value: "Avalie o João" },
    })
    fireEvent.click(screen.getByTestId("sandbox-simulate-button"))

    await waitFor(() => expect(screen.getByTestId("sandbox-result")).toBeTruthy())

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/backend-proxy/custom-agents/agent-1/dry-run",
      expect.objectContaining({ method: "POST" }),
    )

    const list = screen.getByTestId("sandbox-would-do-list")
    expect(list.querySelectorAll("li").length).toBe(2)
    expect(list.textContent).toContain("wouldDoVerb.send_email")
    expect(list.textContent).toContain("wouldDoVerb.move_candidate")

    expect(screen.getByTestId("mock-decision-tree-body")).toBeTruthy()
  })

  it("calls onActivate when the recruiter clicks 'Ativar agente'", async () => {
    const onActivate = vi.fn()
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => DRY_RUN_RESPONSE }))

    render(<AgentSandboxPanel agent={AGENT} open onClose={() => {}} onActivate={onActivate} />)

    fireEvent.change(screen.getByTestId("sandbox-message-input"), { target: { value: "x" } })
    fireEvent.click(screen.getByTestId("sandbox-simulate-button"))
    await waitFor(() => expect(screen.getByTestId("sandbox-activate-button")).toBeTruthy())

    fireEvent.click(screen.getByTestId("sandbox-activate-button"))
    expect(onActivate).toHaveBeenCalledWith(AGENT)
  })

  it("shows empty state when no write actions would run", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ ...DRY_RUN_RESPONSE, would_do_actions: [] }),
      }),
    )
    render(<AgentSandboxPanel agent={AGENT} open onClose={() => {}} onActivate={() => {}} />)
    fireEvent.change(screen.getByTestId("sandbox-message-input"), { target: { value: "x" } })
    fireEvent.click(screen.getByTestId("sandbox-simulate-button"))
    await waitFor(() => expect(screen.getByTestId("sandbox-no-actions")).toBeTruthy())
  })
})

describe("AgentSandboxInline (Fase 3 Sprint 3 — test-as-you-build inline)", () => {
  it("renders WITHOUT its own Dialog (no nested modal)", () => {
    const { container } = render(<AgentSandboxInline agent={AGENT} onActivate={() => {}} />)
    // No Radix dialog role rendered by the inline body itself.
    expect(container.querySelector('[role="dialog"]')).toBeNull()
    expect(screen.getByTestId("agent-sandbox-inline")).toBeTruthy()
    expect(screen.getByTestId("sandbox-simulation-banner")).toBeTruthy()
  })

  it("renders RH example chips for the agent category", () => {
    render(<AgentSandboxInline agent={AGENT} onActivate={() => {}} />)
    const chips = screen.getByTestId("sandbox-example-chips")
    expect(chips).toBeTruthy()
    // screening category → 3 curated examples
    expect(screen.getByTestId("sandbox-example-chip-seniorPython")).toBeTruthy()
    expect(screen.getByTestId("sandbox-example-chip-weakProfile")).toBeTruthy()
    expect(screen.getByTestId("sandbox-example-chip-midGeneralist")).toBeTruthy()
  })

  it("clicking an example chip triggers the dry-run in one click", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => DRY_RUN_RESPONSE })
    vi.stubGlobal("fetch", fetchMock)

    render(<AgentSandboxInline agent={AGENT} onActivate={() => {}} />)
    fireEvent.click(screen.getByTestId("sandbox-example-chip-seniorPython"))

    await waitFor(() => expect(screen.getByTestId("sandbox-result")).toBeTruthy())
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/backend-proxy/custom-agents/agent-1/dry-run",
      expect.objectContaining({ method: "POST" }),
    )
    // The chip label was used as the simulation message body.
    const body = JSON.parse((fetchMock.mock.calls[0][1] as { body: string }).body)
    expect(body.message).toContain("examples.screening.seniorPython")
  })

  it("exposes the 'Ativar agente' CTA after a simulation", async () => {
    const onActivate = vi.fn()
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => DRY_RUN_RESPONSE }))
    render(<AgentSandboxInline agent={AGENT} onActivate={onActivate} />)
    fireEvent.click(screen.getByTestId("sandbox-example-chip-weakProfile"))
    await waitFor(() => expect(screen.getByTestId("sandbox-activate-button")).toBeTruthy())
    fireEvent.click(screen.getByTestId("sandbox-activate-button"))
    expect(onActivate).toHaveBeenCalledWith(AGENT)
  })
})
